# E6-v4 — τεχνική αναφορά διακοπής

**Κατάσταση: BLOCKED_BEFORE_BULK_SCORING. Η αξιολόγηση δεν εκτελέστηκε.**

Η επίσημη `bert-score==0.3.13` απέτυχε στο τεχνητό smoke test με `OverflowError: int too big to convert`. Εφαρμόστηκε η ρητή οδηγία της ενότητας 3: «Αν η επίσημη αντιστοίχιση δεν είναι διαθέσιμη ή η βιβλιοθήκη είναι ασύμβατη, σταμάτησε πριν από scoring και τεκμηρίωσε το τεχνικό εμπόδιο».

## Επαληθευμένο baseline και κατάσταση αποτελεσμάτων

| Έκδοση | Correct | Accuracy | Spearman | Νέα RF fits |
|---|---:|---:|---:|---:|
| E6-v3, αποθηκευμένο baseline | 474/561 | 0.8449197861 | 0.7816945786 | 0 |
| E6-v4 | Δεν υπολογίστηκε | — | — | 0 |

Επαληθεύτηκαν τα 561 μοναδικά IDs, τα folds, οι ανθρώπινες δυαδικές ετικέτες και το p_hallucination έναντι του canonical manifest. Οι αποθηκευμένες προβλέψεις v3 ταυτίζονται αριθμητικά ανά ID/fold με τα paired diagnostics και αναπαράγουν το καταγεγραμμένο αποτέλεσμα. Δεν έγινε baseline fit. Οι πέντε validation πληθυσμοί είναι 113,112,112,112,112.

## Συγκεκριμένο τεχνικό εμπόδιο

Το επίσημο BERTScore καλεί `tokenizer.encode(..., max_length=tokenizer.model_max_length, truncation=True)` στο `packages/bert_score/utils.py`, συνάρτηση `sent_encode`. Στο υπάρχον περιβάλλον transformers 5.5.4 / tokenizers 0.22.2, ο φορτωμένος DebertaTokenizer έχει `model_max_length=1000000000000000019884624838656`, δηλαδή την τιμή sentinel μη καθορισμένου ορίου. Το checkpoint δηλώνει `max_position_embeddings=512`, αλλά το παγωμένο tokenizer_config.json δεν ορίζει model_max_length.

Η μεταβίβαση της τιμής sentinel στο backend `enable_truncation` προκαλεί OverflowError πριν παραχθούν BERTScore τιμές για τα τεχνητά κείμενα. Η αποτυχία αφορά τον συγκεκριμένο συνδυασμό επίσημου package, pinned tokenizer και υπάρχοντος runtime· δεν αποδεικνύει ασυμβατότητα σε κάθε άλλο περιβάλλον. Το πλήρες traceback βρίσκεται στο `provenance/compatibility.json` και το αρχικό console log στο `provenance/compatibility_console.txt`.

Δεν εφαρμόστηκε χειροκίνητο max_length=512, τροποποίηση της βιβλιοθήκης, αλλαγή checkpoint/tokenizer ή downgrade. Η επίσημη αντιστοίχιση layer υπάρχει και δίνει **18**· η αποτυχία αφορά tokenization, όχι επιλογή layer.

## Provenance

- Model/tokenizer: `microsoft/deberta-large-mnli`, revision `7296194b9009373def4f7c5dad292651e4b5cf4e`, ακριβώς το cached checkpoint του αρχικού E3. Επαληθεύτηκαν και τα πέντε pinned model/tokenizer αρχεία έναντι του αποθηκευμένου provenance E6-v1.
- Official wheel: `bert_score-0.3.13-py3-none-any.whl`, SHA-256 `bbbb4c7fcdaa46d7681aff49f37f96faa09ed74e1b150e659bdc6b58a66989b9`. Επαληθεύτηκαν 84 hashed RECORD entries και μεγέθη. Το package παραμένει ατροποποίητο μέσα στον φάκελο v4.
- Distribution metadata: 0.3.13. Το ίδιο upstream wheel δηλώνει εσωτερικά `__version__=0.3.12`. Καταγράφονται και οι δύο τιμές χωρίς διόρθωση του upstream κώδικα.
- Πραγματικό official BERTScore hash string: `microsoft/deberta-large-mnli_L18_no-idf_version=0.3.12(hug_trans=5.5.4)`. Το hash string δεν περιλαμβάνει το model revision· το πλήρες provenance το καταγράφει χωριστά.
- idf=False, rescale_with_baseline=False, num_layers=18 από την επίσημη αντιστοίχιση. CPU float32, batch size 2, τέσσερα intra/inter-op threads. Πλήρεις εκδόσεις στο configuration.
- Έγινε μόνο λήψη του απαιτούμενου package wheel/metadata για τοπική χρήση, χωρίς εγκατάσταση/αλλαγή των κοινών dependencies. Το checkpoint ήταν ήδη cached. Το compatibility test είχε αποκλεισμένο δίκτυο και μηδενικές απόπειρες δικτύου. Δεν έγιναν retrieval, απομακρυσμένο inference ή LLM/API calls.

## Έλεγχοι και μη παραχθέντα παραδοτέα

Οι 36 αρχικές στήλες επαληθεύτηκαν ως προς hash, σειρά, πεπερασμένες τιμές και 561 IDs. Δεν δημιουργήθηκε νέα μήτρα για να πιστοποιηθεί ισότητα του πρώτου block μέσα σε αυτήν. Αποθηκεύτηκε μόνο το προβλεπόμενο schema των 43 χαρακτηριστικών και τα ακριβή label-free reference/hyp inputs. Η αντιστοίχιση reference=tgt για DM/MT, src για PG ελέγχθηκε και έναντι των canonical strings.

Τα deterministic structural contracts σε τεχνητά κείμενα πέρασαν. Στο αρχικό compatibility test πέρασε η assertion κατεύθυνσης της επίσημης greedy matching συνάρτησης σε τεχνητά orthogonal embeddings (precision=1, recall=2/3). Αυτό δεν υποκαθιστά τα neural smoke tests: ίδια πρόταση, omission, addition, αλλαγή αριθμού και προσθήκη/αφαίρεση άρνησης δεν απέδωσαν neural scores λόγω της αποτυχίας tokenization.

**Πραγματικά δείγματα με νέα χαρακτηριστικά: 0. Πραγματικά BERTScore pairs: 0. RF fits E6-v4: 0. Πρόσθετα baseline fits: 0.** Η πλήρης εξαγωγή δεν άρχισε, επομένως ο χρόνος πλήρους εξαγωγής και το πλήθος truncated πραγματικών δειγμάτων είναι μη διαθέσιμα, όχι μετρημένα μηδενικά.

Δεν υπάρχουν επτά νέα χαρακτηριστικά ανά ID, μήτρα 43 χαρακτηριστικών, 561 E6-v4 OOF predictions ή paired diagnostics v4. Δεν μπορούν να υπολογιστούν metrics ανά fold/task/evidence, διορθώσεις/νέα λάθη, McNemar ή bootstrap έναντι v3. Δεν αποδίδονται πλασματικές τιμές και δεν επαναχρησιμοποιούνται baseline predictions ως v4.

Το `E6_V4_PROTOCOL.md`, το configuration, το ordered schema, οι deterministic κανόνες, ο κώδικας ελέγχου και το provenance τεκμηριώνουν το μπλοκαρισμένο στάδιο. Το πρωτόκολλο καταγράφηκε μετά την απόπειρα τεχνητού compatibility test, πριν από οποιοδήποτε SHROOM scoring ή fit. Δεν δηλώνεται επιτυχές execution freeze ή feature-matrix freeze.

## Ακεραιότητα και ερευνητικό όριο

Ο τελικός έλεγχος SHA-256 επαλήθευσε **1784 προστατευμένα αρχεία**, περιλαμβανομένων προηγούμενων πειραμάτων και error analysis. Οι νέες εγγραφές περιορίστηκαν στον φάκελο E6-v4. Δεν έγινε official-test access, αλλαγή synthetic δεδομένων, commit/push/tag ή άλλο πείραμα.

Η προτεινόμενη επέκταση παραμένει adaptive exploratory development-only επειδή επιλέχθηκε μετά την ανάλυση σφαλμάτων. Δεν υπάρχει μετρημένη βελτίωση ή υποβάθμιση v4. Αν μπορούσε να εκτελεστεί με εγκεκριμένη συμβατή διαδικασία, οι προβλεπόμενοι στατιστικοί έλεγχοι θα ήταν descriptive exploratory statistics, χωρίς ανεξάρτητη confirmatory ερμηνεία.
