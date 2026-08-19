# Transitivity summary (`example_run.jsonl`)

Model: `gpt-4o-mini`. Rows: 54. Unparsed: 0/54 = 0.000.

## Preference direction (inferred, all conditions)

| pair        |   n_parsed |   prefer_first |   prop_first | direction     |
|:------------|-----------:|---------------:|-------------:|:--------------|
| STORE-HOME  |         18 |             13 |        0.722 | STORE > HOME  |
| STORE-RIVER |         18 |              0 |        0.000 | STORE < RIVER |
| HOME-RIVER  |         18 |              0 |        0.000 | HOME < RIVER  |

## Intransitivity

Matched triples are `(wording, sample_index)` after both orders agree. Cycle rate: **0/4 = 0.000**. Order-split (excluded): 5.

| triple_id     | wording   |   sample_index | cycle   | status      |
|:--------------|:----------|---------------:|:--------|:------------|
| saturday_hour | direct    |              0 | False   | order_split |
| saturday_hour | direct    |              1 | False   | complete    |
| saturday_hour | direct    |              2 | False   | order_split |
| saturday_hour | indirect  |              0 | False   | complete    |
| saturday_hour | indirect  |              1 | False   | order_split |
| saturday_hour | indirect  |              2 | False   | complete    |
| saturday_hour | reversed  |              0 | False   | order_split |
| saturday_hour | reversed  |              1 | False   | complete    |
| saturday_hour | reversed  |              2 | False   | order_split |

## Order effect

Δ = P(canonical first | ab) − P(canonical first | ba). Fisher exact; per-cell *n* is small.

| pair        |   P(first|ab) |   P(first|ba) |   delta |   p_fisher |
|:------------|--------------:|--------------:|--------:|-----------:|
| STORE-HOME  |         0.444 |         1.000 |  -0.556 |      0.029 |
| STORE-RIVER |         0.000 |         0.000 |   0.000 |      1.000 |
| HOME-RIVER  |         0.000 |         0.000 |   0.000 |      1.000 |

## Wording effect

Range = max − min P(canonical first) across frames. χ² on 3×2 counts; expected cells often < 5.

| pair        |   P(direct) |   P(indirect) |   P(reversed) |   range |   p_chi2 |
|:------------|------------:|--------------:|--------------:|--------:|---------:|
| STORE-HOME  |       0.667 |         0.833 |         0.667 |   0.167 |    0.758 |
| STORE-RIVER |       0.000 |         0.000 |         0.000 |   0.000 |  nan     |
| HOME-RIVER  |       0.000 |         0.000 |         0.000 |   0.000 |  nan     |

## Polarity consistency

Inferred-preference match rate, reversed vs prefer frames, aligned on `(order, sample_index)`.

| pair        |   n |   match_rate |
|:------------|----:|-------------:|
| STORE-HOME  |  12 |        0.750 |
| STORE-RIVER |  12 |        1.000 |
| HOME-RIVER  |  12 |        1.000 |

