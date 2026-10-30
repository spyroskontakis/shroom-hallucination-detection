# E11-A frozen development result

Protocol content SHA-256: `518c2df610a1483472b94e8baf3c0c4b277275f351e7448822e35d9dc871772d`. Five locked A100 folds, one seed (42), final epoch-5 checkpoints, 561/561 held-out predictions.

**Accuracy:** 460/561 = 0.819964349; **Spearman:** 0.717256508.

Confusion matrix (rows gold 0/1, columns predicted 0/1): `[[261, 46], [55, 199]]`. Precision 0.812244898, recall 0.783464567, F1 0.797595190.

| Task | Correct / total | Accuracy | Spearman |
|---|---:|---:|---:|
| DM | 166/211 | 0.786729858 | 0.670921316 |
| MT | 189/216 | 0.875000000 | 0.750551926 |
| PG | 105/134 | 0.783582090 | 0.642978679 |

| Fold | Training rows | Held out | Correct | Train seconds | Final loss | Peak GPU GiB |
|---|---:|---:|---:|---:|---:|---:|
| 1 | 448 | 113 | 92 | 50.3 | 0.006413 | 10.21 |
| 2 | 449 | 112 | 89 | 85.5 | 0.003129 | 10.19 |
| 3 | 449 | 112 | 95 | 73.1 | 0.006116 | 10.21 |
| 4 | 449 | 112 | 92 | 67.8 | 0.003178 | 9.13 |
| 5 | 449 | 112 | 92 | 79.2 | 0.006612 | 10.22 |

| Baseline | Correct | Accuracy | Spearman | E11-A Δ correct | E11-A Δ accuracy | E11-A Δ Spearman | McNemar p | Bootstrap 95% Δ accuracy |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| E6-v3 | 474/561 | 0.844919786 | 0.781694579 | -14 | -0.024955437 | -0.064438071 | 0.108857 | [-0.053476, +0.003565] |
| E10 | 475/561 | 0.846702317 | 0.782809294 | -15 | -0.026737968 | -0.065552786 | 0.0864372 | [-0.055258, +0.001783] |

E11-A correct-count change versus E10 by task: DM -5, MT -1, PG -9.
E11-A is below E10 on frozen development accuracy and Spearman; it should not replace E10 as the current final-model candidate.

Paired McNemar tests are exact two-sided; bootstrap resamples the same 561 OOF rows 10,000 times with seed 42. These are descriptive development comparisons and do not include retraining uncertainty.

No hyperparameter or threshold tuning, second seed, pseudo-labels, official-test access, commit, or push was performed by this result assembly.
