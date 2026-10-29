# Retrospective E8 versus E6-v3 comparison

**POST-HOC, DESCRIPTIVE / EXPLORATORY — saved OOF predictions only.** Computed during the 2026-09-11 publication audit and documented on 2026-09-12. No new model fit, inference, hyperparameter selection or experiment evaluation occurred. No redesign/tuning used this comparison.

E6-v3 was **not** the original E8 baseline. E8 was designed on the 25 frozen E6-v1 features and originally compared with E6-v1 (453/561). That protocol, research question, grid, baseline and interpretation remain unchanged in E8_PROTOCOL.md and E8_RESULTS.md. E6-v3 has 36 features; therefore this later system comparison cannot isolate the causal effect of RF tuning.

| System | Features | Correct/N | Accuracy | Spearman |
|---|---:|---:|---:|---:|
| E6-v3 | 36 | 474/561 | 0.8449197860962567 | 0.7816945786401444 |
| E8 | 25 | 452/561 | 0.8057040998217468 | 0.7528866687040761 |

Taking E6-v3 as the retrospective comparator, E8 has **23 corrections**, **45 regressions**, net **-22**; both correct 429, both wrong 64. Accuracy difference E8 minus E6-v3 is -0.0392156862745098, or -3.9215686274509802 percentage points.

Post-hoc descriptive exact two-sided McNemar p = **0.01033766119369546**. Paired-bootstrap 95% percentile interval for accuracy difference = **[-0.0677361853832442, -0.0106951871657754]**, or **[-6.7736185383244205, -1.06951871657754] percentage points**.

## Procedure and subgroup results

The 561 saved canonical IDs, folds, frozen binary labels and p_hallucination align exactly. Threshold is unchanged at prediction >=0.5. Spearman uses unrounded human targets and predictions rounded to 12 decimals. McNemar is scipy.stats.binomtest(23, 68, 0.5), two-sided. Bootstrap uses the per-ID correctness difference (E8 correct minus E6-v3 correct) in canonical order, numpy.default_rng(42), 10,000 successive resamples of 561 indices with replacement and numpy.quantile at [0.025, 0.975]. No retraining occurs in bootstrap. Source hashes and full-precision aggregate results are in publication/posthoc_e8_vs_e6_v3.json.

| Group | N | E6-v3 correct | E8 correct | E6-v3 accuracy | E8 accuracy | E6-v3 Spearman | E8 Spearman |
|---|---:|---:|---:|---:|---:|---:|---:|
| Fold 1 | 113 | 100 | 93 | 0.8849557522 | 0.8230088496 | 0.8161783605 | 0.7753405271 |
| Fold 2 | 112 | 91 | 86 | 0.8125000000 | 0.7678571429 | 0.7693547089 | 0.7508365517 |
| Fold 3 | 112 | 93 | 90 | 0.8303571429 | 0.8035714286 | 0.7703346139 | 0.7567080297 |
| Fold 4 | 112 | 92 | 87 | 0.8214285714 | 0.7767857143 | 0.7792654109 | 0.7343213344 |
| Fold 5 | 112 | 98 | 96 | 0.8750000000 | 0.8571428571 | 0.7840673179 | 0.7465907070 |
| DM | 211 | 169 | 161 | 0.8009478673 | 0.7630331754 | 0.6852178827 | 0.6542583925 |
| MT | 216 | 191 | 187 | 0.8842592593 | 0.8657407407 | 0.8327371481 | 0.8029352198 |
| PG | 134 | 114 | 104 | 0.8507462687 | 0.7761194030 | 0.7522106511 | 0.7109578997 |
| Without definition | 368 | 317 | 304 | 0.8614130435 | 0.8260869565 | 0.8119705384 | 0.7808249324 |
| With definition | 193 | 157 | 148 | 0.8134715026 | 0.7668393782 | 0.6941425689 | 0.6606953631 |

Definition availability is a descriptive subgroup; retrieved definitions are available exclusively for DM. The no-definition group also contains every MT/PG row. These subgroup contrasts do not identify a causal effect of definitions.

The frozen E6-v3 remains the best development milestone among these systems. This negative E8 comparison is exploratory on a reused development set. Neither nested CV nor these post-hoc statistics creates an independent test. The intervals condition on fixed OOF predictions and omit refitting/selection variability and adaptive/multiple-comparison adjustment. They are not confirmatory evidence of generalization.
