# Known limitations

- The repository is not self-contained for exact replay because datasets, model weights, caches and row-level research artifacts are external.
- The original 499-example E1-E4 evaluation and the locked 561-example canonical evaluation are different populations.
- Module 3 closed as a diagnostic stage; no standalone final gated-RAG executable was located.
- The full historical retrieval ranking before the E6 reconstruction is unavailable.
- The MPNet replay verifies current cached artifacts but cannot prove the exact historical runtime revision.
- The [historical E8 report source](../research/experiments/phase2_rag_features/e8_rf_tuning/historical_implementations/report_e8.py) contains a preserved historical syntax error. A [separate rendering correction](../research/experiments/phase2_rag_features/e8_rf_tuning/scripts/report_e8_render_fixed.py) is available; the historical source is unchanged.
- E10 official-test results are reconstructed retrospectively.
- E11-B has no final student model or Accuracy/Spearman result.
- Historical scripts retain machine-specific input/output assumptions. They are not approved direct-execution instructions for the reorganized checkout.
- Project-owned material is MIT-licensed within the [approved scope](LICENSE_PROPOSAL.md). Third-party rights remain separate; datasets and weights are not included in the grant. Git publication remains a separately approved action.

## Archived historical sources and references

Thirteen original files are grouped in the selected public-baseline source archive.
Their internal namespace preserves immutable historical Markdown/source connections;
one notebook still lacks authentic preservation metadata associated with its exact
published SHA. Archival relocation does not satisfy that missing historical evidence
or establish a runnable original environment. Authenticated Git snapshots preserve
public source identity and namespaces; they do not supply private inputs, original filesystem
timestamps or the different H0 bytes expected by historical checks.

The [immutable E11 audit](../research/historical_sources/public_baseline_11822d9/RAG/results/phase3_e11_task_adaptation/E11_DATA_AUDIT.md)
still has an unresolved relative protocol link at line67. The
[current protocol](../research/data_and_evaluation/canonical/protocols/evaluation_protocol_decision.md)
and [original protocol at the baseline revision](https://github.com/spyroskontakis/shroom-hallucination-detection/blob/11822d92070cd29360445cb4dacd8d110c655248/codex/evaluation_protocol_decision.md)
are valid references. They do not repair the original link or change its protected provenance.

Three E11 D/E checksum mismatches already existed in the public baseline. The
[original source-provenance record](../manifests/source_provenance.public.json)
identifies the public files as privacy-preserving derivatives of the private originals.
The expected historical hashes are unchanged and still fail against those derivatives.
This is not evidence that migration changed the results, and it does not establish independent
numerical equivalence to unavailable originals.

The [strict offline verifier](VERIFICATION.md) reports these failures with a nonzero exit.
The [versioned exception policy](HISTORICAL_EXCEPTIONS.md) conditionally accepts these bounded historical limitations for a research-source release when mandatory gates pass. The original checks remain failed or unverified; a working alternative link is not a repair. Public push, PR or merge still requires separate authorization.
