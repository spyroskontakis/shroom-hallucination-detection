# Exploratory Data Analysis

This page distinguishes descriptive analysis from notebooks that also contain model evaluation or synthetic-data generation. The descriptive EDA script is under `research/analysis/`. Seven historical notebooks are now under research/data_and_evaluation/historical_baselines/notebooks/. Two other historical sources remain under data/ and codex/data/; the latter is required at its old path by an E10 audit.

The [development EDA script](../analysis/development_eda/prompt6_development_eda.py) describes the model-agnostic and model-aware development data. Its broader descriptive scope does not change the model-agnostic focus of the evaluated detector.

## Historical notebook versions

These notebooks contain mixed EDA, baseline or augmentation work, not just plotting. Each version is retained as a distinct research artifact.

| Version | Available source |
|---|---|
| Integrated RAG-area baseline | [RAG/shroom_ensemble.ipynb](../data_and_evaluation/historical_baselines/notebooks/rag_baseline/shroom_ensemble.ipynb) |
| Legacy EDA notebook | [data/2. EDA/shroom_ensemble.ipynb](../../data/2.%20EDA/shroom_ensemble.ipynb) |
| Final-implementation notebook variant | [codex/data/2. EDA/shroom_final_implementation/shroom_ensemble.ipynb](../data_and_evaluation/historical_baselines/notebooks/codex_final_implementation/shroom_ensemble.ipynb) |
| Colab baseline variant | [shroom_ensemble_colab.ipynb](../data_and_evaluation/historical_baselines/notebooks/codex_final_implementation/shroom_ensemble_colab.ipynb) |
| Earlier integrated baseline | [codex/data/shroom_ensemble.ipynb](../../codex/data/shroom_ensemble.ipynb) |

The [Phase 1 guide](../experiments/phase1_baselines/README.md) also indexes the four augmentation variants and the older labeled-test ablation notebook. Historical notebooks and the later [canonical pipeline](../core_pipeline/README.md) use different data and evaluation contexts; do not combine their result tables.

Notebook cells can depend on earlier in-memory state, the kernel working directory and `SHROOM_PROJECT_ROOT`. Some include package-install, model-loading or API cells. Their input/output paths and external artifacts need review before execution; this is not a verified Run All guide.

[Back to the research guide](../README.md)
