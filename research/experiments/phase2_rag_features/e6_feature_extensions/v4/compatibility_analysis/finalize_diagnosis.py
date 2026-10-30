"""Read-only audits and diagnosis report; no inference or training."""
from pathlib import Path
import json,hashlib,subprocess,datetime,base64,csv,sys
HERE=Path(__file__).resolve().parent;V4=HERE.parent;ROOT=V4.parents[2]
def read(p):return json.loads(Path(p).read_text(encoding='utf-8'))
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def write(name,data):
 with (HERE/name).open('x',encoding='utf-8') as f:json.dump(data,f,indent=2,ensure_ascii=False)
start=read(HERE/'initial_integrity.json');cur=read(HERE/'minimal_current.json');pin=read(HERE/'minimal_pinned.json');test=read(HERE/'official_pinned_test.json')
assert cur['status']=='REPRODUCED' and pin['status']=='NO_EXCEPTION' and test['status']=='PASS'
protected=read(V4/'config/input_manifest.json')['protected_sha256']
for n,h in protected.items():assert sha(ROOT/n)==h,n
blocked=read(V4/'config/blocked_state_manifest.json')
for n,h in blocked['files'].items():assert sha(V4/n)==h,n
for n,h in start['v4_preexisting_hashes'].items():assert sha(V4/n)==h,n
assert not (V4/'features').exists() and not (V4/'evaluation').exists()
baseline=read(V4/'config/baseline_verification.json')['metrics'];assert baseline=={k:v for k,v in start['baseline'].items() if k!='fits'}
for key in ['sources']:
 for value in cur[key].values():assert sha(value['path'])==value['sha256']
record_counts={}
for record in (HERE/'env/Lib/site-packages').glob('*.dist-info/RECORD'):
 count=0
 with record.open(newline='',encoding='utf-8') as f:
  for name,digest,size in csv.reader(f):
   if not digest:continue
   path=record.parent.parent/name
   # pip --target places generated entrypoints under target/bin, while RECORD
   # retains the install-scheme ../../bin path. Validate the relocated file.
   if not path.exists() and name.startswith('../../bin/'):
    path=record.parent.parent/'bin'/Path(name).name
   assert sha(path)==base64.urlsafe_b64decode(digest.split('=',1)[1]+'==').hex(),name
   assert path.stat().st_size==int(size);count+=1
 record_counts[record.parent.name]=count
wheel_hashes={p.name:sha(p) for p in (HERE/'wheels').glob('*.whl')}
write('package_provenance.json',{'wheels':wheel_hashes,'record_entries_verified':record_counts,
 'isolation':'venv with system-site-packages; three pinned packages installed locally, shared dependencies read from unchanged base environment',
 'package_acquisition':'pip download --no-deps; pip install --no-index --no-deps --no-compile --target env/Lib/site-packages',
 'shared_environment_modified':False,'official_bert_score_package':str(V4/'packages'),
 'official_bert_score_wheel_sha256':sha(V4/'provenance/bert_score-0.3.13-py3-none-any.whl')})
request=Path(__import__('os').environ['SHROOM_DIAGNOSTIC_REQUEST'])
with (HERE/'user_request.txt').open('xb') as f:f.write(request.read_bytes())
sources=[
 {'title':'Official BERTScore v0.3.13 tokenization and model mapping','url':'https://github.com/Tiiiger/bert_score/blob/v0.3.13/bert_score/utils.py'},
 {'title':'Transformers v4.30.2 DebertaTokenizer official 512 mapping','url':'https://github.com/huggingface/transformers/blob/v4.30.2/src/transformers/models/deberta/tokenization_deberta.py'},
 {'title':'Transformers v4.30.2 pretrained maximum-length resolution','url':'https://github.com/huggingface/transformers/blob/v4.30.2/src/transformers/tokenization_utils_base.py'},
 {'title':'Transformers v4.44.2 tokenizer source (mapping already absent)','url':'https://github.com/huggingface/transformers/blob/v4.44.2/src/transformers/models/deberta/tokenization_deberta.py'}]
write('official_sources.json',sources)
status=subprocess.check_output(['git','status','--short'],cwd=ROOT,text=True)
branch=subprocess.check_output(['git','branch','--show-current'],cwd=ROOT,text=True).strip()
assert status==start['git_status'] and branch==start['branch']
assert subprocess.check_output(['git','diff','--stat'],cwd=ROOT,text=True)==''
audit={'status':'PASS','checked_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
 'protected_unchanged':len(protected),'preexisting_v4_manifest_files_unchanged':len(blocked['files']),
 'protocol_configuration_unchanged':True,'baseline':baseline,'branch':branch,'git_status':status,
 'real_features_extracted':0,'rf_fits':0,'e6_v4_evaluations':0,'synthetic_official_score_calls':1,
 'synthetic_scored_pairs':2,'official_package_record_checks':record_counts}
write('final_integrity.json',audit)
scores='\n'.join(f"| `{r['reference']}` | `{r['candidate']}` | {r['P']:.10f} | {r['R']:.10f} | {r['F1']:.10f} |" for r in test['synthetic_scores'])
versions='\n'.join(f"| {n} | {cur['versions'][n]} | {pin['versions'][n]} |" for n in cur['versions'])
hashlines='\n'.join(f'- `{n}`: `{h}`' for n,h in start['v4_preexisting_hashes'].items())
wheel_lines='\n'.join(f'- `{n}`: `{h}`' for n,h in wheel_hashes.items())
report=f'''# E6-v4 — diagnosis and compatibility analysis

**Diagnosis: PASS. Original environment compatibility: FAIL. Isolated synthetic compatibility test: PASS. E6-v4 remains unevaluated.**

Η αιτία αποδείχθηκε με το μικρότερο μη κενό ASCII input, `"a"`, χωρίς φόρτωση νευρωνικού μοντέλου στο minimal reproducer. Πρόκειται για environment/API compatibility issue. Δεν προέκυψε εύρημα επίδοσης ή λόγος αλλαγής του research design. Η δοκιμή νέου περιβάλλοντος δεν τροποποιεί το παγωμένο πρωτόκολλο και δεν επιτρέπει εκτέλεση E6-v4.

## 1. Freeze και integrity πριν από αλλαγές

Branch: `{branch}`. Πριν δημιουργηθεί ο παρών υποφάκελος επαληθεύτηκαν 1784/1784 protected hashes και 108/108 αρχεία του blocked-state manifest. Επαληθεύτηκε το αποθηκευμένο E6-v3 ανά canonical ID, fold, ανθρώπινη ετικέτα/target και OOF prediction: **474/561, accuracy 0.8449197861, Spearman 0.7816945786**, χωρίς baseline fits. Το αποτέλεσμα επαναλήφθηκε ως read-only έλεγχος των αποθηκευμένων προβλέψεων.

Αρχικά hashes (ίδια στον τελικό έλεγχο):

{hashlines}

## 2. Exact failure

Exception: **`builtins.OverflowError: int too big to convert`**.

Model/tokenizer: `microsoft/deberta-large-mnli`, pinned revision `7296194b9009373def4f7c5dad292651e4b5cf4e`. Tokenizer class `DebertaTokenizer`, module `transformers.models.deberta.tokenization_deberta`. Στο transformers 5.5.4 κληρονομεί από `TokenizersBackend`, ακόμη και όταν ζητείται `use_fast=False`.

Python και στα δύο περιβάλλοντα: **3.11.9**. Δεν μεταβλήθηκε η κοινή εγκατάσταση.

| Package | Αρχικό περιβάλλον | Isolated test |
|---|---|---|
{versions}

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
{cur['traceback'].rstrip()}
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
{scores}

Όλες οι τιμές είναι finite. Τα input lengths με specials είναι 3/3 και 6/5. Model load {test['load_seconds']:.3f}s, synthetic scoring {test['score_seconds']:.3f}s. Αυτοί είναι χρόνοι compatibility test, όχι χρόνοι πλήρους εξαγωγής. Official hash: `{test['hash_string']}`. Προηγούμενο hash: `microsoft/deberta-large-mnli_L18_no-idf_version=0.3.12(hug_trans=5.5.4)`.

Χωριστός synthetic tokenizer-only boundary έλεγχος: 602 tokens χωρίς truncation → 512 μέσω official sent_encode. Δεν εκτελέστηκε το μεγάλο synthetic input στο model. Το warning 602>512 αφορά αυτή την καταμέτρηση, όχι failed scoring. Τα unused classifier/pooler weights στο console είναι αναμενόμενα κατά φόρτωση του official AutoModel encoder από MNLI checkpoint.

Οι λήψεις αφορούσαν μόνο dependency wheels και επίσημη τεκμηρίωση. Τα tests είχαν offline flags και socket block· μηδενικές απόπειρες δικτύου στο πλήρες synthetic test. Δεν λήφθηκαν μοντέλα, ορισμοί ή νέα SHROOM δεδομένα.

Wheel SHA-256:

{wheel_lines}

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
{status.rstrip()}
```

Δεν υπάρχει tracked diff. **STOP μετά τη διάγνωση.** Καμία πραγματική εξαγωγή ή αξιολόγηση δεν ξεκινά με την παρούσα άδεια.
'''
with (HERE/'E6_V4_COMPATIBILITY_ANALYSIS.md').open('x',encoding='utf-8') as f:f.write(report)
files={}
for p in HERE.rglob('*'):
 if p.is_file() and 'tmp' not in p.relative_to(HERE).parts and '__pycache__' not in p.parts:
  files[p.relative_to(HERE).as_posix()]=sha(p)
write('diagnosis_manifest.json',{'status':'PASS','scope':'diagnosis only, not E6-v4 completion','files':files,
 'excluded':['tmp/','__pycache__/','diagnosis_manifest.json self-hash'],'created_utc':datetime.datetime.now(datetime.timezone.utc).isoformat()})
print(json.dumps({'diagnosis':'PASS','isolated_synthetic':'PASS','protected':len(protected),'old_v4_files':len(blocked['files']),'new_manifest_files':len(files),'RF_fits':0,'E6_v4_evaluations':0},indent=2))
