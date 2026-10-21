# Module 4 External Lexicon Parser — Frozen Specification

**Version:** `module4-external-parser-v1`  
**Status:** prospectively frozen before source acquisition, retrieval, model inference, labels, predictions, or metrics.

## Inputs and boundaries

- Canonical rows come only from `codex/canonical_human_development_manifest.csv`, in stored order.
- Only `canonical_id`, `task`, `src`, `tgt`, and `hyp` are selected. Label/probability columns are neither selected nor emitted.
- The existing deterministic DM extractor is reproduced exactly: first a closed `<define>…</define>` match; otherwise text between the first two case-insensitive `<define>` markers; blank/non-DM terms are not guessed.
- External acquisition queries use only the extracted term. `tgt`, labels, predictions, probabilities, and fold outcomes are forbidden acquisition/retrieval inputs.

## Frozen sources

- WordNet 3.1: `https://wordnetcode.princeton.edu/wn3.1.dict.tar.gz`.
- English Wiktionary: `https://en.wiktionary.org/w/api.php`.
- User-Agent: `SHROOM-Thesis-Module4/1.0 (academic reproducibility study)`.
- Timeout 30 s; at most three retries after the initial request; deterministic waits 1, 2, 4 s; HTTP 429 honors a numeric `Retry-After`; at least one second between Wiktionary requests; no parallel requests.

## Normalization and exact lookup

`term_key` is Unicode NFKC, casefolded, trimmed and whitespace-collapsed. WordNet lookup additionally maps spaces to underscores. There is no morphology, lemmatization, stemming, fuzzy lookup, suggestion, target conditioning, or padding.

WordNet exact lookup covers `index.noun`, `index.verb`, `index.adj`, `index.adv` and resolves offsets in the corresponding `data.*` files. A definition is the gloss before the first `; "` example segment, or the complete gloss if no example segment exists.

Wiktionary uses two exact-title requests: a revision lock (`query`, revision IDs/timestamp/SHA-1) and then pinned rendered content (`parse`, `oldid`). The parser uses BeautifulSoup 4.14.3 with `html.parser`, isolates the `English` h2, accepts only the frozen POS allowlist, takes direct `li` children of eligible ordered lists, removes nested lists/tables/styles/scripts/citations/references, normalizes rendered text with NFKC and collapsed whitespace, and rejects blanks.

## Frozen POS allowlist

`Noun`, `Proper noun`, `Verb`, `Adjective`, `Adverb`, `Pronoun`, `Preposition`, `Conjunction`, `Determiner`, `Interjection`, `Numeral`, `Particle`, `Phrase`, `Idiom`, `Proverb`, `Letter`, `Symbol`.

## Deduplication and ordering

For definition `d`:

```python
definition_key = " ".join(re.findall(r"[^\W_]+", unicodedata.normalize("NFKC", d).casefold(), flags=re.UNICODE))
```

Within a `term_key`, identical nonblank definition keys collapse to one candidate. `wordnet31` has priority over `enwiktionary`; all source records remain in a deterministically sorted provenance list. `evidence_id` is `M4EV-` plus the first 20 uppercase hexadecimal characters of SHA-256 over `term_key + "\n" + definition_key`. Snapshot ordering is term-manifest order, then source priority, source entry ID, evidence ID.

## Future retrieval lock

```text
query_text = NFKC(term).strip() + "\n" + NFKC(src).strip()
candidate_text = NFKC(candidate_term).strip() + "\n" + NFKC(candidate_definition).strip()
top_k = 5
tie-break = source ascending, source_entry_id ascending, evidence_id ascending
```

No embedding or ranking is executed in Phase 0C.
