# Experiment index

| Experiment | Purpose | Primary implementation |
|---|---|---|
| E1 | Six NLI features | [Implementation guide](../research/experiments/phase1_baselines/README.md) |
| E2 | Eight semantic-similarity features | Same baseline and canonical pipeline |
| E3 | Combined 14-feature Random Forest baseline | Same baseline and canonical pipeline |
| E4 | Synthetic-data augmentation diagnostic | [Implementation guide](../research/experiments/phase1_baselines/README.md) |
| E5 | RAG Modules 1-4: exact, hybrid and external lexical evidence | [Implementation guide](../research/experiments/phase2_rag_features/README.md#e5-rag-modules-1-4) |
| E6 | Direct evidence features, versions v1-v4 | [Implementation guide](../research/experiments/phase2_rag_features/README.md#e6-feature-extensions) |
| E7 | Selective agentic routing | [Implementation guide](../research/experiments/phase2_rag_features/README.md#e7-and-e8) |
| E8 | Nested Random Forest tuning | [Implementation guide](../research/experiments/phase2_rag_features/README.md#e7-and-e8) |
| E9 | Claim decomposition and claim-level verification | [Implementation guide](../research/experiments/phase3_advanced_methods/README.md#e9-claim-level-verification) |
| E10 | FactCG combination and reconstructed official-test evaluation | [Implementation guide](../research/experiments/phase3_advanced_methods/README.md#e10-factcg) |
| E11 | Task adaptation, teacher labels and contrastive training, variants A-E | [Implementation guide](../research/experiments/phase3_advanced_methods/README.md#e11-task-adaptation-and-contrastive-training) |

Failed, blocked and lower-performing variants remain part of the research record. Module 3 has diagnostic reports but no located standalone final evaluation implementation. E11-B is a feasibility result with no trained student or Accuracy/Spearman result.
Source links distinguish physical location from execution context. See [source modes](REPRODUCIBILITY.md).
