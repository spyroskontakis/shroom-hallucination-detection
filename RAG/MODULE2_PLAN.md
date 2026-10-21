# SHROOM RAG E5 — Σχέδιο Module 2

## Κατάσταση και όρια

Το παρόν αρχείο είναι σχέδιο και όχι υλοποίηση. Δεν εγκρίνει εγκατάσταση
βιβλιοθηκών, δημιουργία νέου environment, κατασκευή BM25/dense index ή νέες
Gemini κλήσεις. Τα κλειδωμένα Module 1 artifacts παραμένουν αμετάβλητα και το
Module 2 πρέπει να χρησιμοποιήσει ξεχωριστά outputs και caches.

## Στόχος

Στόχος του Module 2 είναι η βελτίωση της relevance και της usable coverage του
retrieval πριν δοθεί νέο evidence στο Gemini. Η αύξηση της απλής coverage δεν
είναι επαρκής: ένα candidate διαφορετικής σημασίας πρέπει να απορρίπτεται, ακόμη
και αν ταιριάζει λεξικά στον ίδιο όρο.

Το Module 2 πρέπει να απαντήσει offline στα εξής ερωτήματα:

1. Μπορεί το hybrid retrieval να βρίσκει συχνότερα evidence ίδιας σημασίας;
2. Μπορεί να κατατάσσει χαμηλότερα τα different-sense και irrelevant results;
3. Μπορεί να κάνει abstention όταν δεν υπάρχει ασφαλές evidence;
4. Είναι η βελτίωση αρκετή ώστε να δικαιολογηθεί νέο, μικρό API experiment;

## Μεθοδολογικές αρχές

- Η candidate knowledge base παραμένει αποκλειστικά στο unlabeled
  model-agnostic training split.
- Δεν επιτρέπονται `label`, `labels`, `label_bin`, `p(Hallucination)` ή
  `p_hallucination` σε query construction, retrieval, reranking ή tuning.
- Το official test set δεν φορτώνεται.
- Το `tgt` επιτρέπεται ως primary input/reference του SHROOM example και όχι ως
  gold hallucination label.
- Τα development labels δεν χρησιμοποιούνται ούτε για επιλογή regression cases
  ούτε για ρύθμιση thresholds/weights.
- Διατηρούνται `RANDOM_STATE=42`, σταθερή σειρά candidates και deterministic
  tie-breaking.
- Κάθε νέο artifact γράφεται σε ξεχωριστό Module 2 directory. Το Module 1 cache
  δεν διαβάζεται ως retrieval signal και δεν τροποποιείται.

## Προτεινόμενη αρχιτεκτονική

### 1. Exact-term retrieval

Το normalized exact match διατηρείται ως ασφαλές αρχικό σήμα και ως regression
baseline. Ένα exact match δεν θεωρείται αυτόματα relevant, επειδή ο ίδιος όρος
μπορεί να έχει πολλές σημασίες.

Προτεινόμενα outputs ανά candidate:

- `exact_match` boolean,
- normalized term,
- candidate definition,
- candidate source context,
- σταθερό `evidence_id`.

### 2. BM25 lexical candidate generation

Το BM25 δημιουργεί lexical candidates από την ίδια unlabeled DM knowledge base.
Το query μπορεί να συνδυάζει:

- extracted term,
- τοπικό `src` context γύρω από το `<define>` marker,
- primary `tgt` reference.

Τα διαφορετικά πεδία πρέπει να παραμένουν διακριτά, ώστε να μπορεί να ελεγχθεί
με ablation αν το context ή το `tgt` προκαλεί τη βελτίωση. Δεν χρησιμοποιούνται
labels ή πιθανότητες.

### 3. Dense semantic candidate generation

Ο dense retriever κωδικοποιεί το query και κάθε candidate με sentence
embeddings. Η candidate representation μπορεί να περιλαμβάνει definition και
source context, ενώ η query representation μπορεί να περιλαμβάνει term, `src`
context και `tgt` σε σταθερή, τεκμηριωμένη μορφή.

Πριν από χρήση πρέπει να επιβεβαιωθούν offline:

- το ακριβές embedding model,
- η τοπική διαθεσιμότητα των model weights,
- η διάσταση και normalization των vectors,
- deterministic inference settings,
- η απουσία αυτόματου model download χωρίς έγκριση.

### 4. Hybrid score fusion

Οι exact, BM25 και dense λίστες ενώνονται σε κοινό candidate set. Δύο ασφαλείς
αρχικές επιλογές προς offline σύγκριση είναι:

1. Reciprocal Rank Fusion, που δεν απαιτεί άμεση σύγκριση ετερογενών scores.
2. Min-max ή rank normalization ανά query και σταθερός weighted συνδυασμός.

Τα weights δεν επιλέγονται με development hallucination labels. Αρχικά πρέπει
να είναι προκαθορισμένα ή να επιλέγονται μόνο από manual retrieval relevance
annotations.

### 5. Context-aware reranking

Κάθε candidate επαναξιολογείται με βάση πέντε πεδία:

1. extracted term,
2. `src` context,
3. primary `tgt` reference,
4. candidate definition,
5. candidate source context.

Το reranking πρέπει να εκτιμά semantic compatibility και word-sense agreement,
όχι απλώς ομοιότητα λέξεων. Η πρώτη έκδοση μπορεί να χρησιμοποιεί
deterministic similarity features. Πιο σύνθετος cross-encoder reranker θα
εξεταστεί μόνο αν τα offline diagnostics δείξουν ότι είναι αναγκαίος.

### 6. Relevance και ambiguity gate

Πριν δοθεί evidence στον verifier εφαρμόζεται gate που ελέγχει:

- ελάχιστο relevance score,
- διαφορά πρώτου και δεύτερου candidate,
- συμφωνία lexical και dense signals,
- σύγκρουση μεταξύ candidate sense και `src`/`tgt`,
- duplication ή near-duplication των retrieved definitions.

Τα thresholds δεν ρυθμίζονται με hallucination labels. Πρέπει να τεκμηριωθούν
από manual relevance annotations και sensitivity analysis.

### 7. Abstention

Αν κανένα candidate δεν περάσει το gate, το retriever επιστρέφει κενή λίστα και
καταγράφει structured abstention reason. Το Gemini τότε δεν λαμβάνει retrieved
evidence. Η abstention είναι αποδεκτό και συχνά προτιμότερο αποτέλεσμα από την
προώθηση different-sense evidence μόνο για τεχνητή αύξηση της coverage.

## Retrieval evaluation χωρίς leakage

### Σταθερό evaluation sample

Η πρώτη αξιολόγηση χρησιμοποιεί τα ίδια 20 DM development examples του Module
1. Η επιλογή παραμένει σταθερή και δεν αλλάζει ανάλογα με labels ή retrieval
αποτελέσματα.

### Manual relevance annotation

Κάθε retrieved candidate αξιολογείται χωρίς πρόσβαση σε hallucination labels.
Η annotation φόρμα πρέπει να περιέχει term, `src`, `tgt`, candidate definition
και candidate source context, αλλά όχι `label`, `labels` ή
`p(Hallucination)`.

Προτεινόμενες κατηγορίες:

- **relevant same sense**: υποστηρίζει την ίδια σημασία στο συγκεκριμένο context,
- **partially relevant**: έχει χρήσιμη επικάλυψη αλλά είναι ελλιπές ή ευρύτερο,
- **different sense**: αφορά τον ίδιο όρο αλλά άλλη σημασία,
- **irrelevant**: δεν παρέχει χρήσιμη σημασιολογική πληροφορία,
- **no suitable evidence**: κανένας candidate δεν είναι ασφαλής για χρήση.

Για συνέπεια πρέπει να υπάρχει σύντομο annotation guide και, αν είναι εφικτό,
δεύτερος annotator ή επανέλεγχος των αμφίβολων cases.

### Retrieval metrics

| Metric | Προτεινόμενος ορισμός |
|---|---|
| Evidence-eligible coverage | Ποσοστό examples για τα οποία τουλάχιστον ένα candidate περνά το relevance gate. |
| Relevant@1 | Ποσοστό examples με `relevant same sense` στο rank 1. |
| Precision@k | Ποσοστό των top-k candidates που είναι `relevant same sense`, με ξεχωριστή sensitivity αναφορά όταν συμπεριλαμβάνονται τα `partially relevant`. |
| Ambiguity rate | Ποσοστό evidence-eligible examples με different-sense ή αμφίσημα top candidates. |
| Irrelevant-evidence rate | Ποσοστό examples στα οποία το gate θα έστελνε irrelevant/different-sense evidence. |
| Abstention rate | Ποσοστό examples χωρίς evidence μετά το gate. |

Η usable coverage πρέπει να παρουσιάζεται μαζί με Relevant@1 και
irrelevant-evidence rate. Δεν θεωρείται βελτίωση η αύξηση coverage που αυξάνει
ταυτόχρονα τα different-sense errors.

## Υποχρεωτικά regression cases

| Term | Module 1 εύρημα | Αποδεκτή συμπεριφορά Module 2 |
|---|---|---|
| `preciosity` | Ανακτήθηκαν δύο σημασίες, μία σχετική και μία διαφορετική. | Same-sense candidate στην κορυφή ή abstention αν η σημασία παραμένει αβέβαιη. |
| `dateliner` | Το exact evidence ήταν πολύ σχετικό, αλλά επηρέασε αρνητικά τον verifier. | Σωστή κατάταξη με σαφή relevance diagnostics· η μελλοντική prompt χρήση αξιολογείται ξεχωριστά. |
| `continuous` | Ανακτήθηκε μαθηματική σημασία αντί της ζητούμενης. | Απόρριψη του mathematical sense και abstention αν δεν υπάρχει κατάλληλο evidence. |
| `weary` | Ανακτήθηκε διαφορετικό part-of-speech/sense. | Απόρριψη του διαφορετικού sense ή σωστό same-sense candidate. |
| `inconsistent` | Ανακτήθηκε σχετικό evidence και επιβεβαίωσε τη baseline κρίση. | Διατήρηση σχετικού top-ranked evidence με σταθερή κατάταξη. |

Regression pass σημαίνει είτε relevant same-sense top result είτε σωστό
abstention. Δεν απαιτείται evidence για κάθε case.

## Dependency audit

Ο έλεγχος έγινε read-only στο `shroom_ensemble` με Python 3.11.9. Δεν
εγκαταστάθηκε ή αναβαθμίστηκε βιβλιοθήκη.

| Capability | Package | Κατάσταση |
|---|---|---|
| BM25 | `rank-bm25` | Λείπει |
| BM25 alternative | `bm25s` | Λείπει |
| Sentence embeddings | `sentence-transformers` 5.4.1 | Υπάρχει |
| Transformer models | `transformers` 5.5.4 | Υπάρχει |
| Tensor backend | `torch` 2.11.0 | Υπάρχει |
| Cosine similarity | `scikit-learn` 1.8.0 | Υπάρχει |
| Numerical operations | `numpy` 2.4.4, `scipy` 1.17.1 | Υπάρχουν |
| Exact/brute nearest-neighbor search | `scikit-learn` 1.8.0 | Υπάρχει |
| FAISS index | `faiss` / `faiss-cpu` | Λείπει |
| HNSW index | `hnswlib` | Λείπει |
| Annoy index | `annoy` | Λείπει |

### Ελάχιστη προτεινόμενη εγκατάσταση

Αν εγκριθεί BM25 implementation, η ελάχιστη προσθήκη είναι μόνο το
`rank-bm25`. Δεν απαιτείται ακόμη FAISS, HNSW ή Annoy: για περίπου 9.577
candidate rows, normalized embedding matrix και brute-force cosine similarity
με NumPy/scikit-learn είναι επαρκή για το πρώτο offline prototype.

Καμία εγκατάσταση δεν εγκρίνεται από το παρόν σχέδιο. Πριν από μελλοντική
εγκατάσταση πρέπει να καταγραφεί η ακριβής version constraint και να ελεγχθεί
dependency compatibility.

### Environment recommendation

Το υπάρχον `shroom_ensemble` είναι τεχνικά επαρκές για το πρώτο Module 2
prototype, επειδή διαθέτει ήδη sentence embeddings, PyTorch και
scikit-learn. Ξεχωριστό environment μπορεί να εξεταστεί αργότερα μόνο αν
προκύψουν dependency conflicts ή αν απαιτείται αυστηρότερη απομόνωση για
αναπαραγωγιμότητα. Δεν λαμβάνεται ακόμη απόφαση δημιουργίας environment.

## Προτεινόμενα offline tests

1. **Deterministic retrieval:** ίδιο query και ίδιο index παράγουν ακριβώς την
   ίδια σειρά και scores.
2. **No-label query construction:** assertions απορρίπτουν forbidden columns
   και ελέγχουν το τελικό query payload.
3. **Stable ranking:** σταθερό tie-breaking με `evidence_id` και regression
   snapshots για τα top-k.
4. **Duplicate handling:** exact και near-duplicate definitions δεν
   καταλαμβάνουν πολλαπλές θέσεις χωρίς λόγο.
5. **Empty-result abstention:** κενό ή χαμηλής relevance αποτέλεσμα οδηγεί σε
   structured abstention και όχι σε αυθαίρετο evidence.
6. **Score normalization:** constant-score, missing-score και outlier cases δεν
   δημιουργούν NaN ή ασταθή fusion scores.
7. **Context/sense regression tests:** ειδικές assertions για `preciosity`,
   `dateliner`, `continuous`, `weary` και `inconsistent`.
8. **Candidate provenance:** κάθε result διατηρεί `evidence_id`, retrieval
   methods και επιμέρους scores.
9. **Cache isolation:** όλα τα Module 2 outputs γράφονται σε νέο directory και
   δεν ανοίγουν το Module 1 cache σε write mode.
10. **Official-test guard:** assertion ότι κανένα loaded path δεν αντιστοιχεί σε
    official test split.

## Προτεινόμενη σειρά εργασίας

1. Κλείδωμα input corpus και σταθερών 20 evaluation rows με hashes/manifests.
2. Δημιουργία manual annotation guide και relevance sheet χωρίς labels.
3. Exact baseline diagnostics στα ίδια 20 examples.
4. BM25 candidate generation και offline tests.
5. Dense candidate generation και offline tests.
6. Fusion και deterministic score diagnostics.
7. Context-aware reranking, relevance gate και abstention.
8. Manual review και υπολογισμός retrieval metrics.
9. Regression report για τα πέντε υποχρεωτικά cases.
10. Prompt leakage review και πρόταση νέου, σταθερού API sample/budget.

Κάθε βήμα πρέπει να ολοκληρώνεται και να ελέγχεται πριν προχωρήσει το επόμενο.

## Πύλη πριν από νέες API κλήσεις

Νέο Gemini experiment επιτρέπεται μόνο όταν ισχύουν όλα τα παρακάτω:

- έχει ολοκληρωθεί manual retrieval review,
- έχει μειωθεί τεκμηριωμένα το irrelevant/different-sense evidence,
- τα πέντε regression cases περνούν ή κάνουν σωστό abstention,
- τα prompts έχουν ελεγχθεί ξανά για leakage και prompt injection από evidence,
- έχουν παγώσει retriever configuration, thresholds και model identifiers,
- έχει εγκριθεί νέο σταθερό sample,
- έχει εγκριθεί ξεχωριστό API budget και append-only cache path.

Αν κάποιο κριτήριο αποτύχει, δεν πραγματοποιείται API call.

## Ανοιχτά ζητήματα

Τα παρακάτω καταγράφονται χωρίς επίλυση στο Module 2 plan:

- ασυμφωνία E3 artifacts: `n_oof=561` έναντι development 499,
- διαφορετικά αποθηκευμένα E3 metrics,
- ανάγκη calibration πριν χρησιμοποιηθεί το `p_hallucination` ως τελικό
  feature,
- ενσωμάτωση στο E3 μόνο μετά την ολοκλήρωση των Modules 2–3,
- Agentic RAG μόνο αν το απλό hybrid RAG παρουσιάσει σαφή, μετρήσιμη χρησιμότητα.

## Κριτήριο ολοκλήρωσης σχεδιασμού

Το παρόν σχέδιο ολοκληρώνει μόνο τη φάση σχεδιασμού. Η υλοποίηση του Module 2
απαιτεί νέα ρητή έγκριση, μαζί με απόφαση για την ελάχιστη BM25 dependency και
τα συγκεκριμένα offline deliverables.
