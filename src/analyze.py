"""Metrics over a run log. Unparsed rows are counted, never dropped or imputed."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd
from scipy.stats import chi2_contingency, fisher_exact

from prompts import ROOT


def load_rows(path: Path) -> pd.DataFrame:
    df = pd.DataFrame(json.loads(line) for line in path.read_text().splitlines() if line)
    other = df.apply(lambda r: r.right_id if r.parsed_choice == r.left_id else r.left_id, axis=1)
    pref = df["parsed_choice"].where(df["polarity"] == "prefer", other)
    df["inferred"] = pref.where(df["parsed_choice"] != "unparsed", "unparsed")
    df["canon_first"] = df["pair"].str.split("-").str[0]
    return df


def _first(df: pd.DataFrame) -> pd.Series:
    ok = df[df["inferred"] != "unparsed"]
    return ok["inferred"] == ok["canon_first"]


def preference_table(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for pair, g in df.groupby("pair", sort=False):
        p = _first(g)
        n, k = int(p.size), int(p.sum())
        a, b = pair.split("-")
        rows.append({"pair": pair, "n_parsed": n, "prefer_first": k,
                     "prop_first": k / n if n else float("nan"),
                     "direction": f"{a} > {b}" if n and k / n > 0.5 else f"{a} < {b}"})
    return pd.DataFrame(rows)


def intransitivity(df: pd.DataFrame):
    """One triple per (wording, sample_index); both orders must agree."""
    recs, splits = [], 0
    keys = ["triple_id", "wording", "sample_index"]
    for key, g in df.groupby(keys, sort=False):
        prefs, split, missing = {}, False, False
        for pair, pg in g.groupby("pair"):
            parsed = pg.loc[pg["inferred"] != "unparsed", "inferred"]
            if len(parsed) < 2:
                missing = True
            elif parsed.nunique() > 1:
                split = True
            else:
                prefs[pair] = parsed.iloc[0]
        if missing:
            continue
        if split:
            splits += 1
            recs.append({**dict(zip(keys, key)), "cycle": False, "status": "order_split"})
            continue
        if len(prefs) < 3:
            continue
        wins = set()
        for pair, w in prefs.items():
            a, b = pair.split("-")
            wins.add((w, b if w == a else a))
        x, y, z = sorted({p for pair in prefs for p in pair.split("-")})
        cycle = ((x, y) in wins and (y, z) in wins and (z, x) in wins) or (
            (x, z) in wins and (z, y) in wins and (y, x) in wins)
        recs.append({**dict(zip(keys, key)), "cycle": cycle, "status": "complete"})
    detail = pd.DataFrame(recs)
    done = detail[detail["status"] == "complete"] if len(detail) else detail
    n_c, n = (int(done["cycle"].sum()), len(done)) if len(done) else (0, 0)
    return detail, (n_c / n if n else float("nan")), n_c, n, splits


def order_effect(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for pair, g in df.groupby("pair", sort=False):
        ok = g[g["inferred"] != "unparsed"]
        ab, ba = _first(ok[ok["order"] == "ab"]), _first(ok[ok["order"] == "ba"])
        table = [[int(ab.sum()), int((~ab).sum())], [int(ba.sum()), int((~ba).sum())]]
        rows.append({"pair": pair,
                     "P(first|ab)": ab.mean() if len(ab) else float("nan"),
                     "P(first|ba)": ba.mean() if len(ba) else float("nan"),
                     "delta": (ab.mean() - ba.mean()) if len(ab) and len(ba) else float("nan"),
                     "p_fisher": fisher_exact(table)[1] if len(ab) and len(ba) else float("nan")})
    return pd.DataFrame(rows)


def wording_effect(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for pair, g in df.groupby("pair", sort=False):
        props, table = {}, []
        for w, wg in g[g["inferred"] != "unparsed"].groupby("wording"):
            pf = _first(wg)
            props[w] = float(pf.mean()) if len(pf) else float("nan")
            table.append([int(pf.sum()), int((~pf).sum())])
        cols = [sum(r[j] for r in table) for j in range(2)] if table else []
        try:
            pval = chi2_contingency(table)[1] if len(table) >= 2 and all(cols) else float("nan")
        except ValueError:
            pval = float("nan")
        rows.append({"pair": pair,
                     **{f"P({w})": props.get(w, float("nan")) for w in ("direct", "indirect", "reversed")},
                     "range": max(props.values()) - min(props.values()) if props else float("nan"),
                     "p_chi2": pval})
    return pd.DataFrame(rows)


def polarity_consistency(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for pair, g in df.groupby("pair", sort=False):
        merged = g[(g["polarity"] == "prefer") & (g["inferred"] != "unparsed")].merge(
            g[(g["polarity"] == "reject") & (g["inferred"] != "unparsed")],
            on=["order", "sample_index"], suffixes=("_p", "_r"))
        n = len(merged)
        rate = float((merged["inferred_p"] == merged["inferred_r"]).mean()) if n else float("nan")
        rows.append({"pair": pair, "n": n, "match_rate": rate})
    return pd.DataFrame(rows)


def render(df: pd.DataFrame, path: Path) -> str:
    pref, order, wording, polar = preference_table(df), order_effect(df), wording_effect(df), polarity_consistency(df)
    detail, rate, n_c, n_complete, n_split = intransitivity(df)
    n, n_unp = len(df), int((df["parsed_choice"] == "unparsed").sum())
    model = df["model"].iloc[0] if n else "?"
    detail_md = detail.to_markdown(index=False) if len(detail) else "_No complete triples._"
    return "\n".join([
        f"# Transitivity summary (`{path.name}`)",
        "",
        f"Model: `{model}`. Rows: {n}. Unparsed: {n_unp}/{n} = {n_unp / n:.3f}." if n else "Empty log.",
        "",
        "## Preference direction (inferred, all conditions)", "",
        pref.to_markdown(index=False, floatfmt=".3f"), "",
        "## Intransitivity", "",
        f"Matched triples are `(wording, sample_index)` after both orders agree. "
        f"Cycle rate: **{n_c}/{n_complete} = {rate:.3f}**. Order-split (excluded): {n_split}.",
        "", detail_md, "",
        "## Order effect", "",
        "Δ = P(canonical first | ab) − P(canonical first | ba). Fisher exact; per-cell *n* is small.",
        "", order.to_markdown(index=False, floatfmt=".3f"), "",
        "## Wording effect", "",
        "Range = max − min P(canonical first) across frames. χ² on 3×2 counts; expected cells often < 5.",
        "", wording.to_markdown(index=False, floatfmt=".3f"), "",
        "## Polarity consistency", "",
        "Inferred-preference match rate, reversed vs prefer frames, aligned on `(order, sample_index)`.",
        "", polar.to_markdown(index=False, floatfmt=".3f"), "",
    ]) + "\n"


def main() -> None:
    src = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "results" / "example_run.jsonl"
    dest = Path(sys.argv[2]) if len(sys.argv) > 2 else ROOT / "results" / "example_summary.md"
    dest.parent.mkdir(exist_ok=True)
    md = render(load_rows(src), src)
    dest.write_text(md)
    print(md, end="")
    print(f"Wrote {dest}", file=sys.stderr)


if __name__ == "__main__":
    main()
