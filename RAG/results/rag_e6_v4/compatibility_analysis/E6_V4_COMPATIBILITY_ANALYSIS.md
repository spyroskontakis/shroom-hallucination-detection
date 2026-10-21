# E6-v4 — diagnosis and compatibility analysis

**Diagnosis: PASS. Original environment compatibility: FAIL. Isolated synthetic compatibility test: PASS. E6-v4 remains unevaluated.**

Η αιτία αποδείχθηκε με το μικρότερο μη κενό ASCII input, `"a"`, χωρίς φόρτωση νευρωνικού μοντέλου στο minimal reproducer. Πρόκειται για environment/API compatibility issue. Δεν προέκυψε εύρημα επίδοσης ή λόγος αλλαγής του research design. Η δοκιμή νέου περιβάλλοντος δεν τροποποιεί το παγωμένο πρωτόκολλο και δεν επιτρέπει εκτέλεση E6-v4.

## 1. Freeze και integrity πριν από αλλαγές

Branch: `agentic-rag-e7`. Πριν δημιουργηθεί ο παρών υποφάκελος επαληθεύτηκαν 1784/1784 protected hashes και 108/108 αρχεία του blocked-state manifest. Επαληθεύτηκε το αποθηκευμένο E6-v3 ανά canonical ID, fold, ανθρώπινη ετικέτα/target και OOF prediction: **474/561, accuracy 0.8449197861, Spearman 0.7816945786**, χωρίς baseline fits. Το αποτέλεσμα επαναλήφθηκε ως read-only έλεγχος των αποθηκευμένων προβλέψεων.

Αρχικά hashes (ίδια στον τελικό έλεγχο):

- `E6_V4_PROTOCOL.md`: `4b349aaf37ef664eecbfb2e9979e0e02aada8bb06b064c96d41e8e0b29cd7ae8`
- `config/run_config.json`: `07f92a980fdc6cbfb6b676f858ee2ba11f30656deeaf3eff3965295ffaedf32a`
- `E6_V4_RESULTS.md`: `8a77e55fe64ca9d1d11d153dd4d2a94b1435c0869e9bf603c477b77e0959ce27`
- `config/blocked_state_manifest.json`: `9d529b798461e48fac2810d595bb1795a950935fabea5c232ee01212364e9d89`

## 2. Exact failure

Exception: **`builtins.OverflowError: int too big to convert`**.

Model/tokenizer: `microsoft/deberta-large-mnli`, pinned revision `7296194b9009373def4f7c5dad292651e4b5cf4e`. Tokenizer class `DebertaTokenizer`, module `transformers.models.deberta.tokenization_deberta`. Στο transformers 5.5.4 κληρονομεί από `TokenizersBackend`, ακόμη και όταν ζητείται `use_fast=False`.

Python και στα δύο περιβάλλοντα: **3.11.9**. Δεν μεταβλήθηκε η κοινή εγκατάσταση.

| Package | Αρχικό περιβάλλον | Isolated test |
|---|---|---|
| bert-score | 0.3.13 | 0.3.13 |
| transformers | 5.5.4 | 4.30.2 |
| tokenizers | 0.22.2 | 0.13.3 |
| torch | 2.11.0 | 2.11.0 |
| huggingface-hub | 1.11.0 | 0.25.2 |

Το wheel metadata δηλώνει bert-score 0.3.13, αλλά το ίδιο επίσημο wheel περιέχει εσωτερικό `__version__=0.3.12`. Διατηρήθηκε ατροποποίητο. Αυτό εξηγεί την έκδοση στο hash string, όχι το OverflowError.

Το `sys.settrace` κατέγραψε την πραγματική κλήση χωρίς αλλαγή arguments:

```python
tokenizer.encode('a', add_special_tokens=True,
    max_length=1000000000000000019884624838656,
    truncation=True, padding=False, stride=0)
```

`text_pair=None`, effective truncation `LONGEST_FIRST`, effective padding `DO_NOT_PAD`. Input: 1 χαρακτήρας / 1 UTF-8 byte. Ο έλεγχος χωρίς truncation δίνει `[1,102,2]`: ένα content token και δύο special tokens. Δεν είναι υπέρβαση μήκους του input.

Πλήρες relevant traceback της νέας αναπαραγωγής:

```text
Traceback (most recent call last):
  File "RAG\results\rag_e6_v4\compatibility_analysis\reproduce_minimal.py", line 32, in <module>
    ids=sent_encode(tok,'a')
        ^^^^^^^^^^^^^^^^^^^^
  File "RAG\results\rag_e6_v4\packages\bert_score\utils.py", line 224, in sent_encode
    return tokenizer.encode(
           ^^^^^^^^^^^^^^^^^
  File "external-artifacts/local-925d92b5d1ab/tokenization_utils_base.py", line 2264, in encode
    encoded_inputs = self._encode_plus(
                     ^^^^^^^^^^^^^^^^^^
  File "external-artifacts/local-f0e526facbee/tokenization_utils_tokenizers.py", line 942, in _encode_plus
    self.set_truncation_and_padding(
  File "external-artifacts/local-f0e526facbee/tokenization_utils_tokenizers.py", line 839, in set_truncation_and_padding
    self._tokenizer.enable_truncation(**target)
OverflowError: int too big to convert
```

Οι line numbers αφορούν τα ακριβή τοπικά installed sources, όχι διαφορετική online έκδοση: BERTScore `utils.py:224` (argument στο 227), transformers `tokenization_utils_base.py:2264`, `tokenization_utils_tokenizers.py:942` και `:839`. Το τελευταίο καλεί το compiled tokenizers backend· δεν υπάρχει βαθύτερο Python source frame. Τα source hashes, signatures, περιεχόμενα συναρτήσεων και πλήρη arguments αποθηκεύτηκαν στο `minimal_current.json`. Το προηγούμενο traceback ολόκληρης BERTScorer.score διατηρείται στο `../provenance/compatibility.json`.

## 3. Αιτιώδης έλεγχος A–E

| Υπόθεση | Παρατήρηση / συμπέρασμα |
|---|---|
| A — sentinel | Επιβεβαιώθηκε. Το μη καθορισμένο όριο `int(1e30)` περνά στο backend truncation. Το checkpoint tokenizer_config δεν ορίζει μέγιστο μήκος. |
| B — package compatibility | Επιβεβαιώθηκε για τον δοκιμασμένο συνδυασμό. Το ίδιο unmodified BERTScore και τα ίδια cached assets περνούν με 4.30.2/0.13.3/0.25.2. |
| C — padding/truncation | Με sentinel και truncation=True αποτυγχάνει τόσο padding=False όσο και padding=True. Με το ίδιο sentinel, padding=False και truncation=False περνά. Το padding δεν είναι η αιτία. Το truncation=False χρησιμοποιήθηκε μόνο ως διαγνωστικός έλεγχος, όχι ως metric fix. |
| D — model/tokenizer mismatch | Δεν υποστηρίζεται: ίδια pinned assets, hashes και tokenizer vocabulary. Η αποτυχία αναπαράγεται χωρίς model loading. Στο πλήρες isolated test επιβεβαιώθηκε το model commit και το όριο 512. |
| E — άλλο API regression | Αλλαγή backend και απουσία παλαιάς model-ID mapping εξηγούν το φαινόμενο. Δεν έγινε version bisect για την πρώτη προβληματική έκδοση· δεν αποδίδεται αποκλειστικά σε μία συγκεκριμένη release ή στο tokenizers μόνο. |

Στον [επίσημο DebertaTokenizer 4.30.2](https://github.com/huggingface/transformers/blob/v4.30.2/src/transformers/models/deberta/tokenization_deberta.py) υπάρχει mapping του συγκεκριμένου model ID σε 512. Ο [επίσημος loader 4.30.2](https://github.com/huggingface/transformers/blob/v4.30.2/src/transformers/tokenization_utils_base.py) εφαρμόζει αυτή την τιμή κατά from_pretrained. Στο isolated test παρατηρήθηκε αυτόματα 512, χωρίς override. Το `model_max_position_embeddings=512` συμφωνεί. Δεν αρκεί αόριστο pin `transformers<5`: η mapping απουσιάζει ήδη από τον [κώδικα 4.44.2](https://github.com/huggingface/transformers/blob/v4.44.2/src/transformers/models/deberta/tokenization_deberta.py), και διαφορετικές εκδόσεις μπορεί να έχουν διαφορετικό χειρισμό.

## 4. Official BERTScore contract

Χρησιμοποιείται αποκλειστικά η επίσημη `bert_score.BERTScorer(...).score(cands=..., refs=...)` του ατροποποίητου wheel 0.3.13. Model όπως παραπάνω, `num_layers=None` που επιλύεται από `model2layers` σε **18**, `all_layers=False`, `idf=False`, `idf_sents=None`, `rescale_with_baseline=False`, `lang=None` και ρητό model_type, `use_fast_tokenizer=False`. CPU float32, batch_size=2, nthreads=4 και τέσσερα torch intra/inter-op threads. Κανένα layer tuning.

Τα exact frozen strings περνούν στην API χωρίς πρόσθετη normalization. Η επίσημη υλοποίηση εσωτερικά εφαρμόζει `sent.strip()`, special tokens, truncation με tokenizer.model_max_length και κατόπιν dynamic batch padding στη δική της `padding` συνάρτηση. Precision: hyp covered by reference, recall: reference covered by hyp. Το BERTScore δεν συμπεραίνει όριο από το model config και δεν προστατεύει εδώ τη sentinel τιμή. Αυτό ελέγχθηκε στον [επίσημο κώδικα](https://github.com/Tiiiger/bert_score/blob/v0.3.13/bert_score/utils.py) και στο ακριβές τοπικό wheel.

Η BERTScorer.__init__/score της εγκατεστημένης 0.3.13 δεν εκθέτει argument `max_length` ούτε tokenizer injection. Συνεπώς, ένα υποτιθέμενο `scorer.score(..., max_length=512)` δεν είναι διαθέσιμη επίσημη λύση σε αυτό το contract. Δεν αντικαταστάθηκε το metric από sentence cosine, custom embeddings ή custom BERTScore.

## 5. Compatibility options — δύο επιλογές, καμία αλλαγή research design

| Επιλογή | Τι αλλάζει / ορισμός metric | Reproducibility / risk | Νέο environment | Protocol amendment |
|---|---|---|---|---|
| **1. Προτιμώμενη: ακριβές pin 4.30.2 / 0.13.3 / hub 0.25.2** | Μόνο τρεις runtime dependencies στο isolated test. Ίδιο official BERTScore, model, layer και IDF/rescale. Αποκαθίσταται το ιστορικό official slow tokenizer με αυτόματο 512. | PASS σε synthetic pairs. Νέο runtime/hash πρέπει να παγώσει. Δεν ισχυριζόμαστε bitwise ισότητα με το μη λειτουργικό 5.5.4, ούτε γενική επάρκεια για πραγματικό dataset. | Ναι, απομονωμένο extraction environment. | **Ναι**, πριν από οποιαδήποτε μελλοντική πραγματική εξαγωγή. Καταγραφή νέων pins, hash και tokenization provenance, ίδια RF βάση. |
| 2. Ρητό όριο tokenizer 512, μόνο ως τεκμηριωμένη μελλοντική adaptation | Θα διόρθωνε τον sentinel σε τιμή που τεκμηριώνουν checkpoint και historical mapping. Ο μαθηματικός τύπος P/R/F1 δεν αλλάζει, αλλά η truncation επηρεάζει το κείμενο που βαθμολογείται. Δεν υπάρχει αντίστοιχο public max_length argument στον BERTScorer 0.3.13. | **Δεν εφαρμόστηκε και δεν αποδείχθηκε απόλυτη ισοδυναμία.** Χρειάζονται tokenizer/output equivalence checks σε synthetic boundaries. Private attribute adaptation έχει μεγαλύτερο maintenance risk. | Όχι υποχρεωτικά, αλλά isolation ενδείκνυται. | **Ναι**, ρητή έγκριση και τεκμηρίωση πριν εφαρμογή. |

Δεν προτείνεται τρίτη αυθαίρετη λύση. Το 512 περιλαμβάνει special tokens: ένα μεμονωμένο input έχει έως 510 content tokens. Η υπάρχουσα επίσημη βιβλιοθήκη αναθέτει το όριο στον tokenizer· δεν το επιδιορθώνει από μόνη της. Απλή αφαίρεση truncation ή αλλαγή σε fast tokenizer δεν θεωρούνται αποδεδειγμένα ισοδύναμα fixes.

Η επιλογή 1 προτιμάται επειδή πέρασε την ακριβή official call χωρίς package patch, tokenizer mutation ή νέα weights. Το όριο που εφαρμόστηκε προήλθε από επίσημο versioned source. Η αλλαγή εξαρτήσεων απαιτεί amendment του παγωμένου runtime contract, ακόμη κι αν διατηρεί τη μεθοδολογική πρόθεση. **Δεν έγινε amendment τώρα.**

## 6. Safest isolated test — πραγματικά αποτελέσματα

Δημιουργήθηκε `env/` με ξεχωριστό interpreter/site-packages και τα τρία pins. Χρησιμοποιεί read-only κοινά system-site-packages για torch και άλλες υπάρχουσες εξαρτήσεις: είναι process/package isolation, όχι πλήρως hermetic environment. Οι ενεργές εκδόσεις αποτυπώνονται στο `official_pinned_test.json`. Η κοινή εγκατάσταση δεν τροποποιήθηκε.

Official call: μία `BERTScorer.score` με **δύο synthetic pairs**, χωρίς labels:

| Reference | Candidate | P | R | F1 |
|---|---|---:|---:|---:|
| `a` | `a` | 0.9999998808 | 0.9999998808 | 0.9999998808 |
| `A cat sleeps.` | `A cat.` | 0.8436069489 | 0.7194966674 | 0.7766246200 |

Όλες οι τιμές είναι finite. Τα input lengths με specials είναι 3/3 και 6/5. Model load 10.696s, synthetic scoring 0.924s. Αυτοί είναι χρόνοι compatibility test, όχι χρόνοι πλήρους εξαγωγής. Official hash: `microsoft/deberta-large-mnli_L18_no-idf_version=0.3.12(hug_trans=4.30.2)`. Προηγούμενο hash: `microsoft/deberta-large-mnli_L18_no-idf_version=0.3.12(hug_trans=5.5.4)`.

Χωριστός synthetic tokenizer-only boundary έλεγχος: 602 tokens χωρίς truncation → 512 μέσω official sent_encode. Δεν εκτελέστηκε το μεγάλο synthetic input στο model. Το warning 602>512 αφορά αυτή την καταμέτρηση, όχι failed scoring. Τα unused classifier/pooler weights στο console είναι αναμενόμενα κατά φόρτωση του official AutoModel encoder από MNLI checkpoint.

Οι λήψεις αφορούσαν μόνο dependency wheels και επίσημη τεκμηρίωση. Τα tests είχαν offline flags και socket block· μηδενικές απόπειρες δικτύου στο πλήρες synthetic test. Δεν λήφθηκαν μοντέλα, ορισμοί ή νέα SHROOM δεδομένα.

Wheel SHA-256:

- `huggingface_hub-0.25.2-py3-none-any.whl`: `1897caf88ce7f97fe0110603d8f66ac264e3ba6accdf30cd66cc0fed5282ad25`
- `tokenizers-0.13.3-cp311-cp311-win_amd64.whl`: `ecf182bf59bd541a8876deccf0360f5ae60496fd50b58510048020751cf1724c`
- `transformers-4.30.2-py3-none-any.whl`: `c332e3a3097f9ed89ce556b403251235931c00237b8bc2d7adaa19d226c13f1d`

## 7. Minimal reproducer και αναπαραγωγή του ασφαλούς test

Ο πυρήνας της αναπαραγωγής, με το επίσημο package στο sys.path και cached model ID δεσμευμένο στο pinned revision:

```python
from bert_score.utils import get_tokenizer, sent_encode
tokenizer = get_tokenizer('microsoft/deberta-large-mnli', use_fast=False)
sent_encode(tokenizer, 'a')
```

Το `reproduce_minimal.py` περιλαμβάνει offline guard, tracing, τρεις ελέγχους padding/truncation, versions και source hashes. Εκτελέστηκε μία φορά σε κάθε περιβάλλον. Αποθηκεύει exclusive JSON και συνεπώς αποτρέπει σιωπηρή αντικατάσταση προηγούμενων diagnostics. Το `test_official_pinned.py` περιλαμβάνει την ακριβή official scoring call και synthetic-only inputs, επίσης με exclusive output. Δεν χρειάζεται επανεκτέλεση: όλα τα πραγματικά outputs διατηρούνται.

## 8. Τελική κατάσταση, αρχεία και stop

- Diagnosis **PASS**· original compatibility **FAIL**· isolated synthetic official test **PASS**.
- Real SHROOM BERTScore features extracted = **0**. RF fits = **0**. E6-v4 evaluations = **0**.
- Baseline, 1784 protected files και όλα τα 108 pre-existing v4 manifest files **unchanged**. Πρωτόκολλο/config/results v4 διατηρούν τα αρχικά hashes.
- Μόνο ο νέος υποφάκελος `RAG/results/rag_e6_v4/compatibility_analysis/` δημιουργήθηκε. Δεν τροποποιήθηκαν προηγούμενα αρχεία, synthetic datasets, test data ή το research design. Δεν έγινε commit/push/tag.
- Νέα κύρια αρχεία: `E6_V4_COMPATIBILITY_ANALYSIS.md`, `initial_integrity.json`, `final_integrity.json`, `minimal_current.json`, `minimal_pinned.json`, `official_pinned_test.json`, `official_pinned_console.txt`, `package_provenance.json`, `official_sources.json`, `user_request.txt`, τρία scripts και `diagnosis_manifest.json`. Βοηθητικά: `wheels/`, `env/`, `tmp/`. Το τελικό manifest καταγράφει ακριβή paths/hashes κώδικα, installed packages, wheels και diagnostics· εξαιρούνται μόνο temp/cache αρχεία και το ίδιο το manifest.

Git status πριν/μετά (ίδιο, επειδή ολόκληρος ο v4 φάκελος ήταν ήδη untracked):

```text
?? "Augmentation Pipeline.txt"
?? RAG/results/rag_e6_v2/
?? RAG/results/rag_e6_v3/
?? RAG/results/rag_e6_v4/
?? RAG/results/rag_e7_agentic_v1/
?? RAG/results/rag_e8_rf_tuning_v1/
```

Δεν υπάρχει tracked diff. **STOP μετά τη διάγνωση.** Καμία πραγματική εξαγωγή ή αξιολόγηση δεν ξεκινά με την παρούσα άδεια.
