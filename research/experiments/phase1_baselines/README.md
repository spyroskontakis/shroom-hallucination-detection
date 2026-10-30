# Phase 1: Semantic Features and Synthetic-Data Diagnostics

E1-E3 compare NLI, semantic similarity and their combination. E4 investigates synthetic-data augmentation. The experiments share implementations; they are not three independent baseline packages.

## Canonical evaluation

The [core pipeline guide](../../core_pipeline/README.md) links to the canonical code, fixed-fold records and evaluation decisions in `codex/`. The [shared CV implementation](../../../codex/canonical_development_cv.py) evaluates E1-E4 on the later 561-example human development pool. Canonical E4 is diagnostic-only and adds synthetic rows only to training folds.

Read the [canonical results summary](../../data_and_evaluation/canonical/results/canonical_561/canonical_cv_results_summary.md) for that evaluation. It is separate from the older settings below.

## Historical development experiments: 499 examples

The [integrated baseline notebook](../../../RAG/shroom_ensemble.ipynb) retains the earlier E1-E3 evaluation and development E4 work. Other distinct source versions are indexed under [exploratory analysis](../../exploratory_analysis/README.md).

The following aggregate CSVs are archived in this directory; their producer notebooks remain at the original paths.

| Record | Available table |
|---|---|
| Combined E1-E4 summary | [Development summary](e1_e3_baselines/results/development_499/development_experiment_summary.csv) |
| E1: NLI | [Fold results](e1_e3_baselines/results/development_499/e1_nli_dev_cv_results.csv) |
| E2: similarity | [Fold results](e1_e3_baselines/results/development_499/e2_similarity_dev_cv_results.csv) |
| E3: NLI and similarity | [Fold results](e1_e3_baselines/results/development_499/e3_nli_similarity_dev_cv_results.csv) |
| E4: synthetic diagnostic | [Fold results](e4_augmentation/results/development_499/e4_synthetic_dev_cv_results.csv) and [task results](e4_augmentation/results/development_499/e4_synthetic_dev_task_results.csv) |

The combined summary preserves E4 as excluded from model selection. These are historical development-499 records, not substitutes for the canonical-561 tables.

### Augmentation notebook variants

Four source versions retain their original sampling settings: [5 samples per task](../../../codex/data/5.%20Augmentation/5%20samples%20-%20augmentation_outputs_vertex/shroom_ensemble.ipynb), [20](../../../codex/data/5.%20Augmentation/20%20samples%20-%20augmentation_outputs_vertex/shroom_ensemble.ipynb), [50](../../../codex/data/5.%20Augmentation/50%20samples%20-%20augmentation_outputs_vertex/shroom_ensemble.ipynb) and [200](../../../codex/data/5.%20Augmentation/200%20samples%20-%20augmentation_outputs_vertex/shroom_ensemble.ipynb). The sampling setting is not a claim about the final number of generated rows.

## Historical ablation using labeled test data

The [older synthetic-ablation notebook](../../../data/7.%20Ablation%20Synthetic%20Data/7.Ablation_Synthetic_Data.ipynb) compares Trial-only and Trial-plus-Synthetic training using labeled-test-derived evaluation features. Its archived outputs are:

- [Overall results](e4_augmentation/historical_ablation/ablation_summary_results.csv) and [per-task results](e4_augmentation/historical_ablation/ablation_per_task_results.csv).
- [Feature importances](e4_augmentation/historical_ablation/ablation_feature_importance.csv).
- [Synthetic-ratio sweep](e4_augmentation/historical_ablation/ablation_synthetic_ratio_results.csv) and [synthetic-weight sweep](e4_augmentation/historical_ablation/ablation_synthetic_weight_results.csv).
- [Fixed errors by task/type](e4_augmentation/historical_ablation/fixed_errors_by_task_and_type.csv) and [introduced errors by task/type](e4_augmentation/historical_ablation/introduced_errors_by_task_and_type.csv).

These records are not canonical development results or an untouched test evaluation. Keep them separate from both development-499 and canonical-561 comparisons.

The notebooks have not been rewritten to follow the archive locations. A future run could recreate outputs at old paths. Full replay from the public repository has not been verified; review [data access](../../../docs/DATA_ACCESS.md) and [reproducibility](../../../docs/REPRODUCIBILITY.md) before execution. Migration checks do not independently confirm the saved metrics.

[Back to the research guide](../../README.md)
