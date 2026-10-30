# Frozen E9-B GPU package

This package computes support scores only for **bespokelabs/Bespoke-MiniCheck-7B**.
Inputs contain exactly 561 canonical development/trial samples and 575 already-frozen
claims. The five-field JSONL allowlist is canonical_id, task, claim_index, claim_text,
reference_text. DM/MT use tgt; PG uses src. No labels, predictions, RF outputs, folds,
or official test rows are exported. The fallback claims are retained verbatim.

## Fixed implementation and hardware

- Official MiniCheck commit: `00a1ed40715ba11b9718ef251a3b0c493992944e`.
- Exact checkpoint/tokenizer/code revision: `1ed7786bcda3fa1dc35f7c4ed9e3f36b785d33b8`.
- Official MiniCheck.score / LLMCheck / vLLM path; original whole-claim prompt and
  scoring code. Later upstream code adds SentenceFusion; it is deliberately not used.
- BF16, no quantization, one GPU, context 32768, document chunk size 32468,
  prefix caching off, seed 2024, temperature 0, max_tokens 1, logprobs 5.
  The official support score sums the probabilities of returned top-5 tokens whose
  decoded text is `yes` ignoring case, then takes the maximum across reference chunks.
  It does not renormalize yes/no logits. Frozen claims are never split or rewritten.
- The only engine adapter adds checkpoint/tokenizer/code revision pins and makes
  CUDA/no-quantization/default memory settings explicit. No prompt or scorer patch.
- Linux x86_64, Python 3.11, PyTorch 2.4.0 CUDA 12.1, vLLM 0.6.3.post1.
  A working CUDA BF16 kernel is required. CUDA toolkit installation is not needed
  with these wheels; the host NVIDIA driver must support the CUDA 12.1 runtime.
- Use an A100 40/80GB or comparable BF16 GPU. The conservative package gate requires
  39 GiB total and 35 GiB free VRAM, 24 GiB available host RAM and 35 GiB free cache
  disk. These are preparation safety limits, not a measured vendor minimum or an OOM
  guarantee. T4/P100 and typical 16GB notebook GPUs are blocked. No reduced context,
  precision switch, CPU fallback or automatic retries are permitted.

Sources: [official pinned implementation](https://github.com/Liyan06/MiniCheck/tree/00a1ed40715ba11b9718ef251a3b0c493992944e),
[exact model snapshot](https://huggingface.co/bespokelabs/Bespoke-MiniCheck-7B/tree/1ed7786bcda3fa1dc35f7c4ed9e3f36b785d33b8),
[vLLM engine](https://github.com/vllm-project/vllm/tree/v0.6.3.post1).

## Colab / Kaggle / Linux execution

1. Select a qualifying GPU runtime and enable internet for dependency/model downloads.
   Upload **only** `minicheck_gpu_portable.zip`; do not upload the repository or E9-A
   matrix. Extract it to a writable directory. Kaggle dataset mounts are read-only;
   extract to `/kaggle/working`. Colab can use `/content`.
2. Run the following in a terminal, or a notebook `%%bash` cell. Set `WORK` to the
   writable directory containing the archive. Use a clean Python 3.11 environment;
   notebook kernel packages are not used. If python3.11 is unavailable, use an
   equivalent Linux image providing it; do not relax package pins.

```bash
set -euo pipefail
WORK=/content                         # Kaggle: /kaggle/working
cd "$WORK"
unzip minicheck_gpu_portable.zip
cd minicheck_gpu
python3.11 -m venv .venv
.venv/bin/python -m pip install pip==24.3.1
.venv/bin/python -m pip install -r requirements_gpu.lock.txt
.venv/bin/python -m pip check
.venv/bin/python -B validate_gpu_inputs.py
CUDA_VISIBLE_DEVICES=0 .venv/bin/python -B run_minicheck_gpu.py \
  --run --output-dir gpu_run_001 --cache-dir "$WORK/minicheck_model_cache"
.venv/bin/python -B validate_gpu_outputs.py gpu_run_001/minicheck_scores.jsonl
zip -j minicheck_gpu_return.zip gpu_run_001/minicheck_scores.jsonl \
  gpu_run_001/MINICHECK_GPU_REPORT.json gpu_run_001/MINICHECK_GPU_REPORT.md \
  gpu_run_001/environment_freeze.txt
```

For a hardware/dependency check without loading/downloading weights, omit `--run`
and use a new output directory. The report then has BLOCKED status with an explicit
preflight-only reason even when checks pass. Every run needs a fresh directory.
An interrupted/failed run keeps `.partial.jsonl` and cannot be imported. Hard process
termination may prevent report creation; such a run is incomplete and rejected.
There is no resume/retry behavior. Correct the environment and launch a fresh run.

Return the four files in `minicheck_gpu_return.zip`. Keep the local original manifest;
do not replace it with a remote copy. Hashes establish byte integrity and pairing,
not cryptographic proof that inference was actually performed on a particular GPU.

## Return to this Windows checkout (after a successful GPU run)

Extract the returned archive into a new `returned_001` directory under this package.
From the repository root in PowerShell:

```powershell
$gpu = 'RAG/results/phase3_e9_claim_verification/minicheck_gpu'
$python = 'external-artifacts/local-50a4676b99b3/python.exe'
& $python -B "$gpu/validate_gpu_outputs.py" "$gpu/returned_001/minicheck_scores.jsonl"
& $python -B "$gpu/return_to_local.py" "$gpu/returned_001/minicheck_scores.jsonl"
```

The importer verifies the original local claims, canonical reference manifest, E9-A
matrix and configuration against frozen hashes, and compares every exported input
with those local fields. It requires 575 unique claim keys, finite probabilities in
[0,1], exact model and scoring metadata, a PASS report and matching output hash.
It creates `../features/minicheck_return/E9-B.csv` plus a freeze record exclusively.
The result has canonical_id plus 49 features, preserving every original E9-A cell
string and row order. Appended features are mean, min, max, population std (ddof=0),
and fraction strictly below 0.5. It never imports or runs Random Forest.

## Local preparation and limits

`prepare_gpu_inputs.py` is a one-time local export and refuses to replace a frozen
manifest. It is not needed on the GPU host. `test_gpu_package.py` uses synthetic
scores only inside temporary directories, including a 561x49 import test.
Run locally with `python -B test_gpu_package.py`. The portable archive includes these
local utility scripts for completeness; do not run them on the GPU host, where the
original frozen local files are absent.

The manifest records per-file package hashes, each original input/matrix hash,
canonical claim/reference content digest, official source hashes and inference pins.
English NLTK Punkt tables are bundled and hashed so scoring never downloads mutable
tokenizer data. The Linux dependency lock is resolved during preparation; the runtime
also records `pip freeze`. Local tests do not establish CUDA execution compatibility:
the first Linux GPU run must pass preflight, model loading and complete output validation.
No real scores or production E9-B matrix are created by preparation.

Lock generation used uv 0.8.22, target Python 3.11/Linux x86_64 manylinux_2_28,
with PyPI releases before 2024-11-30 to match the fixed inference stack's era.
The historical Outlines dependency `pyairports` is installed from its original
[pinned source](https://github.com/NICTA/pyairports/tree/9699eae8c6b03c97239018dea92e01daa8594936),
because its historical PyPI release is unavailable. No dependency source is patched.
Dependency resolution succeeded locally; installation/imports remain GPU-host checks.
