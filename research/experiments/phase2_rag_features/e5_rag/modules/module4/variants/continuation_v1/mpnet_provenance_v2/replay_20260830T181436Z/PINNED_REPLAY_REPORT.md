# SHROOM E5 Module 4 — Authorized pinned offline replay

## Scope and verdict

The authorized replay was limited to one offline pinned feature generation and one offline pinned exact-overlap audit. No training, predictions, evaluation metrics, source acquisition, or protected-data access occurred.

**Verdict: `PINNED_ARTIFACT_REPLAY_IDENTICAL`**

The replay establishes that the two accepted artifacts are reproducible byte-for-byte under the explicitly pinned local snapshots recorded below. It does **not** retroactively prove which revision was loaded by the earlier unpinned historical executions. Their historical status remains **`HISTORICAL_REVISION_UNPROVEN`**.

## Integrity and tests

- Locked label-free input: 561/561 rows, 6/6 expected columns, 561/561 unique identifiers; SHA-256 `3f92a0b398b97873716dda69d108467a4309fe28bd565be692a74e1af74523d5`.
- Frozen external lexical snapshot SHA-256: `7677937ace64644afa4f39d8745f54711640a578f1387d9e389008b1e0440d40`.
- Prepared pinned feature builder SHA-256: `56ff9521c96cfc4d6a8793c86dc60194f4afac16e57aa922e0c9218c72eaf0de`.
- Prepared pinned overlap audit SHA-256: `ab055f5873b3500adf2f64e41f69d655ebe0bedef365c35cdab22c70e2942f15`.
- Static replay tests: 6/6 PASS.
- Frozen synthetic feature tests: 9/9 PASS.
- Total: 15/15 PASS; model loads during tests: 0.
- Process-local network guard was active before model imports. Recorded and blocked network attempts: 0.

## Observed pinned resolution

MPNet was requested as `sentence-transformers/all-mpnet-base-v2@e8c3b32edf5434bc2275fc9bab85f82640a19130` and resolved locally to:

`external-artifacts/local-54c26f7df1bd/e8c3b32edf5434bc2275fc9bab85f82640a19130`

Key MPNet bytes were locked as follows: `model.safetensors` 437,971,872 bytes, SHA-256 `78c0197b6159d92658e319bc1d72e4c73a9a03dd03815e70e555c5ef05615658`; `config.json` SHA-256 `d46a3e04ded82bba22528424480697d394eeda6a27484e08c5bb2bdf5906cfa0`; `tokenizer.json` SHA-256 `b8be2c30ba5dd723a6d5ee26d013da103d5408d92ddcb23747622f9e48f1d842`; pooling config SHA-256 `a37f83ada23e7887be6b88f4998927dbeac0038af301553c7cd5461413bf1a56`.

NLI was requested as `microsoft/deberta-large-mnli@7296194b9009373def4f7c5dad292651e4b5cf4e` and resolved locally to:

`external-artifacts/local-da623a571fc2/7296194b9009373def4f7c5dad292651e4b5cf4e`

Its `pytorch_model.bin` was 1,624,928,186 bytes with SHA-256 `3abd875c9e6dd137a689a1fa1a433f0c2d6bc7462afc42a0095878f88f23be87`; `config.json` SHA-256 was `d9f6829f2e13bdb4743f97bd4c0866412b91129bfa0195cdd0414d836cc6f130`.

Full relevant file inventories are recorded in `RUNTIME_PROVENANCE_MANIFEST.json` and the three mode-specific runtime provenance records.

## Runtime

- Python 3.11.9: `external-artifacts/local-21bb07554028/python.exe`.
- CPU execution; CUDA not used; frozen float32/default model policy.
- `sentence-transformers` 5.4.1, `transformers` 5.5.4, `torch` distribution 2.11.0 (`torch.__version__` 2.11.0+cpu), `numpy` 2.4.4.
- Offline flags before model imports: `HF_HUB_OFFLINE=1`, `TRANSFORMERS_OFFLINE=1`, `HF_DATASETS_OFFLINE=1`, `HF_HUB_DISABLE_TELEMETRY=1`, `PYTHONDONTWRITEBYTECODE=1`.
- Preflight duration: 2.836726 s. Feature generation duration: 229.251151 s. Exact-overlap duration: 61.862240 s. Sum of these recorded stages: 293.950117 s.
- No runtime compatibility deviation was observed. Explicit revision pins, the offline guard, and provenance recording were deliberate controls added for this replay; they do not rewrite the historical provenance record.

## Replay results

### Pinned feature generation

- Exactly one generation was executed.
- Model loads: MPNet 1, NLI 1.
- Output: 561/561 rows, 8/8 feature columns, 561/561 aligned unique IDs, all numeric values finite.
- MT/PG zero-policy checks: 350/350 applicable rows compliant. Forbidden columns: 0.
- Output size: 38,385 bytes.
- Output SHA-256: `708483b831430d876135d1484ad841bf6ba0d9c9a2d0a5f22df6280535fe3160`.
- Accepted artifact SHA-256: `708483b831430d876135d1484ad841bf6ba0d9c9a2d0a5f22df6280535fe3160`.
- Comparison: byte-identical.

### Pinned exact-overlap audit

- Exactly one audit was executed.
- Model loads: MPNet 1, NLI 0.
- Output: 561/561 rows; 18/561 exact-overlap rows.
- Output size: 16,350 bytes.
- Output SHA-256: `0fab92f6907da36ae1be609d26230f8b7db054b42bff1f02b578b8719bba714a`.
- Accepted artifact SHA-256: `0fab92f6907da36ae1be609d26230f8b7db054b42bff1f02b578b8719bba714a`.
- Comparison: byte-identical.

## Interpretation and boundaries

The identical outputs show compatibility of the accepted artifacts with the explicit pinned snapshots and runtime used in this replay. This narrows the provenance uncertainty but cannot convert current reproducibility into historical proof. The earlier feature generation and overlap audit remain `HISTORICAL_REVISION_UNPROVEN` because no execution-linked historical resolved snapshot or model-file hashes were available.

No historical incident accounting was erased or reset. Earlier protocol deviations and network incidents remain documented separately in the existing continuation records. This replay made 0 network requests and observed 0 blocked network attempts.

## Final accounting

- Network requests: 0.
- Blocked network attempts: 0.
- Model loads: 3 total (MPNet 2, NLI 1).
- Feature generations: 1.
- Exact-overlap audits: 1.
- Training, prediction, and metric runs: 0.
- Source acquisitions/downloads/installations: 0.
- Label, mixed-E3, holdout, official-test, annotation, credential, protected, or quarantine accesses: 0.
- Existing artifacts modified: 0.
- New replay-scoped files: 13, including this report and the runtime provenance manifest.

No downstream Module 4 evaluation was started.
