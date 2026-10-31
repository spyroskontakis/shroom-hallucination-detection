# Shared Utilities and Tests

Shared tools and experiment-specific helpers are linked at their actual current locations. This page is an index, not a new shared Python package. Fixed paths, local imports and source-hash checks still apply.

| Purpose | Source and related tests |
|---|---|
| Module 2 dense cache | [Cache utility](../experiments/phase2_rag_features/e5_rag/modules/module2/scripts/module2_dense_cache.py) |
| Module 4 external lexical evidence | [Lexicon builder](lexical_evidence/module4_build_external_lexicon.py) and [tests](lexical_evidence/tests/test_module4_external_lexicon.py) |
| Module 4 release verification | [Verifier](../experiments/phase2_rag_features/e5_rag/modules/module4/historical_release_v1/verify_module4.py) and [tests](../experiments/phase2_rag_features/e5_rag/modules/module4/historical_release_v1/tests/test_verify_module4.py) |
| E6-v3 feature/evaluation helpers | [v3_common.py](../experiments/phase2_rag_features/e6_feature_extensions/v3/scripts/v3_common.py) and [tests](../experiments/phase2_rag_features/e6_feature_extensions/v3/tests/test_v3.py) |
| E9 evaluation helpers | [e9_common.py](../experiments/phase3_advanced_methods/e9_claim_verification/scripts/e9_common.py) and [tests](../experiments/phase3_advanced_methods/e9_claim_verification/tests/test_e9.py) |
| E11 scoring contracts | [scoring_common.py](../experiments/phase3_advanced_methods/e11_transformer_finetuning/scoring_common.py) and [tests](../experiments/phase3_advanced_methods/e11_transformer_finetuning/test_scoring.py) |
| Verification of thesis result sources | [verify_sources.py](../../thesis_writing/chapter9_phase1/verify_sources.py) |

The [core pipeline](../core_pipeline/README.md) is shared across baseline evaluation and later experiments. Experiment-specific helpers are not interchangeable: some load other modules or expect full frozen artifacts. The links above do not imply that every test can run from a clean clone or that a test suite was executed during repository organization.

Use the [environment matrix](../../docs/ENVIRONMENTS.md) and [reproducibility notes](../../docs/REPRODUCIBILITY.md) to identify the required context.

[Back to the research guide](../README.md)

## Module 2: adapted execution context

The helper and three notebooks are adapted implementations under `research/experiments/phase2_rag_features/e5_rag/modules/module2/`. Original versions remain at Git checkpoint `67fb57f4fe311ce96dcf2d7556b133ae0328d214`. Saved outputs and execution counts still describe historical runs.

For a separately approved run, declare absolute local paths:
- `SHROOM_MODULE2_CODE_ROOT`: the current Module 2 directory.
- `SHROOM_MODULE2_HELPER_SHA256`: independently reviewed helper digest `7c0d0b79b83fb902459b59a47238d3f0dac4a180eefbc123680170a42db5f1ae`.
- `SHROOM_MODULE2_INPUT_ROOT`: input tree with the original `data/` layout.
- `SHROOM_MODULE2_EVIDENCE_ROOT`: immutable historical snapshot with original `RAG/` source/artifact layout and bytes required by frozen guards.
- `SHROOM_MODULE2_RUN_DIR`: new external run directory, existing parent, outside Git and read-only roots.
- `SHROOM_MODULE2_CACHE_DIR`: explicit external complete dense cache for retrieval.
- `SHROOM_MODULE2_LIBRARY_CACHE`: dedicated prepared offline library cache, outside Git and all other roots. It must already contain required local model files. Use an approved disposable copy, not protected originals.

Use a fresh kernel for each notebook and disable Python bytecode writing. Imports verify the helper pin and reject stale modules. Phase B and holdout do not initialize ML libraries or dense/model caches; they still require historical inputs.

The helper CLI requires `--input-root`, `--evidence-root`, `--run-dir`, `--cache-dir` and exactly one of `--check-paths` or `--build-cache`. Path-check mode creates no files and loads no ML libraries. Cache building requires separate approval, Python 3.11.9 and an adapted-owned writable cache. Unknown/historical caches cannot be adopted for writing by fabricating an ownership marker.

Run outputs cannot replace existing files. Only a manifest in an adapted-owned dense cache can be updated for resume; existing chunks remain immutable. Historical input/source hashes remain unchanged. Missing originals or public-safe bytes differing from original hashes must fail, not fall back or receive refreshed hashes. The ten public H1 records are now in the [Module 2 historical archive](../experiments/phase2_rag_features/e5_rag/modules/module2/historical_records/). The [Module 2 requirements](../experiments/phase2_rag_features/e5_rag/modules/module2/configs/requirements-rag-module2.txt) are now at their planned location. This completes the 21-file Module 2 physical relocation. The old requirements link was repaired with an exact historical Git permalink; that repair is preserved. Original H0 runtime evidence still requires a separately authenticated snapshot.

Static and isolated helper/path/writer tests passed. The notebooks were not run; actual retrieval, cache/model compatibility, evaluation and full reproduction remain NOT VERIFIED. Third-party library writes need a separately audited isolated run; offline flags are not an OS sandbox. See [safe execution](../../docs/SAFE_EXECUTION.md).

## Module 2 current files and historical originals

These current files are available in this working layout. The baseline links identify the original public snapshot at commit `11822d92070cd29360445cb4dacd8d110c655248`; relocated/adapted files must not be treated as original frozen runtime evidence.

| File | Current location | Original baseline |
|---|---|---|
| Retrieval notebook | [Current](../experiments/phase2_rag_features/e5_rag/modules/module2/notebooks/shroom_rag_e5_module2_retrieval.ipynb) | [Historical](https://github.com/spyroskontakis/shroom-hallucination-detection/blob/11822d92070cd29360445cb4dacd8d110c655248/RAG/shroom_rag_e5_module2_retrieval.ipynb) |
| Phase-B notebook | [Current](../experiments/phase2_rag_features/e5_rag/modules/module2/notebooks/shroom_rag_e5_module2_phase_b_evaluation.ipynb) | [Historical](https://github.com/spyroskontakis/shroom-hallucination-detection/blob/11822d92070cd29360445cb4dacd8d110c655248/RAG/shroom_rag_e5_module2_phase_b_evaluation.ipynb) |
| Holdout notebook | [Current](../experiments/phase2_rag_features/e5_rag/modules/module2/notebooks/shroom_rag_e5_module2_holdout_evaluation.ipynb) | [Historical](https://github.com/spyroskontakis/shroom-hallucination-detection/blob/11822d92070cd29360445cb4dacd8d110c655248/RAG/shroom_rag_e5_module2_holdout_evaluation.ipynb) |
| Cache helper | [Current](../experiments/phase2_rag_features/e5_rag/modules/module2/scripts/module2_dense_cache.py) | [Historical](https://github.com/spyroskontakis/shroom-hallucination-detection/blob/11822d92070cd29360445cb4dacd8d110c655248/RAG/scripts/module2_dense_cache.py) |
| BM25 dependency spec | [Current](../experiments/phase2_rag_features/e5_rag/modules/module2/configs/requirements-rag-module2.txt) | [Historical](https://github.com/spyroskontakis/shroom-hallucination-detection/blob/11822d92070cd29360445cb4dacd8d110c655248/RAG/requirements-rag-module2.txt) |

Six earlier broken historical links were repaired with exact baseline permalinks. One hash-locked E11 audit link remains open; these alternatives do not repair it. The BM25 pin is not a complete runtime environment; full notebook and scientific reproduction remain NOT VERIFIED.

## Read-only source contexts

The [repository source context v2](repository_source_context_v2.py) reuses the unchanged v1/H2-P0 validator with an independently pinned [source catalog](../../project_records/current_layout/repository_sources_v2.json). The [v1 catalog](../../project_records/current_layout/repository_sources_v1.json) remains available for its original context. These contexts separate original public Git bytes (H1), reviewed current files (H2), and original experiment inputs (H0). They do not launch experiments. An unimplemented H2 entry or a missing H0 input is not replaced with another context.

For a read-only source check, supply the absolute checkout root, the original logical path and either `H1_SNAPSHOT` or `H2_CURRENT` to the validator's CLI. H1 reads only the fixed public baseline commit. H2 checks the measured current path and digest. A source check does not verify the reported scientific results.

The [saved E6-v3 analysis context](saved_analysis_context_v1.py) provides isolated I/O bindings for the relocated [analysis sources](../experiments/phase2_rag_features/e6_feature_extensions/v3/error_analysis/). Its [separate contract](../../project_records/current_layout/e6_v3_saved_analysis_h2_v1.json) retains the original input hashes. The four adapted Python files reject direct execution. Context construction requires authentic original inputs and separate, new run/cache/temporary roots before any output creation or module loading. Full saved-result analysis has not been rerun. The [Node CSV authoring source](../experiments/phase2_rag_features/e6_feature_extensions/v3/error_analysis/build_csv.mjs) is now an independently identified current implementation. It requires an authentic diagnostic input matching the recorded original hash, an explicit hash-pinned package entry and a fresh external output root. The historical authoring-check record is unchanged at the same new directory. Its CSV render logic and output safety passed isolated unit fixtures; the native Workbook runtime remains NOT VERIFIED (native addon denied in the strict probe). This does not reproduce the original 561-row diagnostic table.

Only offline synthetic context, path and I/O checks were performed. Future execution requires the [safe execution procedure](../../docs/SAFE_EXECUTION.md), the independently verified contract digest and separately approved inputs. Historical frozen contracts, AccessGuards and E10/E11 consumers are unchanged.

The final E11 summary, table and manifest are now at their [current location](../experiments/phase3_advanced_methods/e11_transformer_finetuning/). Their bytes and historical metrics are unchanged. Relocated E11 checksum lists retain their historical contents. The [D checksum list](../experiments/phase3_advanced_methods/e11_transformer_finetuning/e11d_training/SHA256SUMS.txt) and [E checksum list](../experiments/phase3_advanced_methods/e11_transformer_finetuning/e11e_training/SHA256SUMS.txt) are now relocated byte-identical source records. Catalog.checksum_evidence() reads them against an explicitly authenticated H1 namespace. The unchanged frozen metadata-reader bodies retain the same public-H1 file inventory there; this is not the missing original private preservation ledger. Three existing public-JSON/H0 checksum differences remain explicit failures, and full finalization/replay remains NOT VERIFIED. No original finalization or runtime gate was bypassed. Current source verification is not a rerun of the E11 experiments.

## Cross-experiment E6-v2/v3 binding

The [compatibility layer](repository_compatibility.py) composes the unchanged cross-experiment API with the master catalog's current paths. Use Catalog.cross() for the supported current E6-v2/v3 integrations. Old cross and source-context v1/v2/v3 catalogs remain pinned milestone contexts; validate them against the authenticated Phase 26 snapshot, not the later working tree.

The layer also provides separately hashed current library views for E7, E8, FactCG and E11 scoring. It preserves AccessGuard class bodies and original-input hashes. Tests use isolated synthetic inputs and selected read-only public configuration checks. They do not launch full experimental pipelines.

For modes, scope and the source-only CLI, read [reproducibility](../../docs/REPRODUCIBILITY.md). No historical source or public-safe record replaces a missing authentic original input.

## Consolidated offline checks

Use [verify_repository.py](verify_repository.py) for the committed source, migration and local-link checks, and optional isolated regression tests. The [verification guide](../../docs/VERIFICATION.md) explains the explicit scratch requirement, historical test contexts and known failures. It does not authorize experiment execution or certify historical metric reproduction.
