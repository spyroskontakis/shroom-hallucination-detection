# Canonical CV results summary — Prompt 7E-A

Protocol: development-only CV using the locked 561-sample canonical human development pool and locked five folds.

Official test set used: **false**.

## Experiments

- E1_NLI_only: six NLI features.
- E2_similarity_only: eight semantic similarity features.
- E3_NLI_similarity: all 14 features.
- E4_synthetic_diagnostic: same 14 features as E3, plus 505 synthetic samples in training folds only; diagnostic-only.

## Overall metrics

| experiment | selection_eligible | n_oof | mean_cv_accuracy | std_cv_accuracy | overall_oof_accuracy | mean_cv_spearman | std_cv_spearman | overall_oof_spearman | mean_cv_precision | std_cv_precision | mean_cv_recall | std_cv_recall | mean_cv_f1 | std_cv_f1 | overall_precision | overall_recall | overall_f1 | tn | fp | fn | tp |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| E1_NLI_only | True | 561 | 0.773609 | 0.036107 | 0.773619 | 0.688745 | 0.034265 | 0.689355 | 0.752323 | 0.032644 | 0.743961 | 0.061789 | 0.747666 | 0.045635 | 0.752988 | 0.744094 | 0.748515 | 245 | 62 | 65 | 189 |
| E2_similarity_only | True | 561 | 0.677370 | 0.019130 | 0.677362 | 0.535433 | 0.046673 | 0.534292 | 0.650156 | 0.007183 | 0.622220 | 0.070213 | 0.634262 | 0.039429 | 0.650206 | 0.622047 | 0.635815 | 222 | 85 | 96 | 158 |
| E3_NLI_similarity | True | 561 | 0.793189 | 0.043201 | 0.793226 | 0.738203 | 0.016093 | 0.739040 | 0.771056 | 0.042746 | 0.771418 | 0.062537 | 0.770928 | 0.050498 | 0.771654 | 0.771654 | 0.771654 | 249 | 58 | 58 | 196 |
| E4_synthetic_diagnostic | False | 561 | 0.805673 | 0.038263 | 0.805704 | 0.721730 | 0.043295 | 0.723751 | 0.764098 | 0.042971 | 0.826869 | 0.062347 | 0.793384 | 0.042826 | 0.763636 | 0.826772 | 0.793951 | 242 | 65 | 44 | 210 |

## Per-task metrics

| experiment | task | n | accuracy | spearman | precision | recall | f1 | tn | fp | fn | tp |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| E1_NLI_only | DM | 211 | 0.715640 | 0.591283 | 0.694215 | 0.785047 | 0.736842 | 67 | 37 | 23 | 84 |
| E1_NLI_only | MT | 216 | 0.824074 | 0.749539 | 0.893333 | 0.690722 | 0.779070 | 111 | 8 | 30 | 67 |
| E1_NLI_only | PG | 134 | 0.783582 | 0.656715 | 0.690909 | 0.760000 | 0.723810 | 67 | 17 | 12 | 38 |
| E2_similarity_only | DM | 211 | 0.649289 | 0.443516 | 0.651376 | 0.663551 | 0.657407 | 66 | 38 | 36 | 71 |
| E2_similarity_only | MT | 216 | 0.750000 | 0.670813 | 0.726316 | 0.711340 | 0.718750 | 93 | 26 | 28 | 69 |
| E2_similarity_only | PG | 134 | 0.604478 | 0.262114 | 0.461538 | 0.360000 | 0.404494 | 63 | 21 | 32 | 18 |
| E3_NLI_similarity | DM | 211 | 0.734597 | 0.640010 | 0.714286 | 0.794393 | 0.752212 | 70 | 34 | 22 | 85 |
| E3_NLI_similarity | MT | 216 | 0.856481 | 0.796045 | 0.912500 | 0.752577 | 0.824859 | 112 | 7 | 24 | 73 |
| E3_NLI_similarity | PG | 134 | 0.783582 | 0.696181 | 0.690909 | 0.760000 | 0.723810 | 67 | 17 | 12 | 38 |
| E4_synthetic_diagnostic | DM | 211 | 0.767773 | 0.630667 | 0.730159 | 0.859813 | 0.789700 | 70 | 34 | 15 | 92 |
| E4_synthetic_diagnostic | MT | 216 | 0.856481 | 0.775314 | 0.843750 | 0.835052 | 0.839378 | 104 | 15 | 16 | 81 |
| E4_synthetic_diagnostic | PG | 134 | 0.783582 | 0.665754 | 0.698113 | 0.740000 | 0.718447 | 68 | 16 | 13 | 37 |

## Selection

Selected experiment: `E3_NLI_similarity`.

Selection was restricted to E1-E3. E4 did not participate in selection.

## Diagnostic E4 versus E3

| e3_overall_oof_accuracy | e4_overall_oof_accuracy | delta_accuracy_e4_minus_e3 | e3_overall_oof_spearman | e4_overall_oof_spearman | delta_spearman_e4_minus_e3 | delta_precision_e4_minus_e3 | delta_recall_e4_minus_e3 | delta_f1_e4_minus_e3 | fixed_errors | introduced_errors | unchanged_correct | unchanged_incorrect |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0.793226 | 0.805704 | 0.012478 | 0.739040 | 0.723751 | -0.015289 | -0.008017 | 0.055118 | 0.022297 | 23 | 16 | 429 | 93 |

Fixed errors: 23.
Introduced errors: 16.

## Limitations

- Development-only results are not official test benchmark results.
- E4 is diagnostic-only.
- Feature importances are descriptive and were not used for feature removal or model selection.