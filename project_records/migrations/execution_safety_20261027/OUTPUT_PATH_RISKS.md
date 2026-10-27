# Phase 15 - Output-path risks

Static analysis, 2026-10-27. No producer was imported, modified or run. Cells below use zero-based indexes into the current notebook JSON, not execution counters.

## Migrated CSV producer map

The Phase9-11 migrations moved 13 CSVs and four historical Markdown reports. All 17 are archival moves, not a change to producer paths. For the 13 CSVs, the following writers remain in the unchanged source:

| Archived file | Original archived path | Current archive | Confirmed producer / cell | Scientific context |
|---|---|---|---|---|
| `fixed_errors_by_task_and_type.csv` | `data/7. Ablation Synthetic Data/fixed_errors_by_task_and_type.csv` | [archived CSV](<../../../research/experiments/phase1_baselines/e4_augmentation/historical_ablation/fixed_errors_by_task_and_type.csv>) | [notebook](<../../../data/7.%20Ablation%20Synthetic%20Data/7.Ablation_Synthetic_Data.ipynb>) / 24 | Historical labeled-test synthetic ablation |
| `introduced_errors_by_task_and_type.csv` | `data/7. Ablation Synthetic Data/introduced_errors_by_task_and_type.csv` | [archived CSV](<../../../research/experiments/phase1_baselines/e4_augmentation/historical_ablation/introduced_errors_by_task_and_type.csv>) | [notebook](<../../../data/7.%20Ablation%20Synthetic%20Data/7.Ablation_Synthetic_Data.ipynb>) / 24 | Historical labeled-test synthetic ablation |
| `ablation_summary_results.csv` | `data/7. Ablation Synthetic Data/ablation_summary_results.csv` | [archived CSV](<../../../research/experiments/phase1_baselines/e4_augmentation/historical_ablation/ablation_summary_results.csv>) | [notebook](<../../../data/7.%20Ablation%20Synthetic%20Data/7.Ablation_Synthetic_Data.ipynb>) / 12 | Historical labeled-test synthetic ablation |
| `ablation_per_task_results.csv` | `data/7. Ablation Synthetic Data/ablation_per_task_results.csv` | [archived CSV](<../../../research/experiments/phase1_baselines/e4_augmentation/historical_ablation/ablation_per_task_results.csv>) | [notebook](<../../../data/7.%20Ablation%20Synthetic%20Data/7.Ablation_Synthetic_Data.ipynb>) / 14 | Historical labeled-test synthetic ablation |
| `ablation_feature_importance.csv` | `data/7. Ablation Synthetic Data/ablation_feature_importance.csv` | [archived CSV](<../../../research/experiments/phase1_baselines/e4_augmentation/historical_ablation/ablation_feature_importance.csv>) | [notebook](<../../../data/7.%20Ablation%20Synthetic%20Data/7.Ablation_Synthetic_Data.ipynb>) / 16 | Historical labeled-test synthetic ablation |
| `e1_nli_dev_cv_results.csv` | `data/2. EDA/shroom_final_implementation/e1_nli_dev_cv_results.csv` | [archived CSV](<../../../research/experiments/phase1_baselines/e1_e3_baselines/results/development_499/e1_nli_dev_cv_results.csv>) | [notebook](<../../../RAG/shroom_ensemble.ipynb>) / 118 | Development-499; E4 diagnostic only |
| `e2_similarity_dev_cv_results.csv` | `data/2. EDA/shroom_final_implementation/e2_similarity_dev_cv_results.csv` | [archived CSV](<../../../research/experiments/phase1_baselines/e1_e3_baselines/results/development_499/e2_similarity_dev_cv_results.csv>) | [notebook](<../../../RAG/shroom_ensemble.ipynb>) / 133 | Development-499; E4 diagnostic only |
| `e3_nli_similarity_dev_cv_results.csv` | `data/2. EDA/shroom_final_implementation/e3_nli_similarity_dev_cv_results.csv` | [archived CSV](<../../../research/experiments/phase1_baselines/e1_e3_baselines/results/development_499/e3_nli_similarity_dev_cv_results.csv>) | [notebook](<../../../RAG/shroom_ensemble.ipynb>) / 142 | Development-499; E4 diagnostic only |
| `e4_synthetic_dev_cv_results.csv` | `data/2. EDA/shroom_final_implementation/e4_synthetic_dev_cv_results.csv` | [archived CSV](<../../../research/experiments/phase1_baselines/e4_augmentation/results/development_499/e4_synthetic_dev_cv_results.csv>) | [notebook](<../../../RAG/shroom_ensemble.ipynb>) / 164 | Development-499; E4 diagnostic only |
| `e4_synthetic_dev_task_results.csv` | `data/2. EDA/shroom_final_implementation/e4_synthetic_dev_task_results.csv` | [archived CSV](<../../../research/experiments/phase1_baselines/e4_augmentation/results/development_499/e4_synthetic_dev_task_results.csv>) | [notebook](<../../../RAG/shroom_ensemble.ipynb>) / 164 | Development-499; E4 diagnostic only |
| `development_experiment_summary.csv` | `data/2. EDA/shroom_final_implementation/development_experiment_summary.csv` | [archived CSV](<../../../research/experiments/phase1_baselines/e1_e3_baselines/results/development_499/development_experiment_summary.csv>) | [notebook](<../../../RAG/shroom_ensemble.ipynb>) / 165 | Development-499; E4 diagnostic only |
| `ablation_synthetic_ratio_results.csv` | `data/7. Ablation Synthetic Data/ablation_synthetic_ratio_results.csv` | [archived CSV](<../../../research/experiments/phase1_baselines/e4_augmentation/historical_ablation/ablation_synthetic_ratio_results.csv>) | [notebook](<../../../data/7.%20Ablation%20Synthetic%20Data/7.Ablation_Synthetic_Data.ipynb>) / 27 | Historical labeled-test synthetic ablation |
| `ablation_synthetic_weight_results.csv` | `data/7. Ablation Synthetic Data/ablation_synthetic_weight_results.csv` | [archived CSV](<../../../research/experiments/phase1_baselines/e4_augmentation/historical_ablation/ablation_synthetic_weight_results.csv>) | [notebook](<../../../data/7.%20Ablation%20Synthetic%20Data/7.Ablation_Synthetic_Data.ipynb>) / 29 | Historical labeled-test synthetic ablation |

The writer mapping proves these current sources can emit the same basenames. It does not independently authenticate which notebook instance or kernel CWD produced every historical byte. Prior manifests and the scientific context remain the provenance record.

## Confirmed regeneration and overwrite mechanisms

### Development-499 baseline outputs

- In `RAG/shroom_ensemble.ipynb`, cells 118 and 133 write E1/E2 aggregate and row-level OOF CSV basenames directly into kernel CWD. Cell 142 sets `OUTPUT_DIR = Path(".")`, then writes E3 aggregates and OOF rows. Cell 164 writes E4 aggregate, OOF and per-task basenames. Cell 165 writes `development_experiment_summary.csv` in CWD.
- With the former `data/2. EDA/shroom_final_implementation/` CWD, these names can reappear at their old archived locations. A different CWD produces another copy elsewhere; neither is automatically the authoritative archived result. The summary is built from in-memory values and is not a reader of the relocated CSV.
- The source asserts 499 E3/E4 OOF rows. These historical tables must not be relabeled as canonical-561 results. E4 remains diagnostic and excluded from the historical final E1-E3 selection.

### Historical labeled-test synthetic ablation

- Cell 2 initially sets `DATA_DIR = Path.cwd()`. If `4.nli_similarity_features_dataset.csv` is absent there, it falls back to `SHROOM_PROJECT_ROOT` (default `.`) plus `data/7. Ablation Synthetic Data`. The same directory holds `6.nli_similarity_features_dataset.csv`.
- Cells 12, 14, 16, 24, 27 and 29 write seven migrated aggregate filenames to `DATA_DIR`. Cell 18 also writes private row-level `ablation_predictions.csv`; error-analysis cells create additional row-derived data in memory.
- Restoring inputs at the old data path may recreate outputs beside the producer, while the moved archives remain under research/. Running with CWD in the archive could instead overwrite the preserved CSVs. Existing `to_csv` calls do not implement a no-overwrite transaction.
- Trial + Synthetic ratio/weight sweeps use labeled-test-derived evaluation features. They are not canonical development evidence. Their old names are not permission to rerun or replace them.

### Distinct namespaces and historical reports

- E10 records point to `codex/data/7. Ablation Synthetic Data/...`, not the relocated `data/7. Ablation Synthetic Data/...`. Prior Phase11 review found equal recorded hashes for ratio/weight in distinct paths, with the E10 targets already absent. Do not copy archives into those missing paths to satisfy a check silently.
- Four historical Markdown reports were relocated without changing their path descriptions. Those descriptions remain historical statements, not active launch instructions. Phase15 creates no new producer and changes no old reference.

## Additional pipeline risks

| Pipeline / source | Static evidence and consequence | Required gate before any future test |
|---|---|---|
| Canonical CV | `OUTPUT_DIR.mkdir()` runs at module scope. `CANONICAL_CV_OUTPUT_DIR` redirects many outputs, but `UNMATCHED_COMPATIBILITY_ROWS` remains in `FEATURE_DIR` and is written separately. | Resolve every write, including the compatibility CSV and import-time directories; the output override alone is insufficient. |
| Canonical preparation / fold generation | Fixed codex paths, CSV/JSON write helpers and fold regeneration can overwrite tracked metadata or authoritative runtime inputs. | Keep original folds/manifests read-only; never regenerate them as a path workaround. |
| EDA and plotting/tokenizers | Module-level output creation, plotting caches and optional tokenizer/model initialization can write before a selected analysis helper. | Review transitive imports before launch and enforce scratch-only cache/log/temp writes. |
| RAG Module1/2 | CWD/results paths, retrieval/cache state, annotation and decision artifacts can be reused or overwritten. Protected baseline hashes are checked. | Separate new cache/output state from originals; no API/annotation run in this phase. |
| Module4 builder | `prepare-inputs`, `acquire` and `offline-build` share output roots; acquisition writes raw responses/network logs and uses network. | Mode-specific input and output allowlist; acquire requires separate network approval. |
| E6-v1/v2/v3 | Fixed OUT relative to source; v1 imports pinned Module4 helpers at module scope. Features, OOF, markers and reports share historical trees. | Missing originals and applicable frozen contracts must be resolved before any run; help/import is not presumed read-only. |
| E6-v4 | `execution/common.py` assigns TEMP/TMP, HF_MODULES_CACHE, JOBLIB_TEMP_FOLDER and MPLCONFIGDIR inside execution/tmp and records network state. | Launcher environment overrides alone cannot isolate this unchanged code; stop if a write boundary cannot be enforced. |
| E7/E8 | `__file__` ancestry fixes OUT/ROOT; AccessGuard writes diagnostics and restricts historical OUT. Frozen checks include source paths/hashes and the old root .gitignore. | Preserve checks. A relocated or modified common module is not an exact frozen replay. An original-context execution mirror would require separate review/approval. |
| E9 | Preparation/verification can write records; decomposition has API and historical branch-name gates; claims/cache and full_run are fixed. | Do not spoof the old branch or clear markers. API use is separately approved work, not a source inspection step. |
| E10 / retrospective reconstruction | Acquisition can use HTTP; extraction loads canonical/E6 sources and checks source hashes; scoring writes model/prediction/metric artifacts. | Keep development and retrospective official-test contexts separate. Do not replace missing originals with public-safe derivatives. |
| E11 | Preparation writes manifests; workers train; helpers discover an expected legacy layout or use /opt/e11 and /results. Remote checkpoint verification calls verify.remote and writes verification records. | No cloud, training, checkpoint reads or downloads approved here. /results is a worker mount point, not a volume-native source path. |
| Prototype / archived probes | Prototype import startup may use caches/temp; Modal/Vertex probes can invoke remote services. | Narrow future help/config test needs isolation; archived probes remain static only. |

## Safe execution contract for a later approved test

This is a design, not an implemented sandbox or an approval to execute.

1. Select one exact source, mode and helper/import closure. Record source hashes, versions, inputs, schema, model revisions and the scientific context. Decide whether the goal is a synthetic check, exact historical replay or a new experiment. Do not equate them.
2. Obtain separate approval for that scope. Downloads, model inference, training, API/cloud calls and restoration of private inputs are outside this phase. Select wall-clock/inactivity limits, process-tree termination and a retry policy before launch; do not invent a universal timeout for all pipelines.
3. Allocate a new external run directory, outside all repositories/backups/archives, with separate read-only inputs and writable work/output/cache/temp/log areas. Use exclusive creation and fail if the run/output location already exists. This review created no such run directory.
4. Resolve all paths before code initialization, including input-existence fallbacks, absolute paths, __file__, dynamic imports, source-root discovery, logs and completion markers. Reject reparse-point/link escapes and aliases to protected files. Keep original input and source hashes, fold identity, labels and model revisions unchanged.
5. Set child-process-only bytecode/temp/cache/offline settings relevant to the selected libraries. Examples include PYTHONDONTWRITEBYTECODE, TEMP/TMP/TMPDIR, HF_HOME/HF_HUB_CACHE/HF_MODULES_CACHE, TORCH_HOME, JOBLIB_TEMP_FOLDER and MPLCONFIGDIR. Inspect whether source overrides them. These variables do not enforce filesystem or network containment. Do not change global/system settings.
6. Enforce the approved write and network boundary before imports, including native-library writes and child processes. A Python audit hook or process timeout alone is not that guarantee. Do not pass provider credentials to offline tests. If suitable enforcement is unavailable or conflicts with a fixed path, stop that test.
7. Frozen pipelines may require a separately approved private execution mirror with the original topology and verified originals. Do not modify frozen source, monkeypatch path globals, refresh expected hashes, fabricate a branch, clear markers or validate one source while running another. A mirror is only a possible future design; it was not built or verified here.
8. Before and after the test, compare complete inventories including ignored/untracked files, protected inputs, source/config/fold hashes, Git refs and index. Git status alone cannot see ignored writes. Ignore rules neither prevent writes nor stop overwrites.
9. Stop the process tree on an unexpected write/network request, missing input, hash/schema/fold mismatch, conflicting output, uncontrolled retry or timeout. Retain clearly marked incomplete outputs and diagnostics. Do not delete, overwrite, auto-resume or relaunch.
10. Accept only the approved narrow outcome. Capture exit status, resolved paths, input/output SHA-256, versions, duration and limitations. A source-only validator failure on an absent original is a blocker, not a reason to weaken its check. A helper PASS does not reproduce reported experiment metrics.

## Future sequence (not executed)

- First consider pure synthetic string/schema helpers, after checking their import closure. Do not collect a whole test suite as a shortcut; collection itself may import side-effectful modules.
- Next consider Module4 source-only verification with output captured externally. It can legitimately fail historical-hash checks; preserve that result.
- Prototype help/config-only parity can be considered with a separately approved compatible environment and enforced isolation. Prior Phase4 evidence does not cover a new launcher. Preserve the pre-existing YAML learning-rate string behavior.
- Keep whole notebooks and data/model-dependent pipelines BLOCKED until original prerequisites, provenance and every write path are resolved. No notebook, model, API, training or evaluation trial was run in this review.

## Evidence

- [Phase10 output-safety gate](<../phase1_artifacts_batch2_20261026/OUTPUT_SAFETY.md>).
- The [integrated baseline notebook](<../../../RAG/shroom_ensemble.ipynb>) and [historical ablation notebook](<../../../data/7.%20Ablation%20Synthetic%20Data/7.Ablation_Synthetic_Data.ipynb>) contain the output statements summarized above. The cell indexes refer to unchanged notebook JSON; these are static findings, not new executions.
- [All 17 Phase1 archival moves](<../phase1_artifacts_final_20261026/phase1_all_moves.json>).
- [Current Git ignore rules](<../../../.gitignore>) list excluded artifacts. This links to the policy, not a complete audit record. Ignore rules do not prevent writes or overwrites.
- [Execution matrix](EXECUTION_MATRIX.md) and [public safe-execution statement](<../../../docs/SAFE_EXECUTION.md>).
