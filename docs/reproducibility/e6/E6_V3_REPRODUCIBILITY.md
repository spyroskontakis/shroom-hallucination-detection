# E6-v3 - frozen development milestone and publication scope

E6-v3 is the 36-feature extension of E6-v2 with two frozen HHEM consistency scores. Its completed result is **474/561**, accuracy **0.8449197860962567**, Spearman **0.7816945786401444**. It is the best verified accuracy among the completed E6 versions discussed here, on a reused development pool; it is not an independent test result. This publication adds no experiment, training, inference, evaluation suite or tuning.

## Research history

| Version | Features | Predetermined change | Correct/561 |
|---|---:|---|---:|
| E6 original / v1 | 25 | E5's 21 features plus external top-1 definition→hyp cosine and three NLI scores | 453 |
| E6-v2 | 34 | Nine scores from a second NLI evaluator: entailment/neutral/contradiction for reference→hyp, hyp→reference and selected definition→hyp | 473 |
| **E6-v3** | **36** | **Two HHEM consistency features: reference→hyp and selected definition→hyp** | **474** |
| E6-v4 | 43 | Three official BERTScore reference/hyp P/R/F1 features and four deterministic structural mismatch features, using a formally amended pinned compatibility environment | 468 |

The second NLI evaluator in v2 is `MoritzLaurer/DeBERTa-v3-large-mnli-fever-anli-ling-wanli@b3546ea6b0346eb6f8d5d68b13c7dc6d0376b3d7`. E6-v3 preserves all 34 v2 feature values and their order exactly. Its added evaluator is `vectara/hallucination_evaluation_model@58383384656cbaec2949a75a41f20e891e90a73b`, historical HHEM-1.0-open. Sigmoid is applied once to the single raw output logit; higher means greater consistency/support. The improvement from 473 to 474 concerns the entire two-feature HHEM block and does not establish which individual feature caused it.

Reference is tgt for DM/MT and src for PG; candidate is hyp. The reference/hyp feature covers all 561 rows. The definition/hyp feature covers 193 evidence-bearing DM rows; missing-definition scores are exactly zero on the remaining 368, with evidence availability unchanged. The saved v2 strings and selected v1 definition are reused; there is no new retrieval, reranking or router in v3. Historical reconstructed retrieval provenance limitations remain as documented in the original reports.

## Fixed evaluation and verified integrity

The canonical pool consists of 561 unique IDs (493 development_model_agnostic and 68 trial), with five locked validation folds of 113/112/112/112/112. Regression target is p_hallucination, predictions clipped to [0,1], binary threshold >=0.5. The full 18-parameter RandomForestRegressor configuration in `results/rag_e6_v3/config/run_config.json` is unchanged from v2: 500 estimators, random_state=42, max_features=1.0, min_samples_leaf=1, n_jobs=-1, with all remaining parameters explicitly frozen.

There were exactly **five RF fits, one OOF evaluation and zero baseline verification fits**. Saved OOF predictions, canonical IDs/folds/labels, 36-column finite values and numerical identity of the first 34 columns were verified read-only for publication. Accuracy uses unrounded predictions; Spearman uses predictions rounded to 12 decimal places, matching the frozen evaluation. No model was run to verify the publication.

All **1,327 protected artifacts** and all **439 completed-run manifest entries** passed SHA-256 verification. The subsequent error analysis was also preserved byte-for-byte and remains local. Inference/evaluation network attempts were **zero**, and the frozen reports/code record no official-test access. The model was acquired in an earlier explicitly authorized preparation phase; zero-network claims do not describe that acquisition. No official test was opened during this publication audit.

- Protocol SHA-256: `13e9737fc1881e6cd7ab8afccac42e5f173b000d714f971601a238dc26024a37`
- Configuration SHA-256: `a9d661b533425bc8b9c5cd0583f7e9c49b5fe40c60727a4430548121cbe55acc`
- Runtime: Python 3.11.9; torch 2.11.0 CPU; transformers 5.5.4; tokenizers 0.22.2; numpy 2.4.4; pandas 3.0.2; scipy 1.17.1; scikit-learn 1.8.0. Full configuration includes other pinned dependencies, CPU float32, batch size 2 and four torch intra/inter-op threads.

## What is published and what remains local

The reviewed subset consists of the original protocol/results, original scripts/tests, configuration/manifests, aggregate metrics and acquisition metadata. Frozen scientific files are not edited. Per-directory `.gitignore` explicitly allowlists this subset. `.gitattributes` preserves exact file bytes, including existing CRLF, so that published Git objects retain the frozen SHA-256 hashes.

Required local inputs include the frozen v2 matrix and OOF baseline, canonical development metadata/labels and folds, label-free reference/hyp and definition/hyp pairs, selected-definition mapping, and the pinned HHEM model/tokenizer assets. A clone is **not self-contained**: the repository's conservative publication policy excludes feature/prediction CSVs, raw text and definitions, datasets, model weights/tokenizers, downloaded third-party material, feature chunks, temporary/cache artifacts and operational logs. Original manifests retain hashes of these withheld artifacts and describe the full local run. Excluding them does not change their frozen hashes.

The full error-analysis report contains row-level raw examples and is not automatically republished. Its `node_modules` dependency junction was not traversed or staged. Inventory: **25 existing publication-safe files, 385 generated/model/cache files and 47 row-level/raw/local-only files**, plus the separately excluded local junction. The two publication-control files are new; this note is the only new documentation file, outside the frozen experiment directory. No file above 50 MB is included: the local 737,761,269-byte model weight file remains excluded. Secret scanning found no credentials/provider tokens/private keys in publication candidates. Necessary interpreter paths in frozen runtime provenance were retained; unnecessary raw diagnostic/local dumps remain excluded.

## Read-only status of the other untracked experiments

- `rag_e6_v2`: **completed**, score already observed, 473/561, accuracy 0.8431372549, Spearman 0.7775058305. Results, predictions, five-fit records and a completion manifest exist. It is not preparation-only or evidenced as abandoned.
- `rag_e8_rf_tuning_v1`: **completed**, score already observed, 452/561, accuracy 0.8057040998, Spearman 0.7528866687. Results, outer OOF predictions, nested evaluation manifests and 95 RF fits (90 inner + five outer) exist. It is not partial or preparation-only.

Those directories were inventoried and their existing completion hashes verified read-only. Neither was executed, edited or staged in this publication. `Augmentation Pipeline.txt` likewise remains untouched and untracked. Existing E7/E6-v4 milestones and their historical publication notes are unchanged.

The original [E6-v3 results](../../../research/experiments/phase2_rag_features/e6_feature_extensions/v3/results/reports/E6_V3_RESULTS.md) contain subgroup and paired statistics and the [protocol](../../../research/experiments/phase2_rag_features/e6_feature_extensions/v3/protocols/E6_V3_PROTOCOL.md) defines the fixed procedure. All findings remain **exploratory development-only** on a reused set. This milestone does not authorize E8 execution, another experiment or further optimization.
