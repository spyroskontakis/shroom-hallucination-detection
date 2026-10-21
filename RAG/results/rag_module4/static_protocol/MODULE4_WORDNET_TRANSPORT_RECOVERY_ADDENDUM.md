# E5 Module 4 Phase 0D — WordNet 3.1 Secure Transport Recovery Addendum

## Scope

This addendum resolves only the transport failure recorded in Phase 0C. The logical lexical source remains **Princeton WordNet 3.1**. Only the HTTPS transport endpoint may change, and an acquired archive is accepted exclusively by exact cryptographic identity.

No parser semantics, normalization, term universe, ordering, deduplication, feature schema, or experimental design is changed. No Module 4 feature preparation, model inference, prediction, or score evaluation is authorized by this recovery step.

## Frozen archive identity

- Filename: `wn3.1.dict.tar.gz`
- Expected size: `16358468` bytes
- Expected SHA-256: `3f7d8be8ef6ecc7167d39b10d66954ec734280b5bdcd57f7d9eafe429d11c22a`
- Logical source: `Princeton WordNet 3.1`

## Approved transport policy

The original endpoint and its four previously recorded TLS failures remain part of the audit history. A non-protected, non-quarantined local exact file is preferred. If none is found, transport mirrors are tried in this fixed order:

1. `https://distcache.FreeBSD.org/ports-distfiles/wn3.1.dict.tar.gz`
2. `https://ftpv6.lug.ro/pub/OpenBSD/distfiles/by_cipher/sha256/P3/P32L6O9uzHFn05sQ1mlU7HNCgLW9zVf32er%2BQp0Rwio%3D/wn3.1.dict.tar.gz`

Normal TLS certificate verification is mandatory. Downloads use a `.part` file, are checked for both exact size and SHA-256 before use, and are promoted to the canonical filename only by atomic rename after validation. HTTP, certificate bypasses, unapproved mirrors, alternative lexical datasets, and semantic parser changes are prohibited.

## Pre-acquisition lock

The Phase 0C parser, specification, tests, requirements, and canonical input hashes were revalidated before recovery. The development universe remains 561 ordered rows: DM 211, MT 216, PG 134; 211 RAG-applicable rows and 206 unique normalized DM terms. The recovery outcome, selected transport mirror, request accounting, archive verification, and offline reconstruction identity are recorded in the final static-protocol manifest and report.

## Recovery outcome

No valid local copy was found in the permitted project/cache search locations. Both approved mirrors were then attempted in the frozen order, with normal TLS verification enabled:

- FreeBSD distcache: rejected before HTTP response because certificate hostname validation failed for `distcache.FreeBSD.org`.
- OpenBSD content-addressed mirror: failed before HTTP response because DNS name resolution failed.

No archive bytes were accepted, no extraction occurred, and neither size nor content hash could be validated. TLS verification was not bypassed, HTTP was not used, and no unapproved endpoint was contacted. The four earlier failed Princeton transport attempts remain intact in `network_requests.jsonl`, followed by these two recovery attempts.

The deterministic stop verdict is:

```text
MODULE4_WORDNET_TRANSPORT_RECOVERY_BLOCKED_BOTH_APPROVED_MIRRORS_UNAVAILABLE
```

Stage B, Wiktionary acquisition, snapshot construction, feature preparation, and score evaluation were not started.
