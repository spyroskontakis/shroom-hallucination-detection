# Phase 2: External Knowledge and Additional Features

E5-E8 explore retrieval evidence, extra semantic features, selective routing and Random Forest tuning. The implementations remain under `RAG/`; this directory provides navigation only.

## E5: RAG Modules 1-4

The modules record successive retrieval and evaluation stages. They are not four interchangeable implementations or four steps that can automatically be run in sequence.

| Module | Available implementation and documentation |
|---|---|
| Module 1: exact retrieval prototype | [Notebook](../../../RAG/shroom_rag_e5_module1.ipynb), [Gemini trial variant](../../../RAG/shroom_rag_e5_module1_gemini_trial.ipynb) and [guide](../../../RAG/README_MODULE1.md) |
| Module 2: retrieval and evaluation | [Retrieval notebook](../../../RAG/shroom_rag_e5_module2_retrieval.ipynb), [phase-B evaluation](../../../RAG/shroom_rag_e5_module2_phase_b_evaluation.ipynb), [holdout evaluation](../../../RAG/shroom_rag_e5_module2_holdout_evaluation.ipynb) and [results](e5_rag/modules/module2/protocols/MODULE2_FINAL_RESULTS.md) |
| Module 3: diagnostic investigation | [Final diagnostic report](e5_rag/modules/module3/records/MODULE3_FINAL_RESULTS.md) and [initial failure audit](e5_rag/modules/module3/records/MODULE3_PHASE0_FAILURE_AUDIT.md) |
| Module 4: external lexical evidence and feature fusion | [Static protocol report](../../../RAG/results/rag_module4/static_protocol/MODULE4_STATIC_PROTOCOL_REPORT.md), [lexicon builder](../../../RAG/scripts/module4_build_external_lexicon.py), [pinned feature builder](../../../RAG/results/rag_module4/continuation_v1/mpnet_provenance_v2/scripts/module4_build_rag_features_pinned.py), [fusion evaluator](../../../RAG/results/rag_module4/continuation_v1/schannel_run_v1/scripts/module4_evaluate_fusion.py) and [results](../../../RAG/results/rag_module4/MODULE4_FINAL_RESULTS.md) |

Module 3 closed as a diagnostic stage; no standalone final gated-RAG evaluation implementation was located. The original reports are retained without presenting that stage as a completed executable pipeline.

## E6: feature extensions

| Version | Focus | Protocol and recorded results |
|---|---|---|
| E6-v1 | Additional comparisons with retrieved definitions | [Protocol](../../../RAG/results/rag_e6_v1/E6_PROTOCOL.md), [results](../../../RAG/results/rag_e6_v1/E6_RESULTS.md) |
| E6-v2 | A second NLI evaluator | [Protocol](../../../RAG/results/rag_e6_v2/E6_V2_PROTOCOL.md), [results](../../../RAG/results/rag_e6_v2/E6_V2_RESULTS.md) |
| E6-v3 | HHEM consistency features | [Protocol](../../../RAG/results/rag_e6_v3/E6_V3_PROTOCOL.md), [results](../../../RAG/results/rag_e6_v3/E6_V3_RESULTS.md), [implementation helpers](../../../RAG/results/rag_e6_v3/scripts/v3_common.py) |
| E6-v4 | BERTScore and structural features | [Protocol](../../../RAG/results/rag_e6_v4/E6_V4_PROTOCOL.md), [compatibility amendment](../../../RAG/results/rag_e6_v4/E6_V4_PROTOCOL_AMENDMENT_01.md), [results](../../../RAG/results/rag_e6_v4/E6_V4_RESULTS.md) |

## E7 and E8

- **E7 - selective routing:** a fixed rule selects between E3 and E6-v1 predictions. See the [protocol](../../../RAG/results/rag_e7_agentic_v1/E7_PROTOCOL.md), [implementation helpers](../../../RAG/results/rag_e7_agentic_v1/scripts/e7_common.py) and [results](../../../RAG/results/rag_e7_agentic_v1/E7_RESULTS.md). This is not an autonomous LLM agent.
- **E8 - Random Forest tuning:** nested cross-validation tests RF configurations without adding predictor features. See the [protocol](../../../RAG/results/rag_e8_rf_tuning_v1/E8_PROTOCOL.md), [implementation helpers](../../../RAG/results/rag_e8_rf_tuning_v1/scripts/e8_common.py) and [results](../../../RAG/results/rag_e8_rf_tuning_v1/E8_RESULTS.md).

These experiments depend on the [canonical pipeline](../../core_pipeline/README.md), full frozen artifacts and experiment-specific environments. Their current paths and integrity checks are retained. Some historical configurations in the public package are documented public-safe versions rather than byte-identical original runtime files. Full historical replay is not established by a source link or a migration hash check; read [environment requirements](../../../docs/ENVIRONMENTS.md) and [reproducibility](../../../docs/REPRODUCIBILITY.md).

[Back to the research guide](../../README.md)
