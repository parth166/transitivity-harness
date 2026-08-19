"""Build the full condition grid from YAML. No item names live here."""

from __future__ import annotations

import itertools
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG = ROOT / "config" / "triples.yaml"


def load_config(path: Path | str = DEFAULT_CONFIG) -> dict:
    with open(path) as f:
        return yaml.safe_load(f)


def expand_grid(cfg: dict) -> list[dict]:
    """One dict per call: pair, order, wording, sample_index, prompt, plus ids."""
    conditions: list[dict] = []
    n = int(cfg["n_samples"])
    for triple in cfg["triples"]:
        for a, b in itertools.combinations(triple["options"], 2):
            pair = f"{a['id']}-{b['id']}"
            for order, (left, right) in (("ab", (a, b)), ("ba", (b, a))):
                for wording in cfg["wordings"]:
                    prompt = wording["template"].format(
                        left_id=left["id"],
                        right_id=right["id"],
                        left_text=left["text"],
                        right_text=right["text"],
                    )
                    for sample_index in range(n):
                        conditions.append(
                            {
                                "triple_id": triple["id"],
                                "pair": pair,
                                "order": order,
                                "wording": wording["id"],
                                "polarity": wording["polarity"],
                                "sample_index": sample_index,
                                "left_id": left["id"],
                                "right_id": right["id"],
                                "prompt": prompt,
                            }
                        )
    return conditions
