# E11-B raw detector scoring: prepared, not run

This preparation creates **raw factuality scores**, not hallucination pseudo-labels. Each of four frozen detectors receives the same label-blind `(sample_key, task, reference_text, whole_hypothesis)` row. DM and MT use `tgt` as reference; PG uses `src`. Every claim is the complete original hypothesis. The future fold-specific logistic-regression teachers can reuse a single immutable unlabeled score for each detector because pretrained detector inference uses no SHROOM label. A fold's held-out text is used only for its deterministic eligibility purge; held-out labels never enter scoring, purge, teacher fitting, or student training. The E11 teacher protocol and all E6/E9/E10 files remain unchanged.

## What is prepared

| Artifact | Rows | Purpose |
| --- | ---: | --- |
| `HUMAN_TEACHER_INPUTS.csv` | 561 | Stable human IDs, task/fold, reused FactCG/HHEM/NLI scores, and an explicit pending whole-hypothesis MiniCheck field. No labels or human text. |
| `human_whole_hyp_minicheck_inputs.jsonl` | 561 | One reference and complete hypothesis per human sample for the missing MiniCheck pass. No labels/fold fields. |
| `unlabeled_master.jsonl` | 28,649 | First original row for each normalized `(task,src,tgt,hyp)` key, ordered by sample hash. Contains source fields needed for audit, resolved reference, original index, and source-file provenance. No labels/predictions. |
| `fold_1_eligibility.jsonl` … `fold_5_eligibility.jsonl` | 28,649 each | Sample-key, eligible flag, and first text-only purge reason. Eligible counts: **28,575 / 28,623 / 28,627 / 28,611 / 28,615**. No pseudo-labels. |
| `benchmark_600.jsonl` | 600 | First 200 sample hashes per task: **200 DM, 200 MT, 200 PG**. Identical input for all four detectors. |

The sole unlabeled source is the 30,000-row **model-agnostic** SHROOM training split. Deduplication and fold purges use the exact normalization and four text-key tests frozen in `E11_TEACHER_PROTOCOL.json`; the preparation script refuses changed output bytes on rerun. All 10,000 raw PG targets are empty, so PG reference resolution is explicitly checked against `src`. The benchmark SHA256 is `7f34efa45f358b268e8df281d979a025ff41a48929d1debca820ef6353a4201d`. Every prepared file SHA256 appears in `E11_SCORING_MANIFEST.json` and `E11_INPUT_PREPARATION_REPORT.json`.

The 561 reusable FactCG scores come from the exact `phase3-003` E10 return. HHEM `hhem_ref_hyp_consistency` and NLI `nli2_ref_hyp_{entailment,neutral,contradiction}` come from the hash-verified E6-v3 matrix; IDs join one-to-one and NLI sums are checked. HHEM is a **support-oriented consistency score**, computed by sigmoid of one logit, not a hallucination probability. FactCG is Yes-class support softmax; MiniCheck is official top-5 yes-token support mass; NLI class indices are asserted as entailment=0, neutral=1, contradiction=2. The E9-B MiniCheck claim-level scores are deliberately excluded. Only the 561 human whole-hypothesis MiniCheck scores remain missing.

## Reused implementations and adapters

| Detector | Frozen source reused | E11 wrapper and score |
| --- | --- | --- |
| FactCG | `RAG/results/phase3_e9_claim_verification/factcg_gpu/factcg_backend.py` imported unchanged from the frozen ZIP | `FactCGAdapter` calls its exact `load` and `score`; one whole-hyp support probability per sample. Pinned `yaxili96/FactCG-DeBERTa-v3-Large@0430e3509dbd28d2dff7a117c0eae25359ff3e80`, float32, no quantization, original reference chunking/instruction/aggregation. |
| MiniCheck | `RAG/results/phase3_e9_claim_verification/minicheck_gpu/run_minicheck_gpu.py` and official pinned MiniCheck package imported unchanged | `MiniCheckAdapter` calls its exact pinned `load_scorer` and official `score(docs,claims,chunk_size=32468)` in batches of 16, using each whole hypothesis once. `bespokelabs/Bespoke-MiniCheck-7B@1ed7786bcda3fa1dc35f7c4ed9e3f36b785d33b8`, BF16, no quantization. |
| NLI | E6-v2 `nli_backend.py`/model mirror and `v2_common.py` establish model, class map, tokenization and scores | `PairModelAdapter` loads the unchanged local checkpoint into CUDA float32; paired reference→hypothesis tokenization, longest-first 512, batch 16, softmax in exact class order. `MoritzLaurer/DeBERTa-v3-large-mnli-fever-anli-ling-wanli@b3546ea6b0346eb6f8d5d68b13c7dc6d0376b3d7`. The original CPU backend is not edited. |
| HHEM | E6-v3 `hhem_backend.py`/model mirror and `v3_common.py` establish model, pair direction and sigmoid meaning | `PairModelAdapter` loads the unchanged local checkpoint into CUDA float32; paired reference→hypothesis tokenization, longest-first 512, batch 16, single-logit sigmoid. `vectara/hallucination_evaluation_model@58383384656cbaec2949a75a41f20e891e90a73b`. The original CPU backend is not edited. |

The NLI/HHEM GPU wrappers preserve original input direction, tokenizer/truncation, checkpoint, float32 precision, activation, and class mapping; only placement and batch size differ from the old CPU implementation. Their A100 outputs have **not** been benchmarked yet. Synthetic two-pair CPU smokes of the original E6 backends passed using `external-artifacts/local-21bb07554028/python.exe` (Python 3.11). The system `python` is Python 3.12 with an incompatible older Transformers/NumPy combination for that CPU smoke, so it must not be used to infer GPU readiness.

## Resumable output store

The new persistent Modal Volume is `shroom-e11-raw-detector-scores`, mounted at `/results`; all E11 outputs live under `e11/`. The scoring journals are:

```text
e11/raw_detector_scores/factcg/{scores.jsonl,manifest.json,validation_benchmark.json,validation_full.json}
e11/raw_detector_scores/minicheck/{scores.jsonl,manifest.json,validation_benchmark.json,validation_full.json}
e11/raw_detector_scores/nli/{scores.jsonl,manifest.json,validation_benchmark.json,validation_full.json}
e11/raw_detector_scores/hhem/{scores.jsonl,manifest.json,validation_benchmark.json,validation_full.json}
e11/human_minicheck/{scores.jsonl,manifest.json,validation_human.json}
e11/model_cache/
e11/runs/<run-id>/{STARTED.json,detector_scope_PASS.json,COMPLETE.json or FAILED.json}
```

Each output row contains sample key, SHA256 of the exact four-field input, detector, model ID, revision, and only that detector's frozen raw score fields. The store validates every existing row before resuming: duplicate/foreign keys, wrong input hash/model/revision, nonfinite/out-of-range scores, invalid NLI sums, corrupted JSONL, and mismatched checkpointed-file hash all fail closed. A valid tail written after an interrupted checkpoint is reconciled. The benchmark writes its 600 scores to the **same per-detector journal** later used by the full run, so full scoring skips them. A completed FactCG journal is not recomputed if MiniCheck or another detector fails. Batches are fsynced, checkpointed, and Volume-committed while scoring; a Linux file lock prevents Volume commit during a batch write. `model_cache/` on the same Volume retains downloaded pinned checkpoints where the backend supports caching. Validation reports identify the completed scope and record model-load, inference, and total-stage seconds plus runtime versions; run status records wall time including Volume commits. No journal contains a pseudo-label or teacher output.

The Modal image copies only the three prepared detector input JSONL files, protocol/manifest, E11 scoring code, the two original frozen portable ZIPs, and the NLI/HHEM model mirrors. All required E11 runtime files are copied into **`/opt/e11/`**, and the remote module explicitly adds that directory to `sys.path` before importing `scoring_common`. It extracts the ZIPs at the separate real repo-like path `/opt/SHROOM/SHROOM2024/RAG/results/phase3_e9_claim_verification/` required by the frozen FactCG package. Before model load, the FactCG and MiniCheck adapters call their original frozen input validators and hardware/dependency preflights, including the pinned official MiniCheck source check. MiniCheck runs in its own frozen vLLM/PyTorch environment; FactCG, NLI, and HHEM use the separate frozen FactCG environment. Each stage runs in a subprocess so GPU memory is released before the next. The resource request is **one A100-80GB**, **64 GiB RAM**, **524,288 MiB ephemeral disk**, **12-hour timeout**, eight CPUs, and the dedicated persistent Volume. There is no GPU-to-CPU fallback, quantization, secret, or change to the original packages. The real GPU name/VRAM and baked input hashes are checked before inference.

## Future commands — do not run until GPU spend is approved

From `` in PowerShell. First verify local preparation:

```powershell
python -B RAG/results/phase3_e11_task_adaptation/validate_teacher_protocol.py
python -B RAG/results/phase3_e11_task_adaptation/e11_modal.py --validate-local
python -B RAG/results/phase3_e11_task_adaptation/test_scoring.py
```

**Benchmark only** (600 unlabeled shared across four detectors, plus 561 human whole-hyp MiniCheck inputs):

```powershell
python -m modal run RAG/results/phase3_e11_task_adaptation/e11_modal.py --run-id e11-benchmark-003
python -B RAG/results/phase3_e11_task_adaptation/download_scoring_outputs.py --scope benchmark --run-id e11-benchmark-003 --destination RAG/results/phase3_e11_task_adaptation/downloaded_benchmark/e11-benchmark-003
python -B RAG/results/phase3_e11_task_adaptation/validate_scoring_outputs.py --scope benchmark --directory RAG/results/phase3_e11_task_adaptation/downloaded_benchmark/e11-benchmark-003
```

The benchmark command has no `--full-run` flag and cannot select the master 28,649-row scope. Before approving the full run, inspect its PASS reports, all four detector row counts, human MiniCheck 561/561, score ranges/NLI sums, actual A100 inference times, model download/cache behavior, and projected billable GPU hours. Confirm the provider's current A100/CPU/RAM/storage pricing separately; no price is hardcoded.

**Future full scoring only after benchmark/cost approval:**

```powershell
python -m modal run RAG/results/phase3_e11_task_adaptation/e11_modal.py --run-id e11-full-001 --full-run
```

If interrupted, use the same run ID; existing validated score rows are skipped:

```powershell
python -m modal run RAG/results/phase3_e11_task_adaptation/e11_modal.py --run-id e11-full-001 --full-run --resume
```

Then download and validate the final raw scores:

```powershell
python -B RAG/results/phase3_e11_task_adaptation/download_scoring_outputs.py --scope full --run-id e11-full-001 --destination RAG/results/phase3_e11_task_adaptation/downloaded_full/e11-full-001
python -B RAG/results/phase3_e11_task_adaptation/validate_scoring_outputs.py --scope full --directory RAG/results/phase3_e11_task_adaptation/downloaded_full/e11-full-001
```

The full run requires `--full-run` at the Modal entrypoint and at the raw-scoring subprocess. `--resume` is accepted only with `--full-run`. Downloads use `python -m modal volume get` through the prepared read-only download script. No listed command was executed remotely during this preparation.

## Local audit result and limit

The reproducibility manifest records all source/prepared SHA256 hashes, model revisions, output schemas, resource requests, software requirements, and exact commands. The local test suite covers score joins, normalization, leakage, task/reference policy, benchmark/fold counts, output contracts, duplicate/missing/corrupt score rejection, partial resume, protocol immutability, and the full-run guard. The only missing human raw signal is whole-hypothesis MiniCheck. Static preparation found no path to the official test and no pseudo-label-generation or model-training call in operational code. **End-to-end Linux A100 execution remains unverified** until the 600-row benchmark; the image build, CUDA dependencies, model loading, vLLM integration, and GPU runtime/cost must be confirmed by that benchmark before a full run.

## Infrastructure-only repair after `e11-benchmark-001`

The first benchmark attempt, **`e11-benchmark-001`**, failed while Modal imported `/root/e11_modal.py`, before any MiniCheck, FactCG, NLI, or HHEM inference. The observed exception was `ModuleNotFoundError: No module named 'scoring_common'`. It is an **infrastructure/import failure**, not an experiment or a benchmark measurement; this attempt supplies no valid model timing or score result.

Modal 1.5.5 mounts the function source at `/root/e11_modal.py`, while `Image.add_local_file(..., remote_path=..., copy=True)` copies auxiliary files to the exact absolute `remote_path` in the image. The previous code copied `scoring_common.py` into `/opt/SHROOM/.../phase3_e11_task_adaptation/`, then imported it by bare name from `/root/e11_modal.py`. That image directory was not on Python's import path. The repair copies every required E11 runtime module/input to `/opt/e11/` and explicitly inserts `/opt/e11` in `sys.path` before the first E11 helper import. It also avoids rebuilding the image from local checkout paths during remote module hydration, validates all required remote files and the `/results` Volume mount before detector work, and leaves `retries=0` and the full-run guard intact.

`import_layout_smoke.py` creates a temporary `/opt/e11`-equivalent tree, imports all three helper modules from a separate working directory, then simulates Modal hydrating a copy of `/root/e11_modal.py` from a different directory with `modal.is_local()` false. It verifies the remote path contract and checks that a missing helper produces `E11_LAYOUT_FAIL`. This is local simulation only; it cannot prove Modal's next hydration or GPU execution. The frozen teacher protocol is unchanged.

That import-path repair was tried with a fresh ID, `e11-benchmark-002`. The second attempt exposed the separate path-depth failure documented below. Neither attempt provides an inference result.

## Infrastructure-only repair after `e11-benchmark-002`

The second attempt, **`e11-benchmark-002`**, failed while importing `/opt/e11/scoring_common.py`: its import-time `HERE.parents[2]` lookup was valid in the local checkout but not at the shallow `/opt/e11` location. No detector inference began, so the attempt provides **no valid scores or benchmark timings**.

The scorer now uses `/opt/e11` and `/results` as explicit remote roots. Local-only repository discovery searches for a checkout marker instead of assuming a parent index; remote import does not perform that search. The local protocol validator's separate `HERE.parents[2]` lookup was removed as well. A simulated shallow layout imports `scoring_common`, `detector_adapters`, and `run_detector` from `/opt/e11`-equivalent files, hydrates the Modal function from a separate directory, verifies every prepared input, package, model asset and Volume path, and statically rejects indexed `.parents[...]` lookups throughout E11 Python sources. The frozen protocol, detector semantics, resources, benchmark/full-run guard, packages and Volume paths are unchanged. The next benchmark ID is `e11-benchmark-003`; this repair did not invoke Modal.
