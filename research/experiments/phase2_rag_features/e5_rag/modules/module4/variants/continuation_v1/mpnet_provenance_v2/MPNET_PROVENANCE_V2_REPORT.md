# E5 Module 4 — MPNet Provenance Verification v2

**Ημερομηνία:** 2026-08-30  
**Verdict:** `MPNET_PROVENANCE_V2_REPRODUCTION_BYTE_IDENTICAL`

## Scope και integrity

Η εργασία ήταν νέα, χωριστή, label-free αναπαραγωγή και όχι νέο πείραμα ή αξιολόγηση. Τα πέντε frozen inputs πέρασαν ακριβώς τους απαιτούμενους SHA-256 ελέγχους. Το label-free input είχε 561/561 μοναδικά IDs, schema 6/6, DM 211/561, MT 216/561, PG 134/561 και RAG-applicable 211/561.

## Intended και explicitly used revision

- Model: `sentence-transformers/all-mpnet-base-v2`.
- Intended revision: `e8c3b32edf5434bc2275fc9bab85f82640a19130`.
- Revision που χρησιμοποιήθηκε ρητά σε αυτή τη v2 εκτέλεση: `e8c3b32edf5434bc2275fc9bab85f82640a19130` μέσω `revision=MPNET_REVISION` και `local_files_only=True`.
- Resolved local snapshot: `external-artifacts/local-54c26f7df1bd/e8c3b32edf5434bc2275fc9bab85f82640a19130`.

Το snapshot ήταν ήδη τοπικά διαθέσιμο. Τα hashes των `model.safetensors`, `config.json`, `modules.json`, `tokenizer.json`, `vocab.txt` και `1_Pooling/config.json` ταυτίστηκαν με τα προκαθορισμένα αναμενόμενα hashes. Δεν χρησιμοποιήθηκε fallback snapshot.

## Runtime provenance

- Interpreter: `external-artifacts/local-21bb07554028/python.exe`.
- Python 3.11.9; PyTorch 2.11.0+cpu; Transformers 5.5.4; Sentence Transformers 5.4.1; NumPy 2.4.4; device CPU.
- NLI: `microsoft/deberta-large-mnli@7296194b9009373def4f7c5dad292651e4b5cf4e`, αμετάβλητο.
- Πριν από model imports/loads και σε όλη την εκτέλεση: `HF_HUB_OFFLINE=1`, `TRANSFORMERS_OFFLINE=1`, `HF_DATASETS_OFFLINE=1`, `HF_HUB_DISABLE_TELEMETRY=1`.
- Το pinned feature script διαφέρει από το frozen source κατά μία μόνο γραμμή: προσθήκη του MPNet `revision=`. Το pinned overlap script έχει την αντίστοιχη μοναδική αλλαγή.

## Reproduction results

Το νέο `module4_rag_features_pinned.csv` είχε 561 rows, μία identity και 7/7 frozen RAG features, 561/561 μοναδικά IDs, 0 non-finite values, 0 forbidden columns και 350/350 MT/PG rows με επτά μηδενικά fallback features.

```text
Pinned feature SHA-256: 708483b831430d876135d1484ad841bf6ba0d9c9a2d0a5f22df6280535fe3160
Accepted feature SHA-256: 708483b831430d876135d1484ad841bf6ba0d9c9a2d0a5f22df6280535fe3160
Byte-identical: PASS
```

Μόνο μετά το feature PASS εκτελέστηκε το pinned exact-overlap audit. Παρήγαγε 561 rows, 18/561 exact-match rows και 18/561 exact matches.

```text
Pinned overlap SHA-256: 0fab92f6907da36ae1be609d26230f8b7db054b42bff1f02b578b8719bba714a
Accepted overlap SHA-256: 0fab92f6907da36ae1be609d26230f8b7db054b42bff1f02b578b8719bba714a
Byte-identical: PASS
```

## Ερμηνεία και limitations

Η νέα explicitly pinned αναπαραγωγή με το intended MPNet revision αναπαράγει byte-for-byte και τα δύο accepted label-free artifacts. Αυτό δεν αποδεικνύει αναδρομικά ποιο revision επιλύθηκε στην ιστορική Schannel εκτέλεση, της οποίας η κατάσταση παραμένει `CURRENT_CACHE_COMPATIBLE_HISTORY_UNPROVEN`.

Το προϋπάρχον historical premature label-exposure incident παραμένει καταγεγραμμένο και δεν μηδενίστηκε ή επανερμηνεύτηκε. Η v2 δεν άνοιξε labels, evaluation outputs, predictions, holdout, official test, annotations, protected ή quarantine content. Δεν εκτελέστηκε training, prediction ή metric computation.

## Execution accounting

- Network requests: 0.
- Local model executions: 3 — MPNet 2, NLI 1.
- Feature generations: 1.
- Training executions: 0.
- Prediction executions: 0.
- Metric executions: 0.
- Development-label, holdout, official-test, annotation, protected και quarantine accesses: 0.
- Pre-existing files modified: 0.
