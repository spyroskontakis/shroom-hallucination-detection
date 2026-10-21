# E9 results — BLOCKED_DECOMPOSER_API

OPENAI_API_KEY is unavailable in the execution environment. No decomposition API
request, real smoke run, NLI inference, MiniCheck inference or RF fit was executed.
No alternate model was used. This is a preparation checkpoint, not an E9 result.

| System | Features | Correct | Accuracy | Spearman | Status |
|---|---:|---:|---:|---:|---|
| E6-v3 | 36 verified | 474/561 | 0.8449197860962567 | 0.7816945786401444 | PASS, saved OOF verified |
| E9-A | 44 declared; matrix not built | — | — | — | BLOCKED_DECOMPOSER_API |
| E9-B | 49 declared; matrix not built | — | — | — | Not started; requires completed E9-A |

E6-v3 overall, per-task and per-fold metrics are in evaluation/baseline_metrics.json.
Corrections, regressions, paired significance and confidence intervals for E9 are
unavailable. No Phase-3 winner has been selected.

Actual execution counts: RF fits 0; decomposition LLM calls 0; cache hits 0;
fallbacks 0; MiniCheck inferences 0. Synthetic mock calls in offline unit tests
are not model calls and do not generate canonical claims.

The canonical pool, folds, saved OOF and 36 feature values/order passed verification.
Runtime claim integrity and validation/train separation remain pending an actual run.
The official test set was not accessed. Historical artifacts were not modified.

Resume requires OPENAI_API_KEY in the execution environment and successful access
to the exact pinned model. Do not put the key in reports or source files.

## Verified baseline subgroups

| Group | Correct / n | Accuracy | Spearman |
|---|---:|---:|---:|
| DM | 169/211 | 0.8009478672985783 | 0.6852178827409456 |
| MT | 191/216 | 0.8842592592592593 | 0.8327371480891061 |
| PG | 114/134 | 0.8507462686567164 | 0.7522106510632076 |
| Fold 1 | 100/113 | 0.8849557522123894 | 0.8161783605172331 |
| Fold 2 | 91/112 | 0.8125000000000000 | 0.7693547088943431 |
| Fold 3 | 93/112 | 0.8303571428571429 | 0.7703346139229986 |
| Fold 4 | 92/112 | 0.8214285714285714 | 0.7792654108639516 |
| Fold 5 | 98/112 | 0.8750000000000000 | 0.7840673179486594 |
