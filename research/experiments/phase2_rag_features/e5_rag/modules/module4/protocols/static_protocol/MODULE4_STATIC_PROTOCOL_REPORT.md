# E5 Module 4 Phase 0D — Static Protocol Report

## Verdict

```text
MODULE4_WORDNET_TRANSPORT_RECOVERY_BLOCKED_BOTH_APPROVED_MIRRORS_UNAVAILABLE
```

Phase 0D preserved the valid Phase 0C Stage A lock and attempted only the approved secure transport recovery for the frozen Princeton WordNet 3.1 archive. No exact local copy was found in the permitted non-protected, non-quarantined project/cache locations. Both approved HTTPS mirrors then failed before any successful HTTP response or accepted archive bytes: FreeBSD on TLS hostname verification and OpenBSD on DNS resolution.

TLS verification was not bypassed, HTTP was not used, and no third or unapproved source was attempted. Consequently, archive identity could not be validated, extraction and Wiktionary acquisition did not start, and no term manifest or lexical snapshot was created.

## Frozen archive and transport audit

- Logical source: Princeton WordNet 3.1.
- Frozen filename: `wn3.1.dict.tar.gz`.
- Frozen expected size: 16,358,468 bytes.
- Frozen expected SHA-256: `3f7d8be8ef6ecc7167d39b10d66954ec734280b5bdcd57f7d9eafe429d11c22a`.
- Original Princeton attempts retained: 4/4 failed because the upstream certificate was expired.
- FreeBSD distcache attempts: 1/1 failed TLS hostname validation; HTTP status unavailable; received bytes 0.
- OpenBSD content-addressed attempts: 1/1 failed DNS resolution; HTTP status unavailable; received bytes 0.
- Total WordNet transport attempts: 6; successful responses: 0.
- Wiktionary requests: 0.

## Stage A lock

| Check | Result |
|---|---:|
| Synthetic parser tests | 7/7 PASS |
| WordNet index/data parsing | PASS |
| Noun/verb/adjective/adverb fixtures | PASS |
| WordNet gloss with/without example | PASS |
| Wiktionary English/POS isolation | PASS |
| Nested example/quotation exclusion | PASS |
| Redirect/missing-page fixtures | PASS |
| HTML entity/Unicode/empty definitions | PASS |
| Cross-source deduplication and deterministic IDs | PASS |
| Two-run offline byte identity fixture | PASS |
| Forbidden acquisition-input interface check | PASS |

The parser, specification, tests, requirements, and Phase 0 plan remain byte-unchanged from the prospective lock.

## Canonical development-input lock

- Canonical ordered rows: 561/561.
- Unique canonical IDs: 561/561.
- Task counts: DM 211/561, MT 216/561, PG 134/561.
- RAG-applicable deterministic DM rows: 211/561.
- Unique normalized DM terms: 206/206.
- MT/PG rows with invented terms: 0/350.
- Development labels/probabilities copied, opened, or used: 0.

## Source and coverage accounting

| Item | Count |
|---|---:|
| Canonical inputs | 561/561 |
| Terms accounted in a final manifest | 0/206 (not created because acquisition was blocked) |
| WordNet evidence terms | not computed |
| Wiktionary evidence terms | not computed |
| `NO_SENSE_FOUND` terms | not computed |
| `SOURCE_REQUEST_FAILED` in a final lock | not applicable; no final lock created |
| Total unique senses | not computed |

Coverage values are deliberately not fabricated after transport failure.

## Execution and boundary accounting

- MPNet embedding inference: 0.
- NLI inference: 0.
- Retrieval ranking: 0.
- RAG feature generation: 0.
- Random Forest training: 0.
- Predictions: 0.
- Accuracy/Spearman or other performance metrics: 0.
- Official-test accesses: 0.
- Holdout-label accesses: 0.
- AI-annotation accesses: 0.
- Protected-content accesses: 0.
- Quarantine-content accesses/modifications: 0.
- Existing E1–E4, Modules 1–3, Phase 0 plan, and dataset artifacts modified: 0.

This is the deterministic methodological stop condition required when both approved secure mirrors are unavailable. It is not a parser-test failure and not an experimental performance result. Feature preparation and score evaluation remain unstarted.
