# Frozen E10 preparation: PASS

Prepared only: no model weights loaded, real support scores, RF fits, production E10
matrix, official-test access, commits or pushes. Exact checkpoint:
`yaxili96/FactCG-DeBERTa-v3-Large`, revision
`0430e3509dbd28d2dff7a117c0eae25359ff3e80`.

## Verified population and behavior

- 561 unique canonical rows (493 development_model_agnostic + 68 trial).
- Exact four-field input allowlist, whole original hypotheses, DM/MT=tgt and PG=src.
- E6-v3 numerical/provenance verification PASS: 474/561, accuracy 0.8449197860962567,
  Spearman 0.7816945786401444, unchanged 36 features and five locked folds.
- 16 E10 offline tests PASS, including strict schema/provenance validation,
  missing/duplicate/unknown IDs, invalid scores, hash tampering, CPU/Windows blocking,
  mocked complete/failing inference, shuffled return import and explicit RF opt-in.
- Official template, reference chunking and pinned real tokenization equivalence PASS
  for all 561 inputs and additional long/boundary cases. No weights used.
- Actual population token audit: 561 reference chunks, maximum 162 formatted tokens,
  0 chunks over the official 2048-token limit. No input is truncated.
- Temporary synthetic E10 import: 561 rows, 37 features, all 36 baseline cells exact.
- Existing MiniCheck portable input validation remains PASS (561 samples, 575 claims).
- 2700 pre-existing E9 files, including MiniCheck package and ZIP, remain byte-identical.
- Full Linux/Python 3.11 dependency lock resolved; GPU installation not executed locally.
- Extracted standalone FactCG ZIP validates successfully without repository access.
- Local GPU preflight correctly BLOCKED on Windows before model load; this is not a GPU PASS.

An initial test invocation started before manifest creation completed and failed with
FileNotFoundError. After the exporter completed, the entire 16-test suite passed.
All synthetic results were restricted to automatically removed temporary directories.
The temporary validation environment did not change shroom_ensemble.

## SHA-256

| Artifact | SHA-256 |
|---|---|
| factcg_inputs.jsonl | `10ecdbc5f25bd4b9c7c7d4c2d131194647a86c556591c75418dbcb436ba1753d` |
| canonical content digest | `6398e07f356c49bd1695194c461daa40b63e61f8004cf06cfd7bba7be46dd414` |
| GPU_RUN_MANIFEST.json | `357e2b011f9403dfe9fb28ae84ffc4cd3524eeb5e9f347d3d295f90dceb30d3f` |
| factcg_gpu_portable.zip | `5388d4373f054af19ecdaa10b1960c1ca982affb4827fa6a98028caf46e362ad` |
| frozen E6-v3 36-feature matrix | `1e6386fbd0b89a3a295828259ec8fea9b5b3fc03465d65f82e546687c32e7229` |
| unchanged minicheck_gpu_portable.zip | `02373bfdf2f851b31e3e6883c66225e3ec23618e2272fcaae4478c623613c8f4` |

The manifest includes original canonical, fold, RF configuration and feature hashes,
all package asset hashes, official source and tokenizer assets. Preserve the local
manifest when importing results; hashes establish integrity, not GPU attestation.

## Exact files created

All 36 files below are new and under
`RAG/results/phase3_e9_claim_verification/factcg_gpu/`. No pre-existing workspace file
was modified. Local preflight and audit reports remain local; ZIP contains only the
manifest and its enumerated portable files.

- `.gitignore`
- `FACTCG_PROTOCOL.md`
- `GPU_RUN_MANIFEST.json`
- `LOCAL_TOKENIZATION_AUDIT.json`
- `LOCAL_VALIDATION_REPORT.md`
- `README_GPU_RUN.md`
- `evaluate_e10.py`
- `factcg_backend.py`
- `factcg_common.py`
- `factcg_gpu_portable.zip`
- `factcg_inputs.jsonl`
- `local_preflight/FACTCG_GPU_REPORT.json`
- `local_preflight/FACTCG_GPU_REPORT.md`
- `local_preflight/environment_freeze.txt`
- `nltk_data/tokenizers/punkt_tab/english/abbrev_types.txt`
- `nltk_data/tokenizers/punkt_tab/english/collocations.tab`
- `nltk_data/tokenizers/punkt_tab/english/ortho_context.tab`
- `nltk_data/tokenizers/punkt_tab/english/sent_starters.txt`
- `prepare_gpu_inputs.py`
- `requirements_gpu.lock.txt`
- `requirements_gpu.txt`
- `return_to_local.py`
- `run_factcg_gpu.py`
- `test_factcg_package.py`
- `tokenizer_snapshot/added_tokens.json`
- `tokenizer_snapshot/config.json`
- `tokenizer_snapshot/special_tokens_map.json`
- `tokenizer_snapshot/spm.model`
- `tokenizer_snapshot/tokenizer.json`
- `tokenizer_snapshot/tokenizer_config.json`
- `upstream/LICENSE`
- `upstream/factcg/factcg_score.py`
- `upstream/factcg/inference.py`
- `upstream/factcg/utils.py`
- `validate_gpu_inputs.py`
- `validate_gpu_outputs.py`

## Shared GPU execution

README_GPU_RUN.md contains complete sequential installation, execution, validation,
return packaging and local import commands. Run MiniCheck first with its unchanged
Torch 2.4.0/vLLM environment; after that process exits, run FactCG using a separate
Torch 2.2.1/Transformers 4.38.1 environment on the same GPU. No model is kept alive
in the notebook kernel. The combined session uses an A100 40/80GB or equivalent,
>=39 GiB total / >=35 GiB free VRAM, >=24 GiB free host RAM, Linux x86_64/Python 3.11,
CUDA-12.1-compatible driver and sufficient disk for both environments and checkpoints.
These are conservative gates, not measured minimum requirements.

Future E10 evaluation is frozen in FACTCG_PROTOCOL.md and evaluate_e10.py. Exactly
five fits, 561 OOF predictions, all requested paired diagnostics, and an exclusive
run directory; preparation does not invoke it. Accuracy is primary, Spearman breaks
accuracy ties, and a complete tie or worse retains E6-v3.

## Git status

Branch: `phase3-e9-claim-verification`.
`git diff --stat`: empty; no tracked-file changes.
`git status --short`: `?? RAG/results/phase3_e9_claim_verification/` (already untracked).
New input JSONL, ZIP and local preflight reports are ignored by the new .gitignore.
Nothing staged, committed or pushed.
