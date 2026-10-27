# Core Pipeline and Canonical Evaluation

The shared canonical pipeline remains in `codex/`. This page links to its implementation without changing the paths used by later experiments and frozen records.

| Step | Implementation or record |
|---|---|
| Data preparation and normalization | [canonical_evaluation_data_prep.py](../../codex/canonical_evaluation_data_prep.py) |
| NLI and semantic-similarity features | [canonical_feature_extraction.py](../../codex/canonical_feature_extraction.py) |
| Recorded fold-generation procedure | [regenerate_canonical_folds_sklearn.py](../../codex/regenerate_canonical_folds_sklearn.py) |
| Shared E1-E4 cross-validation | [canonical_development_cv.py](../../codex/canonical_development_cv.py) |
| Evaluation decisions | [Protocol](../../codex/evaluation_protocol_decision.md) and [data description](../../codex/evaluation_data_manifest.md) |
| Component ownership and methodology | [Methodology manifest](../../codex/methodology_component_manifest.md) |

The canonical evaluation uses 561 human-labeled examples and five shared folds stratified by task and binary label. E1, E2 and E3 use six NLI features, eight similarity features and their 14-feature combination. Canonical E4 adds 505 synthetic examples to each training fold, not to validation, and is excluded from model selection.

## Available evaluation records

- [Canonical results summary](../../codex/canonical_cv_outputs/canonical_cv_results_summary.md)
- [Overall OOF metrics](../../codex/canonical_cv_outputs/canonical_cv_overall_metrics.csv)
- [Per-task metrics](../../codex/canonical_cv_outputs/canonical_cv_per_task_metrics.csv)
- [E4 versus E3 diagnostic comparison](../../codex/canonical_cv_outputs/canonical_cv_e4_vs_e3_diagnostic.csv)
- [Model-selection record](../../codex/canonical_cv_outputs/canonical_cv_selection_decision.json)
- [Public canonical ID/fold projection](../../manifests/canonical_fold_assignments.public.csv)

The public fold projection contains only IDs and fold assignments. It is not a replacement for the full canonical fold file or its required schema. Full manifests, row-level features and other original inputs are not included here; do not regenerate or replace frozen folds merely to make a script run.

This canonical evaluation is separate from the [historical development-499 and test-set ablation records](../experiments/phase1_baselines/README.md). Exact replay from the public files alone has not been verified; see [data access](../../docs/DATA_ACCESS.md) and [reproducibility](../../docs/REPRODUCIBILITY.md).

[Back to the research guide](../README.md)
