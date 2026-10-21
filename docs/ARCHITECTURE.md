# Architecture and dependencies

The project evolved through four related layers:

1. Dataset preparation and canonical fold assignment under `codex/`.
2. NLI, semantic-similarity and Random Forest baseline experiments E1–E4.
3. Retrieval and external-evidence modules under `RAG/`, followed by E6–E10 feature and routing experiments.
4. DeBERTa task adaptation and contrastive objectives in E11.

Many scripts intentionally resolve files relative to their own experiment directory. The staging process therefore preserves the original `RAG/`, `codex/` and `solution/` paths. No import, path or source-hash refactoring was applied.

There is no single environment valid for every experiment. Existing requirements and runtime manifests are authoritative for their own stage. E6-v4 uses a separate pinned compatibility environment; E9 has distinct local/GPU specifications; E11 records Python 3.11.12, PyTorch 2.2.1+cu121, CUDA 12.1, Transformers 4.38.1, tokenizers 0.15.2 and NumPy 1.26.4 for the C/D/E runs.