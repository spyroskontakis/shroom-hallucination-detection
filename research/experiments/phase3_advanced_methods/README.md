# Phase 3: Verification and Transformer Fine-Tuning

E9-E11 investigate claim-level verification, whole-hypothesis FactCG support and directly fine-tuned detectors. Most sources and records are physically organized under this research hierarchy. Frozen sources keep their exact historical bytes and require a validated original-layout snapshot for historical source resolution. A new location does not make historical commands runnable.

## E9: claim-level verification

E9 decomposes generated text into claims and investigates NLI and MiniCheck verification. Start with the [protocol](e9_claim_verification/protocols/E9_PROTOCOL.md), [amendment](e9_claim_verification/protocols/E9_PROTOCOL_AMENDMENT_01.md) and [results](e9_claim_verification/results/reports/E9_RESULTS.md). The [evaluation helpers](e9_claim_verification/scripts/e9_common.py) and [decomposition implementation](e9_claim_verification/scripts/run_decomposition.py) are linked at their relocated paths; their frozen scientific logic is unchanged.

## E10: FactCG

E10 has two related but distinct areas; its code is not confined to one E10 directory.

| Setting | Available source and records |
|---|---|
| Development evaluation: FactCG support added to E6-v3 features | [FactCG protocol](e10_factcg/development/gpu/FACTCG_PROTOCOL.md), [evaluator](e10_factcg/development/gpu/evaluate_e10.py) and [development results](e10_factcg/development/results/evaluation/E10_RESULTS.md) |
| Retrospective official-test reconstruction | [Test protocol](e10_factcg/retrospective_official_test/E10_OFFICIAL_TEST_PROTOCOL.md), [reconstruction execution protocol](e10_factcg/retrospective_official_test/reconstructed_v1/E10_EXECUTION_PROTOCOL.md), [CPU feature extraction](e10_factcg/retrospective_official_test/reconstructed_v1/extract_cpu.py) and [recorded test results](e10_factcg/retrospective_official_test/E10_OFFICIAL_TEST_RESULTS.md) |

The official-test reconstruction was retrospective, after label release and earlier exploratory test use. It is not an untouched test or an official SemEval submission. Read the [prior-test-use audit](e10_factcg/retrospective_official_test/recovery_audit/PRIOR_TEST_USE_AUDIT.md) and [MT-overlap audit](e10_factcg/retrospective_official_test/recovery_audit/E10_OFFICIAL_TEST_MT_OVERLAP_AUDIT.md) alongside the results.

## E11: task adaptation and contrastive training

The [E11 summary](e11_transformer_finetuning/E11_FINAL_SUMMARY.md) connects the variants. Unlike the feature-based Random Forest experiments, these variants investigate direct transformer fine-tuning.

| Variant | Available source and records |
|---|---|
| E11-A: human-supervised baseline | [Training protocol](e11_transformer_finetuning/E11A_TRAINING_PROTOCOL.md), [implementation](e11_transformer_finetuning/e11a_train_fold.py) and [results](e11_transformer_finetuning/e11a_results/E11A_RESULTS.md) |
| E11-B: teacher-label feasibility | [Teacher protocol](e11_transformer_finetuning/E11_TEACHER_PROTOCOL.md) and [protocol validator](e11_transformer_finetuning/validate_teacher_protocol.py) |
| E11-C: two-stage training with generated supervision | [Label protocol](e11_transformer_finetuning/e11c/E11C_LLM_LABEL_PROTOCOL.md), [training guide](e11_transformer_finetuning/e11c_training/README.md) and [results](e11_transformer_finetuning/e11c_training/E11C_RESULTS.md) |
| E11-D: human-supervised contrastive training | [Training guide](e11_transformer_finetuning/e11d_training/README.md) and [results](e11_transformer_finetuning/e11d_training/E11D_RESULTS.md) |
| E11-E: two-stage contrastive training | [Training guide](e11_transformer_finetuning/e11e_training/README.md) and [results](e11_transformer_finetuning/e11e_training/E11E_RESULTS.md) |

E11-B is a feasibility result, not a completed trained student with Accuracy/Spearman metrics. Earlier blocked attempts and later completed C/D/E runs remain distinct research records.

The sources depend on the [canonical pipeline](../../core_pipeline/README.md), other experiment components and external models/data. Local and remote execution use different layouts and environments. Full reproduction from this public repository has not been verified; consult [data access](../../../docs/DATA_ACCESS.md), [environment requirements](../../../docs/ENVIRONMENTS.md) and [reproducibility](../../../docs/REPRODUCIBILITY.md). This index does not authorize a cloud job, training run or model download.

## Current organization and checks

The [Modal launcher](e9_claim_verification/modal_gpu/modal_phase3_gpu.py) and the FactCG [local smoke source](e10_factcg/development/local_smoke/run_local_smoke.py) and [CPU smoke source](e10_factcg/development/local_smoke/run_cpu_sun12.py) now live here. Their source-root bindings were adapted. The CPU smoke source also reads byte-identical [selection](e10_factcg/development/local_smoke/SELECTION_MANIFEST.json) and [checkpoint metadata](e10_factcg/development/local_smoke/CHECKPOINT_RELEASE_METADATA.json) records from its new folder. Scientific calculations, model/data asset locations, cache locations and existing run gates are unchanged. The [master current catalog](../../../project_records/current_layout/repository_compatibility_v1.json) records current locations and separate historical identities. The earlier v3 catalog retains its authenticated Phase 26 context. These relocations do not isolate a new model run or authorize execution. The smoke imports and run gates were checked with isolated tests; no model or cloud job was run.

Relocated records retain their original contents, results and historical paths. They document earlier runs; they are not live execution manifests. E9-A/E9-B, E10 development evaluation and retrospective official-test reconstruction, and the E11 variants remain separate.

The [synthetic E10 input-audit tests](e10_factcg/retrospective_official_test/test_audit_data.py) load the single unchanged [audit implementation](e10_factcg/retrospective_official_test/audit_data.py) using its reviewed public source identity and the existing H2-P0 path validator. Only the test loader was adapted. These tests use synthetic inputs and do not score the official test set.

No experiments were rerun. Protected source locks, protocols and historical checks are unchanged. Full runtime reproduction remains NOT VERIFIED. Follow the [safe execution contract](../../../docs/SAFE_EXECUTION.md); historical producers may still write to legacy paths and must not be launched directly in the checkout.

[Back to the research guide](../../README.md)

## Retained immutable E11 audit reference

The [retained E11 audit](../../../RAG/results/phase3_e11_task_adaptation/E11_DATA_AUDIT.md) still contains a broken historical protocol link at line67. Its whole-file identity is protected; the link has not been repaired.

Use the [current protocol](../../data_and_evaluation/canonical/protocols/evaluation_protocol_decision.md) or its [exact original Git version](https://github.com/spyroskontakis/shroom-hallucination-detection/blob/11822d92070cd29360445cb4dacd8d110c655248/codex/evaluation_protocol_decision.md) for navigation. These additional working references do not resolve the protected original URL or certify runtime reproduction.
