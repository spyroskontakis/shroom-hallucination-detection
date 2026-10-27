# Phase 3: Verification and Transformer Fine-Tuning

E9-E11 investigate claim-level verification, whole-hypothesis FactCG support and directly fine-tuned detectors. The code remains in its original `RAG/results/` locations. This page is a navigation index.

## E9: claim-level verification

E9 decomposes generated text into claims and investigates NLI and MiniCheck verification. Start with the [protocol](../../../RAG/results/phase3_e9_claim_verification/E9_PROTOCOL.md), [amendment](../../../RAG/results/phase3_e9_claim_verification/E9_PROTOCOL_AMENDMENT_01.md) and [results](../../../RAG/results/phase3_e9_claim_verification/E9_RESULTS.md). The [evaluation helpers](../../../RAG/results/phase3_e9_claim_verification/scripts/e9_common.py) and [decomposition implementation](../../../RAG/results/phase3_e9_claim_verification/scripts/run_decomposition.py) remain with their original consumers.

## E10: FactCG

E10 has two related but distinct areas; its code is not confined to one E10 directory.

| Setting | Available source and records |
|---|---|
| Development evaluation: FactCG support added to E6-v3 features | [FactCG protocol](../../../RAG/results/phase3_e9_claim_verification/factcg_gpu/FACTCG_PROTOCOL.md), [evaluator](../../../RAG/results/phase3_e9_claim_verification/factcg_gpu/evaluate_e10.py) and [development results](../../../RAG/results/phase3_e9_claim_verification/evaluation/E10/E10_RESULTS.md) |
| Retrospective official-test reconstruction | [Test protocol](../../../RAG/results/e10_official_test_v1/E10_OFFICIAL_TEST_PROTOCOL.md), [reconstruction execution protocol](../../../RAG/results/e10_official_test_v1/reconstructed_v1/E10_EXECUTION_PROTOCOL.md), [CPU feature extraction](../../../RAG/results/e10_official_test_v1/reconstructed_v1/extract_cpu.py) and [recorded test results](../../../RAG/results/e10_official_test_v1/E10_OFFICIAL_TEST_RESULTS.md) |

The official-test reconstruction was retrospective, after label release and earlier exploratory test use. It is not an untouched test or an official SemEval submission. Read the [prior-test-use audit](../../../RAG/results/e10_official_test_v1/recovery_audit/PRIOR_TEST_USE_AUDIT.md) and [MT-overlap audit](../../../RAG/results/e10_official_test_v1/recovery_audit/E10_OFFICIAL_TEST_MT_OVERLAP_AUDIT.md) alongside the results.

## E11: task adaptation and contrastive training

The [E11 summary](../../../RAG/results/phase3_e11_task_adaptation/E11_FINAL_SUMMARY.md) connects the variants. Unlike the feature-based Random Forest experiments, these variants investigate direct transformer fine-tuning.

| Variant | Available source and records |
|---|---|
| E11-A: human-supervised baseline | [Training protocol](../../../RAG/results/phase3_e11_task_adaptation/E11A_TRAINING_PROTOCOL.md), [implementation](../../../RAG/results/phase3_e11_task_adaptation/e11a_train_fold.py) and [results](../../../RAG/results/phase3_e11_task_adaptation/e11a_results/E11A_RESULTS.md) |
| E11-B: teacher-label feasibility | [Teacher protocol](../../../RAG/results/phase3_e11_task_adaptation/E11_TEACHER_PROTOCOL.md) and [protocol validator](../../../RAG/results/phase3_e11_task_adaptation/validate_teacher_protocol.py) |
| E11-C: two-stage training with generated supervision | [Label protocol](../../../RAG/results/phase3_e11_task_adaptation/e11c/E11C_LLM_LABEL_PROTOCOL.md), [training guide](../../../RAG/results/phase3_e11_task_adaptation/e11c_training/README.md) and [results](../../../RAG/results/phase3_e11_task_adaptation/e11c_training/E11C_RESULTS.md) |
| E11-D: human-supervised contrastive training | [Training guide](../../../RAG/results/phase3_e11_task_adaptation/e11d_training/README.md) and [results](../../../RAG/results/phase3_e11_task_adaptation/e11d_training/E11D_RESULTS.md) |
| E11-E: two-stage contrastive training | [Training guide](../../../RAG/results/phase3_e11_task_adaptation/e11e_training/README.md) and [results](../../../RAG/results/phase3_e11_task_adaptation/e11e_training/E11E_RESULTS.md) |

E11-B is a feasibility result, not a completed trained student with Accuracy/Spearman metrics. Earlier blocked attempts and later completed C/D/E runs remain distinct research records.

The sources depend on the [canonical pipeline](../../core_pipeline/README.md), other experiment components and external models/data. Local and remote execution use different layouts and environments. Full reproduction from this public repository has not been verified; consult [data access](../../../docs/DATA_ACCESS.md), [environment requirements](../../../docs/ENVIRONMENTS.md) and [reproducibility](../../../docs/REPRODUCIBILITY.md). This index does not authorize a cloud job, training run or model download.

[Back to the research guide](../../README.md)
