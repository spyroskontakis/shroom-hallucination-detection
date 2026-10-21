# SHROOM RAG E5 — Module 2 Phase A Results

## Κατάσταση και scope

Η Phase A ολοκληρώθηκε μόνο ως offline candidate retrieval για
**unlabeled-training-corpus RAG**. Δεν χρησιμοποιήθηκαν hallucination labels,
official test data, Gemini/API, relevance thresholds ή tuned fusion weights.

Η `Q_SRC_TGT` είναι reference-assisted retrieval και όχι ανεξάρτητη external
validation.

## Root cause και επιδιόρθωση

Το αρχικό Run All κωδικοποιούσε 9.577 πλήρη concatenated candidate contexts σε
ένα μη-resumable cell. Σε CPU δεν ολοκληρώθηκε μέσα σε 1.200 δευτερόλεπτα και
δεν μπορούσε να διατηρήσει μερική πρόοδο.

Αλλαγές:

- Cells 1–2: τεκμηρίωση bounded/resumable dense retrieval και Q_SRC_TGT limitation.
- Cell 3: offline/CPU deterministic settings πριν από Hugging Face imports.
- Cell 5: cache/helper paths και σωστή απομόνωση του report στο Module 2 output.
- Cell 8: token-aware bounded `Q_SRC`/`Q_SRC_TGT` με diagnostics.
- Cell 10: BM25 με τα ίδια bounded query strings.
- Cell 11: compatibility-checked cache load και encoding μόνο 40 queries.
- Cell 16: cache, shape, normalization, deterministic και leakage tests.
- Cell 17: atomic artifacts, πλήρες manifest και ενημερωμένο results report.
- `scripts/module2_dense_cache.py`: benchmark, atomic chunks και deterministic resume.

## Environment και dense configuration

- Environment: `shroom_ensemble`
- Python: `3.11.9`
- `rank-bm25`: `0.2.2`
- Model: `sentence-transformers/all-mpnet-base-v2` (local-only, no download)
- Device: `cpu`
- Dimension: `768`
- Normalization/dtype: `True` / `float32`
- Dense text version: `term_definition_context_window_v1`
- `max_seq_length`: `256`
- Selected batch size: `16`
- Chunk size: `256`

## Token-length statistics

| Inputs | p50 | p90 | p95 | p99 | max |
|---|---:|---:|---:|---:|---:|
| Candidates unbounded | 68.0 | 104.0 | 120.0 | 166.0 | 540 |
| Candidates bounded | 68.0 | 104.0 | 120.0 | 166.0 | 256 |
| Queries unbounded | 57.0 | 99.0 | 104.6 | 121.9 | 125 |
| Queries bounded | 57.0 | 99.0 | 104.6 | 121.9 | 125 |

- Candidate context-only truncations: `7`
  (`0.07%`)
- Candidate definition truncations: `0`
- Candidate marker/term/initial fallbacks: `{'marker': 9577, 'term': 0, 'initial': 0}`
- Query context-only truncations: `0`
- Query primary-reference truncations: `0`
- Query marker/term/initial fallbacks: `{'marker': 40, 'term': 0, 'initial': 0}`
- Όλα τα bounded inputs έως 256 tokens: `True`

## Fixed 128-candidate benchmark

| Batch size | Seconds | Completed | Error type |
|---:|---:|---|---|
| 8 | 22.787 | True |  |
| 16 | 19.640 | True |  |
| 32 | 24.830 | True |  |

Η επιλογή batch size έγινε μόνο με χρόνο/memory/error στο fixed row-order/seed
sample και όχι με relevance ή hallucination labels.

## Dense cache

- Builder launches: `1`
- Resumptions: `0`
- Completed chunks: `38`
- Total chunk encoding time: `1413.292` seconds
- Last-launch cache hits: `0`
- Cache complete and compatibility-verified: `True`

## Inputs και artifacts

- DM knowledge-base rows: `9577`
- Fixed development sample: `20/20`
- Distinct bounded queries: `40/40`
- Knowledge-base SHA-256: `7C6146106BBE465A57A6D5A497AA53DE49E5467D0AD7C489892D4D2566839AF2`
- Sample SHA-256: `4852D256518E6C7C1D5AC4A1A982AE8D0A49688E459940BA649B0B17E1E3AD36`
- Manifest rows: `1`
- Candidate JSONL rows: `612`
- Annotation template rows: `120`
- Manual annotations filled: `0`

## Candidate counts

| Query variant | Retrieval method | Candidate rows |
|---|---|---:|
| `Q_SRC` | `bm25` | 100 |
| `Q_SRC` | `dense` | 100 |
| `Q_SRC` | `exact` | 6 |
| `Q_SRC` | `rrf` | 100 |
| `Q_SRC_TGT` | `bm25` | 100 |
| `Q_SRC_TGT` | `dense` | 100 |
| `Q_SRC_TGT` | `exact` | 6 |
| `Q_SRC_TGT` | `rrf` | 100 |

- Exact non-empty coverage for `Q_SRC`: `25.0%`
- Exact non-empty coverage for `Q_SRC_TGT`: `25.0%`

Οι παραπάνω αριθμοί είναι candidate/coverage diagnostics και όχι relevance
metrics. Δεν υπολογίζονται Precision@k, Relevant@1 ή usable coverage πριν από
manual annotation.

## Regression previews

Τα regression cases προέρχονται από το Module 1 και δεν αποτελούν ανεξάρτητο
evaluation set. Δεν αποδίδεται αυτόματη relevance κρίση.

| Index | Diagnostic term | Query variant | Rank | Evidence ID | Candidate term | Methods | Definition preview |
|---:|---|---|---:|---:|---|---|---|
| 30 | `preciosity` | `Q_SRC` | 1 | 17462 | preciosity | bm25, dense, exact | (obsolete, uncountable) The quality of being precious (of high value or worth). |
| 30 | `preciosity` | `Q_SRC` | 2 | 15708 | preciosity | dense, exact | (usually, pejorative, uncountable) The quality of being overly refined in an affected way (often used to describe spe... |
| 30 | `preciosity` | `Q_SRC` | 3 | 10439 | mapful | bm25 | A quantity (of something) that forms a map or a map-like image. |
| 30 | `preciosity` | `Q_SRC_TGT` | 1 | 17462 | preciosity | bm25, dense, exact | (obsolete, uncountable) The quality of being precious (of high value or worth). |
| 30 | `preciosity` | `Q_SRC_TGT` | 2 | 15708 | preciosity | exact | (usually, pejorative, uncountable) The quality of being overly refined in an affected way (often used to describe spe... |
| 30 | `preciosity` | `Q_SRC_TGT` | 3 | 10439 | mapful | bm25 | A quantity (of something) that forms a map or a map-like image. |
| 55 | `dateliner` | `Q_SRC` | 1 | 19672 | dateliner | bm25, dense, exact | (journalism) An article that is published under a dateline. |
| 55 | `dateliner` | `Q_SRC` | 2 | 11431 | tyrannophilia | bm25 | A preference for autocratic forms of leadership. |
| 55 | `dateliner` | `Q_SRC` | 3 | 18278 | datemarks | dense | A marking that indicates a date. |
| 55 | `dateliner` | `Q_SRC_TGT` | 1 | 19672 | dateliner | bm25, dense, exact | (journalism) An article that is published under a dateline. |
| 55 | `dateliner` | `Q_SRC_TGT` | 2 | 11431 | tyrannophilia | bm25 | A preference for autocratic forms of leadership. |
| 55 | `dateliner` | `Q_SRC_TGT` | 3 | 18278 | datemarks | dense | A marking that indicates a date. |
| 122 | `continuous` | `Q_SRC` | 1 | 17226 | continuous | bm25, dense, exact | (mathematics, more generally, of a function between two topological spaces) Such that each open set in the target spa... |
| 122 | `continuous` | `Q_SRC` | 2 | 12614 | transportance | dense | (obsolete) transportation |
| 122 | `continuous` | `Q_SRC` | 3 | 19230 | layerization | bm25 | The condition of being layerized; the process of layerizing something. |
| 122 | `continuous` | `Q_SRC_TGT` | 1 | 17226 | continuous | bm25, dense, exact | (mathematics, more generally, of a function between two topological spaces) Such that each open set in the target spa... |
| 122 | `continuous` | `Q_SRC_TGT` | 2 | 11731 | continuatively | dense | in continuative manner |
| 122 | `continuous` | `Q_SRC_TGT` | 3 | 19230 | layerization | bm25 | The condition of being layerized; the process of layerizing something. |
| 161 | `weary` | `Q_SRC` | 1 | 14712 | weary | bm25, dense, exact | To make or to become weary. |
| 161 | `weary` | `Q_SRC` | 2 | 11889 | bushed | dense | (Canada) Mentally unwell due to isolation, especially due to working in a remote mine or camp; experiencing cabin fever. |
| 161 | `weary` | `Q_SRC` | 3 | 12403 | motherly | bm25 | In a way pertaining to, befitting, or of a mother. |
| 161 | `weary` | `Q_SRC_TGT` | 1 | 14712 | weary | bm25, dense, exact | To make or to become weary. |
| 161 | `weary` | `Q_SRC_TGT` | 2 | 12403 | motherly | bm25 | In a way pertaining to, befitting, or of a mother. |
| 161 | `weary` | `Q_SRC_TGT` | 3 | 18489 | tiring | dense | That tires or tire. |
| 185 | `inconsistent` | `Q_SRC` | 1 | 12239 | inconsistent | bm25, dense, exact | Not consistent or coherent in thought or behavior. |
| 185 | `inconsistent` | `Q_SRC` | 2 | 10514 | unCanadian | bm25 | Not Canadian; contrary to or inconsistent with Canada or Canadian values and traditions. |
| 185 | `inconsistent` | `Q_SRC` | 3 | 13891 | miscomment | dense | A comment that is untrue. |
| 185 | `inconsistent` | `Q_SRC_TGT` | 1 | 12239 | inconsistent | bm25, dense, exact | Not consistent or coherent in thought or behavior. |
| 185 | `inconsistent` | `Q_SRC_TGT` | 2 | 10514 | unCanadian | bm25 | Not Canadian; contrary to or inconsistent with Canada or Canadian values and traditions. |
| 185 | `inconsistent` | `Q_SRC_TGT` | 3 | 18736 | disclarity | dense | The quality of being inconsistent; inconsistency |

## Offline και leakage verification

- Tests passed: `20/20`
- Final top-to-bottom notebook Run All: `1`
- Executed notebook code cells: `17/17` με διαδοχικά execution counts `1–17`
- Stored notebook error outputs: `0`
- Notebook syntax και `nbformat.validate`: `PASS`
- Manifest JSON, candidate JSONL και annotation CSV validity: `PASS`
- Cache embeddings: `(9577, 768)`, normalized float32, finite
- Query embeddings: `(40, 768)`, normalized float32, finite
- Duplicate candidates μέσα σε ranked list: `0`
- Query variants distinct: `True`
- Forbidden label/probability columns: `0`
- Official test used: `False`
- Gemini/API/credential operations: `0`
- Downloads: `0`
- Installed package snapshot unchanged: `True`
- Manual annotations filled: `0`
- Module 1 hashes unchanged: `True`
- E1–E4 notebook snapshots unchanged: `True` (`19/19` files)

## Limitations και επόμενα βήματα

- Δεν υπάρχουν ακόμη manual relevance annotations.
- Δεν επιλέγεται καλύτερος retriever και δεν ορίζεται relevance gate/threshold.
- Η `Q_SRC_TGT` χρησιμοποιεί την primary reference και δεν αποτελεί ανεξάρτητη
  εξωτερική επιβεβαίωση.
- Τα πέντε regression cases είναι diagnostics, όχι γενίκευση.

Επόμενο επιτρεπτό βήμα είναι μόνο η ξεχωριστά εγκεκριμένη manual συμπλήρωση του
annotation template και ο προκαθορισμός retrieval-development/holdout rows πριν
από οποιοδήποτε tuning ή relevance metric.
