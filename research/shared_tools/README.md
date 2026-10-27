# Shared Utilities and Tests

The research utilities remain beside their original consumers. This page is an index, not a new shared Python package. Fixed paths, local imports and source-hash checks still apply.

| Purpose | Source and related tests |
|---|---|
| Module 2 dense cache | [Cache utility](../../RAG/scripts/module2_dense_cache.py) |
| Module 4 external lexical evidence | [Lexicon builder](../../RAG/scripts/module4_build_external_lexicon.py) and [tests](../../RAG/tests/test_module4_external_lexicon.py) |
| Module 4 release verification | [Verifier](../../RAG/module4_release_v1/verify_module4.py) and [tests](../../RAG/module4_release_v1/tests/test_verify_module4.py) |
| E6-v3 feature/evaluation helpers | [v3_common.py](../../RAG/results/rag_e6_v3/scripts/v3_common.py) and [tests](../../RAG/results/rag_e6_v3/tests/test_v3.py) |
| E9 evaluation helpers | [e9_common.py](../../RAG/results/phase3_e9_claim_verification/scripts/e9_common.py) and [tests](../../RAG/results/phase3_e9_claim_verification/tests/test_e9.py) |
| E11 scoring contracts | [scoring_common.py](../../RAG/results/phase3_e11_task_adaptation/scoring_common.py) and [tests](../../RAG/results/phase3_e11_task_adaptation/test_scoring.py) |
| Verification of thesis result sources | [verify_sources.py](../../thesis_writing/chapter9_phase1/verify_sources.py) |

The [core pipeline](../core_pipeline/README.md) is shared across baseline evaluation and later experiments. Experiment-specific helpers are not interchangeable: some load other modules or expect full frozen artifacts. The links above do not imply that every test can run from a clean clone or that a test suite was executed during repository organization.

Use the [environment matrix](../../docs/ENVIRONMENTS.md) and [reproducibility notes](../../docs/REPRODUCIBILITY.md) to identify the required context.

[Back to the research guide](../README.md)
