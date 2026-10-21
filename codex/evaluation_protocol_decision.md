# Evaluation protocol decision — Prompt 7B

Scope: read-only audit and protocol decision. No DOCX, notebook, model, API, or feature-extraction execution was performed.

## 1. Decision summary

The raw 80 + 499 = 579 human-labeled pool is **not safe as-is** for canonical cross-validation, because the read-only overlap audit found exact duplicate `(task, src, tgt, hyp)` items between:

- `codex\data\Trial\SHROOM_trial-v1.1\trial-v1.json`
- `Dev\SHROOM_dev-v2\val.model-agnostic.json`

Observed duplicate structure:

- 12 exact trial/development duplicate text triples.
- 1 additional exact duplicate text triple within the model-agnostic development split.
- 566 unique text triples after concatenating trial + model-agnostic development and deduplicating by `(task, src, tgt, hyp)` before internal-conflict and development-test overlap removal.

Canonical decision:

1. Use the Prompt 7C canonical human-labeled development pool derived from trial + model-agnostic development after duplicate handling and exact development-test overlap removal.
2. The canonical pool size for cross-validation is **561 human-labeled samples**, not the raw 579 rows.
3. Plain `StratifiedKFold` over the raw 579 rows is not permitted; the locked fold file is based only on the canonical 561-row manifest.

## 2. Role of each split

| Split/artifact | Role in corrected protocol |
|---|---|
| Trial set (`trial-v1.json`, 80 rows) | Human-labeled development evidence; can be used only after duplicate handling against model-agnostic development. |
| Model-agnostic development set (`val.model-agnostic.json`, 499 rows) | Main human-labeled development evidence; can be merged with trial only after duplicate handling. |
| Model-aware development set (`val.model-aware.v2.json`, 501 rows) | Descriptive comparison only for this model-agnostic thesis pipeline, unless a separate model-aware protocol is explicitly defined. |
| Unlabeled model-agnostic train (`train.model-agnostic.json`, 30,000 rows) | Source pool from which synthetic samples were generated. It must not contribute human labels. |
| Canonical diagnostic synthetic data (`canonical_synthetic_diagnostic_manifest.csv`, 505 rows) | Diagnostic auxiliary training data only, never validation data. |
| Official labeled model-agnostic test (`test.model-agnostic.json`, 1,500 rows) | Final official test benchmark only after model/configuration selection from development CV. Because it has already been used in previous exploratory artifacts, it must not be described as pristine or fully independent. |

## 3. Canonical protocol

Recommended canonical protocol:

1. Build the human-labeled model-agnostic development pool from:
   - `codex\data\Trial\SHROOM_trial-v1.1\trial-v1.json`
   - `Dev\SHROOM_dev-v2\val.model-agnostic.json`
2. Use the locked 561-row `canonical_human_development_manifest.csv`.
3. Use 5-fold cross-validation over the canonical human-labeled pool.
4. Preserve the same fold assignment for E1–E4.
5. Use stratification by `task + binary label`.
6. The validation fold must contain only human-labeled samples.
7. Synthetic samples may appear only in the training portion of a fold, and only in the E4 diagnostic setting.

## 4. Experiments

| Experiment | Features | Synthetic data | Status in corrected protocol |
|---|---|---:|---|
| E1 | 6 NLI features | No | Eligible for main development-CV comparison. |
| E2 | 8 semantic similarity features | No | Eligible for main development-CV comparison. |
| E3 | 14 NLI + semantic similarity features | No | Eligible for main development-CV comparison. |
| E4 | Same 14 features | Yes, training folds only | Diagnostic-only unless a later prompt explicitly authorizes synthetic-data model selection. |

## 5. Synthetic-data decision

Decision: **A — diagnostic-only**.

Rationale:

- The synthetic set is generated and filtered heuristically.
- The current artifacts already include ratio/weight sweeps, but those were evaluated in a historical protocol that used the labeled model-agnostic test set.
- To avoid optimistic conclusions, synthetic-data ratio/weight tuning should not be used for final model selection at this stage.

Current locked handling:

- Use the 505 canonical diagnostic synthetic rows only as a fixed E4 diagnostic comparison.
- In every CV fold, add synthetic rows only to the training split.
- Never place synthetic rows in validation folds.
- Do not tune synthetic ratio, synthetic weights, threshold, or calibration from the official test benchmark.

If the supervisor later wants synthetic data to be eligible for final selection, that must be a separate locked decision using development-only CV and explicit leakage controls.

## 6. Model and prediction rule

Model:

- `RandomForestRegressor`
- `n_estimators=500`
- `random_state=42`
- `n_jobs=-1`

Target and post-processing:

- Target: `p_hallucination`
- Clip predicted probabilities to `[0, 1]`
- Binary threshold: `0.5`
- No threshold tuning
- No Platt scaling
- No isotonic regression
- No probability calibration

## 7. Metrics and selection rule

Primary metrics:

- Mean CV Accuracy
- Overall out-of-fold Accuracy
- Mean CV Spearman
- Overall out-of-fold Spearman

Supplementary metrics:

- Precision
- Recall
- F1
- Confusion matrix
- Per-task Accuracy
- Per-task Spearman
- Fold-level standard deviation

Selection rule:

1. Select the main model among E1–E3 using development-only CV.
2. Accuracy is the primary criterion.
3. Spearman is a secondary/tie-break criterion.
4. E4 remains diagnostic-only under the current decision.
5. The official test benchmark must not be used for model selection, threshold selection, synthetic ratio/weight selection, or feature selection.

## 8. Official test benchmark wording

Required wording:

> official test benchmark με περιορισμό λόγω προηγούμενης διερευνητικής χρήσης του test set

Do not call the labeled model-agnostic test set:

- untouched
- pristine
- fully independent
- unbiased final estimate

It may be used as an official benchmark after development-CV selection, with the above caveat.

## 9. Contamination and leakage caveats

Read-only audit found:

- 12 exact duplicate text triples between trial and model-agnostic development.
- 1 exact duplicate text triple within model-agnostic development.
- 4 exact duplicate text triples between model-agnostic development and model-agnostic test.
- 5 source-pair overlaps between balanced synthetic data and model-agnostic test, but 0 exact synthetic/test text-triple overlaps.
- 1 source-pair overlap between balanced synthetic data and model-agnostic development, but 0 exact synthetic/development text-triple overlaps.

These observations do not invalidate the project, but they require careful wording and leakage controls.

## 10. Leakage prohibitions

The corrected protocol must not:

- use official test labels for model selection, hyperparameter tuning, threshold tuning, calibration, synthetic ratio selection, synthetic weight selection, or feature selection;
- place synthetic samples in validation folds;
- allow exact duplicate text triples to appear in both training and validation folds;
- describe historical test-set results as unbiased final estimates;
- describe the test set as pristine or untouched.

## 11. Next execution needed

Before Chapter 6 can be written, execute a new development-only experiment pipeline that:

1. creates a deduplicated human-labeled pool from trial + model-agnostic development;
2. generates or attaches the missing 6 NLI + 8 semantic similarity features for the 499 model-agnostic development rows;
3. reuses or carefully remaps the existing 80 trial feature rows from the augmented feature artifact, or recomputes trial features consistently with development;
4. runs locked 5-fold development CV for E1–E3;
5. optionally runs fixed E4 as diagnostic-only with synthetic data in training folds only;
6. only after selection, evaluates the selected configuration on the official labeled model-agnostic test benchmark with the required caveat.

## 12. Prompt 7C locked canonical data decision

Prompt 7C created the canonical manifests and locked the fold assignments before feature extraction.

### Final canonical human pool

Final canonical human development samples: **561**.

Derivation:

1. Start from 80 trial rows + 499 model-agnostic development rows = 579 raw human-labeled rows.
2. Remove 12 duplicate trial rows because their exact text keys also occur in model-agnostic development. Development rows take precedence.
3. Exclude the internal model-agnostic development duplicate group because it has annotation conflict: binary labels agree, but `p(Hallucination)` and individual annotation lists differ.
4. Remove 4 exact development-test overlaps from the human development pool. The corresponding official test rows are not removed.

Final source composition:

- `development_model_agnostic`: 493 rows
- `trial`: 68 rows

### Duplicate precedence policy

Trial-development duplicates:

- keep the model-agnostic development row;
- remove the duplicate trial row;
- do not average labels or probabilities;
- record whether `label_bin`, `p_hallucination`, and individual annotation lists agree.

Internal development duplicates:

- if `label_bin`, `p_hallucination`, and individual annotation lists agree, keep one row;
- if any annotation conflict exists, exclude the whole duplicate group as `excluded_annotation_conflict`.

In the observed internal development duplicate group, the binary labels agree, but `p(Hallucination)` and individual annotation lists do not agree. Therefore both rows in that duplicate group were excluded.

### Exact development-test overlap removal

Exact development-test overlaps removed from the human development pool: **4**.

These rows were recorded in:

`codex\excluded_human_test_overlaps.csv`

The official test rows remain unchanged. The final benchmark wording remains:

> official test benchmark με περιορισμό λόγω προηγούμενης διερευνητικής χρήσης του test set

### Canonical synthetic diagnostic set

Final canonical diagnostic synthetic samples: **505** out of 518.

Excluded synthetic rows: **13**.

Synthetic rows were excluded if their `source_pair_key` or `task_reference_key` occurred in either:

- the final canonical human development pool, or
- the official model-agnostic test set.

E4 remains diagnostic-only.

### Locked fold assignment

Fold assignments were written to:

`codex\canonical_fold_assignments.csv`

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

All strata have at least 5 samples.

Prompt 7C-A replaced the earlier audit fallback with final fold assignments generated by:

```python
sklearn.model_selection.StratifiedKFold(
    n_splits=5,
    shuffle=True,
    random_state=42
)
```

Rows were sorted deterministically by `canonical_id` before splitting. The previous fallback assignment is preserved only for audit in:

`codex\canonical_fold_assignments_fallback_audit.csv`

Fold sizes:

| Fold | Validation samples |
|---|---:|
| 1 | 113 |
| 2 | 112 |
| 3 | 112 |
| 4 | 112 |
| 5 | 112 |

Validation-fold assignment checks passed:

- each `canonical_id` appears exactly once as a validation sample;
- no `exact_text_key` appears in more than one fold;
- the maximum fold-size difference is 1 sample;
- the same fold assignments are locked for E1-E4.

### Feature extraction decision

For the next stage, features must be recomputed for the entire canonical human development pool, including trial-derived rows. The older 80 trial features from the 598-row augmented artifact must not be used as the primary source.

Rationale:

- common code;
- common checkpoints;
- common schema;
- common row mapping;
- avoidance of inconsistencies between older trial features and newly generated development features.

## 13. Prompt 7E development-only selection decision

Development-only CV was completed for E1-E3 using the locked canonical folds. Fixed E4 was run as diagnostic-only with canonical synthetic data added only to the training portion of each fold.

Selection rule:

1. Consider only E1-E3.
2. Use overall out-of-fold Accuracy as the primary criterion.
3. Use overall out-of-fold Spearman as the secondary/tie-break criterion.
4. Do not allow E4 to change the selected configuration.
5. Do not use the official test benchmark for selection.

Development-only results:

| Experiment | Selection eligible | Overall OOF Accuracy | Overall OOF Spearman |
|---|---:|---:|---:|
| E1_NLI_only | yes | 0.773619 | 0.689419 |
| E2_similarity_only | yes | 0.677362 | 0.534279 |
| E3_NLI_similarity | yes | 0.793226 | 0.739049 |
| E4_synthetic_diagnostic | no | 0.805704 | 0.723760 |

Selected development configuration:

`E3_NLI_similarity`

E4 remains diagnostic-only. Its result may be discussed as a development-only diagnostic observation, but it must not be presented as the selected final configuration unless a later prompt explicitly changes the protocol.

## 14. Prompt 7E-A locked CV audit and reproducibility decision

Prompt 7E-A completed the missing CV audit deliverables and performed a reproducibility rerun using the same canonical development inputs, locked folds, feature sets, Random Forest parameters, clipping rule, and binary threshold.

The deterministic selection rule is now fully locked:

1. Consider only `E1_NLI_only`, `E2_similarity_only`, and `E3_NLI_similarity`.
2. Select the highest overall out-of-fold Accuracy.
3. If there is an exact tie, select the higher overall out-of-fold Spearman.
4. If there is still an exact tie, select the experiment with fewer predictor features: E1=6, E2=8, E3=14.
5. Keep `E4_synthetic_diagnostic` diagnostic-only.

Locked Prompt 7E-A development-only results:

| Experiment | Selection eligible | Overall OOF Accuracy | Overall OOF Spearman |
|---|---:|---:|---:|
| E1_NLI_only | yes | 0.773619 | 0.689355 |
| E2_similarity_only | yes | 0.677362 | 0.534292 |
| E3_NLI_similarity | yes | 0.793226 | 0.739040 |
| E4_synthetic_diagnostic | no | 0.805704 | 0.723751 |

Selected development configuration remains:

`E3_NLI_similarity`

Integrity audit status: passed.

Reproducibility audit status: passed.

Maximum absolute raw prediction difference between canonical run and reproducibility rerun: `3.3306690738754696e-16`.

Maximum absolute clipped prediction difference between canonical run and reproducibility rerun: `3.3306690738754696e-16`.

The Prompt 7E selection, Accuracy values, binary predictions, and confusion matrices remained unchanged. Prompt 7E-A supersedes the earlier Spearman display values with the reproducibility-stable Spearman values above, computed after deterministic rounding of clipped predictions for rank-correlation stability.

The official test benchmark was not used. Chapter 6 must still wait for the next authorized official benchmark step or an explicit decision to defer it.
