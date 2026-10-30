# Core Pipeline and Canonical Evaluation

The shared preparation, feature and CV code remains in `codex/`. The recorded fold-generation script is under `research/data_and_evaluation/canonical/scripts/`. Other experiment paths and frozen records are unchanged.

| Step | Implementation or record |
|---|---|
| Data preparation and normalization | [canonical_evaluation_data_prep.py](../../codex/canonical_evaluation_data_prep.py) |
| NLI and semantic-similarity features | [canonical_feature_extraction.py](../../codex/canonical_feature_extraction.py) |
| Recorded fold-generation procedure | [regenerate_canonical_folds_sklearn.py](../data_and_evaluation/canonical/scripts/regenerate_canonical_folds_sklearn.py) |
| Shared E1-E4 cross-validation | [canonical_development_cv.py](../../codex/canonical_development_cv.py) |
| Evaluation decisions | [Protocol](../data_and_evaluation/canonical/protocols/evaluation_protocol_decision.md) and [data description](../data_and_evaluation/canonical/protocols/evaluation_data_manifest.md) |
| Component ownership and methodology | [Methodology manifest](../data_and_evaluation/canonical/protocols/methodology_component_manifest.md) |

The canonical evaluation uses 561 human-labeled examples and five shared folds stratified by task and binary label. E1, E2 and E3 use six NLI features, eight similarity features and their 14-feature combination. Canonical E4 adds 505 synthetic examples to each training fold, not to validation, and is excluded from model selection.

## Available evaluation records

The canonical-561 aggregate records are under `research/data_and_evaluation/canonical/results/canonical_561/`. Their contents and recorded historical hashes are unchanged. They are historical evaluation evidence, not inputs that should be regenerated to fit this layout.

- [Canonical results summary](../data_and_evaluation/canonical/results/canonical_561/canonical_cv_results_summary.md)
- [Overall OOF metrics](../data_and_evaluation/canonical/results/canonical_561/canonical_cv_overall_metrics.csv)
- [Per-task metrics](../data_and_evaluation/canonical/results/canonical_561/canonical_cv_per_task_metrics.csv)
- [E4 versus E3 diagnostic comparison](../data_and_evaluation/canonical/results/canonical_561/canonical_cv_e4_vs_e3_diagnostic.csv)
- [Model-selection record](../data_and_evaluation/canonical/results/canonical_561/canonical_cv_selection_decision.json)
- [Public canonical ID/fold projection](../../manifests/canonical_fold_assignments.public.csv)

The public fold projection contains only IDs and fold assignments. It is not a replacement for the full canonical fold file or its required schema. Full manifests, row-level features and other original inputs are not included here; do not regenerate or replace frozen folds merely to make a script run.

This canonical evaluation is separate from the [historical development-499 and test-set ablation records](../experiments/phase1_baselines/README.md). Exact replay from the public files alone has not been verified; see [data access](../../docs/DATA_ACCESS.md) and [reproducibility](../../docs/REPRODUCIBILITY.md).

[Back to the research guide](../README.md)

## Historical canonical records

The three protocol documents and these aggregate audits retain historical paths, hashes and results; they are not current run instructions.

- [Feature compatibility audit](../data_and_evaluation/canonical/historical_records/feature_extraction/canonical_feature_compatibility_audit.csv)
- [Feature quality audit](../data_and_evaluation/canonical/historical_records/feature_extraction/canonical_feature_quality_audit.csv)

The protocol is now linked above at its new location. Its [original version at the baseline commit](https://github.com/spyroskontakis/shroom-hallucination-detection/blob/11822d92070cd29360445cb4dacd8d110c655248/codex/evaluation_protocol_decision.md) and the [E11 audit in that original layout](https://github.com/spyroskontakis/shroom-hallucination-detection/blob/11822d92070cd29360445cb4dacd8d110c655248/RAG/results/phase3_e11_task_adaptation/E11_DATA_AUDIT.md#L67) provide historical context. The unchanged local E11 audit retains its old relative protocol link (historical exception H1).

The feature producer still writes the two CSVs at their legacy paths. Do not run it in the repository; a future run requires separately approved output isolation and dependency adaptation. These archival moves do not verify experiment reproduction.

The unchanged CV producer still defaults to legacy output paths and has import-time output-directory creation. Do not import or execute it directly in the checkout. Future execution requires explicit external output isolation, including every CSV/JSON/log writer and compatibility-row output. Moving the records does not certify a new run or make the missing original features and datasets available.
