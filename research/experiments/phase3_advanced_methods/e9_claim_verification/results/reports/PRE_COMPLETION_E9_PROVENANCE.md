# Latest execution checkpoint

Full-run orchestration is in scripts/run_decomposition.py. Matching semantic-v2 caches were imported without overwriting earlier smoke artifacts. API responses and token usage are stored immediately under ignored claims/full_run/events; headers and keys are never persisted. Reports/full_decomposition_checkpoint.json records the HTTP-429 stop and partial statistics. Earlier preparation statements below describe the original checkpoint, not the new attempt.

# E9 provenance

Repository branch: phase3-e9-claim-verification.
Starting HEAD: 6e3c702be45329ae0e3199def4091de61911621f.
All created files are under RAG/results/phase3_e9_claim_verification/.

Authoritative baseline: RAG/results/rag_e6_v3/config/run_config.json,
config/feature_freeze.json, features/e6_v3_36_features.csv,
features/e6_v3_added_2_features.csv, inputs/locked_outer_folds.csv,
evaluation/e6_v3_oof_predictions.csv and evaluation/e6_v3_metrics.json.
Cross-checks use the E6-v2 34-column matrix and codex's canonical human
development manifest, canonical fold assignments and canonical 14-feature metadata.
Only these explicit development artifacts are loaded; no raw test data or test
overlap file is opened or hashed. Historical broad integrity helpers are not run.

provenance/baseline_verification.json records the input SHA-256 values,
runtime package versions, population counts, column checks and recalculated saved
OOF metrics. Subsequent verification rejects any change to this allowlisted input
set. The 34 old columns and two additions are checked numerically as well as by
the frozen 36-feature file hash. All CSV reads use round-trip float precision.

Method sources consulted on 2026-09-27:

- Metropolitansky & Larson, [Towards Effective Extraction and Evaluation of Factual Claims](https://aclanthology.org/2025.acl-long.348/), ACL 2025, particularly stages 3.2–3.4 and Appendix D.
- [OpenAI structured outputs](https://developers.openai.com/api/docs/guides/structured-outputs), for the pinned model's JSON-schema response interface.
- Existing local E6-v2 nli_backend.py and E6-v3 evaluate_v3.py/configuration for inference and evaluation compatibility.

No models were downloaded or loaded during preparation. The decomposer transport
and cached real-response handling have not been live-tested. E9-B dependency/VRAM
preflight and model-specific execution adapter remain deferred until E9-A completes.
No E9 feature matrix, row-level claim dataset or OOF prediction file exists.
