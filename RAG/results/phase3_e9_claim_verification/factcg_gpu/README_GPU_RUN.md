# E10 FactCG GPU package and shared Phase 3 session

This package scores exactly 561 whole-hypothesis/reference pairs with
`yaxili96/FactCG-DeBERTa-v3-Large` at revision
`0430e3509dbd28d2dff7a117c0eae25359ff3e80`. See FACTCG_PROTOCOL.md for the frozen
prompt, reference chunking, class-1 probability and future evaluation rules.
No training, threshold tuning, decomposition or retrieval changes.

## One rented GPU, two sequential processes

Upload only `minicheck_gpu_portable.zip` and `factcg_gpu_portable.zip`.
Never upload the repository, feature matrices, labels or predictions.
Use Linux x86_64, Python 3.11, git, unzip/zip and a CUDA-12.1-compatible NVIDIA driver.
For both runs, use A100 40/80GB or equivalent: MiniCheck requires BF16 support,
>=39 GiB total / >=35 GiB free VRAM and >=24 GiB available RAM. Allow at least
50 GiB free disk for model caches plus environments/wheels (more may be needed).
FactCG alone uses float32, batch 1, and conservatively requires >=15 GiB total /
>=12 GiB free VRAM, >=8 GiB available RAM and >=6 GiB free cache disk. These safety
gates are not measured minimum requirements or guarantees against OOM.

Separate virtualenvs preserve MiniCheck's frozen dependencies and the FactCG release's
Torch 2.2.1 version. Both use the same GPU/driver, one process at a time. Each process
exits before the next loads a model, releasing GPU memory. Do not load these models
inside the notebook kernel. No install/upgrade inside the existing MiniCheck environment.

From a terminal or a notebook `%%bash` cell (Colab WORK=/content; Kaggle
WORK=/kaggle/working; other Linux: choose a writable working directory):

```bash
set -euo pipefail
WORK=/content
cd "$WORK"
unzip minicheck_gpu_portable.zip
unzip factcg_gpu_portable.zip

python3.11 -m venv minicheck_gpu/.venv
minicheck_gpu/.venv/bin/python -m pip install pip==24.3.1
minicheck_gpu/.venv/bin/python -m pip install -r minicheck_gpu/requirements_gpu.lock.txt
minicheck_gpu/.venv/bin/python -m pip check
minicheck_gpu/.venv/bin/python -B minicheck_gpu/validate_gpu_inputs.py
CUDA_VISIBLE_DEVICES=0 minicheck_gpu/.venv/bin/python -B minicheck_gpu/run_minicheck_gpu.py \
  --run --output-dir "$WORK/minicheck_gpu/gpu_run_001" --cache-dir "$WORK/minicheck_cache"
minicheck_gpu/.venv/bin/python -B minicheck_gpu/validate_gpu_outputs.py \
  "$WORK/minicheck_gpu/gpu_run_001/minicheck_scores.jsonl"

python3.11 -m venv factcg_gpu/.venv
factcg_gpu/.venv/bin/python -m pip install pip==24.3.1
factcg_gpu/.venv/bin/python -m pip install -r factcg_gpu/requirements_gpu.lock.txt
factcg_gpu/.venv/bin/python -m pip check
factcg_gpu/.venv/bin/python -B factcg_gpu/validate_gpu_inputs.py
CUDA_VISIBLE_DEVICES=0 factcg_gpu/.venv/bin/python -B factcg_gpu/run_factcg_gpu.py \
  --run --output-dir "$WORK/factcg_gpu/gpu_run_001" --cache-dir "$WORK/factcg_cache"
factcg_gpu/.venv/bin/python -B factcg_gpu/validate_gpu_outputs.py \
  "$WORK/factcg_gpu/gpu_run_001/factcg_scores.jsonl"

zip -j minicheck_gpu_return.zip minicheck_gpu/gpu_run_001/minicheck_scores.jsonl \
  minicheck_gpu/gpu_run_001/MINICHECK_GPU_REPORT.json \
  minicheck_gpu/gpu_run_001/MINICHECK_GPU_REPORT.md minicheck_gpu/gpu_run_001/environment_freeze.txt
zip -j factcg_gpu_return.zip factcg_gpu/gpu_run_001/factcg_scores.jsonl \
  factcg_gpu/gpu_run_001/FACTCG_GPU_REPORT.json \
  factcg_gpu/gpu_run_001/FACTCG_GPU_REPORT.md factcg_gpu/gpu_run_001/environment_freeze.txt
```

The shell stops on any failure. Fix environmental problems without relaxing model,
precision, context, scoring or dependency pins, then use a new output directory.
Omit `--run` for a no-weights preflight in a fresh directory. It returns BLOCKED with
an explicit preflight-only reason on suitable hardware. Actual unavailable CUDA,
dependency and hardware failures are also BLOCKED; inference errors are FAIL.
No automatic retries, CPU fallback or partial-output import. Hard process termination
may prevent report creation; missing report means an incomplete run.

## Return to local Windows

Download both return archives before ending the GPU session. Extract the FactCG files
under `factcg_gpu/returned_001/` and the MiniCheck files under `minicheck_gpu/returned_001/`.
Keep the original local manifests; do not overwrite them with remote copies.
From the repository root in PowerShell:

```powershell
$python = 'external-artifacts/local-50a4676b99b3/python.exe'
$phase = 'RAG/results/phase3_e9_claim_verification'
& $python -B "$phase/minicheck_gpu/validate_gpu_outputs.py" "$phase/minicheck_gpu/returned_001/minicheck_scores.jsonl"
& $python -B "$phase/minicheck_gpu/return_to_local.py" "$phase/minicheck_gpu/returned_001/minicheck_scores.jsonl"
& $python -B "$phase/factcg_gpu/validate_gpu_outputs.py" "$phase/factcg_gpu/returned_001/factcg_scores.jsonl"
& $python -B "$phase/factcg_gpu/return_to_local.py" "$phase/factcg_gpu/returned_001/factcg_scores.jsonl"
```

FactCG creates `features/e10_return/E10.csv` (561 rows, canonical_id + 37 features),
its freeze record and validated raw scores/report. It never fits Random Forest.
The existing MiniCheck importer independently creates its 49-feature E9-B matrix.

Only later, after return validation, run E10 once in the original local environment:

```powershell
& $python -B "$phase/factcg_gpu/evaluate_e10.py" --run-rf
```

This produces 561 OOF predictions, five fit records and the full requested comparison
in `evaluation/E10/`. The preparation task does not execute this command.

## Reproducibility and validation

The manifest hashes the portable input, package files, original canonical manifest,
36-feature matrix, folds, RF configuration and existing E9 provenance. The source
snapshot under upstream/ is for audit and equivalence tests; runtime uses the small
HF adapter, not the training package. Bundled NLTK tables avoid mutable data downloads.
requirements_gpu.lock.txt pins the Linux transitive environment, resolved with uv
0.8.22 for Python 3.11/manylinux_2_28 using releases before 2024-11-30. Dependency
resolution is checked locally; installation/model execution must pass remotely.

Local tests use synthetic probabilities only in temporary directories. Tokenization
tests use the real pinned tokenizer and NLTK tables but no weights. No real support
scores or production E10 matrix are produced during preparation. Hashes verify
integrity and association, not hardware attestation. The full created-file list,
test results and transfer hashes are in LOCAL_VALIDATION_REPORT.md.
