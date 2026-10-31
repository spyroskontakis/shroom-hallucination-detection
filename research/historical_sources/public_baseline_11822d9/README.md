# Selected public-baseline sources

This directory contains the final 13 historical files from the original public
baseline, preserved byte-for-byte. The internal RAG/ and codex/ names keep ten
immutable relative references valid. They are historical namespace segments,
not top-level development directories or duplicate active implementations.

Baseline: [11822d92070cd29360445cb4dacd8d110c655248](https://github.com/spyroskontakis/shroom-hallucination-detection/tree/11822d92070cd29360445cb4dacd8d110c655248).

| Source | Purpose |
|---|---|
| [RAG/E6_REPRODUCIBILITY.md](RAG/E6_REPRODUCIBILITY.md) | Historical E6 reproducibility record |
| [RAG/results/phase3_e11_task_adaptation/E11_DATA_AUDIT.md](RAG/results/phase3_e11_task_adaptation/E11_DATA_AUDIT.md) | Immutable E11 data and protocol audit |
| [RAG/results/phase3_e9_claim_verification/factcg_gpu/factcg_backend.py](RAG/results/phase3_e9_claim_verification/factcg_gpu/factcg_backend.py) | Historical FactCG backend source |
| [RAG/results/phase3_e9_claim_verification/minicheck_gpu/run_minicheck_gpu.py](RAG/results/phase3_e9_claim_verification/minicheck_gpu/run_minicheck_gpu.py) | Historical MiniCheck GPU producer source |
| [RAG/results/rag_e6_v1/E6_PROTOCOL.md](RAG/results/rag_e6_v1/E6_PROTOCOL.md) | Frozen E6-v1 protocol |
| [RAG/results/rag_e6_v1/E6_RESULTS.md](RAG/results/rag_e6_v1/E6_RESULTS.md) | Recorded E6-v1 results |
| [RAG/results/rag_e6_v1/config/completion_manifest.json](RAG/results/rag_e6_v1/config/completion_manifest.json) | E6-v1 completion provenance |
| [RAG/results/rag_e6_v1/config/run_config.json](RAG/results/rag_e6_v1/config/run_config.json) | E6-v1 recorded run configuration |
| [RAG/results/rag_e6_v2/scripts/nli_backend.py](RAG/results/rag_e6_v2/scripts/nli_backend.py) | Historical NLI backend source |
| [RAG/results/rag_e6_v3/scripts/evaluate_v3.py](RAG/results/rag_e6_v3/scripts/evaluate_v3.py) | Historical E6-v3 evaluation source |
| [RAG/results/rag_e6_v3/scripts/hhem_backend.py](RAG/results/rag_e6_v3/scripts/hhem_backend.py) | Historical HHEM backend source |
| [codex/canonical_fold_generation_metadata.json](codex/canonical_fold_generation_metadata.json) | Recorded canonical-fold metadata |
| [codex/data/shroom_ensemble.ipynb](codex/data/shroom_ensemble.ipynb) | Historical baseline notebook variant |

This is a selected 13-file source archive, not the complete 944-file H1 snapshot
and not a runnable experiment package. Existing authenticated historical-snapshot
validation still requires the full exact tree outside Git, and historical H0
requirements still need the genuine original inputs. Do not run these producers
from the archive or use it as an evidence/input root.

The E11 audit's original protocol link at line67 remains broken. No historical
Markdown contents, source locks or numerical results were modified to fix it.
The notebook's public SHA does not match the different original SHA associated
with saved filesystem metadata. That evidence remains unavailable and unverified;
the notebook has not been executed or represented as an authentic timestamped original.

The [current-layout catalog](../../../project_records/current_layout/repository_compatibility_root_archive_v1.json)
and [verification index](../../../project_records/current_layout/repository_verification_index.json)
bind each current source to its original Git blob and SHA-256. The original V2
migration plan and historical catalogs remain unchanged. There are no compatibility
aliases, symlinks or second active copies.

Read the [research guide](../../README.md), [safe execution contract](../../../docs/SAFE_EXECUTION.md)
and [documented historical exceptions](../../../docs/HISTORICAL_EXCEPTIONS.md).
