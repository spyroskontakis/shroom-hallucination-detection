# Core Pipeline and Canonical Evaluation

Preparation, feature extraction, shared CV and the recorded fold-generation source are under research/data_and_evaluation/canonical/. The two newly relocated preparation/feature sources keep their exact historical bytes; they are not newly adapted runnable entry points. Historical replay requires the validated original layout and authentic inputs. One canonical metadata file is in the selected public-baseline archive, beside the unchanged E11 audit namespace, so their original relative link still resolves.

| Step | Implementation or record |
|---|---|
| Data preparation and normalization | [canonical_evaluation_data_prep.py](../data_and_evaluation/canonical/scripts/canonical_evaluation_data_prep.py) |
| NLI and semantic-similarity features | [canonical_feature_extraction.py](../data_and_evaluation/canonical/scripts/canonical_feature_extraction.py) |
| Recorded fold-generation procedure | [regenerate_canonical_folds_sklearn.py](../data_and_evaluation/canonical/scripts/regenerate_canonical_folds_sklearn.py) |
| Shared E1-E4 cross-validation | [canonical_development_cv.py](../data_and_evaluation/canonical/scripts/canonical_development_cv.py) |
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

The protocol is now linked above at its new location. Its [original version at the baseline commit](https://github.com/spyroskontakis/shroom-hallucination-detection/blob/11822d92070cd29360445cb4dacd8d110c655248/codex/evaluation_protocol_decision.md) and the [E11 audit in that original layout](https://github.com/spyroskontakis/shroom-hallucination-detection/blob/11822d92070cd29360445cb4dacd8d110c655248/RAG/results/phase3_e11_task_adaptation/E11_DATA_AUDIT.md#L67) provide historical context. The unchanged archived E11 audit retains its old relative protocol link, which remains broken (historical exception H1).

The feature producer still writes the two CSVs at their legacy paths. Do not run it in the repository; a future run requires separately approved output isolation and dependency adaptation. These archival moves do not verify experiment reproduction.

The adapted CV producer no longer creates an output directory at import. Its entry point requires a new absolute CANONICAL_CV_OUTPUT_DIR and an existing absolute CANONICAL_CV_TEMP_DIR outside Git and input roots. CANONICAL_CV_INPUT_ROOT can select an explicit canonical input directory; its default remains the legacy codex input location. The existing shared IO validator checks all required input paths and rejects output reuse or overlap before any run directory is created. The compatibility-row CSV now goes to the isolated output directory. Algorithms, settings, folds and metrics were not changed. Import and synthetic path checks do not certify a new CV run or provide the missing original inputs.
