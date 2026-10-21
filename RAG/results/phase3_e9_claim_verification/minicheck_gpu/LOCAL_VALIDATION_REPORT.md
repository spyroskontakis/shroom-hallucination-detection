# E9-B GPU package: local preparation PASS

No real inference, model download, RF fit, commit, push or official-test access occurred.
The original E9 experiment files were not modified. Only this new package directory
was created. The actual Linux CUDA run remains unverified.

- Portable input: 561 canonical samples; 575 frozen claims; 68 sample fallbacks retained.
- Task references: DM/MT=tgt; PG=src. Every claim/reference matches the saved E9-A NLI input hashes.
- 11 new offline tests PASS; 14 existing E9 offline tests PASS.
- Synthetic import in a temporary directory: 561 rows, 49 features, exact first-44 cell preservation.
- Rejected: missing/duplicate/extra/unknown claims, bad indices, nonfinite/out-of-range probabilities,
  wrong model/provenance, altered input/output hashes, duplicate JSON keys and extra output fields.
- Threshold boundary 0.5 and population standard deviation verified.
- Isolated extraction of the portable zip: input validation PASS without repository access.
- Local real preflight: BLOCKED (Linux x86_64 required), model_loaded=false, claims_processed=0.
- Full Linux/Python 3.11 dependency resolution PASS (uv 0.8.22); installation not executed locally.
- Existing E9 inventory: 2678 files remain byte-identical.
- Source E9-A: 44 features. Production E9-B has not been created.

## Integrity (SHA-256)

| Artifact | SHA-256 |
|---|---|
| minicheck_inputs.jsonl | `e41506779d4798c0ad2476e8da38ca197ebda2960a100848890181b852f3080a` |
| canonical claims/reference digest | `7b63bdbfc62a2a5b6d0598ef7664fb3867cf9865ceca3304b159ee8db6ecaa0c` |
| original full_claims.jsonl | `da0426cae48478f8cb8ba8473f37a80008057e86d89a328bd5d002d3fd48190e` |
| original E9-A.csv | `26fcaaab5b10c1710984c2f9a923c98df1f922284622299dc4baae8a4dc846b0` |
| GPU_RUN_MANIFEST.json | `29661b0377ccfc5bae18dede57924e7440385c3eb75eef460a94ab6c4e863be7` |
| minicheck_gpu_portable.zip | `02373bfdf2f851b31e3e6883c66225e3ec23618e2272fcaae4478c623613c8f4` |

## Files created

All paths below are relative to `RAG/results/phase3_e9_claim_verification/minicheck_gpu/`.
No pre-existing file was modified.

- `.gitignore`
- `GPU_RUN_MANIFEST.json`
- `LOCAL_VALIDATION_REPORT.md`
- `README_GPU_RUN.md`
- `gpu_common.py`
- `local_preflight/MINICHECK_GPU_REPORT.json`
- `local_preflight/MINICHECK_GPU_REPORT.md`
- `local_preflight/environment_freeze.txt`
- `minicheck_gpu_portable.zip`
- `minicheck_inputs.jsonl`
- `nltk_data/tokenizers/punkt_tab/english/abbrev_types.txt`
- `nltk_data/tokenizers/punkt_tab/english/collocations.tab`
- `nltk_data/tokenizers/punkt_tab/english/ortho_context.tab`
- `nltk_data/tokenizers/punkt_tab/english/sent_starters.txt`
- `prepare_gpu_inputs.py`
- `requirements_gpu.lock.txt`
- `requirements_gpu.txt`
- `return_to_local.py`
- `run_minicheck_gpu.py`
- `test_gpu_package.py`
- `validate_gpu_inputs.py`
- `validate_gpu_outputs.py`

## Git status

Branch: `phase3-e9-claim-verification`.
`git diff --stat`: empty (no tracked-file changes).
`git status --short`: `?? RAG/results/phase3_e9_claim_verification/` (already untracked at task start).
Input JSONL, archive and local preflight reports are ignored by the new package .gitignore.
Nothing staged, committed or pushed.

## Run

Upload `minicheck_gpu_portable.zip` only. Follow README_GPU_RUN.md for the complete
Colab/Kaggle/Linux install, execution and return commands. Use a BF16-capable GPU
(e.g. A100 40/80GB), at least 39 GiB total / 35 GiB free VRAM, 24 GiB free host RAM,
35 GiB free cache disk, Linux x86_64 and Python 3.11. Safety gates are conservative,
not measured minimum requirements. No automatic downgrades or retries.
