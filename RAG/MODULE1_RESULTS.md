# SHROOM RAG E5 — Αποτελέσματα Module 1

## Κατάσταση

Το Module 1 ολοκληρώθηκε ως ελεγχόμενο prototype exact retrieval για το task
Definition Modeling (DM). Τα αποτελέσματα είναι διαγνωστικά και δεν αποτελούν
model selection. Δεν εγκρίνονται νέες exact-RAG API κλήσεις πριν ολοκληρωθεί η
offline αξιολόγηση του Module 2.

## Μεθοδολογία

- Η knowledge base δημιουργήθηκε αποκλειστικά από το unlabeled
  model-agnostic training split.
- Το retrieval περιορίστηκε σε DM examples και χρησιμοποίησε normalized exact
  term matching με έως τρεις ορισμούς.
- Χρησιμοποιήθηκε σταθερό prototype 20 development examples με
  `RANDOM_STATE=42`.
- Τα `label`, `labels`, `label_bin`, `p(Hallucination)` και
  `p_hallucination` δεν χρησιμοποιήθηκαν σε retrieval queries ή prompts.
- Τα development labels ενώθηκαν με τις προβλέψεις μόνο μετά την αποθήκευση των
  απαντήσεων, αποκλειστικά για περιγραφική αξιολόγηση.
- Ο verifier χρησιμοποίησε το `gemini-2.5-flash-lite` και structured output με
  `p_hallucination`, `label`, `reason` και `evidence_ids`.
- Κάθε επιτυχής απάντηση αποθηκεύτηκε αμέσως σε append-only JSONL cache.
- Το smoke test περιλάμβανε 3 baseline και 3 RAG κλήσεις στα ίδια examples.
- Η εγκεκριμένη allowlist ήταν `30`, `55`, `185`, που αντιστοιχεί στους όρους
  `preciosity`, `dateliner`, `inconsistent`.
- Δεν φορτώθηκε το official test set και δεν εκτελέστηκε κώδικας E1–E4 ή NLI.

## Offline αποτελέσματα

| Μέγεθος ή έλεγχος | Αποτέλεσμα |
|---|---:|
| Unlabeled model-agnostic training samples | 30.000 |
| Model-agnostic development samples | 499 |
| DM training samples | 10.000 |
| Έγκυρες knowledge-base εγγραφές | 9.577 |
| Μοναδικοί normalized terms | 9.197 |
| Επιτυχής term extraction | 20/20 |
| Examples με exact evidence | 5/20 |
| Exact-retrieval coverage | 25% |

Τα πέντε evidence-bearing examples ήταν τα `preciosity`, `dateliner`,
`continuous`, `weary` και `inconsistent`. Η χειροκίνητη επιθεώρηση έδειξε ότι
το exact matching μπορεί να επιστρέψει σωστό evidence, αλλά δεν επιλύει το
word-sense ambiguity. Ειδικά τα `continuous` και `weary` επέστρεψαν evidence
διαφορετικής σημασίας και αποκλείστηκαν από το API smoke test.

## Gemini smoke test

Η εκτέλεση πραγματοποίησε ακριβώς έξι API attempts. Και οι έξι ολοκληρώθηκαν
επιτυχώς, χωρίς retry ή cache hit. Το cache περιέχει έξι μοναδικά records, χωρίς
duplicates, και όλες οι απαντήσεις έχουν
`label_probability_consistent=True`.

| Index | Term | Mode | `p_hallucination` | Predicted label | Consistent | `evidence_ids` | Σύντομη αιτιολόγηση |
|---:|---|---|---:|---|---|---|---|
| 30 | `preciosity` | baseline | 1.0 | Hallucination | True | `[]` | Το reference ερμηνεύτηκε ως συγκεκριμένο αντικείμενο αξίας, ενώ το hypothesis ως αφηρημένη ιδιότητα. |
| 30 | `preciosity` | RAG | 0.0 | Not Hallucination | True | `[]` | Η ιδιότητα του «πολύτιμου» κρίθηκε συμβατή με τη σημασία της υψηλής αξίας. |
| 55 | `dateliner` | baseline | 0.0 | Not Hallucination | True | `[]` | Η σύνδεση άρθρου, dateline και συγκεκριμένης ημερομηνίας κρίθηκε εύλογη. |
| 55 | `dateliner` | RAG | 1.0 | Hallucination | True | `[19672]` | Το reference και το evidence κρίθηκε ότι δεν ορίζουν τη συγκεκριμένη ημερομηνία ως βασικό γνώρισμα. |
| 185 | `inconsistent` | baseline | 0.0 | Not Hallucination | True | `[]` | Το «Not consistent» αναγνωρίστηκε ως άμεση παράφραση του reference. |
| 185 | `inconsistent` | RAG | 0.0 | Not Hallucination | True | `[12239]` | Το retrieved definition επιβεβαίωσε την ίδια σημασία. |

### Baseline και RAG ανά example

| Index | Μεταβολή πιθανότητας | Αλλαγή label | Ερμηνεία |
|---:|---:|---|---|
| 30 | -1.0 | Hallucination → Not Hallucination | Η RAG παραλλαγή διόρθωσε τη baseline πρόβλεψη, χωρίς όμως ρητή αναφορά σε evidence ID. |
| 55 | +1.0 | Not Hallucination → Hallucination | Το cited evidence μετέτρεψε μία σωστή baseline πρόβλεψη σε λανθασμένη. |
| 185 | 0.0 | Καμία αλλαγή | Το evidence επιβεβαίωσε την ήδη σωστή baseline πρόβλεψη. |

### Περιγραφικά metrics

| Mode | N | Accuracy | Spearman |
|---|---:|---:|---:|
| Baseline | 3 | 0.666667 | 0.500000 |
| RAG | 3 | 0.666667 | 0.500000 |

## Αυστηρή επιστημονική ερμηνεία

- `preciosity`: «Το RAG prompt διόρθωσε την πρόβλεψη, αλλά επειδή το μοντέλο
  επέστρεψε `evidence_ids=[]`, η αλλαγή δεν μπορεί να αποδοθεί με βεβαιότητα σε
  συγκεκριμένο retrieved definition.»
- `dateliner`: «Το retrieved evidence επηρέασε αρνητικά την απόφαση και
  μετέτρεψε μία σωστή baseline πρόβλεψη σε λανθασμένη.»
- `inconsistent`: «Το evidence επιβεβαίωσε την ήδη σωστή baseline κρίση χωρίς
  αλλαγή πιθανότητας ή label.»

Η Accuracy και η Spearman correlation παρέμειναν ίδιες στα δύο modes
(`0.666667` και `0.500000`, αντίστοιχα). Το δείγμα είναι πολύ μικρό και
επιλέχθηκε βάσει της ύπαρξης exact evidence. Επομένως, τα metrics είναι μόνο
περιγραφικά, δεν αποτελούν model selection και δεν επιτρέπουν συμπέρασμα
γενίκευσης. Οι ακραίες τιμές `0.0/1.0` δεν αποτελούν απόδειξη calibration.

Τα αποτελέσματα δεν υποστηρίζουν έναν γενικό ισχυρισμό ότι το RAG βοήθησε.
Αντίθετα, δείχνουν ότι απαιτούνται relevance filtering, sense-aware reranking
και δυνατότητα abstention πριν δοθούν νέα retrieved definitions στον verifier.

## Συμπέρασμα Module 1

Το Module 1 απέδειξε ότι:

- η τεχνική υποδομή RAG, structured output και append-only caching λειτουργεί,
- το exact matching μόνο του δεν είναι αρκετά αξιόπιστο,
- άσχετο ή διαφορετικής σημασίας evidence μπορεί να βλάψει τον verifier,
- δεν δικαιολογούνται 20 νέες Gemini κλήσεις με τον ίδιο exact retriever.

Το επόμενο βήμα περιορίζεται στον offline σχεδιασμό και έλεγχο βελτιωμένου
retrieval. Δεν εγκρίνεται ακόμη Module 2 implementation ή νέο API budget.

## Ακεραιότητα κλειδωμένων artifacts

Τα παρακάτω SHA-256 hashes ορίζουν τα κλειδωμένα Module 1 artifacts:

| Artifact | SHA-256 |
|---|---|
| `shroom_rag_e5_module1_gemini_trial.ipynb` | `A7E0455A11EFFB7C195EFFB1CACB542DD82992FCCE027FB0D297BE598557D20B` |
| `results/rag_module1/module1_gemini_cache.jsonl` | `A942A0CC228DEF64B61389BCF7B7A5CB0A93BBCC7B0AA1D726826A9993B14CA5` |

Τα artifacts δεν πρέπει να τροποποιηθούν, μετακινηθούν, καθαριστούν ή
επανεκτελεστούν.
