# Evaluation data manifest — Prompt 7B

Scope: read-only audit of raw datasets, feature matrices, synthetic artifacts, overlap checks, and missing inputs for the next execution.

## 1. Raw datasets

| Dataset | Exact path | Rows | Columns | Tasks | Labels | Identifier field |
|---|---|---:|---:|---|---|---|
| Trial | `codex\data\Trial\SHROOM_trial-v1.1\trial-v1.json` | 80 | 9 | DM 36; PG 9; MT 35 | Hallucination 42; Not Hallucination 38 | No explicit ID field; row index only |
| Model-agnostic development | `Dev\SHROOM_dev-v2\val.model-agnostic.json` | 499 | 9 | DM 187; PG 125; MT 187 | Hallucination 218; Not Hallucination 281 | No explicit ID field; row index only |
| Model-aware development | `Dev\SHROOM_dev-v2\val.model-aware.v2.json` | 501 | 9 | DM 188; PG 125; MT 188 | Hallucination 206; Not Hallucination 295 | No explicit ID field; row index only |
| Labeled model-agnostic test | `codex\data\Labeled test\SHROOM_test-labeled\test.model-agnostic.json` | 1,500 | 8 | MT 562; DM 563; PG 375 | Hallucination 611; Not Hallucination 889 | `id` |
| Labeled model-aware test | `codex\data\Labeled test\SHROOM_test-labeled\test.model-aware.json` | 1,500 | 8 | DM 562; MT 563; PG 375 | Hallucination 551; Not Hallucination 949 | `id` |
| Unlabeled model-agnostic train | `codex\data\Unlabeled train\SHROOM_unlabeled-training-data-v2\train.model-agnostic.json` | 30,000 | 6 | MT 10,000; DM 10,000; PG 10,000 | No labels | No explicit ID field; row index only |
| Unlabeled model-aware train | `codex\data\Unlabeled train\SHROOM_unlabeled-training-data-v2\train.model-aware.v2.json` | 30,000 | 6 | DM 10,000; PG 10,000; MT 10,000 | No labels | No explicit ID field; row index only |
| Balanced synthetic data | `codex\data\6. Feature Extraction on Augmented Training Data\filtered_synthetic_data_balanced.csv` | 518 | 16 | MT 228; PG 191; DM 99 | Hallucination 259; Not Hallucination 259 | `sample_id` |

Raw JSON schema notes:

- Trial and development splits contain: `hyp`, `label`, `labels`, `model`, `p(Hallucination)`, `ref`, `src`, `task`, `tgt`.
- Labeled test splits contain: `hyp`, `id`, `label`, `labels`, `p(Hallucination)`, `src`, `task`, `tgt`.
- Unlabeled train splits contain: `hyp`, `model`, `ref`, `src`, `task`, `tgt`.

## 2. Synthetic data linkability

Balanced synthetic file:

- Path: `codex\data\6. Feature Extraction on Augmented Training Data\filtered_synthetic_data_balanced.csv`
- Rows: 518
- Unique `sample_id` values: 390
- `sample_id` is within bounds for the 30,000-row unlabeled model-agnostic train split.
- 262 source `sample_id` values appear once.
- 128 source `sample_id` values appear twice.

Mapping audit against `train.model-agnostic.json`:

- `task` matches the source row for 518/518 synthetic rows.
- `src` matches the source row for 518/518 synthetic rows.
- `original_hyp` matches the source row's `hyp` for 516/518 rows.
- `tgt` matches the source row's `tgt` for 327/518 rows.

Interpretation:

- `sample_id` is linkable to the unlabeled model-agnostic training row by row index.
- Because `tgt`/reference handling differs for some rows, exact reconstruction should use `sample_id`, `task`, `src`, and `original_hyp`, not only `(task, src, tgt)`.

## 3. Overlap and duplicate checks

Duplicate checks used normalized exact text triples:

`(task, src, tgt, hyp)`

Within-split duplicates:

| Split | Duplicate explicit IDs | Duplicate exact text triples | Duplicate source pairs `(task, src, tgt)` |
|---|---:|---:|---:|
| Trial | 0 | 0 | 0 |
| Model-agnostic development | 0 | 1 | 2 |
| Model-aware development | 0 | 0 | 0 |
| Labeled model-agnostic test | 0 | 9 | 21 |
| Labeled model-aware test | 0 | 0 | 0 |
| Unlabeled model-agnostic train | 0 | 1,358 | 2,252 |
| Unlabeled model-aware train | 0 | 0 | 1 |

Important between-split overlaps:

| Pair | Exact text-triple overlap | Source-pair overlap | Notes |
|---|---:|---:|---|
| Trial vs model-agnostic development | 12 | 12 | Raw 579 pool is not safe as-is. |
| Trial vs model-agnostic test | 0 | 0 | No exact overlap found. |
| Model-agnostic development vs model-agnostic test | 4 | 17 | Test benchmark must be caveated. |
| Balanced synthetic vs trial | 0 | 0 | No exact synthetic/trial overlap found. |
| Balanced synthetic vs model-agnostic development | 0 | 1 | One source-pair overlap; no exact synthetic/development triple overlap. |
| Balanced synthetic vs model-agnostic test | 0 | 5 | Five source-pair overlaps; no exact synthetic/test triple overlap. |
| Balanced synthetic vs unlabeled model-agnostic train | 0 | 249 using `(task, src, tgt)` | `sample_id` is the safer linkage key. |

Note: splits without explicit IDs were audited by row index for uniqueness only; row-index placeholders are not semantically comparable across files.

## 4. Feature matrices

Canonical feature names:

- NLI features: `src_ent`, `src_neu`, `src_con`, `tgt_ent`, `tgt_neu`, `tgt_con`
- Semantic similarity features: `sim_src_hyp`, `sim_tgt_hyp`, `sim_src_tgt`, `sim_max`, `sim_min`, `sim_mean`, `sim_gap_tgt_src`, `sim_hyp_distance_from_truth`

| Artifact | Rows | Columns | Dataset/split represented | NLI features | Similarity features | Identifier |
|---|---:|---:|---|---:|---:|---|
| `codex\data\4. NLI + Sim\nli_features_dataset.csv` | 1,500 | 21 | Labeled model-agnostic test | 6 | 0 | `id` |
| `codex\data\4. NLI + Sim\nli_similarity_features_dataset.csv` | 1,500 | 29 | Labeled model-agnostic test | 6 | 8 | `id` |
| `codex\data\2. EDA\shroom_final_implementation\nli_similarity_features_dataset.csv` | 1,500 | 18 | Labeled model-agnostic test | 0 | 8 | `id` |
| `codex\data\6. Feature Extraction on Augmented Training Data\synthetic_nli_features_dataset.csv` | 598 | 17 | Trial + balanced synthetic | 6 | 0 | No explicit ID |
| `codex\data\6. Feature Extraction on Augmented Training Data\nli_similarity_features_dataset.csv` | 598 | 25 | Trial + balanced synthetic | 6 | 8 | No explicit ID |
| `codex\data\7. Ablation Synthetic Data\4.nli_similarity_features_dataset.csv` | 1,500 | 29 | Copy/derived artifact for labeled model-agnostic test | 6 | 8 | `id` |
| `codex\data\7. Ablation Synthetic Data\6.nli_similarity_features_dataset.csv` | 598 | 25 | Copy/derived artifact for trial + balanced synthetic | 6 | 8 | No explicit ID |

The 598-row trial + synthetic combined feature matrix contains:

- `source_type = human_labeled`: 80 rows
- `source_type = synthetic_hallucination`: 259 rows
- `source_type = synthetic_faithful`: 259 rows

## 5. Answers to feature availability questions

1. Are six NLI + eight similarity features already available for the 499 model-agnostic development samples?
   - **No.** No existing CSV with 499 model-agnostic development rows and the 14 canonical features was found.

2. Are six NLI + eight similarity features already available for the 80 trial samples?
   - **Yes, but only embedded inside the 598-row augmented feature artifact**:
     `codex\data\6. Feature Extraction on Augmented Training Data\nli_similarity_features_dataset.csv`
   - The 80 rows are marked with `source_type = human_labeled`.

3. Can trial and development features be safely concatenated?
   - **Not yet.** Trial features exist, but model-agnostic development features are missing. Also, the raw trial/development pool contains duplicate exact text triples, so deduplication or grouped fold assignment is required.

4. Which feature extraction is missing?
   - Missing for `Dev\SHROOM_dev-v2\val.model-agnostic.json`:
     - six NLI features;
     - eight semantic similarity features;
     - a combined 14-feature matrix compatible with the trial feature schema;
     - stable row identifiers or a manifest mapping row index to normalized `(task, src, tgt, hyp)`.

5. Is new computationally expensive NLI inference required?
   - **Yes, for the 499 model-agnostic development rows**, unless an undiscovered precomputed development feature artifact exists outside the audited paths.
   - The cached NLI config confirms label mapping only; it does not provide the missing development NLI outputs.

## 6. Cached NLI configuration

Read-only verified config:

`external-artifacts/local-ba247bf9f1e2/config.json`

Observed `id2label`:

```json
{
  "0": "CONTRADICTION",
  "1": "NEUTRAL",
  "2": "ENTAILMENT"
}
```

Implication:

- The label-ID mapping is now locally confirmed.
- No GPU was required for this audit.
- Future NLI feature extraction for the 499 development rows may be run on CPU or GPU, but GPU is strongly preferable for runtime.

## 7. Historical test-set use

Existing artifacts show previous use of the labeled model-agnostic test set in:

- 1,500-row NLI feature extraction artifacts;
- 1,500-row similarity feature artifacts;
- 1,500-row combined NLI + similarity feature artifacts;
- previous baseline/cross-validation and out-of-fold CSV outputs under `data\4. NLI + Sim`;
- previous ablation comparison artifacts under `data\7. Ablation Synthetic Data`;
- descriptive test-set EDA figures from earlier project stages.

Therefore the labeled model-agnostic test set must be described as:

> official test benchmark με περιορισμό λόγω προηγούμενης διερευνητικής χρήσης του test set

It must not be described as untouched, pristine, fully independent, or an unbiased final estimate.

## 8. Exact inputs needed for next execution

Required existing inputs:

1. `codex\data\Trial\SHROOM_trial-v1.1\trial-v1.json`
2. `Dev\SHROOM_dev-v2\val.model-agnostic.json`
3. `codex\data\6. Feature Extraction on Augmented Training Data\nli_similarity_features_dataset.csv`
4. `codex\data\6. Feature Extraction on Augmented Training Data\filtered_synthetic_data_balanced.csv`
5. `codex\data\Labeled test\SHROOM_test-labeled\test.model-agnostic.json`
6. `codex\data\4. NLI + Sim\nli_similarity_features_dataset.csv`

Required new/derived artifacts before Chapter 6:

1. A deduplicated human-development manifest for trial + model-agnostic development.
2. A 499-row model-agnostic development NLI feature matrix.
3. A 499-row model-agnostic development semantic-similarity feature matrix.
4. A combined model-agnostic development 14-feature matrix.
5. A canonical human-development feature matrix after duplicate handling.
6. Development-only fold assignments shared by E1–E4.
7. Development-only CV outputs for E1–E3, and optionally fixed diagnostic E4.

## 9. Prompt 7C canonical manifests and outputs

Prompt 7C created the following new files:

| File | Purpose |
|---|---|
| `codex\canonical_evaluation_data_prep.py` | Deterministic lightweight data-preparation script. No model inference, feature extraction, notebook execution, Random Forest training, or API calls. |
| `codex\duplicate_group_audit.csv` | Audit of exact duplicate groups within or across trial and model-agnostic development. |
| `codex\excluded_human_test_overlaps.csv` | Exact development-test overlaps removed from the canonical human development pool. |
| `codex\canonical_human_development_manifest.csv` | Final canonical human development manifest after duplicate handling and development-test overlap removal. |
| `codex\canonical_synthetic_diagnostic_manifest.csv` | Final canonical diagnostic synthetic manifest after overlap filtering. |
| `codex\excluded_synthetic_overlap_rows.csv` | Synthetic rows excluded because of overlap with canonical human development or official test keys. |
| `codex\canonical_fold_assignments.csv` | Locked final 5-fold validation assignment for the canonical human development pool, regenerated in Prompt 7C-A with scikit-learn. |
| `codex\canonical_fold_assignments_fallback_audit.csv` | Preserved copy of the previous fallback fold assignment; audit only, not canonical. |
| `codex\regenerate_canonical_folds_sklearn.py` | Script that regenerates final folds using `sklearn.model_selection.StratifiedKFold`. |
| `codex\canonical_fold_generation_metadata.json` | Metadata for final fold generation: interpreter, package versions, hashes, splitter config, fold sizes, stratum counts. |
| `codex\canonical_fold_balance_audit.csv` | Fold-by-stratum balance audit for the final scikit-learn folds. |

## 10. Prompt 7C final counts

### Duplicate groups

| Duplicate category | Groups | Rows affected | Policy |
|---|---:|---:|---|
| Trial-development exact duplicates | 12 | 24 | Keep development row; remove duplicate trial row. |
| Internal development exact duplicate with annotation conflict | 1 | 2 | Exclude whole duplicate group as `excluded_annotation_conflict`. |

Annotation consistency across the 13 duplicate groups:

- Binary labels disagreed in 2 of the 12 trial-development duplicate groups.
- `p(Hallucination)` values differed in 8 duplicate groups total.
- Individual annotation lists differed in all 13 duplicate groups.
- The internal development duplicate group had binary-label agreement, but `p(Hallucination)` and individual annotation-list disagreement.

### Human development pool

Final canonical human development samples: **561**.

Source counts:

| Source split | Rows |
|---|---:|
| `development_model_agnostic` | 493 |
| `trial` | 68 |

Task counts:

| Task | Rows |
|---|---:|
| DM | 211 |
| MT | 216 |
| PG | 134 |

Binary label counts:

| label_bin | Rows |
|---|---:|
| 0 | 307 |
| 1 | 254 |

### Exact development-test overlaps

Removed exact development-test overlaps: **4**.

All four removed development rows came from `development_model_agnostic` and overlapped exact text keys in the official model-agnostic test set. The official test rows were not changed.

### Canonical diagnostic synthetic set

Final canonical diagnostic synthetic samples: **505**.

Excluded synthetic rows: **13**.

Canonical synthetic counts:

| Category | Count |
|---|---:|
| synthetic_faithful | 253 |
| synthetic_hallucination | 252 |
| label_bin 0 | 253 |
| label_bin 1 | 252 |
| DM | 97 |
| MT | 218 |
| PG | 190 |

Excluded synthetic reasons:

| Reason | Rows |
|---|---:|
| `source_pair_in_official_test;task_reference_in_official_test` | 6 |
| `task_reference_in_official_test` | 3 |
| `task_reference_in_canonical_human_development` | 2 |
| `task_reference_in_canonical_human_development;task_reference_in_official_test` | 1 |
| `source_pair_in_canonical_human_development;task_reference_in_canonical_human_development` | 1 |

## 11. Locked fold assignments

Fold assignment file:

`codex\canonical_fold_assignments.csv`

Prompt 7C-A regenerated this file using:

```python
sklearn.model_selection.StratifiedKFold(
    n_splits=5,
    shuffle=True,
    random_state=42
)
```

Execution environment:

- Python executable: `external-artifacts/local-21bb07554028/python.exe`
- Python version: `3.11.9`
- scikit-learn version: `1.8.0`
- pandas version: `3.0.2`

The previous fallback assignment was preserved only for audit:

`codex\canonical_fold_assignments_fallback_audit.csv`

Stratum definition:

`stratum = task + "__" + label_bin`

Stratum counts:

| Stratum | Count |
|---|---:|
| DM__0 | 104 |
| DM__1 | 107 |
| MT__0 | 119 |
| MT__1 | 97 |
| PG__0 | 84 |
| PG__1 | 50 |

Fold sizes:

| Fold | Validation samples |
|---|---:|
| 1 | 113 |
| 2 | 112 |
| 3 | 112 |
| 4 | 112 |
| 5 | 112 |

Fold-by-stratum counts:

| Fold | DM__0 | DM__1 | MT__0 | MT__1 | PG__0 | PG__1 |
|---:|---:|---:|---:|---:|---:|---:|
| 1 | 21 | 22 | 24 | 20 | 16 | 10 |
| 2 | 21 | 21 | 23 | 20 | 17 | 10 |
| 3 | 21 | 21 | 24 | 19 | 17 | 10 |
| 4 | 21 | 21 | 24 | 19 | 17 | 10 |
| 5 | 20 | 22 | 24 | 19 | 17 | 10 |

All strata have at least 5 samples. Each `canonical_id` appears exactly once as a validation sample. No `exact_text_key` appears in more than one fold. The maximum fold-size difference is 1 sample.

Input SHA-256:

`754b66c6c4eca2e92902d0408db4854e922d7dfb396953a0cc043c5477bd6a9b`

Output fold-file SHA-256:

`f5a5964923806a23dd34a8bcc137f3cf489437e033d645e9d0845bf40792eb5d`

Optional task-reference audit:

- task-reference keys appearing in more than one canonical human sample: 5
- repeated task-reference keys spanning more than one fold: 3

## 12. Prompt 7D canonical feature outputs

Feature extraction was completed in Prompt 7D without official test-set use, Random Forest training, CV scoring, notebook modification, DOCX modification, or API call.

Output folder:

`codex\canonical_feature_outputs`

Final CSV outputs:

| File | Rows | Columns | SHA-256 |
|---|---:|---:|---|
| `canonical_human_nli_features.csv` | 561 | 7 | `10d96e0d1941fa9e284a09b9eda79fc0670c247b6b60789c95c9a394286a4366` |
| `canonical_human_similarity_features.csv` | 561 | 9 | `90fdab43830d7e4a792bd0c042ad7b9abf5cc423e54400fa7dcff3e5e820bd0b` |
| `canonical_human_14_features.csv` | 561 | 23 | `3038bd8752a94064e05389e03b063484a1191f9e9a6164f06d11b40688a6828b` |
| `canonical_synthetic_nli_features.csv` | 505 | 7 | `b755ff52b6012ea214e2c54f758752b18b77dce6bd2da2fc5d4aacdb53887c1e` |
| `canonical_synthetic_similarity_features.csv` | 505 | 9 | `fe39b8fc9ec65a2cdbc3455b04cd406eb1dcab08e30c42c524abad47b15f2665` |
| `canonical_synthetic_14_features.csv` | 505 | 23 | `3ba57e611df885a0afe9fd6a12f962d49590938c740afef48665a1d0a72fd462` |

Audit and metadata outputs:

| File | Rows/notes | SHA-256 |
|---|---:|---|
| `canonical_feature_quality_audit.csv` | 30 checks; all passed | `87db0e56e522fdf960d650d0f1af1b903d74260b4ee197093fa91e9f8b4db6b7` |
| `canonical_feature_compatibility_audit.csv` | 16 rows | `243ccdbb668f279425e57ca77e3e72d6c087df4e43592d5daacace7ca2058fac` |
| `canonical_feature_extraction_metadata.json` | environment, models, hashes, runtime notes | updated after final verification |
| `canonical_feature_extraction.log` | execution log | log file |

Canonical feature order:

1. `src_ent`
2. `src_neu`
3. `src_con`
4. `tgt_ent`
5. `tgt_neu`
6. `tgt_con`
7. `sim_src_hyp`
8. `sim_tgt_hyp`
9. `sim_src_tgt`
10. `sim_max`
11. `sim_min`
12. `sim_mean`
13. `sim_gap_tgt_src`
14. `sim_hyp_distance_from_truth`

Environment:

- Python executable: `external-artifacts/local-21bb07554028/python.exe`
- Python version: `3.11.9`
- torch version: `2.11.0+cpu`
- transformers version: `5.5.4`
- sentence-transformers version: `5.4.1`
- numpy version: `2.4.4`
- pandas version: `3.0.2`
- device: CPU
- CUDA: unavailable

Model cache snapshots:

- NLI: `external-artifacts/local-da623a571fc2/7296194b9009373def4f7c5dad292651e4b5cf4e`
- Similarity: `external-artifacts/local-54c26f7df1bd/e8c3b32edf5434bc2275fc9bab85f82640a19130`

Quality checks:

- 561 human rows and 505 synthetic rows verified.
- No missing feature values.
- No NaN/Inf feature values.
- NLI probability triples sum to approximately 1.
- NLI values are in `[0,1]`.
- Base similarity values are in `[-1,1]`.
- Derived similarity formulas passed with tolerance `1e-5`.

Compatibility audit:

- 64 of the 68 trial-derived canonical rows matched old human-labeled trial rows by normalized `(task, src, tgt, hyp)`.
- Mean/max absolute differences were tiny floating-point-level differences.
- Pearson and Spearman correlations were 1.0 for all directly comparable features.
- NLI permutation indicators showed same-label correlations approximately 1.0; no NLI label permutation was indicated.

Next stage:

- Run development-only CV for E1-E3 using `canonical_fold_assignments.csv` and `canonical_human_14_features.csv`.
- Run fixed diagnostic E4 using `canonical_synthetic_14_features.csv`.
- Do not use the official test benchmark until after development-CV selection.

## 13. Prompt 7E development-only CV outputs

Prompt 7E completed development-only cross-validation for E1-E3 and fixed diagnostic E4. No official test set was used. No pretrained model or feature extraction was executed. No DOCX, notebook, canonical manifest, fold file, or feature CSV was modified.

Script:

`codex\canonical_development_cv.py`

Output folder:

`codex\canonical_cv_outputs`

Environment:

- Python executable: `external-artifacts/local-21bb07554028/python.exe`
- Python version: `3.11.9`
- scikit-learn version: `1.8.0`
- numpy version: `2.4.4`
- pandas version: `3.0.2`
- scipy version: `1.17.1`
- CPU cores: 8

Random Forest configuration:

```python
RandomForestRegressor(
    n_estimators=500,
    random_state=42,
    n_jobs=-1
)
```

Prediction rule:

- target: `p_hallucination`
- predictions clipped to `[0, 1]`
- binary threshold: `0.5`
- no calibration
- no threshold tuning

CV summary:

| Experiment | Selection eligible | Overall OOF Accuracy | Overall OOF Spearman | Mean CV Accuracy | Mean CV Spearman |
|---|---:|---:|---:|---:|---:|
| E1_NLI_only | yes | 0.773619 | 0.689419 | 0.773609 | 0.688754 |
| E2_similarity_only | yes | 0.677362 | 0.534279 | 0.677370 | 0.535466 |
| E3_NLI_similarity | yes | 0.793226 | 0.739049 | 0.793189 | 0.738240 |
| E4_synthetic_diagnostic | no | 0.805704 | 0.723760 | 0.805673 | 0.721706 |

Selection result:

- selected configuration: `E3_NLI_similarity`
- selection rule: E1-E3 only; primary `overall_oof_accuracy`; secondary `overall_oof_spearman`
- E4 remains diagnostic-only and does not change the selected configuration.

Output files:

| File | Rows | SHA-256 |
|---|---:|---|
| `canonical_cv_fold_results.csv` | 20 | `a16abf8be8dd374d2a012447798330dc6a281c3c479caeac9f36bdb3f9b2698b` |
| `canonical_cv_oof_predictions.csv` | 2,244 | `b2a24952063bc1a404d8802513ab18b185864d28b2ae4556c2a07c86c09f7b9f` |
| `canonical_cv_summary.csv` | 4 | `59753ad49393cd2d8884441587f57119a36bd5a82b350e49cf29b098d77ed5ef` |
| `canonical_cv_per_task_results.csv` | 12 | `fd27cfcebd6867f057a787b8e3745a62659bc649ed4a0d1b2540b019993845a3` |
| `canonical_cv_feature_importance_by_fold.csv` | 210 | `c565c89ba7ea8b827b9c785679b5447a8acb3d9d06129c9b4c7bd3d0197e6da4` |
| `canonical_cv_model_selection.csv` | 1 | `99b334a8691e64475b256662b5ea3b06e9743c48ef6400589d157d39850df6ab` |
| `canonical_cv_metadata.json` | metadata | `e7fcdafa145a9bb618bc9d1b3998feb17b3ac70114b1b628af90245e91934185` |
| `canonical_feature_compatibility_unmatched_rows.csv` | 4 | `2140e6ecb48d5c7e4e6d523332adc19918ef0bb33a7f651676ec9d7c77a00ae5` |

Prompt 7D metadata correction:

- `canonical_feature_extraction_metadata.json` now records `resumptions_or_retries = 11` and includes `execution_notes`.
- Updated metadata SHA-256: `A35217C423697064AC03B102AE7AB8983758355283081DC83D730203DBD2D446`.

Next stage:

- official benchmark evaluation of the selected `E3_NLI_similarity` configuration may be run only in the next authorized prompt.
- Do not write final Chapter 6 until the official benchmark is completed or explicitly deferred.

## Prompt 7E-A canonical CV audit outputs

Prompt 7E-A preserved the initial Prompt 7E outputs in:

`codex\canonical_cv_outputs\prompt7e_initial_outputs\`

It then regenerated the canonical development-only CV outputs with explicit raw, clipped, and binary prediction columns:

- `y_pred_reg_raw`
- `y_pred_reg_clipped`
- `y_pred_bin`

The official test benchmark was not read or used. The reproducibility rerun was written to `canonical_cv_outputs/reproducibility_rerun/`, compared against the canonical outputs, and its files were removed after comparison. The directory may remain as an empty folder because folder removal was blocked by the local execution policy.

Locked Prompt 7E-A output files:

| File | Rows | Role |
|---|---:|---|
| `canonical_cv_fold_metrics.csv` | 20 | fold-level metrics for E1-E4 |
| `canonical_cv_overall_metrics.csv` | 4 | overall OOF metrics for E1-E4 |
| `canonical_cv_per_task_metrics.csv` | 12 | per-task metrics |
| `canonical_cv_confusion_matrices.csv` | 24 | overall and fold confusion matrices |
| `canonical_cv_feature_importance_summary.csv` | 42 | descriptive feature-importance summary |
| `canonical_cv_e4_vs_e3_diagnostic.csv` | 1 | diagnostic E4-E3 comparison |
| `e4_fixed_errors.csv` | 23 | samples fixed by E4 relative to E3 |
| `e4_introduced_errors.csv` | 16 | samples worsened by E4 relative to E3 |
| `canonical_cv_selection_decision.json` | metadata | deterministic selection decision |
| `canonical_cv_integrity_audit.csv` | 18 | integrity audit checks |
| `canonical_cv_reproducibility_audit.json` | metadata | reproducibility comparison |
| `canonical_cv_results_summary.md` | summary | human-readable results summary |
| `canonical_cv_execution.log` | log | timestamped execution log |
| `canonical_cv_experiment_metadata.json` | metadata | environment, parameters, hashes, audit status |

Locked selected configuration:

`E3_NLI_similarity`

Integrity audit passed and reproducibility audit passed.
