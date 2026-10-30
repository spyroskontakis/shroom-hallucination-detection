# E8 v1 — Limited Random Forest tuning on frozen E6 features

## Research question and fixed scope

Can a small, predefined Random Forest hyperparameter search improve E6 hallucination-detection performance? This experiment evaluates the nested configuration-selection procedure, not a single globally selected configuration. It uses the E6 prediction path on every example, without the E7 router. E3/E5/E6/E7 remain immutable.

Use the same 561 ordered canonical development IDs, approved binary label_bin, target p_hallucination and five locked outer folds (113/112/112/112/112). Retain exactly the 25 frozen E6 predictors, in their accepted order. Read the frozen feature CSV with float_precision='round_trip', and verify hashes, exact E3 plus E5 feature alignment, canonical IDs and folds. No scaling, feature selection, imputation, extraction or retrieval is added. No official test, external data, MPNet/NLI inference/training, synthetic-data change, API or LLM call.

## Fully specified configurations

The ordered candidates are fixed before any E8 fit:

| ID | min_samples_leaf | max_features |
|---|---:|---:|
| C0 | 1 | 1.0 |
| C1 | 3 | 1.0 |
| C2 | 5 | 1.0 |
| C3 | 1 | 0.5 |
| C4 | 3 | 0.5 |
| C5 | 5 | 0.5 |

All other RandomForestRegressor parameters are explicitly recorded and passed: n_estimators=500, random_state=42, n_jobs=-1, criterion='squared_error', max_depth=None, min_samples_split=2, min_weight_fraction_leaf=0.0, max_leaf_nodes=None, min_impurity_decrease=0.0, bootstrap=True, oob_score=False, max_samples=None, ccp_alpha=0.0, monotonic_cst=None, verbose=0, warm_start=False. C0 must equal the complete accepted E6 run_config.random_forest dictionary; verify the constructor's effective parameters equal each explicit candidate dictionary. Clip every prediction to [0,1]; binary prediction is >=0.5.

Runtime must match the accepted E6 environment: Python3.11.9, scikit-learn1.8.0, numpy2.4.4, pandas3.0.2, scipy1.17.1. No dependency installation or version migration. Store executable, library versions and full parameter dictionaries for all candidates in configurations.json.

## Frozen outer and inner splits

For each outer fold f, outer_train is exactly IDs outside f; outer_validation is exactly IDs in f. Within canonical-ordered outer_train, form strata as task + '_' + str(label_bin), using the approved binary label, never a newly thresholded regression target. Confirm every training stratum contains at least three observations. Instantiate a fresh StratifiedKFold(n_splits=3, shuffle=True, random_state=42) in each outer fold. Use the same resulting three splits for all six candidates. Save train/validation canonical IDs, fold assignments and stratum counts before fitting.

All inner train and validation IDs must be subsets of outer_train, disjoint from outer_validation. Each outer_train ID must occur in exactly one inner validation split; each inner train set is the complement within outer_train. Outer validation sets partition all561 IDs. A failure in strata adequacy, IDs, folds, input hashes or leakage controls blocks execution.

## Nested selection and final predictions

For each outer fold, the tuning function receives ONLY that outer-training frame, its three inner splits and the six explicit configurations. It does not receive outer-validation rows, labels or baseline predictions. For each candidate in C0-C5 order, train three fresh RFs only on inner_train, then predict inner_validation. Reassemble predictions in canonical outer-training order and compute POOLED inner OOF accuracy and Spearman over the entire outer-training set, not an average of three fold scores. Never use estimator.score or regression R-squared.

Select greatest pooled accuracy, then greatest Spearman, then earliest C0-C5 in a full tie. Undefined/nonfinite Spearman is ranked below all defined Spearman values when comparing equal accuracy; no numeric epsilon is used for ties. Regression target stays p_hallucination. Spearman follows E6: unrounded target, predictions rounded to12 decimals. Persist all six scores and the selected candidate BEFORE the selected model sees outer-validation features. Train that candidate once on all outer_train and predict only outer_validation. Different outer folds may select different candidates.

Generate one complete nested OOF suite: 5x6x3=90 inner fits plus5 selected outer fits =95 E8 fits. No tuning outside this grid, no reseeding, no model warm-start, no retraining after outer scores, and no final all-data model fitting. Outer metrics are computed after all five selections and predictions exist. Save every candidate's inner OOF predictions/scores and the561 final outer OOF predictions.

## Baseline and statistical comparison

Use frozen saved E6 OOF predictions as primary baseline:453/561, accuracy0.8074866310160428, Spearman0.744420539373989. Verify their SHA-256, exact ID/fold mapping and recomputed metrics with approved labels. Read baseline prediction CSV with the accepted ordinary pandas parser. E7's already verified fresh E6 predictions provide an additional per-ID numeric check (atol1e-12,rtol0), exact binary equality and exact ranks after12-decimal rounding. No new baseline verification fits are planned; log baseline fits separately as0. C0 parameters equal E6, but C0 inner training subsets differ from the original outer fits, so its inner predictions are not expected to match E6 outer OOF.

Report correct/N, accuracy and Spearman overall, each outer fold, task DM/MT/PG and evidence availability. Report selection frequency for all C0-C5 including zero counts. Undefined subgroup Spearman is null for fewer than two rows or constant target/rounded predictions.

Primary paired comparison: E8 versus E6 corrections, regressions, net correct, accuracy difference, exact two-sided McNemar binomtest(b,b+c,0.5),p=1 if no discordance. Paired bootstrap of fixed per-row correctness differences:10,000 resamples of561 paired rows, numpy.default_rng(42), percentile2.5/97.5 using numpy.quantile. Preserve E6 iteration order. Report accuracy difference and CI both raw and in percentage points. No multiplicity or adaptive-research correction is claimed. Subgroups are descriptive.

## Pre-fit freeze, contracts and execution guard

Before the first fit, freeze this protocol, configurations, splits, full implementation/test hashes, protected/input hashes, baseline verification, runtime and passing contracts with UTC timestamps. Mark the sole evaluation started using exclusive file creation; refuse a second run if its marker exists. After freeze, do not change protocol, configuration or implementation because of results. Write a started/completed record for every actual RF fit, with train/predict IDs and stage. Check guard state before and after fit/predict. Final audit verifies95 completed fits,90inner+5outer,561 valid unique OOF predictions and unchanged inputs.

Contracts cover exact candidate order/parameter differences, C0 identity, pooled metric/selection priorities and ties/undefined Spearman, inner/outer isolation, shared inner splits, complete OOF coverage, label_bin strata, feature/ID/fold alignment, baseline reproduction and no network/frozen writes. Synthetic fixtures and runtime thread smoke do not fit estimators.

Use the E7-tested Python process-local audit guard copied into the E8 directory: writes only under E8, repository reads only from a named protected allowlist, system/runtime library reads only from their known roots. Block network and subprocess operations. Keep the reviewed Python3.11.9 Windows platform shell-probe suppression, selecting the native version fallback without permission relaxation. Use -B/offline flags; joblib temporary path stays inside E8. Scientific data access is restricted to named development files; hash reads of other protected bytes are integrity checks. This is defense-in-depth, not OS sandboxing.

All new files live under RAG/results/rag_e8_rf_tuning_v1/. Preserve existing untracked E7 and Augmentation Pipeline.txt. No Git add/commit/push/tag, no next experiment. On critical integrity, access, split, runtime or prediction failure, stop and report without silently restarting the evaluation.

## Interpretation and limitations

EXPLORATORY DEVELOPMENT-ONLY on a reused development pool. Nested CV isolates hyperparameter selection from the corresponding outer-validation labels; it does not erase prior experiment/design exposure or create an independent test set. The procedure may select different configurations across outer folds; no globally best setting is inferred from aggregate inner or outer results. The paired bootstrap conditions on saved OOF predictions and omits retraining/selection variability. Non-significance is not equivalence. Inherited E6 reference-assisted features, DM-only evidence coverage and Module4 provenance limitations remain. A fresh GitHub clone is not self-contained without authorized canonical/frozen per-row data. Report the outcome regardless of whether E8 improves, without altering the search.
