# E9 results — BLOCKED_MINICHECK_WITH_E9_A_COMPLETE

E9-A completed with exactly five Random Forest fits and 561 OOF predictions.
The frozen decomposer and Amendment 01 were unchanged. The accepted limitations
in claim atomicity/self-containment remain; no post-score tuning was performed.

## Full decomposition

Exactly 561 canonical samples, with 575 final claims.
Mean 1.0249554367201426; median 1.0; maximum 4.
One-claim samples 551; two-claim samples 8;
three-plus-claim samples 2.
Fallbacks 68. API attempts 687; successful responses
684; additional attempts after first payload request
152. Sample-level cache reuse 26; unique cached
payload reuse 20.

Input tokens 334015; output tokens 36588;
total 370603; provider-cached input tokens
0. Estimated incremental full-run API cost:
USD 1.20091750. This includes full-run validation attempts and
excludes previously paid smoke calls. HTTP 429 interrupted the initial invocation;
the user explicitly authorized continuation. Successful responses from an interrupted
row were replayed through the unchanged validator rather than purchased again.
Counts cover both invocations; initial HTTP failures are included in attempted calls.
Billing-ledger cost was not independently available.

## E6-v3 saved baseline

| Group | Correct / n | Accuracy | Spearman |
|---|---:|---:|---:|
| Overall | 474/561 | 0.8449197860962567 | 0.7816945786401444 |
| DM | 169/211 | 0.8009478672985783 | 0.6852178827409456 |
| MT | 191/216 | 0.8842592592592593 | 0.8327371480891061 |
| PG | 114/134 | 0.8507462686567164 | 0.7522106510632076 |
| Fold 1 | 100/113 | 0.8849557522123894 | 0.8161783605172331 |
| Fold 2 | 91/112 | 0.8125000000000000 | 0.7693547088943431 |
| Fold 3 | 93/112 | 0.8303571428571429 | 0.7703346139229986 |
| Fold 4 | 92/112 | 0.8214285714285714 | 0.7792654108639516 |
| Fold 5 | 98/112 | 0.8750000000000000 | 0.7840673179486594 |

## E9-A: 44 features

| Group | Correct / n | Accuracy | Spearman |
|---|---:|---:|---:|
| Overall | 471/561 | 0.8395721925133690 | 0.7804191219308901 |
| DM | 167/211 | 0.7914691943127962 | 0.6841392163860768 |
| MT | 191/216 | 0.8842592592592593 | 0.8323378002744434 |
| PG | 113/134 | 0.8432835820895522 | 0.7461168272925336 |
| Fold 1 | 99/113 | 0.8761061946902655 | 0.8115118534135977 |
| Fold 2 | 91/112 | 0.8125000000000000 | 0.7696292516064224 |
| Fold 3 | 93/112 | 0.8303571428571429 | 0.765740595082547 |
| Fold 4 | 91/112 | 0.8125000000000000 | 0.779155211153799 |
| Fold 5 | 97/112 | 0.8660714285714286 | 0.7848804103105484 |

Corrections: 1; regressions: 4;
net correct change: -3. Exact two-sided paired McNemar p:
0.375. Accuracy difference: -0.0053475935828877.
Paired bootstrap percentile 95% CI: [-0.0142602495543672, 0.0017825311942959] (accuracy units),
10,000 resamples, default_rng(42). These statistics were not used to tune the model.

## E9-B

BLOCKED_MINICHECK. Native Windows with CPU-only PyTorch and no CUDA device; minicheck and vllm are absent. The authors document the exact 7B MiniCheck/vLLM interface as Linux-only. Available RAM is insufficient even for an unquantized 7B two-byte-per-parameter weights estimate (14 GB), before runtime overhead. The frozen protocol prohibits quantization, substitution or OOM redesign.

No model substitution, MiniCheck inference, 49-column matrix or E9-B RF fit.

## Integrity and stop

561 canonical IDs/order and original locked folds verified. All 36 baseline columns
are numerically/order-identical; claims are nonempty for every row. Requests contain
only hyp/task sample data. NLI input hashes verify DM/MT=tgt and PG=src with claim
as hypothesis. Every aggregate was reconstructed from saved claim probabilities.
Training records verify only training-row targets/features for each fit. No OOF
prediction is a feature. Baseline verification required zero refits.

The official 1,500-row test was not accessed, loaded, inspected, evaluated or used.
No historical E1-E8 file was modified. No threshold, feature, fold, RF configuration,
reference policy or decomposer change was made after results. No E9-C.
No commit or push. Exact changed paths are recorded in reports/FULL_RUN_FILES_CHANGED.md.
Row-level claims, NLI scores, features and OOF files remain local and ignored.
All findings are exploratory OOF results on the reused development pool.

E6-v3 remains the better completed comparison on both accuracy and Spearman. This does not trigger any official-test evaluation.
