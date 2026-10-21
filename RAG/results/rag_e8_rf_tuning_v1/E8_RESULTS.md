# E8 v1 — Random Forest tuning on frozen E6 features

**COMPLETED — EXPLORATORY DEVELOPMENT-ONLY.** One frozen nested evaluation; 95 E8 fits and zero additional baseline verification fits. No configuration, feature, threshold or selection rule was changed after seeing results.

## Overall result

| Procedure | Correct / N | Outer OOF accuracy | Outer OOF Spearman |
|---|---:|---:|---:|
| E6 | 453/561 | 0.8074866310 (80.7487%) | 0.7444205394 |
| E8 | 452/561 | 0.8057040998 (80.5704%) | 0.7528866687 |

Nested tuning reduced the E6 development correct count: net -1/561; accuracy difference -0.178253 percentage points.

## Fixed inputs, estimator and baseline

Exactly the 25 frozen E6 columns, same ordered 561 canonical IDs and locked five outer folds; all samples use the E6 feature path, with no E7 router. Target is p_hallucination; binary strata use the approved label_bin. No features were recomputed or transformed. E6 features were parsed with float_precision="round_trip"; exact arrays, ID order, labels and folds were validated against canonical artifacts.

C0 is identical to all 18 accepted E6 RF parameters. Every fit receives an explicit full dictionary: n_estimators=500, criterion="squared_error", max_depth=None, min_samples_split=2, min_weight_fraction_leaf=0.0, max_leaf_nodes=None, min_impurity_decrease=0.0, bootstrap=True, oob_score=False, n_jobs=-1, random_state=42, verbose=0, warm_start=False, ccp_alpha=0.0, max_samples=None, monotonic_cst=None, plus the candidate min_samples_leaf and max_features below. Predictions are clipped to [0,1]; classification uses >=0.5. Full machine-readable dictionaries and runtime are in config/configurations.json.

Runtime matches E6: Python 3.11.9, scikit-learn 1.8.0, NumPy 2.4.4, pandas 3.0.2, SciPy 1.17.1. The saved E6 baseline reproduces 453/561, accuracy 0.8074866310160428 and Spearman 0.744420539373989. E7's existing fresh E6 predictions agree per ID within 1e-12 (actual maximum difference 4.4408920985006262e-16), with identical binary and 12-decimal-rounded predictions. This verification required zero new baseline fits.

## Predefined configurations and selection frequency

| ID | min_samples_leaf | max_features | Selected outer folds | Frequency |
|---|---:|---:|---|---:|
| C0 | 1 | 1.0 | 3 | 1/5 |
| C1 | 3 | 1.0 | none | 0/5 |
| C2 | 5 | 1.0 | none | 0/5 |
| C3 | 1 | 0.5 | none | 0/5 |
| C4 | 3 | 0.5 | 1, 2, 5 | 3/5 |
| C5 | 5 | 0.5 | 4 | 1/5 |

## Nested selection and leakage checks

Within each canonical-ordered outer-training set, a fresh StratifiedKFold(n_splits=3, shuffle=True, random_state=42) uses task + "_" + str(label_bin). All six candidates share those three saved splits. Minimum outer-training stratum counts by outer fold are [40, 40, 40, 40, 40]; all strata have at least three rows. The frozen split JSON records the training and validation IDs and all stratum counts; the inner assignment CSV has 2,244 rows.

For each candidate, the three inner predictions cover the entire outer-training set once. Selection uses pooled inner OOF accuracy, then pooled inner OOF Spearman, then earliest C0–C5. Undefined Spearman ranks below defined values at equal accuracy. No R² or average-of-fold scores enter selection. Spearman uses unrounded target and predictions rounded to 12 decimals.

The tuning function receives only outer-training rows, inner splits, feature names and configurations. Inner train/validation IDs are disjoint from outer validation. Each selection and all six inner scores were saved before selected outer-model fitting/prediction. Outer-validation labels enter scoring only after all five selections and outer OOF predictions exist. This evaluates a selection procedure, not a globally chosen RF configuration.

| Outer fold | Selected | Selected inner correct / N | Selected inner accuracy | Selected inner Spearman |
|---|---|---:|---:|---:|
| 1 | C4 | 358/448 | 0.7991071429 | 0.7410620969 |
| 2 | C4 | 374/449 | 0.8329621381 | 0.7686933942 |
| 3 | C0 | 363/449 | 0.8084632517 | 0.7292186977 |
| 4 | C5 | 359/449 | 0.7995545657 | 0.7534910999 |
| 5 | C4 | 360/449 | 0.8017817372 | 0.7544875608 |

All 30 candidate/outer-fold scores are in evaluation/inner_scores.csv; all candidate inner OOF predictions are saved separately for each outer fold.

## Outer OOF results by fold, task and evidence

| Group | N | E6 correct | E8 correct | E6 accuracy | E8 accuracy | E6 Spearman | E8 Spearman |
|---|---:|---:|---:|---:|---:|---:|---:|
| Fold 1 | 113 | 93 | 93 | 0.8230088496 | 0.8230088496 | 0.7636250604 | 0.7753405271 |
| Fold 2 | 112 | 85 | 86 | 0.7589285714 | 0.7678571429 | 0.7313740768 | 0.7508365517 |
| Fold 3 | 112 | 90 | 90 | 0.8035714286 | 0.8035714286 | 0.7567080297 | 0.7567080297 |
| Fold 4 | 112 | 87 | 87 | 0.7767857143 | 0.7767857143 | 0.7254257584 | 0.7343213344 |
| Fold 5 | 112 | 98 | 96 | 0.8750000000 | 0.8571428571 | 0.7348041615 | 0.7465907070 |
| DM | 211 | 162 | 161 | 0.7677725118 | 0.7630331754 | 0.6483380720 | 0.6542583925 |
| MT | 216 | 186 | 187 | 0.8611111111 | 0.8657407407 | 0.7969005342 | 0.8029352198 |
| PG | 134 | 105 | 104 | 0.7835820896 | 0.7761194030 | 0.6950040245 | 0.7109578997 |
| With definition | 193 | 149 | 148 | 0.7720207254 | 0.7668393782 | 0.6565323714 | 0.6606953631 |
| Without definition | 368 | 304 | 304 | 0.8260869565 | 0.8260869565 | 0.7701942329 | 0.7808249324 |

## Paired comparison against E6

Corrections: **2**. New errors: **3**. Net: **-1**. Exact two-sided McNemar p = **1.0000000000**.

Accuracy difference E8 minus E6: **-0.0017825312**, or **-0.178253 percentage points**. Paired-bootstrap 95% percentile interval: **[-0.0089126560, +0.0053475936]**, or **[-0.891266, +0.534759] percentage points**.

The existing procedure is preserved: exact binomtest(corrections, discordant total, 0.5), p=1 for no discordance; 10,000 paired row resamples with numpy.default_rng(42), sample size 561 and percentile 2.5/97.5. Bootstrap conditions on fixed OOF correctness and omits retraining/selection variability. Every correction and new-error canonical ID is in evaluation/e8_metrics.json; evaluation/paired_row_diagnostics.csv covers all rows.

## Freeze chronology, fit accounting and integrity

Existing protocol freeze: 2026-09-09T18:28:49.7711816Z. Complete code/configuration/split freeze: 2026-09-10T07:18:39.333674+00:00. First-suite marker: 2026-09-10T07:19:06.922178+00:00. Evaluation completed: 2026-09-10T07:20:47.850955+00:00.

The directory initially contained only E8_PROTOCOL.md, initial_integrity.json, protocol_freeze.json and e8_common.py. No prior E8 fit or result was present. Those files were retained; the incomplete implementation was completed without changing the frozen protocol.

Pre-fit contracts: **10 PASS**, plus real data alignment, runtime, C0 identity, saved baseline and thread-execution checks. **90 inner fits + 5 selected outer fits = 95 E8 fits**. Additional baseline verification fits: **0**. No final all-data fit or second nested run occurred.

Final read-only audit: 95 fit-start/fit-completion pairs; 285 training/target/prediction array hashes; all inner/outer ID partitions; all 30 pooled inner scores and five selections recomputed; 561 unique finite outer OOF predictions; all subgroup and paired statistics verified; **557 protected E3/E5/E6/E7 files unchanged**. Operational network/access violations: zero. Process-local guards are defense-in-depth, not OS isolation.

## Interpretation and limitations

The paired 95% interval includes zero; this run does not establish an accuracy advantage over E6.

**Exploratory development-only on a reused development pool.** Nested CV keeps each outer-validation label out of its hyperparameter selection, but does not erase prior experiment/design exposure or turn the pool into an independent test. No globally best configuration is inferred from selection frequency or aggregate outer results. Subgroups are descriptive, no adaptive-research correction is claimed, and non-significance does not establish equivalence. The inherited E6 reference-assisted features, DM-only definition coverage and Module 4 provenance limitations remain.

All new files are under RAG/results/rag_e8_rf_tuning_v1/. E3/E5/E6/E7 and existing user changes, including untracked E7, were preserved. No retrieval, MPNet/NLI extraction, external data, LLM/API calls, synthetic-data edits, official-test access, package changes, commit, push, tag or next experiment occurred.

## Artifact map

- E8_PROTOCOL.md: unchanged preregistered protocol; config/configurations.json: full six parameter dictionaries and runtime.
- splits/: canonical outer assignments, 2,244 inner assignments, full inner/outer ID lists and stratum counts.
- config/execution_freeze.json: pre-fit source/test/input-reference/config/split hashes; config/final_integrity.json and completion_manifest.json: final audits.
- scripts/: data checks, nested selector, preparation, one-shot evaluation and report/audit; tests/test_e8.py: pre-fit contracts.
- evaluation/: 30 inner score rows, all inner OOF predictions, five selection records, 561 final OOF predictions, paired row diagnostics and metrics.
- evaluation/fit_events.jsonl: 190 start/completion records for 95 fits, full parameters/IDs and array hashes.

## Report-rendering repair

The originally frozen report_e8.py had an unterminated display string at line 138 and stopped at parsing, before any audit/report execution. It remains unchanged. report_e8_render_fixed.py fixes only that closing quote and adds this disclosure. All experiment inputs, splits, candidate settings, selection code, training code, OOF predictions and scores remain frozen. No fit was repeated. See config/report_render_repair.json for both source hashes.
