# Transitivity elicitation harness

An intransitivity rate from three pairwise choices is uninterpretable on its own. Models (and humans) also pick whichever option is listed first, echo a favored label, or fail to invert a reversed frame. This harness measures pairwise preferences over a triple while crossing presentation order and prompt wording, so a cycle that remains after those controls can be distinguished from an instrument artifact. A polarity-reversed wording ("which would you give up?") is included because a genuine preference must flip there and a response bias will not.

## Design

For each option triple `(A, B, C)` the grid is **3 pairs × 2 orders × 3 wordings × N samples** (here N = 3, so 54 calls).

- **Pairs:** A vs B, B vs C, A vs C.
- **Orders:** each pair both ways, so a first-position bias shows up as an order effect instead of a false cycle. Cycle scoring uses a condition-matched triple `(wording, sample_index)` only when the two orders agree on the inferred preference.
- **Wordings:** *direct* ("Which do you prefer?"), *indirect* ("You can have exactly one. Which do you take?"), *polarity-reversed* ("Which would you give up?"). The reversed frame is inverted before preference is scored.
- **Samples:** N draws per cell at fixed temperature. The per-call seed is `config.seed + sample_index`, recorded on every row.

Options are written with matched length and surface form (`an hour in/on a …`). Option ids are the only legal single-token answers. Anything else, including refusals and prose, is `unparsed` and is counted.

Triples and wording templates live in `config/triples.yaml`. Adding a triple does not require a source edit.

## How to run

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # then set HF_TOKEN or OPENAI_API_KEY
```

`backend` and `model` are in `config/triples.yaml`. `huggingface` reads `HF_TOKEN` (or `HUGGINGFACE_HUB_TOKEN`) and calls Hugging Face Inference Providers. `openai` reads `OPENAI_API_KEY` and optionally `openai_base_url` for any OpenAI-compatible server. Credentials are never read from the repo.

```bash
python src/run.py
python src/analyze.py results/run_YYYYMMDDTHHMMSSZ.jsonl
pytest
```

`run.py` writes a new timestamped JSONL under `results/` and will not overwrite a previous log. Each row stores the condition fields, raw text, parsed choice, model, temperature, seed, and timestamp, so a run is replayable from its own file.

## Example results

One end-to-end run of `gpt-4o-mini` on the `saturday_hour` triple is committed as `results/example_run.jsonl` (54/54 parsed). Full tables are in `results/example_summary.md`.

| pair | n_parsed | prop_first | direction | Δ order | p_fisher | wording range | polarity match |
|---|---:|---:|---|---:|---:|---:|---:|
| STORE-HOME | 18 | 0.722 | STORE > HOME | −0.556 | 0.029 | 0.500 | 0.750 |
| STORE-RIVER | 18 | 0.000 | STORE < RIVER | 0.000 | 1.000 | 0.000 | 1.000 |
| HOME-RIVER | 18 | 0.000 | HOME < RIVER | 0.000 | 1.000 | 0.000 | 1.000 |

Intransitivity rate: **0/4 = 0** among condition-matched triples whose two orders agreed; **5/9** triples were order-split and excluded.

The cycle rate is zero, but that is not evidence of a stable preference relation. RIVER beats STORE and HOME in every parsed cell and the reversed frame flips as it should (polarity match = 1). The only contested pair, STORE vs HOME, has a large order effect (Δ = −0.556): aggregated “STORE > HOME” is an average over two presentation orders that often disagree. An intransitivity rate computed without the order and wording crosses would have been unreadable for that reason.

Per-cell *n* is 3. Treat *p*-values as descriptive; the columns that matter are the effect sizes (Δ, range, match rate) and the unparsed rate.

## Known limitations

- Per-cell samples are small, so cell-level distributions are noisy and significance tests are underpowered. Effect sizes are reported alongside *p*-values for that reason.
- The three wordings are a convenience sample of frames, not a systematic space of prompts.
- Content-driven consistency is not ruled out. If the triple is ordered by a salient dimension (cost, prestige, moral valence), apparent coherence may be a property of the item set rather than of the model.
- Single-token constraint reduces but does not eliminate parse failures; the unparsed rate is part of the result, not a data-cleaning step.
