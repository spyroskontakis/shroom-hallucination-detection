# Phase 2: External Knowledge and Additional Features

E5-E8 explore retrieval evidence, extra semantic features, selective routing and Random Forest tuning. Most implementations remain under `RAG/`. Module 2's adapted helper and notebooks are under the Module 2 directory linked below.

## E5: RAG Modules 1-4

The modules record successive retrieval and evaluation stages. They are not four interchangeable implementations or four steps that can automatically be run in sequence.

| Module | Available implementation and documentation |
|---|---|
| Module 1: exact retrieval prototype | [Notebook](e5_rag/modules/module1/notebooks/shroom_rag_e5_module1.ipynb), [Gemini trial variant](e5_rag/modules/module1/notebooks/shroom_rag_e5_module1_gemini_trial.ipynb) and [guide](e5_rag/modules/module1/protocols/README_MODULE1.md) |
| Module 2: retrieval and evaluation | [Retrieval notebook](e5_rag/modules/module2/notebooks/shroom_rag_e5_module2_retrieval.ipynb), [phase-B evaluation](e5_rag/modules/module2/notebooks/shroom_rag_e5_module2_phase_b_evaluation.ipynb), [holdout evaluation](e5_rag/modules/module2/notebooks/shroom_rag_e5_module2_holdout_evaluation.ipynb) and [results](e5_rag/modules/module2/protocols/MODULE2_FINAL_RESULTS.md) |
| Module 3: diagnostic investigation | [Final diagnostic report](e5_rag/modules/module3/records/MODULE3_FINAL_RESULTS.md) and [initial failure audit](e5_rag/modules/module3/records/MODULE3_PHASE0_FAILURE_AUDIT.md) |
| Module 4: external lexical evidence and feature fusion | [Static protocol report](e5_rag/modules/module4/protocols/static_protocol/MODULE4_STATIC_PROTOCOL_REPORT.md), [lexicon builder](../../../RAG/scripts/module4_build_external_lexicon.py), [pinned feature builder](../../../RAG/results/rag_module4/continuation_v1/mpnet_provenance_v2/scripts/module4_build_rag_features_pinned.py), [fusion evaluator](../../../RAG/results/rag_module4/continuation_v1/schannel_run_v1/scripts/module4_evaluate_fusion.py) and [results](e5_rag/modules/module4/results/reports/MODULE4_FINAL_RESULTS.md) |

Module 3 closed as a diagnostic stage; no standalone final gated-RAG evaluation implementation was located. The original reports are retained without presenting that stage as a completed executable pipeline.

Module 1 is physically organized under its module directory. The two notebooks are adapted implementations; their saved outputs still describe historical runs. The protocol guide records the original setup. Adapted runs require absolute SHROOM_DATA_DIR, a new external SHROOM_MODULE1_RUN_DIR and a pre-created external SHROOM_MODULE1_TEMP_ROOT. SHROOM_MODULE1_CACHE_INPUT may declare a separate read-only original cache; new records append only to the owned run cache. Historical sources and frozen hashes remain separate. The notebooks were not rerun; full reproduction and real library behavior remain NOT VERIFIED.

Module 2 now uses explicit input, historical-evidence and external output roots. Saved results are historical; the adapted notebooks have not been rerun. See the [adapted execution notes](../../shared_tools/README.md#module-2-adapted-execution-context).

Some Module 4 protocol records and publication-safe aggregate records from E6, E7 and E8 have been relocated under this research hierarchy. The other frozen executable pipelines and their required runtime metadata remain at their existing RAG paths. E6-v4 has a separate current-layout context described below. The relocated inventories retain historical paths and hashes; they are not current execution manifests. The [E6-v3 publication guide](../../../docs/reproducibility/e6/E6_V3_REPRODUCIBILITY.md) and [MPNet source-provenance tests](e5_rag/modules/module4/variants/continuation_v1/mpnet_provenance_v2/tests/test_mpnet_provenance_static.py) are available at their current locations. Do not rerun historical writers to recreate files at old paths. These moves do not establish full runtime reproducibility.

## E6: feature extensions

| Version | Focus | Protocol and recorded results |
|---|---|---|
| E6-v1 | Additional comparisons with retrieved definitions | [Protocol](../../../RAG/results/rag_e6_v1/E6_PROTOCOL.md), [results](../../../RAG/results/rag_e6_v1/E6_RESULTS.md) |
| E6-v2 | A second NLI evaluator | [Protocol](e6_feature_extensions/v2/protocols/E6_V2_PROTOCOL.md), [results](e6_feature_extensions/v2/results/reports/E6_V2_RESULTS.md) |
| E6-v3 | HHEM consistency features | [Protocol](../../../RAG/results/rag_e6_v3/E6_V3_PROTOCOL.md), [results](e6_feature_extensions/v3/results/reports/E6_V3_RESULTS.md), [implementation helpers](../../../RAG/results/rag_e6_v3/scripts/v3_common.py) |
| E6-v4 | BERTScore and structural features | [Protocol](e6_feature_extensions/v4/protocols/E6_V4_PROTOCOL.md), [compatibility amendment](e6_feature_extensions/v4/protocols/E6_V4_PROTOCOL_AMENDMENT_01.md), [results](e6_feature_extensions/v4/results/reports/E6_V4_RESULTS.md) |


### E6-v2/v3: current binding and retained historical consumers

A [shared current-layout binding](../../shared_tools/cross_experiment_context_v1.py) now covers the E6-v2/v3 source and record group. Its [execution/source contract](../../../project_records/current_layout/e6_cross_experiment_h2_v1.json) records original public bytes separately from current and derived source identities. Relocated Python files reject direct execution or import; use the explicit binding rather than a historical command at a new path.

The binding reuses the existing pinned H2 safety engine. Original expected hashes are checked only against a separately authenticated original input tree. Current sources are validated independently; an adapted source cannot stand in for an original. Explicit outside-Git original/run/temporary roots and a prepared cache below the temporary root are required before execution. Missing inputs, model assets or schema identities fail before run creation or model loading. Existing runs cannot be adopted, and original evaluation markers are not removed or bypassed.

Some sources and records remain under RAG because unchanged E9/E10/E11 consumers require their exact paths. These include the original common helpers, model backends, acquisition records and E6-v3 baseline metadata. The pinned E6-v3 publication guide and its protocol target also remain unchanged. Source-generation, model-acquisition and freeze-authoring entries are static-only in this binding; it is not a verified end-to-end replay workflow.

Only offline synthetic context/import/guard tests were executed. They do not repeat the experiments or independently verify their metrics. Full historical runtime reproducibility remains NOT VERIFIED.

### E6-v4: current layout and historical execution

All 62 E6-v4 source, configuration, protocol, vendor and record files are now under this version's research directory. Their raw historical contents have not changed. The BERTScore package retains its independent MIT notice.

The [current H2 binding](e6_feature_extensions/v4/verification/h2_adapter_v2.py) and [current source contract](e6_feature_extensions/v4/configs/current_layout_h2_v2.json) use the unchanged, pinned [v1 adapter engine](e6_feature_extensions/v4/verification/h2_adapter_v1.py). The engine derives reviewed IO/root/import views in memory from exact raw sources; it does not replace historical sources or frozen hashes. The new binding changes the remaining current file locations and records original and derived identities. Its default plan mode verifies sources without creating files; it requires the independently verified contract SHA-256. Direct historical commands are not validated instructions for the new layout.

The [current offline tests](e6_feature_extensions/v4/tests/test_h2_current_layout.py) reuse the original safety tests and add current-layout failure cases. The unchanged [v1 contract](e6_feature_extensions/v4/configs/current_layout_h2_v1.json) and [v1 tests](e6_feature_extensions/v4/tests/test_h2_context.py) describe their prior layout. They were verified against an authenticated copy of that exact pre-migration source snapshot, not silently rebound to new paths. V1 rejects the current layout; choose the explicit current binding for current source checks. Real execution needs separately approved, hash-verified original evidence, model assets and external run/temp roots. Missing or changed originals fail before model loading or writes. Historical records cannot substitute for a fresh run's missing outputs.

The [original Git snapshot](https://github.com/spyroskontakis/shroom-hallucination-detection/tree/11822d92070cd29360445cb4dacd8d110c655248/RAG/results/rag_e6_v4) remains the reference for historical locations. No model execution or numerical reproduction was performed for this migration. Full runtime reproducibility remains NOT VERIFIED.

## E7 and E8

- **E7 - selective routing:** a fixed rule selects between E3 and E6-v1 predictions. See the [protocol](../../../RAG/results/rag_e7_agentic_v1/E7_PROTOCOL.md), [implementation helpers](../../../RAG/results/rag_e7_agentic_v1/scripts/e7_common.py) and [results](../../../RAG/results/rag_e7_agentic_v1/E7_RESULTS.md). This is not an autonomous LLM agent.
- **E8 - Random Forest tuning:** nested cross-validation tests RF configurations without adding predictor features. See the [protocol](../../../RAG/results/rag_e8_rf_tuning_v1/E8_PROTOCOL.md), [implementation helpers](../../../RAG/results/rag_e8_rf_tuning_v1/scripts/e8_common.py) and [results](../../../RAG/results/rag_e8_rf_tuning_v1/E8_RESULTS.md).

These experiments depend on the [canonical pipeline](../../core_pipeline/README.md), full frozen artifacts and experiment-specific environments. Their current paths and integrity checks are retained. Some historical configurations in the public package are documented public-safe versions rather than byte-identical original runtime files. Full historical replay is not established by a source link or a migration hash check; read [environment requirements](../../../docs/ENVIRONMENTS.md) and [reproducibility](../../../docs/REPRODUCIBILITY.md).

[Back to the research guide](../../README.md)
