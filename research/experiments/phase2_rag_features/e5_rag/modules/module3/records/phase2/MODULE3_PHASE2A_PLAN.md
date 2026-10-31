# SHROOM RAG E5 — Module 3 Phase 2A Plan

## 1. Στόχος και scope

Η Phase 2A είναι ξεχωριστό offline **knowledge-base sense-coverage probe**. Ακολουθεί την επίσημη Phase 1 απόφαση `KB_EXPANSION_FIRST` και ελέγχει, πριν από οποιαδήποτε external KB expansion, αν κατάλληλο same-sense evidence μπορεί να υπάρχει ήδη στην υφιστάμενη knowledge base αλλά να μην είχε εντοπιστεί από το προηγούμενο retrieval.

Η preparation περιορίζεται στα 7/7 development coverage-failure examples:

```text
preciosity
bandslash
nonentertainment
continuous
foreboding
tetaniform
keen
```

Δεν πραγματοποιείται relevance annotation, relevance inference, Phase 2 απόφαση, external knowledge addition, reranking, gate redesign, Gemini experiment ή E5 integration. Το Module 2 παραμένει `CLOSED — NO_GO_FOR_GEMINI` και η Phase 1 παραμένει `KB_EXPANSION_FIRST`.

## 2. Integrity preflight και canonical inputs

Όλα τα paths είναι canonical κάτω από ``. Οι 69/69 artifact hashes και οι 2/2 external-input hashes του Module 2 final manifest επαληθεύτηκαν read-only πριν από τη δημιουργία output. Δεν ανοίχθηκε ή χρησιμοποιήθηκε AI-completed annotation αρχείο.

| Input | SHA-256 |
|---|---|
| `RAG/AGENTS.md` | `8dc147df8c11ef967ccc5b9af44f68b9c76ac2c43b67186c021bb78523c83594` |
| `RAG/MODULE2_FINAL_RESULTS.md` | `574a75f7e0a2bef4ad2ac1b4c68e2892e8356fd9134a885293549e2773c82d92` |
| `RAG/results/rag_module2/MODULE2_FINAL_ARTIFACT_MANIFEST.json` | `29ce9cd021d722076a2589a8265e7259e33953f78686c41275c631539ee9c864` |
| `RAG/results/rag_module3/MODULE3_PHASE0_FAILURE_AUDIT.md` | `cee0c89916639020710a917483da82e531522d00d771f08deae2c3fb0b8c6d3f` |
| `RAG/results/rag_module3/annotation/MODULE3_PHASE1_PLAN.md` | `5fe74662e93111fb480783cbeb546cc8f9d4be00501aa9bffeb7f8e498e396e1` |
| `RAG/results/rag_module3/MODULE3_PHASE1_RESULTS.md` | `00e8ae47d5ee6ddc98c568afe8fce6278a31244cc75c73bf7ebc37510c9f17bd` |
| `RAG/results/rag_module2/annotation/module2_annotation_dev_human_completed.csv` | `3f1f0a6d3eb9a75de69344f6e1df13b88745e464c98f94e1ce87997302669ed5` |
| `RAG/results/rag_module3/annotation/module3_phase1_top5_extension_blinded_human_completed.csv` | `955996793820c71d12be63ee801d3342d62b42265f2cb2683825d8a9d4f7ab99` |
| `data/Unlabeled train/SHROOM_unlabeled-training-data-v2/train.model-agnostic.json` | `dead22eb9b11bbd5bf8e895d01e11ab517a7a7dcebe82f82c6349a3f235d86a3` |
| `RAG/tools/relevance_annotation_ui.html` | `0a997deebc1c78948f1099cfe84c3d127f5146f43bf4e105dd0a242ccbd31670` |

Η canonical knowledge base ανακατασκευάστηκε deterministic in-memory με την παγωμένη Module 2 διαδικασία από το unlabeled training JSON:

- valid rows: 9.577/9.577,
- unique `evidence_id`: 9.577/9.577,
- unique normalized terms: 9.197/9.197,
- ordered KB SHA-256: `7c6146106bbe465a57a6d5a497aa53de49e5467d0ad7c489892d4d2566839af2`,
- ordered candidate-ID SHA-256: `b6d78dc7f70048360e58be40f354c270d5dc2b7905e9e2b97d2152d759e64008`.

Η Phase 1 επαληθεύτηκε ως 40/40 human rows, 0/40 strict rows και 0/7 strict-positive examples. Το official test δεν προσπελάστηκε.

## 3. Frozen candidate-generation configuration

Χρησιμοποιήθηκε μία και μόνο configuration, χωρίς comparison ή tuning:

```text
Query representation: tgt definition only
Candidate representation: candidate_definition only
Model: sentence-transformers/all-mpnet-base-v2
Execution: CPU, eval mode, local_files_only=True
Embeddings: normalized float32
Cosine similarity: normalized-query dot normalized-candidate
Maximum sequence length: 256 tokens
Dense depth: top-5 new candidates ανά example
Tie-break: ascending evidence_id
RANDOM_STATE: 42
```

Το `src`, το query `term` και το `candidate_context` δεν εισήχθησαν στα dense texts. Το `candidate_context` διατηρήθηκε μόνο ως βοηθητικό annotation field. Το `tgt` είναι reference-assisted input και η Phase 2A παραμένει development diagnostic, όχι external validation.

Το μοντέλο βρέθηκε ήδη στο local Hugging Face cache και φορτώθηκε με `local_files_only=True`. Δεν έγινε download ή network request. Χρησιμοποιήθηκε το καταγεγραμμένο Module 2 Python environment (`Python 3.11.9`, `sentence-transformers 5.4.1`, `transformers 5.5.4`, `torch 2.11.0`, `numpy 2.4.4`).

Execution accounting:

- frozen dense configurations executed: 1/1,
- model loads: 1/1,
- encode calls: 2/2,
- candidate definitions encoded: 9.577/9.577,
- `tgt` query definitions encoded: 7/7,
- total encoded rows: 9.584/9.584,
- BM25/RRF/NLI/reranker executions: 0.

## 4. Exclusion και exact-term inventory

Για κάθε example συγκεντρώθηκαν όλα τα `(example_id, evidence_id)` pairs από τα canonical Module 2 development human annotations και Module 3 Phase 1 human annotations. Το union είχε 103/103 unique pairs και αφαιρέθηκε πριν επιλεγούν οι πρώτοι 5/5 νέοι dense candidates ανά example.

Το normalized exact-term inventory χρησιμοποίησε μόνο την canonical Module 2 normalization: Unicode NFKC, lowercase, ενοποίηση dash spacing, αφαίρεση μη επιτρεπτών punctuation, μετατροπή underscore/dash σε whitespace και whitespace collapse. Δεν εφαρμόστηκε stemming, fuzzy matching ή morphology expansion.

Προστέθηκαν όλοι οι προηγουμένως μη annotated KB rows με exact normalized-term equality. Στην πραγματική KB/exclusion κατάσταση βρέθηκαν 0/0 νέοι exact-term candidates: όλα τα exact-term rows για αυτά τα examples είχαν ήδη καλυφθεί από το ανθρώπινα annotated union. Η exact channel επομένως δεν πρόσθεσε row και δεν επικαλύφθηκε με τη dense channel.

## 5. Candidate counts

| `example_id` | Term | Previously annotated excluded | Dense new | Exact-term new | Dense/exact overlap | Deduplicated pool |
|---|---|---:|---:|---:|---:|---:|
| `EX-590A0B447A17` | `preciosity` | 15/15 | 5/5 | 0/0 | 0/5 | 5/5 |
| `EX-1AA2C1DAFB9C` | `bandslash` | 16/16 | 5/5 | 0/0 | 0/5 | 5/5 |
| `EX-7565997D951E` | `nonentertainment` | 14/14 | 5/5 | 0/0 | 0/5 | 5/5 |
| `EX-D4E131D57443` | `continuous` | 11/11 | 5/5 | 0/0 | 0/5 | 5/5 |
| `EX-C47370FB429F` | `foreboding` | 16/16 | 5/5 | 0/0 | 0/5 | 5/5 |
| `EX-1E6E8BDB9874` | `tetaniform` | 18/18 | 5/5 | 0/0 | 0/5 | 5/5 |
| `EX-6681F3007742` | `keen` | 13/13 | 5/5 | 0/0 | 0/5 | 5/5 |
| **Σύνολο** | **7/7 examples** | **103/103** | **35/35** | **0/0** | **0/35** | **35/35** |

Οι 35/35 selected pairs είναι μοναδικοί και έχουν overlap 0/35 με τα 103/103 previously annotated pairs.

## 6. Phase 2 human annotation policy

Οι παρακάτω ορισμοί παγώνουν πριν από annotation:

```text
relevant_same_sense:
Η candidate_definition εκφράζει άμεσα την ίδια σημασία που απαιτούν τα src και tgt.

partially_relevant:
Η candidate_definition έχει χρήσιμη αλλά ευρύτερη, στενότερη ή ελλιπή σημασιολογική επικάλυψη.

different_sense:
Η candidate_definition αφορά το ίδιο ή στενά σχετικό lexical item, αλλά διαφορετική σημασία.

irrelevant:
Η candidate_definition δεν παρέχει χρήσιμη υποστήριξη της απαιτούμενης σημασίας.

uncertain_review:
Δεν είναι δυνατή αξιόπιστη απόφαση χωρίς δεύτερο έλεγχο.
```

Το `candidate_context` μπορεί να χρησιμοποιηθεί μόνο βοηθητικά στο annotation UI. Προκαθορισμένος Phase 2 κανόνας:

```text
Μια τυχαία σχετική λέξη ή έννοια μόνο μέσα στο candidate_context δεν αρκεί για relevant_same_sense όταν το candidate_term και η candidate_definition αφορούν διαφορετική έννοια.
```

Ο κανόνας δεν εφαρμόζεται αναδρομικά στις Phase 0/1 annotations.

## 7. Blinding και provenance

Το blinded CSV έχει 35/35 data rows και ακριβώς 12/12 ordered columns:

```text
annotation_id
example_id
term
src
tgt
evidence_id
candidate_term
candidate_definition
candidate_context
relevance_category
annotation_confidence
annotation_notes
```

Οι τελευταίες 3/12 στήλες είναι κενές σε 35/35 rows. Δεν υπάρχουν method, rank, score, similarity, selection channel, agreement, προηγούμενο relevance label, hallucination label ή probability. Τα candidate fields αντιγράφηκαν απευθείας από την canonical KB χωρίς αλλαγή.

Το deterministic `annotation_id` ορίζεται ως:

```text
M3P2A-ANN- + first 16 uppercase hexadecimal characters of
SHA-256("module3-phase2a|seed=42|example_id={example_id}|evidence_id={evidence_id}")
```

Η blinded σειρά είναι ascending SHA-256 του UTF-8 string:

```text
module3-phase2a-blind-order|seed=42|annotation_id={annotation_id}
```

με tie-break το `annotation_id`. Τα 35/35 IDs και τα 35/35 `(example_id, evidence_id)` pairs είναι μοναδικά.

Το hidden provenance έχει 35/35 rows στην ίδια ordered `annotation_id` σειρά και καταγράφει μόνο deterministic selection lineage: selection channel, dense new/filtered/full-KB rank, cosine similarity, exact-term flag, normalized terms, candidate-record hash και frozen configuration ID. Δεν προορίζεται για τον annotator.

## 8. Frozen Phase 2 decision rule

Ο κανόνας παγώνει πριν από annotation και θα εφαρμοστεί μόνο μετά την ολοκλήρωση human-only annotations:

```text
0–1/7 examples με νέο strict candidate:
EXTERNAL_KB_EXPANSION_REQUIRED

2–3/7 examples με νέο strict candidate:
COMBINED_EXPANSION_AND_SENSE_RETRIEVAL

4–7/7 examples με νέο strict candidate:
SENSE_AWARE_RETRIEVAL_FIRST
```

Η preparation δεν υπολογίζει relevance metrics και δεν εφαρμόζει τον κανόνα.

## 9. Offline UI compatibility

Δεν δημιουργήθηκε νέο UI. Το υπάρχον generic `RAG/tools/relevance_annotation_ui.html` παραμένει hash-locked και συμβατό, επειδή το νέο CSV έχει θετικό row count, ακριβώς το απαιτούμενο 12-column schema, κενές annotation στήλες και μοναδικά IDs/pairs. Ο annotator πρέπει να φορτώσει μόνο το blinded CSV και όχι το provenance JSONL.

## 10. Output integrity

| Output available before writing this plan | Bytes | SHA-256 |
|---|---:|---|
| `RAG/results/rag_module3/phase2/annotation/module3_phase2a_kb_coverage_blinded.csv` | 18.328 | `23a4668a4777d6afa42ff7c059008b878a9359ba1e3dc70d29af8cafcdd75ff2` |
| `RAG/results/rag_module3/phase2/annotation/module3_phase2a_kb_coverage_provenance.jsonl` | 20.200 | `27e03ace6510307fbfe9847cb86badbd0902fc23173697c0ca27f3d00ad612aa` |

Το exact SHA-256 του ίδιου του `MODULE3_PHASE2A_PLAN.md` υπολογίζεται μετά το final write και παρέχεται στο τελικό handoff, επειδή η literal ενσωμάτωση self-hash θα άλλαζε το byte stream που περιγράφει.

## 11. Limitations και artifact hygiene

- Η Phase 2A αφορά 7/10 development examples και δεν αποτελεί independent sample, generalization evidence ή external validation.
- Το `tgt` είναι reference-assisted input.
- Το full-KB candidate universe περιορίζεται στην υπάρχουσα unlabeled-training KB των 9.577/9.577 rows· δεν περιλαμβάνει external knowledge.
- Η definition-only similarity μπορεί να εντοπίσει semantic proximity, αλλά δεν αποτελεί relevance annotation και δεν επιτρέπεται να ερμηνευθεί ως τέτοια.
- Η human annotation δεν πραγματοποιείται στην preparation.

Δημιουργήθηκαν μόνο τα τρία εγκεκριμένα Phase 2A preparation artifacts: το παρόν plan, το blinded CSV και το hidden provenance JSONL. Persistent notebook, metrics file, manifest, project script, cache ή νέο UI: 0. Existing Module 1/2 και Phase 0/1 artifacts modified: 0. Existing annotation rows modified: 0. Artifacts moved/deleted: 0.

API/network/Gemini calls: 0. Downloads/installations/package changes: 0. Official test accesses: 0. Notebook executions: 0. BM25/RRF/NLI/reranker executions: 0. E5 integration operations: 0.

Η Phase 2A σταματά εδώ. Δεν ξεκινά annotation, relevance evaluation, Phase 2 decision, external KB expansion, reranker, gate redesign, Gemini experiment ή E5 integration.
