# Known limitations

- The repository is not self-contained for exact replay because datasets, model weights, caches and row-level research artifacts are external.
- The original 499-example E1-E4 evaluation and the locked 561-example canonical evaluation are different populations.
- Module 3 closed as a diagnostic stage; no standalone final gated-RAG executable was located.
- The full historical retrieval ranking before the E6 reconstruction is unavailable.
- The MPNet replay verifies current cached artifacts but cannot prove the exact historical runtime revision.
- `RAG/results/rag_e8_rf_tuning_v1/scripts/report_e8.py` contains a preserved historical syntax error. Use `report_e8_render_fixed.py` for report rendering.
- E10 official-test results are reconstructed retrospectively.
- E11-B has no final student model or Accuracy/Spearman result.
- Several historical reports contain local absolute paths. These are provenance and portability warnings, not credentials.
- Project-owned material is MIT-licensed within the [approved scope](LICENSE_PROPOSAL.md). Third-party rights remain separate; datasets and weights are not included in the grant. Git publication remains a separately approved action.