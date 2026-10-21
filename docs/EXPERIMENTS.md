# Experiment index

| Experiment | Purpose | Primary implementation |
|---|---|---|
| E1 | Six NLI features | `RAG/shroom_ensemble.ipynb`, `codex/canonical_*` |
| E2 | Eight semantic-similarity features | Same baseline and canonical pipeline |
| E3 | Combined 14-feature Random Forest baseline | Same baseline and canonical pipeline |
| E4 | Synthetic-data augmentation diagnostic | `data/7. Ablation Synthetic Data/7.Ablation_Synthetic_Data.ipynb` |
| E5 | RAG Modules 1–4: exact, hybrid and external lexical evidence | `RAG/shroom_rag_e5_*`, `RAG/results/rag_module*` |
| E6 | Direct evidence features, versions v1–v4 | `RAG/results/rag_e6_v*` |
| E7 | Selective agentic routing | `RAG/results/rag_e7_agentic_v1` |
| E8 | Nested Random Forest tuning | `RAG/results/rag_e8_rf_tuning_v1` |
| E9 | Claim decomposition and claim-level verification | `RAG/results/phase3_e9_claim_verification` |
| E10 | FactCG combination and reconstructed official-test evaluation | E9 `evaluation/E10` and `RAG/results/e10_official_test_v1` |
| E11 | Task adaptation, teacher labels and contrastive training, variants A–E | `RAG/results/phase3_e11_task_adaptation` |

Failed, blocked and lower-performing variants remain part of the research record. Module 3 has diagnostic reports but no located standalone final evaluation implementation. E11-B is a feasibility result with no trained student or Accuracy/Spearman result.