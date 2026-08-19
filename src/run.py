"""Execute every cell in the grid. Writes a new timestamped JSONL; never overwrites."""

from __future__ import annotations

import json
import os
import re
import sys
import time
from datetime import datetime, timezone

from prompts import ROOT, expand_grid, load_config

REFUSAL = ("i can't", "i cannot", "i won't", "as an ai", "i am unable")


def parse_choice(text: str | None, left_id: str, right_id: str) -> str:
    """Map a response to one option id, or unparsed. No guessing."""
    if not text or not text.strip():
        return "unparsed"
    raw = text.strip()
    if any(p in raw.lower() for p in REFUSAL):
        return "unparsed"
    tokens = re.findall(r"[A-Za-z0-9]+", raw)
    ids = {left_id.upper(): left_id, right_id.upper(): right_id}
    hit = [ids[t.upper()] for t in tokens if t.upper() in ids]
    if tokens and len(hit) == 1 and tokens[0].upper() in ids:
        return hit[0]
    return "unparsed"


def complete(prompt: str, cfg: dict, seed: int) -> str:
    kwargs = dict(
        model=cfg["model"], messages=[{"role": "user", "content": prompt}],
        temperature=float(cfg["temperature"]), max_tokens=int(cfg.get("max_tokens", 8)), seed=seed,
    )
    if cfg["backend"] == "openai":
        from openai import OpenAI
        key = os.environ.get("OPENAI_API_KEY")
        if not key:
            sys.exit("Set OPENAI_API_KEY")
        client = OpenAI(api_key=key, base_url=cfg.get("openai_base_url"))
    elif cfg["backend"] == "huggingface":
        from huggingface_hub import InferenceClient
        key = os.environ.get("HF_TOKEN") or os.environ.get("HUGGINGFACE_HUB_TOKEN")
        if not key:
            sys.exit("Set HF_TOKEN")
        client = InferenceClient(api_key=key, provider=cfg.get("hf_provider"))
    else:
        sys.exit(f"Unknown backend: {cfg['backend']}")
    try:
        resp = client.chat.completions.create(**kwargs)
    except Exception:
        kwargs.pop("seed", None)
        resp = client.chat.completions.create(**kwargs)
    return resp.choices[0].message.content or ""


def main() -> None:
    cfg, grid = load_config(), expand_grid(load_config())
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out = ROOT / "results" / f"run_{stamp}.jsonl"
    out.parent.mkdir(exist_ok=True)
    print(f"Writing {len(grid)} rows to {out}", file=sys.stderr)
    with out.open("w") as f:
        for i, cond in enumerate(grid, 1):
            seed = int(cfg["seed"]) + cond["sample_index"]
            text, err = "", None
            for attempt in range(3):
                try:
                    text, err = complete(cond["prompt"], cfg, seed), None
                    break
                except Exception as exc:
                    err = exc
                    time.sleep(2 * (attempt + 1))
            if err:
                sys.exit(f"API failed after retries: {err}")
            parsed = parse_choice(text, cond["left_id"], cond["right_id"])
            f.write(json.dumps({
                **cond, "raw_response": text, "parsed_choice": parsed,
                "model": cfg["model"], "backend": cfg["backend"],
                "temperature": cfg["temperature"], "seed": seed,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }) + "\n")
            f.flush()
            print(f"[{i}/{len(grid)}] {cond['pair']} {cond['order']} "
                  f"{cond['wording']} s{cond['sample_index']} -> {parsed}", file=sys.stderr)
    print(out)


if __name__ == "__main__":
    main()
