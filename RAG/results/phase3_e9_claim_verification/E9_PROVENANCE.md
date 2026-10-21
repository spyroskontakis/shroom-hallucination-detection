# E9 completed execution provenance

Branch: phase3-e9-claim-verification. Starting HEAD: 6e3c702be45329ae0e3199def4091de61911621f.
All created/modified experiment files are confined to this E9 directory.

The frozen gpt-4o-2024-08-06 semantic-v2 decomposer (temperature 0), validator,
retry/fallback policy, prompt and Amendment 01 were unchanged. API sample content
was restricted to hyp/task. The initial HTTP 429 checkpoint remains preserved;
user-authorized continuation serialized requests with one-second spacing. Existing
successful responses from an interrupted row were replayed through the frozen
validator, without additional purchases or resetting its attempt budget.

Persistent cache reuse: 26 canonical rows, comprising 20 previously cached unique
payloads and six repeated payloads. All 561 canonical rows are represented by 575
claims. Full-run incremental token-priced cost is USD 1.2009175, excluding prior
smoke tests. Provider billing ledger was not available.
Pricing: https://developers.openai.com/api/docs/models/gpt-4o

Only explicitly allowlisted canonical development/trial and historic E6 artifacts
were loaded. provenance/baseline_verification.json records their hashes and runtime.
Baseline saved OOF verification required zero fits. E9-A used the exact 36 baseline
features plus eight frozen aggregates and exactly five original-fold RF fits.
The frozen DeBERTa checkpoint/backend scored 575 pairs; no pair was truncated.

E9-B preflight ran after successful E9-A. Exact model:
bespokelabs/Bespoke-MiniCheck-7B. BLOCKED_MINICHECK: native Windows, CPU-only PyTorch,
no CUDA device, absent minicheck/vllm, insufficient available RAM for unquantized
weights. No download, model load, substitution, quantization or E9-B fit occurred.
Primary sources: https://github.com/Liyan06/MiniCheck#installation and
https://huggingface.co/bespokelabs/Bespoke-MiniCheck-7B
Measured hardware and reason: reports/minicheck_preflight.json.

Full results: E9_RESULTS.md; machine-readable summary: reports/final_summary.json.
Exact created/modified paths: reports/FULL_RUN_FILES_CHANGED.md.
Prior checkpoint provenance is preserved in reports/PRE_COMPLETION_E9_PROVENANCE.md.
No official test access, historical E1-E8 modifications, commit or push.
