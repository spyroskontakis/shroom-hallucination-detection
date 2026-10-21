# SHROOM RAG — Αναφορά οργάνωσης και καθαρισμού

**Ημερομηνία:** 2026-09-09  
**Πεδίο αλλαγών:** μόνο `RAG`· έγινε μόνο στατική ανάγνωση, χωρίς εκτέλεση notebook, training, retrieval, model inference ή LLM/API call.

## 1. Συμπέρασμα

Η ενεργή τελική υλοποίηση δεν είναι ένα μόνο notebook. Είναι μία αλυσίδα παγωμένων artifacts:

1. Το αρχικό E1–E4 βρίσκεται στο `RAG/shroom_ensemble.ipynb` και στα αποθηκευμένα αποτελέσματά του κάτω από `data/2. EDA/shroom_final_implementation/`.
2. Τα Modules 1–2 υλοποιούνται από τα πέντε `shroom_rag_e5_module*.ipynb`, το `RAG/scripts/module2_dense_cache.py` και τα artifacts `RAG/results/rag_module1` και `RAG/results/rag_module2`.
3. Το Module 3 είναι διαγνωστικός, ολοκληρωμένος κλάδος στο `RAG/results/rag_module3`. Δεν παρήγαγε τελική E5 σύντηξη και διατηρείται ολόκληρος ως επιστημονικό ιστορικό.
4. Η τελική σύγκριση E3–E5 του Module 4 βρίσκεται στο `RAG/results/rag_module4/continuation_v1/schannel_run_v1`, με pinned replay/provenance στο `continuation_v1/mpnet_provenance_v2` και release index στο `RAG/module4_release_v1`.

Η αρχική επιλογή E3 και η μεταγενέστερη Module 4 σύγκριση χρησιμοποιούν **διαφορετικούς πληθυσμούς**. Το E5 έχει μικρό development-only αριθμητικό κέρδος (+1/561), αλλά το αποθηκευμένο McNemar p-value είναι 1,0 και το paired-bootstrap 95% interval περιλαμβάνει το μηδέν. Συνεπώς το E5 δεν αντικαθιστά τεκμηριωμένα το E3 ως τελικό γενικεύσιμο μοντέλο.

## 2. Git και προστασία υπαρχουσών αλλαγών

Το project root είναι Git repository στη branch `shroom2024-current`, με upstream `origin/shroom2024-current`. Κατά την αρχική αποτύπωση υπήρχαν μη παρακολουθούμενα αρχεία/δέντρα, μεταξύ άλλων τα Module 1/2 reports, `module4_release_v1`, `mpnet_provenance_v2`, `module2_dense_cache.py` και `thesis_revision_module4`. Θεωρήθηκαν αλλαγές του χρήστη και διατηρήθηκαν.

Το `RAG` είχε 31 tracked paths. Δεν τροποποιήθηκε κανένα προϋπάρχον tracked αρχείο. Δεν έγινε `reset`, checkout, commit ή αλλαγή αρχείου εκτός `RAG`. Η μοναδική εγγραφή εκτός `RAG` είναι το ρητά τεκμηριωμένο backup των έξι αρχείων που αφαιρέθηκαν.

## 3. Χαρτογράφηση αρχείων

Μετά το cleanup το `RAG` περιέχει 1.062 αρχεία: 612 εκτός `.venv` και 450 μέσα στο τοπικό environment. Η απογραφή κάλυψε 7 notebooks (6 μοναδικά root notebooks και 1 hash-identical delivery copy), 20 Python source files, 38 NPZ dense-cache chunks, 27 CSV, 13 JSONL, 416 JSON, 42 Markdown reports και τα υπόλοιπα requirements, figures, documents και delivery artifacts.

### Notebooks

| Notebook | Ρόλος | Κύριες είσοδοι | Παραγόμενα/χρησιμοποιούμενα artifacts |
|---|---|---|---|
| `shroom_ensemble.ipynb` | Αρχικό E1–E4 ablation | development JSON, augmented 14-feature dataset | NLI/similarity features, κοινά folds στη μνήμη, E1–E4 CV και OOF CSV |
| `shroom_rag_e5_module1.ipynb` | Module 1 exact lexical prototype | unlabeled train model-agnostic, 499-row development | deterministic 20-DM sample· προαιρετικό append-only Module 1 cache |
| `shroom_rag_e5_module1_gemini_trial.ipynb` | Κλειδωμένο 3+3 smoke test | ίδιες είσοδοι Module 1 | `results/rag_module1/module1_gemini_cache.jsonl` |
| `shroom_rag_e5_module2_retrieval.ipynb` | Module 2 Phase A retrieval | train/development, Module 1 notebook/cache, dense cache | input manifest, top-5 candidates, blank relevance annotations, Phase A report |
| `shroom_rag_e5_module2_phase_b_evaluation.ipynb` | Module 2 Phase B | candidates, provenance, blinded/human annotations | retrieval metrics, gate sensitivity, decisions, selected config, report |
| `shroom_rag_e5_module2_holdout_evaluation.ipynb` | Frozen holdout αξιολόγηση | blinded/human holdout, frozen manifest, selected config | holdout metrics, unblinded decisions, report |

Το `RAG/v2 sent/shroom_ensemble.ipynb` είναι hash-identical αντίγραφο παράδοσης του αρχικού notebook, όχι ενεργό διαφορετικό experiment. Διατηρήθηκε επειδή ο γειτονικός φάκελος είναι αυτοτελές delivery bundle και η αφαίρεσή του θα αλλοίωνε το πακέτο παράδοσης.

### Scripts και configurations

- `RAG/scripts/module2_dense_cache.py`: δημιουργία/επικύρωση chunked dense embedding cache και manifest για το Module 2.
- `RAG/scripts/module4_build_external_lexicon.py`: frozen external lexical parser (`module4-external-parser-v1`) και κατασκευή label-free 561-row inputs/snapshot.
- `RAG/results/rag_module4/continuation_v1/scripts/module4_build_wiktionary_lexicon.py`: orchestration της τελικής Wiktionary-only απόκλισης.
- `.../scripts/module4_build_rag_features.py`: παραγωγή των επτά RAG features για 561 μοναδικά IDs.
- `.../schannel_run_v1/scripts/module4_schannel_acquire.py`: τελική ασφαλής λήψη και snapshot/provenance.
- `.../schannel_run_v1/scripts/module4_evaluate_fusion.py`: frozen E3 reproduction και μοναδική E5 σύγκριση.
- `.../schannel_run_v1/scripts/module4_exact_overlap_audit.py` και `module4_finalize_diagnostics.py`: exact-overlap και paired/fold diagnostics.
- `RAG/results/rag_module4/continuation_v1/mpnet_provenance_v2`: pinned MPNet/NLI scripts, tests, runtime provenance και byte-identical replay outputs.
- `RAG/module4_release_v1/verify_module4.py` και `RELEASE_MANIFEST.json`: read-only verifier/index των source και accepted local artifacts.
- Τα τρία requirements files διατηρούνται ως ελάχιστες, module-specific dependency δηλώσεις. Η `.venv` δεν θεωρήθηκε canonical configuration και παραμένει αβέβαιη/τοπική.

### Δεδομένα και αποτελέσματα

| Οικογένεια | Περιεχόμενο | Απόφαση |
|---|---|---|
| `results/rag_module1` | append-only Gemini cache | Απαραίτητο ιστορικό και smoke-run evidence |
| `results/rag_module2/dense_cache` | 38 NPZ chunks + manifest | Απαραίτητο για αναπαραγωγή χωρίς νέο encoding |
| `results/rag_module2/annotation`, `evaluation`, `holdout` | blinded/completed annotations, provenance, config, decisions, metrics, reports | Απαραίτητα/αναπαραγωγή |
| `results/rag_module3` | phase plans, blinded/human/AI-independent annotations, source snapshots και αρνητικά/διαγνωστικά reports | Χρήσιμο ιστορικό· διατηρήθηκε στη θέση του |
| `results/rag_module4/static_protocol` | 561-row locked label-free inputs, parser spec, network failure log και manifests | Απαραίτητα/αναπαραγωγή |
| `results/rag_module4/continuation_v1/schannel_run_v1` | raw responses, lexical snapshot, term manifest, 7 features, fused 21 features, OOF predictions, metrics | Τελική Module 4 υλοποίηση |
| `results/rag_module4/continuation_v1/mpnet_provenance_v2` | accepted pinned features και ανεξάρτητο byte-identical replay | Απαραίτητο provenance· όχι περιττό παρά τα ίδια hashes |
| `figures` | EDA plots, περιλαμβανομένων development/trial/test-named figures | Ιστορική τεκμηρίωση· καμία μετακίνηση λόγω άγνωστων binary-document links |
| `thesis_revision_module4` και DOCX/PDF delivery copies | thesis drafts, changelogs και QA | Τεκμηρίωση· όχι ενεργός κώδικας, αλλά μοναδικό συγγραφικό ιστορικό |
| `cleanup_review` | παλαιότερο project-wide read-only audit και path-level inventory | Χρήσιμο ιστορικό audit· οι προτάσεις του δεν εφαρμόστηκαν αυτόματα |

## 4. Επαλήθευση τελικής υλοποίησης και αριθμών

### Αρχικό ablation — 499 γραμμές

- Πηγή: `Dev/SHROOM_dev-v2/val.model-agnostic.json`, SHA-256 `5ca9b6400b6dc1a86d69e1b8fa0d121275650f836fdba87fb23784d1d61ce611`.
- Το `shroom_ensemble.ipynb` περιέχει assertions για 499 development rows και πέντε common stratified folds.
- E3: 6 NLI + 8 similarity = 14 features.
- `data/2. EDA/shroom_final_implementation/e3_nli_similarity_dev_oof_predictions.csv`: 499 rows, **403 σωστές**.
- `.../e4_synthetic_dev_oof_predictions.csv`: 499 rows, **399 σωστές**.
- Τα counts επαληθεύτηκαν στατικά από `y_true_bin == y_pred_bin`, όχι από τίτλο ή timestamp notebook.

### Canonical/Module 4 — 561 γραμμές

- Η πηγή των 561 είναι: 80 trial + 499 model-agnostic development = 579 raw rows, αφαίρεση 18 exact text duplicates = **561** μοναδικές γραμμές (493 development + 68 trial).
- Η σύνθεση τεκμηριώνεται στα `codex/evaluation_protocol_decision.md`, `codex/evaluation_data_manifest.md` και `codex/canonical_human_development_manifest.csv`. Τα αρχεία είναι εκτός `RAG` και ελέγχθηκαν μόνο στατικά.
- Canonical manifest SHA-256: `754b66c6c4eca2e92902d0408db4854e922d7dfb396953a0cc043c5477bd6a9b`.
- Locked folds SHA-256: `f5a5964923806a23dd34a8bcc137f3cf489437e033d645e9d0845bf40792eb5d`.
- Canonical 14-feature matrix SHA-256: `3038bd8752a94064e05389e03b063484a1191f9e9a6164f06d11b40688a6828b`.
- E3: 445/561, accuracy 0,7932263815, Spearman 0,7390395613.
- E5: 446/561, accuracy 0,7950089127, Spearman 0,7421719692.
- E5 schema: τα ίδια 14 E3 features συν ακριβώς 7 features: evidence availability, sense count, top-1 retrieval cosine, max target-definition cosine, max entailment, max contradiction και max lexical overlap.
- Το accepted 7-feature CSV έχει SHA-256 `708483b831430d876135d1484ad841bf6ba0d9c9a2d0a5f22df6280535fe3160`. Το pinned replay είναι byte-identical.
- Τα OOF/metrics και το `module4_evaluate_fusion.py` συμφωνούν. Η E5 διόρθωσε 5 και εισήγαγε 4 σφάλματα· καθαρό +1. Το 95% paired-bootstrap interval είναι [-0,0089126560, 0,0124777184].

### Απόκλιση που πρέπει να διατηρείται ορατή

Το `RAG/AGENTS.md` και το αρχικό notebook ορίζουν 499 development δείγματα. Το μεταγενέστερο canonical Chapter 6/Module 4 πρωτόκολλο χρησιμοποιεί 561 γραμμές μετά από συγχώνευση trial και development και deduplication. Επομένως τα 403/499 και 445/561 δεν είναι αποτελέσματα στο ίδιο evaluation population. Η Module 4 αναπαραγωγή του E3 είναι εσωτερικά ακριβής για τις 561 γραμμές, αλλά δεν αποτελεί αναπαραγωγή του αρχικού 403/499 πάνω στο ίδιο δείγμα.

## 5. Ταξινόμηση και ενέργειες

### Απαραίτητα για την ενεργή υλοποίηση

Διατηρήθηκαν όλα τα notebooks/scripts/configurations που αναφέρονται στις ενότητες 3–4, όλα τα Module 1–4 manifests, οι locked IDs/folds, τα candidate/retrieval artifacts, οι αποθηκευμένοι ορισμοί και raw source responses, τα 14/7/21-feature matrices, οι OOF προβλέψεις, τα metrics και οι τελικές αναφορές.

### Χρήσιμο ιστορικό και πειραματική τεκμηρίωση

Διατηρήθηκαν τα Module 2 plans και sensitivity/holdout artifacts, ολόκληρο το Module 3, τα blocked TLS/WordNet attempts και μηδενικά network logs, exact-overlap audits, replay copies, thesis changelogs/QA, EDA figures και το παλαιότερο cleanup audit. Αρνητικό ή αποτυχημένο αποτέλεσμα δεν αντιμετωπίστηκε ως σκουπίδι.

### Επιβεβαιωμένα περιττά

Αφαιρέθηκαν μόνο έξι compiled Python caches (`.pyc`, συνολικά 106.228 bytes), επειδή αναγεννώνται από διατηρημένο source και δεν αναφέρονται από κώδικα ή manifest:

- `results/rag_module4/continuation_v1/schannel_run_v1/scripts/__pycache__/module4_schannel_acquire.cpython-312.pyc`
- `results/rag_module4/continuation_v1/scripts/__pycache__/module4_build_rag_features.cpython-311.pyc`
- `results/rag_module4/continuation_v1/scripts/__pycache__/module4_build_rag_features.cpython-312.pyc`
- `results/rag_module4/continuation_v1/scripts/__pycache__/module4_build_wiktionary_lexicon.cpython-312.pyc`
- `scripts/__pycache__/module4_build_external_lexicon.cpython-312.pyc`
- `tests/__pycache__/test_module4_external_lexicon.cpython-312.pyc`

Δεν διαγράφηκαν τα τέσσερα επιστημονικά exact-duplicate groups που βρέθηκαν εκτός `.venv`: δύο delivery copies (notebook/DOCX) και δύο τριπλά groups των accepted/replay Module 4 feature/overlap CSV. Οι διαδρομές τους έχουν διαφορετικό ρόλο και τα replay αντίγραφα αναφέρονται ρητά από το release manifest.

### Αβέβαια — παραμένουν στη θέση τους

- `RAG/.venv`: τοπικό environment χωρίς πλήρες authoritative lock. Δεν είναι μέρος της επιστημονικής αλυσίδας, αλλά δεν αφαιρέθηκε επειδή μπορεί να είναι το μόνο άμεσα λειτουργικό περιβάλλον.
- `RAG/tmp`: δεν μετακινήθηκε μαζικά, επειδή η απουσία στατικής reference δεν αποκλείει notebook/manual workflow χρήση.
- `RAG/v2 sent`, DOCX/PDF και thesis revisions: πιθανές παλαιότερες εκδόσεις, αλλά μοναδική τεκμηρίωση παράδοσης/συγγραφής.
- Figures με test-related ονόματα: εκτός ενεργού RAG pipeline, αλλά πιθανώς ενσωματωμένες σε binary έγγραφα και δεν εξετάστηκαν ως προς labels.
- Empty `network_attempts.jsonl`: παραμένει ως τεκμήριο ότι το pinned replay δεν έκανε network call.

Δεν έγινε φυσική αρχειοθέτηση χρήσιμου υλικού: τα published hashes, relative imports και manifest paths καθιστούν ασφαλέστερη τη λογική οργάνωση μέσω της παρούσας αναφοράς.

## 6. Backup και επαναφορά

Το επαληθευμένο backup βρίσκεται στο:

`.cleanup_backups\RAG_20260909T150000+0300\RAG`

Διατηρεί τις αρχικές σχετικές διαδρομές. Πριν από την αφαίρεση, κάθε source/backup pair συγκρίθηκε με SHA-256 και ήταν ταυτόσημο. Για πλήρη επαναφορά από PowerShell, από το project root:

```powershell
Copy-Item -LiteralPath '.cleanup_backups\RAG_20260909T150000+0300\RAG\*' -Destination 'RAG' -Recurse -Force
```

Η επαναφορά αφορά μόνο αναγεννώμενα `.pyc` και δεν απαιτείται για εκτέλεση: η Python μπορεί να τα δημιουργήσει ξανά από τα διατηρημένα `.py`.

## 7. Στατικός τελικός έλεγχος

Ο τελικός έλεγχος καλύπτει:

- ύπαρξη όλων των paths που δηλώνονται ως source/local artifacts στο `module4_release_v1/RELEASE_MANIFEST.json`·
- SHA-256 των locked 561-row inputs, canonical folds, 14-feature matrix, accepted 7-feature CSV, OOF predictions και metrics·
- παρουσία όλων των notebooks, scripts, annotation/provenance files και reports των Modules 1–4·
- μηδενικά εναπομείναντα `.pyc` εκτός `.venv`·
- Git diff ώστε να επιβεβαιωθεί ότι κανένα προϋπάρχον tracked πειραματικό αρχείο δεν άλλαξε.

Αποτέλεσμα τελικού ελέγχου: **PASS**. Επαληθεύτηκαν 19/19 source/local-artifact entries του release manifest ως προς path και SHA-256, 5/5 πρόσθετα κρίσιμα locked/canonical/OOF hashes, 0 εναπομείναντα `.pyc` εκτός `.venv`, 6/6 backup files (106.228 bytes) και κενό `git diff --name-only -- RAG` για τα προϋπάρχοντα tracked αρχεία. Το νέο report και τα ήδη υπάρχοντα user artifacts παραμένουν untracked· δεν έγινε αυτόματο `git add`.

Δεν εκτελέστηκαν tests που εισάγουν modules, επειδή ακόμη και import μπορεί να ξαναδημιουργήσει `__pycache__`. Δεν έγινε επιστημονικός επανυπολογισμός· ο έλεγχος είναι αποκλειστικά path/hash/static-content based.
