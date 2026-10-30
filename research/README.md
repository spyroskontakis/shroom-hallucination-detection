# Research Guide

This guide connects the thesis methodology to code, protocols and recorded results. Most implementations are physically organized under research/; a small set remains under codex/ and RAG/ for documented compatibility and provenance requirements. Each page distinguishes current entry points, unchanged historical sources and records; a source link alone does not certify runtime reproduction.

| Area | What to explore |
|---|---|
| [Core pipeline](core_pipeline/README.md) | Canonical data preparation, semantic features, fixed folds and shared evaluation |
| [Exploratory analysis](exploratory_analysis/README.md) | Descriptive EDA and the different historical notebook versions |
| [Shared tools and tests](shared_tools/README.md) | Shared utilities, source-mode validation and experiment-specific tests |
| [Phase 1: E1-E4](experiments/phase1_baselines/README.md) | NLI, similarity, their combination and synthetic-data diagnostics |
| [Phase 2: E5-E8](experiments/phase2_rag_features/README.md) | RAG Modules 1-4, additional features, routing and Random Forest tuning |
| [Phase 3: E9-E11](experiments/phase3_advanced_methods/README.md) | Claim verification, FactCG and transformer fine-tuning |
| [Entailment prototype](prototypes/entailment_prototype/README.md) | A separate Python/CLI implementation; see its [quickstart](prototypes/entailment_prototype/QUICKSTART.md) |

## Reading the research record

Keep three evaluation settings separate:

- Historical E1-E4 development experiments on 499 examples.
- The later canonical evaluation on 561 human-labeled examples, with shared fixed folds. Canonical E4 adds synthetic examples only to training folds and is diagnostic-only.
- The older synthetic ablation using labeled test data. Its results are historical and are not canonical development results.

The [results overview](../docs/RESULTS.md) also separates development comparisons from the retrospective E10 official-test reconstruction. The prototype and [historical source snapshots](../project_records/historical_versions/README.md) are separate from the main experiment suite; snapshots are not standalone runnable releases.

## Reproducibility

The repository contains research code, protocols, documentation and recorded results. It does not include all original datasets, model weights or generated artifacts. Full reproduction using only this public repository has not been verified. File migration checks are not new experiment runs or independent confirmation of the reported metrics.

Read [data access](../docs/DATA_ACCESS.md), [environment requirements](../docs/ENVIRONMENTS.md) and [reproducibility limitations](../docs/REPRODUCIBILITY.md) before considering execution. Historical notebooks can write to old input/output locations or call external services; this guide does not provide a verified Run All procedure.

[Back to the project README](../README.md)
