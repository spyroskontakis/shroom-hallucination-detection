# Methodology Component Manifest — Prompt 7

Το manifest δημιουργήθηκε πριν από τη συγγραφή του Κεφαλαίου 5 στο `thesis_until_experiments_working.docx`. Βασίζεται σε ανάγνωση notebooks και αποθηκευμένων CSV/JSON artifacts, χωρίς επανεκτέλεση notebook, χωρίς feature extraction και χωρίς API calls.

| Component | Ακριβές notebook/αρχείο | Κελιά/συναρτήσεις ή section | Input | Output/features | Model/checkpoint | Parameters | Artifact που επιβεβαιώνει εκτέλεση | Κατάσταση |
|---|---|---|---|---|---|---|---|---|
| Dataset loading | `data/2. EDA/shroom_final_implementation/shroom_ensemble.ipynb` | cell 7, paths/loading configuration | SHROOM trial, labeled test, unlabeled train JSON | pandas DataFrames | Δεν εφαρμόζεται | `RANDOM_STATE=42`, `N_SPLITS=5`, `THRESHOLD=0.5`, `EVALUATION_TRACK="model-agnostic"` | JSON files: `trial-v1.json` 80 items, `test.model-agnostic.json` 1.500 items, `train.model-agnostic.json` 30.000 items | Implemented with reproducibility caveat |
| Label encoding | `data/2. EDA/shroom_final_implementation/shroom_ensemble.ipynb`; feature CSVs | preprocessing cells before feature extraction | `label`, `p(Hallucination)` | `label_bin`, `p_hallucination` | Δεν εφαρμόζεται | Hallucination → 1, Not Hallucination → 0, target `p_hallucination` | `data/4. NLI + Sim/nli_similarity_features_dataset.csv` columns `label_bin`, `p_hallucination` | Implemented and verified |
| p(Hallucination) regression target | Main notebook and ablation notebook | `evaluate_predictions`, `train_and_evaluate` | Human aggregate `p(Hallucination)` | Continuous training target | RandomForestRegressor downstream | Regression target clipped predictions to [0,1]; threshold 0.5 only for binary conversion | `nli_sim_baseline_oof_predictions.csv`, `ablation_predictions.csv` | Implemented and verified |
| Task-dependent semantic reference | Main notebook, augmentation cells 133–135, filtering cell 138 | `get_reference_text`, prompt construction, synthetic filtering | `src`, `tgt`, `hyp`, `task`, `ref` | Reference text for generation/filtering | Δεν εφαρμόζεται | PG uses source as reference; DM/MT use target as reference where implemented in augmentation/filtering | `filtered_synthetic_data.csv` column `reference_text`; `augmented_training_data.csv` | Implemented and verified |
| NLI feature extraction | `data/2. EDA/shroom_final_implementation/shroom_ensemble.ipynb`; `data/4. NLI + Sim/nli_features_dataset.csv` | cells 89–94, `get_nli_scores` | `src→hyp`, `tgt→hyp` text pairs | `src_ent`, `src_neu`, `src_con`, `tgt_ent`, `tgt_neu`, `tgt_con` | `microsoft/deberta-large-mnli` | transformers pipeline, `truncation=True`, `max_length=512`, `device=-1`, `top_k=None` | `data/4. NLI + Sim/nli_features_dataset.csv` rows=1.500, cols=21 | Implemented and verified |
| NLI label-ID mapping | Cached Hugging Face config for `microsoft/deberta-large-mnli` at `external-artifacts/local-f04cb147286e/config.json` | read-only configuration check, no inference and no notebook execution | model config JSON | `id2label`: 0=CONTRADICTION, 1=NEUTRAL, 2=ENTAILMENT; `label2id`: CONTRADICTION=0, NEUTRAL=1, ENTAILMENT=2 | `microsoft/deberta-large-mnli` | not applicable | cached `config.json` | Implemented and verified |
| Semantic similarity embeddings | Main notebook; `data/4. NLI + Sim/nli_similarity_features_dataset.csv` | cells 105–110 | `src`, `hyp`, `tgt` | normalized embeddings and cosine-style dot products | `sentence-transformers/all-mpnet-base-v2` | `batch_size=64`, `normalize_embeddings=True`, `show_progress_bar=True` | `data/4. NLI + Sim/nli_similarity_features_dataset.csv` rows=1.500, cols=29 | Implemented and verified |
| Cosine similarities | Main notebook | cells 107–109 | normalized `src`, `hyp`, `tgt` embeddings | `sim_src_hyp`, `sim_tgt_hyp`, `sim_src_tgt` | `sentence-transformers/all-mpnet-base-v2` | Dot product of normalized embeddings | `data/4. NLI + Sim/nli_similarity_features_dataset.csv` | Implemented and verified |
| Derived similarity features | Main notebook | cell 109 | basic similarity features | `sim_max`, `sim_min`, `sim_mean`, `sim_gap_tgt_src`, `sim_hyp_distance_from_truth` | Δεν εφαρμόζεται | max/min/mean over `sim_src_hyp`, `sim_tgt_hyp`; `sim_tgt_hyp - sim_src_hyp`; `1.0 - sim_tgt_hyp` | `data/4. NLI + Sim/nli_similarity_features_dataset.csv` | Implemented and verified |
| Feature merging | Main notebook; ablation notebook | cells 110, 112, 120, ablation cell 4 | NLI + similarity columns | 14-feature matrix for final RF configurations | Δεν εφαρμόζεται | feature_cols include six NLI + eight similarity features | `data/4. NLI + Sim/nli_similarity_features_dataset.csv`; `data/7. Ablation Synthetic Data/4.nli_similarity_features_dataset.csv` | Implemented and verified |
| RandomForestRegressor | Main notebook; ablation notebook | cells 98, 113, 120, 122; ablation cell 8 | feature matrices and `p_hallucination` | predicted continuous score | scikit-learn `RandomForestRegressor` | `n_estimators=500`, `random_state=42`, `n_jobs=-1` | OOF prediction CSVs and ablation prediction CSVs | Implemented and verified |
| Clipping | Main notebook; ablation notebook | cells 98, 113, 120; ablation cell 8 | RF regression outputs | scores clipped to [0,1] | Δεν εφαρμόζεται | `np.clip(pred, 0.0, 1.0)` | prediction CSVs with `y_pred_reg`/`pred_p_hallucination` | Implemented and verified |
| Threshold 0.5 | Main notebook; ablation notebook | cell 7 and evaluation cells | clipped regression score | binary label | Δεν εφαρμόζεται | score >= 0.5 → 1/Hallucination, otherwise 0/Not Hallucination | `*_oof_predictions.csv`, `ablation_predictions.csv` | Implemented and verified |
| Synthetic data generation | Main notebook; augmentation notebooks | cells 129, 133–136 | `train.model-agnostic.json`, task-balanced sampled unlabeled data | `synthetic_raw_data.csv` | Gemini via Vertex AI: primary `gemini-2.5-flash-lite`, fallback `gemini-2.5-flash` | `SAMPLES_PER_TASK=200`, `BATCH_SIZE=2`, `REQUEST_SLEEP=3.0`, `MAX_BATCH_RETRIES=2`, `RETRY_SLEEP_SECONDS=5`, `SKIP_FAILED_BATCHES=True`, `CHECKPOINT_MODE="gemini_batch_v3"` | `data/5. Augmentation/200 samples - augmentation_outputs_vertex/synthetic_raw_data.csv` rows=1.200 | Implemented with reproducibility caveat |
| Task-specific synthetic prompts | Main notebook | cell 133 and batch prompt in cell 134 | task, source, target, reference | faithful and hallucinated JSON fields | Gemini models above | PG reference=source; MT/DM reference=target; outputs short, English, JSON-only | `synthetic_raw_data.csv` columns `source_type`, `generation_mode` | Implemented and verified |
| Gemini model | Main notebook | cells 129–134 | batch prompt | JSON response | `gemini-2.5-flash-lite`; fallback `gemini-2.5-flash` | Vertex AI client through `google.genai`; smoke test disabled by default | `synthetic_raw_data.csv` with `generation_mode=gemini_batch_v3` | Implemented with reproducibility caveat |
| Checkpoints/resume mechanism | Main notebook | cell 136 | existing `synthetic_raw_data.csv` | remaining sample generation only | Gemini models above | completed `sample_id` recovery, batch checkpoint after progress, failed generation log | `synthetic_raw_data.csv`; possible `synthetic_failed_generation.csv` | Implemented with reproducibility caveat |
| Basic filtering | Main notebook | cell 138 | raw synthetic data | filtered candidates | Δεν εφαρμόζεται | non-empty `hyp`; `hyp_tokens` 3–200; remove exact reference copies; `hyp_tokens <= 3 * reference_tokens` | `filtered_synthetic_data.csv` rows=763 | Implemented and verified |
| Semantic filtering | Main notebook | cell 138 | basic-filtered synthetic data | `sim_ref_hyp`, semantic-filtered synthetic data | `sentence-transformers/all-mpnet-base-v2` | hallucination similarity 0.30–0.95; faithful similarity 0.75–0.99; `batch_size=64`, normalized embeddings | `filtered_synthetic_data.csv` rows=763, `sim_ref_hyp` min≈0.309, max≈0.987 | Implemented and verified |
| Balancing | Main notebook | cells 138, 140 | filtered synthetic data | balanced synthetic dataset | Δεν εφαρμόζεται | downsample by `label` to min_count, `random_state=42` | `filtered_synthetic_data_balanced.csv` rows=518, 259/259 labels | Implemented and verified |
| Feature extraction στα synthetic samples | `data/6. Feature Extraction on Augmented Training Data/shroom_ensemble.ipynb`; CSVs | feature extraction cells analogous to main pipeline | 80 trial + 518 balanced synthetic samples | NLI + similarity features for 598 rows | `microsoft/deberta-large-mnli`; `sentence-transformers/all-mpnet-base-v2` | same NLI/similarity settings where visible; feature artifacts saved | `data/6. Feature Extraction on Augmented Training Data/nli_similarity_features_dataset.csv` rows=598, cols=25 | Implemented and verified |
| Synthetic ratio ablation | `data/7. Ablation Synthetic Data/7.Ablation_Synthetic_Data.ipynb` | cell 27 | human trial rows + sampled synthetic rows | ratio result grid | RandomForestRegressor | ratios 0.0, 0.25, 0.5, 0.75, 1.0; stratified synthetic sample by label; `random_state=42` | `ablation_synthetic_ratio_results.csv` rows=5 | Implemented and verified |
| Synthetic weighting ablation | `data/7. Ablation Synthetic Data/7.Ablation_Synthetic_Data.ipynb` | cell 29 | 80 human + 518 synthetic rows | weight result grid | RandomForestRegressor | human weight 1.0; synthetic weights 0.1, 0.25, 0.5, 0.75, 1.0 | `ablation_synthetic_weight_results.csv` rows=5 | Implemented and verified |
| Fixed/introduced errors | `data/7. Ablation Synthetic Data/7.Ablation_Synthetic_Data.ipynb` | cell 20 | prediction CSV for Trial only and Trial + Synthetic | fixed/introduced error artifacts | Δεν εφαρμόζεται | set comparison over misclassified `id`s | `errors_fixed_by_synthetic.csv` rows=77; `errors_introduced_by_synthetic.csv` rows=124 | Partially implemented |
| Confusion/error-type artifacts | Ablation artifacts | saved CSVs | false positive/false negative records | grouped counts by task and error type | Δεν εφαρμόζεται | derived from predictions and correctness flags | `fixed_errors_by_task_and_type.csv` rows=3; `introduced_errors_by_task_and_type.csv` rows=3 | Partially implemented |
| Evaluation protocol A | Main notebook | cells 98, 113, 120 | `data/4. NLI + Sim` feature matrix from labeled model-agnostic test set | 5-fold OOF predictions | RandomForestRegressor | `StratifiedKFold(n_splits=5, shuffle=True, random_state=42)` with task+label stratification | `nli_sim_baseline_cv_results.csv`; `nli_sim_baseline_oof_predictions.csv` | Implemented with protocol caveat |
| Evaluation protocol B | Ablation notebook | cells 6, 8, 10 | trial-only or trial+synthetic training; model-agnostic test feature matrix | test-set predictions and summaries | RandomForestRegressor | train on 80 trial or 598 augmented rows; evaluate on 1.500 model-agnostic test rows | `ablation_summary_results.csv`; `ablation_predictions.csv` | Implemented with protocol caveat |

## Remaining Methodology TODOs

- [[TODO METHODOLOGY: απαιτείται οριστικοποίηση του evaluation protocol πριν από τη συγγραφή του Κεφαλαίου 6.]]
- [[TODO SOURCE: απαιτείται πρωτογενής πηγή για DeBERTa]]
- [[TODO METHODOLOGY: απαιτείται επιβεβαίωση πλήρους clean Run All για τα computationally expensive notebooks, εάν ζητηθεί πλήρης αναπαραγωγή.]]

## Prompt 7A update

- Read-only cached config check for `microsoft/deberta-large-mnli` confirmed `id2label`: `0=CONTRADICTION`, `1=NEUTRAL`, `2=ENTAILMENT`; no inference, download, API call, feature extraction or notebook execution was performed.
- The NLI label-ID mapping TODO was removed because the mapping is now verified from an existing cached config.
- The DeBERTa primary-source TODO remains open.
- The ablation design was clarified into E1?E4 feature-group ablations and separate synthetic-data investigations.

## Prompt 7D update — canonical feature extraction

Canonical feature extraction was completed with common code for the locked canonical data:

| Component | Artifact | Rows | Features | Status |
|---|---:|---:|---|---|
| Human NLI features | `canonical_feature_outputs/canonical_human_nli_features.csv` | 561 | `src_ent`, `src_neu`, `src_con`, `tgt_ent`, `tgt_neu`, `tgt_con` | Completed |
| Human semantic similarity features | `canonical_feature_outputs/canonical_human_similarity_features.csv` | 561 | eight similarity features | Completed |
| Human 14-feature matrix | `canonical_feature_outputs/canonical_human_14_features.csv` | 561 | six NLI + eight similarity features | Completed |
| Synthetic diagnostic NLI features | `canonical_feature_outputs/canonical_synthetic_nli_features.csv` | 505 | six NLI features | Completed |
| Synthetic diagnostic semantic similarity features | `canonical_feature_outputs/canonical_synthetic_similarity_features.csv` | 505 | eight similarity features | Completed |
| Synthetic diagnostic 14-feature matrix | `canonical_feature_outputs/canonical_synthetic_14_features.csv` | 505 | six NLI + eight similarity features | Completed |

Environment and checkpoints:

- Python executable: `external-artifacts/local-21bb07554028/python.exe`
- Device: CPU (`torch 2.11.0+cpu`, CUDA unavailable)
- NLI checkpoint: `microsoft/deberta-large-mnli`
- Sentence embedding checkpoint: `sentence-transformers/all-mpnet-base-v2`
- NLI mapping confirmed during inference: `0=CONTRADICTION`, `1=NEUTRAL`, `2=ENTAILMENT`
- No Random Forest training, CV scoring, official test-set use, notebook modification, DOCX modification, or API call was performed.

Quality checks passed; compatibility audit with old trial features found 64 matched trial-derived rows with near-identical values and no indication of NLI label permutation.

## Prompt 7E update — development-only CV

Development-only CV was completed using only canonical development artifacts:

- `canonical_feature_outputs/canonical_human_14_features.csv`
- `canonical_feature_outputs/canonical_synthetic_14_features.csv`
- `canonical_fold_assignments.csv`

No official test set was used.

| Experiment | Feature set | Synthetic data | Role | Overall OOF Accuracy | Overall OOF Spearman |
|---|---|---:|---|---:|---:|
| E1_NLI_only | six NLI features | no | selection-eligible | 0.773619 | 0.689419 |
| E2_similarity_only | eight semantic similarity features | no | selection-eligible | 0.677362 | 0.534279 |
| E3_NLI_similarity | all 14 features | no | selection-eligible | 0.793226 | 0.739049 |
| E4_synthetic_diagnostic | all 14 features | yes, training folds only | diagnostic-only | 0.805704 | 0.723760 |

Selection rule:

- E1-E3 only;
- primary criterion: overall OOF Accuracy;
- secondary criterion: overall OOF Spearman.

Selected development configuration:

`E3_NLI_similarity`

E4 remains diagnostic-only and did not participate in model selection, even though its diagnostic Accuracy was higher.

Artifacts:

- `canonical_cv_outputs/canonical_cv_summary.csv`
- `canonical_cv_outputs/canonical_cv_fold_results.csv`
- `canonical_cv_outputs/canonical_cv_oof_predictions.csv`
- `canonical_cv_outputs/canonical_cv_per_task_results.csv`
- `canonical_cv_outputs/canonical_cv_feature_importance_by_fold.csv`
- `canonical_cv_outputs/canonical_cv_model_selection.csv`
- `canonical_cv_outputs/canonical_cv_metadata.json`

Prompt 7E did not modify notebooks, DOCX files, canonical manifests, folds, or feature CSVs.

## Prompt 7E-A update — CV audit and reproducibility lock

Prompt 7E-A extended the development-only CV script without changing canonical inputs, fold assignments, feature values, feature sets, Random Forest parameters, clipping, threshold, or selection eligibility.

Implementation script:

- `canonical_development_cv.py`

Canonical inputs:

- `canonical_feature_outputs/canonical_human_14_features.csv`
- `canonical_feature_outputs/canonical_synthetic_14_features.csv`
- `canonical_fold_assignments.csv`

Prediction outputs now explicitly store:

- `y_pred_reg_raw`
- `y_pred_reg_clipped`
- `y_pred_bin`

Metrics use clipped continuous predictions for Spearman and thresholded clipped predictions for Accuracy, Precision, Recall, F1, and confusion matrices.

Locked experiment roles:

| Experiment | Features | Synthetic training rows | Selection role |
|---|---:|---:|---|
| E1_NLI_only | 6 | 0 | selection-eligible |
| E2_similarity_only | 8 | 0 | selection-eligible |
| E3_NLI_similarity | 14 | 0 | selection-eligible |
| E4_synthetic_diagnostic | 14 | 505 per fold | diagnostic-only |

Locked selected development configuration:

`E3_NLI_similarity`

Audit artifacts:

- `canonical_cv_outputs/canonical_cv_integrity_audit.csv`
- `canonical_cv_outputs/canonical_cv_reproducibility_audit.json`
- `canonical_cv_outputs/canonical_cv_selection_decision.json`
- `canonical_cv_outputs/canonical_cv_experiment_metadata.json`

Integrity audit passed. Reproducibility audit passed. The official test set was not used; no pretrained model, feature extraction, API call, notebook modification, DOCX modification, canonical manifest modification, fold modification, or feature-value modification was performed.

Remaining methodology blocker:

- The selected `E3_NLI_similarity` configuration still requires the next authorized official benchmark evaluation before final Chapter 6 experimental reporting can be completed.
