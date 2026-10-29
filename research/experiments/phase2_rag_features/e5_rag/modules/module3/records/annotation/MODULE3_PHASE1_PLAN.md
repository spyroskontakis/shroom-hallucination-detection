# SHROOM RAG E5 — Module 3 Phase 1 Plan

## 1. Στόχος και scope

Η Phase 1 προετοιμάζει ένα blinded, human-only annotation package για τους 40/40 πρόσθετους unique candidates που υπάρχουν ήδη στο stored Phase A top-5 artifact αλλά δεν περιλαμβάνονταν στο ανθρώπινα annotated top-3 pool των επτά development coverage-failure examples. Δεν πραγματοποιείται annotation, relevance inference, retrieval, model execution, retuning ή evaluation.

Η ιστορική κατάσταση παραμένει:

```text
Module 2: CLOSED — NO_GO_FOR_GEMINI
Module 2 configuration: frozen
Module 3 Phase 0 decision: INSUFFICIENT_EVIDENCE
Gemini calls: prohibited
E5 integration into E3: not performed
Official test: prohibited
```

Η Phase 1 είναι νέο diagnostic extension και δεν αλλάζει εκ των υστέρων το Module 2.

## 2. Input paths και SHA-256

Όλα τα paths είναι canonical κάτω από ``.

| Input | Bytes | SHA-256 |
|---|---:|---|
| `RAG/AGENTS.md` | 3.244 | `8dc147df8c11ef967ccc5b9af44f68b9c76ac2c43b67186c021bb78523c83594` |
| `RAG/MODULE2_FINAL_RESULTS.md` | 14.619 | `574a75f7e0a2bef4ad2ac1b4c68e2892e8356fd9134a885293549e2773c82d92` |
| `RAG/results/rag_module2/MODULE2_FINAL_ARTIFACT_MANIFEST.json` | 25.510 | `29ce9cd021d722076a2589a8265e7259e33953f78686c41275c631539ee9c864` |
| `RAG/results/rag_module2/annotation/MODULE2_ANNOTATION_GUIDE.md` | 3.212 | `b26441828507dcb7dab2dae530a48a22db1bab1f1b0b0b2d4a29782d1f23b64f` |
| `RAG/results/rag_module3/MODULE3_PHASE0_FAILURE_AUDIT.md` | 20.996 | `cee0c89916639020710a917483da82e531522d00d771f08deae2c3fb0b8c6d3f` |
| `RAG/results/rag_module2/module2_candidates_top5.jsonl` | 425.769 | `480ce705b5afb06d4e9efe03f2a1083f45ae8d8e74a52ad8b3f8e6ad46931107` |
| `RAG/results/rag_module2/annotation/module2_annotation_provenance.jsonl` | 240.007 | `3705f9dbb37115715ca922d73b226379efac08f0873d6fa7b704ae6705dd3216` |
| `RAG/results/rag_module2/annotation/module2_annotation_dev_human_completed.csv` | 44.770 | `3f1f0a6d3eb9a75de69344f6e1df13b88745e464c98f94e1ce87997302669ed5` |
| `RAG/results/rag_module2/evaluation/module2_dev_decisions.jsonl` | 4.411 | `32d51e21c03ea5ff9564628d3e340269b7443abd6af9b3c7d2a11fb05ace477f` |
| `RAG/tools/module2_annotation_ui.html` | 18.848 | `140a396b2c33de413086d3ea65daef127c822c1d09f067ec2d8a9eefeab12c55` |

Read-only integrity preflight: Module 2 manifest artifacts 69/69, stored candidates 612/612 rows, development human annotations 83/83 rows και Phase 0 hash exact. Δεν ανοίχθηκε ή χρησιμοποιήθηκε `module2_annotation_dev_completed.csv`, αρχείο με `ai_assisted`, αρχείο με `completed_ai`, ή άλλο AI-generated/AI-prefilled annotation artifact.

## 3. Selection procedure

Για κάθε development example που είχε Phase 0 classification `ANNOTATED_POOL_COVERAGE_FAILURE`:

1. Φορτώθηκαν μόνο οι ήδη αποθηκευμένες Phase A top-5 appearances.
2. Εντοπίστηκαν μέσω του canonical annotation provenance τα evidence IDs του ήδη ανθρώπινα annotated top-3 pool.
3. Αφαιρέθηκαν όλα αυτά τα evidence IDs από το stored top-5 set του ίδιου example.
4. Έγινε deduplication με canonical key `(development_index, evidence_id)`.
5. Διατηρήθηκαν όλες οι stored appearances κάθε πρόσθετου candidate χωρίς αλλαγή candidate text ή provenance.

Το νέο deterministic `annotation_id` ορίζεται ως:

```text
M3P1-ANN- + first 16 uppercase hexadecimal characters of
SHA-256("module3-phase1|seed=42|example_id={example_id}|evidence_id={evidence_id}")
```

Δεν κωδικοποιεί method, query variant, rank, score ή relevance. Η blinded σειρά ορίζεται με ascending SHA-256 του ASCII/UTF-8 string:

```text
module3-phase1-blind-order|seed=42|annotation_id={annotation_id}
```

με tie-break το `annotation_id`. Η διαδικασία χρησιμοποιεί `RANDOM_STATE=42` ως σταθερό seed label και δεν καλεί pseudo-random generator.

## 4. Counts ανά example και συνολικά

| Development index | `example_id` | Term | Additional unique candidates |
|---:|---|---|---:|
| 30 | `EX-590A0B447A17` | `preciosity` | 6/6 |
| 42 | `EX-1AA2C1DAFB9C` | `bandslash` | 6/6 |
| 78 | `EX-7565997D951E` | `nonentertainment` | 6/6 |
| 122 | `EX-D4E131D57443` | `continuous` | 4/4 |
| 154 | `EX-C47370FB429F` | `foreboding` | 7/7 |
| 158 | `EX-1E6E8BDB9874` | `tetaniform` | 7/7 |
| 175 | `EX-6681F3007742` | `keen` | 4/4 |
| **Σύνολο** | **7/7 examples** |  | **40/40** |

Οι Phase 0 classifications επαληθεύτηκαν από τα canonical human annotations και frozen decisions: `STRICT_SUCCESS_ACCEPTED` 1/10, `RANKING_FAILURE` 2/10, `ANNOTATED_POOL_COVERAGE_FAILURE` 7/10 και `GATE_FALSE_ABSTENTION` 0/10.

## 5. Blinding guarantees

Το `module3_phase1_top5_extension_blinded.csv` έχει 40/40 data rows και ακριβώς τις 12/12 στήλες:

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

- Οι τρεις annotation στήλες είναι απολύτως κενές σε 40/40 rows.
- Τα 40/40 `annotation_id` και τα 40/40 `(example_id, evidence_id)` pairs είναι μοναδικά.
- Δεν υπάρχουν method, query variant, rank, score, agreement, gate, hallucination label ή probability fields.
- Τα reference και candidate texts αντιγράφονται αμετάβλητα από τα canonical human input fields και stored Phase A rows.
- Το CSV έχει UTF-8 BOM, CRLF row endings και RFC 4180-compatible escaping για commas, quotes και embedded newlines.
- Δεν μεταφέρθηκε καμία παλιά annotation value.

Το `module3_phase1_top5_extension_provenance.jsonl` έχει 40/40 rows στην ίδια ordered `annotation_id` σειρά. Περιλαμβάνει όλες τις stored Phase A appearances, query variant, retrieval method, original rank, stored score/score field, method agreement, retrieval-method overlap, original ranks/scores και source artifact line identifier/hash. Είναι hidden analysis provenance και δεν αποτελεί annotator input.

## 6. Human-only annotation protocol

Ο ανθρώπινος annotator αξιολογεί αποκλειστικά αν το candidate evidence ταιριάζει σημασιολογικά με `term`, `src` και `tgt`. Οι επιτρεπόμενες categories είναι:

- `relevant_same_sense`
- `partially_relevant`
- `different_sense`
- `irrelevant`
- `uncertain_review`

Η confidence είναι ακριβώς `high`, `medium` ή `low`, ενώ τα notes είναι προαιρετικά. Hallucination prediction, retrieval diagnostics και AI suggestions δεν χρησιμοποιούνται. Τα `partially_relevant` δεν θεωρούνται αυτομάτως strict ή ασφαλή evidence. `uncertain_review` και low-confidence cases απαιτούν ξεχωριστό human review πριν από evaluation.

**Κατά την annotation δεν πρέπει να ανοιχθεί, φορτωθεί ή συμβουλευτεί το provenance JSONL.**

## 7. Οδηγίες χρήσης του UI

Το hash-locked `module2_annotation_ui.html` δεν επαναχρησιμοποιείται: έχει hard-coded απαίτηση 83/83 rows και hard-coded Module 2 export filenames. Δημιουργήθηκε το generic offline `RAG/tools/relevance_annotation_ui.html`.

1. Άνοιξε το `RAG/tools/relevance_annotation_ui.html` σε browser χωρίς network requirement.
2. Πάτησε **Load blank CSV** και επίλεξε **μόνο** το `module3_phase1_top5_extension_blinded.csv`.
3. Επιβεβαίωσε ότι εμφανίζεται `40 blank rows` και progress `0/40`.
4. Χρησιμοποίησε `1–5` για category και `H/M/L` για confidence. Τα notes είναι προαιρετικά.
5. Το **Save & Next** αποθηκεύει deterministic local browser progress για το input stem και την ordered ID sequence. Υπάρχουν επίσης Previous και Next unanswered.
6. Το progress export ονομάζεται `module3_phase1_top5_extension_blinded_human_in_progress.csv`.
7. Το completed export ενεργοποιείται μόνο στο 40/40 και ονομάζεται `module3_phase1_top5_extension_blinded_human_completed.csv`.

Το UI απαιτεί οποιοδήποτε θετικό row count, ακριβώς το 12-column schema, blank annotation inputs και μοναδικά IDs/pairs. Χρησιμοποιεί `textContent` για untrusted fields, δεν φορτώνει provenance και δεν περιέχει network references. Offline source-runtime verification: syntax PASS, embedded deterministic self-tests 13/13 PASS, πραγματικό blinded CSV load 40/40 PASS, initial progress 0/40 και completed export locked.

## 8. Προκαθορισμένοι κανόνες απόφασης

Μετά — και μόνο μετά — την ολοκλήρωση της ανθρώπινης annotation, θα μετρηθεί σε πόσα από τα 7/7 coverage-failure examples εμφανίζεται τουλάχιστον ένας νέος `relevant_same_sense` candidate.

```text
0–1/7 examples with new strict candidate:
KB_EXPANSION_FIRST

2–3/7 examples with new strict candidate:
COMBINED_KB_AND_RERANKER

4–7/7 examples with new strict candidate:
RERANKER_FIRST
```

Οι κανόνες παγώνουν πριν από annotation, είναι diagnostic και δεν αποτελούν generalization estimate. Το `GATE_REDESIGN_FIRST` αποκλείεται ως κύρια Phase 1 απόφαση επειδή το development είχε 0/10 strict false abstentions. Το holdout `rattan` strict false abstention 1/10 παραμένει μελλοντικό gate constraint.

## 9. Limitations

- Η Phase 1 αφορά 7/10 development examples και 40/40 πρόσθετους stored candidates· δεν είναι νέο independent sample.
- Το `tgt` παραμένει reference-assisted input και δεν αποτελεί external validation.
- Η annotation θα πραγματοποιηθεί από έναν ανθρώπινο annotator και δεν προβλέπεται inter-annotator agreement σε αυτή τη μικρή extension.
- Η ύπαρξη ή απουσία strict candidate στο stored top-5 δεν αποδεικνύει ύπαρξη ή απουσία από ολόκληρη την knowledge base.
- Method overlap, ranks και scores παραμένουν κρυφά και δεν αποτελούν relevance evidence.
- Η preparation δεν υπολογίζει relevance metrics και δεν εφαρμόζει τους decision rules.

## 10. Artifact-hygiene statement

Επιτρεπόμενα Phase 1 preparation artifacts:

- `RAG/results/rag_module3/annotation/MODULE3_PHASE1_PLAN.md`
- `RAG/results/rag_module3/annotation/module3_phase1_top5_extension_blinded.csv`
- `RAG/results/rag_module3/annotation/module3_phase1_top5_extension_provenance.jsonl`
- `RAG/tools/relevance_annotation_ui.html`, επειδή το Module 2 UI ήταν ασύμβατο.

Δεν δημιουργήθηκε manifest, notebook, metrics file, completed CSV, project script ή cache. Δεν τροποποιήθηκε κανένα Module 1, Module 2 ή E1–E4 artifact. Δεν έγινε annotation, relevance inference, retrieval, dense/NLI/reranker/model execution, retuning, API/Gemini/network call, official-test access, installation, download, μετακίνηση, μετονομασία, διαγραφή ή cleanup.

Output hashes που ήταν διαθέσιμοι πριν από τη συγγραφή του παρόντος plan:

| Output | Bytes | SHA-256 |
|---|---:|---|
| `module3_phase1_top5_extension_blinded.csv` | 22.788 | `fa983d2dcae8edc6fe4f69dffe14f4dcb0906b8c0204ecc609bba67dfebda90e` |
| `module3_phase1_top5_extension_provenance.jsonl` | 33.303 | `90b36bf328515cfc348ddbbeb8ca6fd9f55cba3ffaca476edb40f5e9167f7a73` |
| `RAG/tools/relevance_annotation_ui.html` | 20.944 | `0a997deebc1c78948f1099cfe84c3d127f5146f43bf4e105dd0a242ccbd31670` |

API/network calls: 0. Experimental executions: 0. Notebook/retrieval/model executions: 0. Official test used: 0. Module 2 artifacts modified: 0.
