# Module 4 Continuation v1 — Authorization and Protocol Deviation

## Authorization and historical deviation

This continuation is explicitly authorized after the recorded incident `MODULE4_OVERNIGHT_STOPPED_STAGE0_PREMATURE_DEVELOPMENT_LABEL_ACCESS`. The incident artifacts remain immutable and their expected sizes and SHA-256 values were verified without displaying their contents.

```text
Historical premature label exposure: YES
Previously reported displayed label-bearing rows: 1
Total historical records read by underlying commands: UNKNOWN unless established by existing audit evidence
Continuation authorized after disclosure: YES
Claim of fully label-blind project history: NO
```

No previously exposed value may be used to alter the population, source, parser, model, feature definition, configuration, or evaluation. During this continuation, the mixed canonical E3 CSV remains content-inaccessible until the seven label-free RAG features are cryptographically locked.

## External-source deviation

The external lexical source universe is narrowed from the prospectively planned WordNet 3.1 plus English Wiktionary design to **English Wiktionary only**. This is a real protocol deviation, not an unchanged source design. It is recorded after the historical label incident but before any new label access, feature inference, training, prediction, or score evaluation in this continuation.

WordNet 3.1 is unavailable after six approved secure transport attempts: four Princeton, one FreeBSD, and one OpenBSD. No new WordNet attempt, replacement dictionary, TLS bypass, HTTP request, or unverified substitute is permitted. The old failure log remains immutable and is linked by SHA-256 `ebb9a79eb9d0b87936e954bd406fb52f962868e750d88104a4a6d0523cc768c1`.

The limited Module 3 Phase 2B diagnostic found that its six strict-positive pilot rows came from English Wiktionary. This supports a constrained lexical-coverage rationale only; it is not evidence that Wiktionary is generally superior, nor evidence of generalization or downstream safety.

## Frozen feature design

The seven feature names and mathematical transformations remain frozen:

1. `rag_evidence_available`
2. `rag_sense_count`
3. `rag_retrieval_top1_cosine`
4. `rag_target_definition_max_cosine`
5. `rag_target_definition_max_entailment`
6. `rag_target_definition_max_contradiction`
7. `rag_target_definition_max_lexical_overlap`

`top_k = 5` remains fixed. Lexical RAG applies only to 211 DM rows. The 350 MT/PG rows use deterministic seven-zero fallback. All evidence counts and evidence-based features now refer exclusively to English Wiktionary senses. No hallucination label or downstream score was used to choose this narrowing.

## Frozen Wiktionary acquisition protocol

- Official endpoint: `https://en.wiktionary.org/w/api.php`.
- Method: HTTPS GET, sequential exact-term requests, no batching, ordered by the first occurrence of each Unicode-NFKC, casefolded, whitespace-collapsed DM term in the locked input.
- Revision query parameters: `action=query`, `format=json`, `formatversion=2`, `redirects=1`, `prop=revisions`, `titles=<surface_term>`, `rvslots=main`, `rvprop=ids|timestamp|sha1`.
- Content query parameters: `action=parse`, `format=json`, `formatversion=2`, `oldid=<resolved_revision_id>`, `prop=text|revid`.
- Timeout: 30 seconds.
- Retry policy: initial attempt plus at most three bounded retries with 1, 2, and 4 second backoff; at least one second between logical requests. A `429` honors a parseable `Retry-After` value within the bounded retry sequence.
- User-Agent: `SHROOM-Thesis-Module4/1.0 (academic reproducibility study)`.
- TLS: normal platform certificate and hostname verification; no bypass.
- Redirects: API `redirects=1`; resolved title/page/revision fields are retained from the raw response.
- Revision identity fields: page ID, resolved title, revision ID, revision timestamp, and Wikimedia SHA-1 where returned.
- Raw storage: deterministic `0001_<term_sha256_prefix>_revision.json` and `_parse.json` files beneath `continuation_v1/raw_sources`; files are written atomically and never silently replaced with a different response.
- Network audit: one JSONL record per transport attempt including endpoint, purpose, term identity, retry, UTC timestamp, HTTP/TLS status, response size/SHA-256, success/failure, and exact error.
- Statuses: `SENSES_FOUND`, `NO_SENSE_FOUND`, or `SOURCE_REQUEST_FAILED`; transport/parse failure is never converted to `NO_SENSE_FOUND`.
- Parsing: the frozen English-language/POS Wiktionary parser from `module4-external-parser-v1`, without changes to normalization, filtering, extraction, deduplication, evidence IDs, or ordering.
- Reconstruction: after network closure, the term manifest and snapshot are built twice only from local raw responses. Both serializations must be byte-identical.

## Corrected continuation gate

The label-access gate depends on locking only the 561×7 RAG feature artifact. It does not depend on creation of the 561×21 fused matrix. A successful lock may state `RAG_7_FEATURES_LOCKED_BEFORE_ANY_NEW_DEVELOPMENT_LABEL_ACCESS`, while the historical record must continue to state `Historical pre-lock label exposure: YES`.
