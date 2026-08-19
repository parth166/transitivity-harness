import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from prompts import expand_grid, load_config

CFG = load_config()
GRID = expand_grid(CFG)


def test_grid_is_the_full_cross():
    n_triples = len(CFG["triples"])
    n_wordings = len(CFG["wordings"])
    expected = n_triples * 3 * 2 * n_wordings * CFG["n_samples"]
    assert len(GRID) == expected


def test_pairs_orders_wordings_balanced():
    expected_per_pair = CFG["n_samples"] * len(CFG["wordings"]) * 2
    pairs = {row["pair"] for row in GRID}
    assert len(pairs) == 3 * len(CFG["triples"])
    for pair in pairs:
        rows = [r for r in GRID if r["pair"] == pair]
        assert len(rows) == expected_per_pair
        assert {r["order"] for r in rows} == {"ab", "ba"}
        assert {r["wording"] for r in rows} == {w["id"] for w in CFG["wordings"]}
        assert {r["sample_index"] for r in rows} == set(range(CFG["n_samples"]))


def test_each_condition_is_traceable():
    keys = {"pair", "order", "wording", "sample_index", "prompt"}
    seen = set()
    for row in GRID:
        assert keys <= row.keys()
        ident = (row["triple_id"], row["pair"], row["order"], row["wording"], row["sample_index"])
        assert ident not in seen
        seen.add(ident)
        assert row["left_id"] in row["prompt"] and row["right_id"] in row["prompt"]


def test_new_triple_needs_no_source_edit(tmp_path):
    extra = yaml.safe_load(Path("config/triples.yaml").read_text())
    extra["triples"].append(
        {
            "id": "synthetic",
            "options": [
                {"id": "X", "text": "option x matched form"},
                {"id": "Y", "text": "option y matched form"},
                {"id": "Z", "text": "option z matched form"},
            ],
        }
    )
    path = tmp_path / "triples.yaml"
    path.write_text(yaml.dump(extra))
    grown = expand_grid(yaml.safe_load(path.read_text()))
    assert len(grown) == 2 * len(GRID)
    assert any(r["triple_id"] == "synthetic" for r in grown)
