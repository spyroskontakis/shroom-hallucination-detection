# E6-v4 — τελικά αποτελέσματα

**PASS / COMPLETED. Μία προκαθορισμένη five-fold OOF αξιολόγηση, 561 δείγματα, 43 χαρακτηριστικά, ακριβώς 5 RF fits, 0 baseline fits. Adaptive exploratory development-only.**

| Έκδοση | Χαρακτηριστικά | Correct/N | Accuracy | Spearman |
|---|---:|---:|---:|---:|
| E6-v3 | 36 | 474/561 | 0.8449197861 | 0.7816945786 |
| E6-v4 | 43 | 468/561 | 0.8342245989 | 0.7820211175 |

Δ accuracy = **-0.0106951872**, δηλαδή **-1.069519 ποσοστιαίες μονάδες**, net correct **-6/561**.

## Phase 1 — initial compatibility failure

Η αρχική official BERTScore προσπάθεια σταμάτησε πριν από πραγματικά features, RF fits ή αξιολόγηση με `OverflowError: int too big to convert`. Το ακριβές αρχικό report διατηρείται στο `execution/E6_V4_RESULTS_PHASE1_ARCHIVE.md` με το αρχικό SHA-256 `8a77e55fe64ca9d1d11d153dd4d2a94b1435c0869e9bf603c477b77e0959ce27`. Το αρχικό `E6_V4_PROTOCOL.md`, `config/run_config.json`, traceback και blocked-state manifest δεν ξαναγράφηκαν.

## Phase 2 — diagnosis

Το σφάλμα αναπαράχθηκε με το συνθετικό `a`. Η sentinel τιμή tokenizer.model_max_length περνούσε στο truncation backend του transformers 5.5.4/tokenizers 0.22.2. Το πρόβλημα ήταν environment compatibility. Η πλήρης διάγνωση και το ανεξάρτητο synthetic test διατηρούνται στο `compatibility_analysis/E6_V4_COMPATIBILITY_ANALYSIS.md`. Δεν προέκυψε E6-v4 score σε αυτή τη φάση.

## Phase 3 — amendment και pinned environment

Το νέο `E6_V4_PROTOCOL_AMENDMENT_01.md` αποθηκεύτηκε πριν από πραγματική εξαγωγή, fitting ή evaluation. SHA-256: **`562023f2e837393eaad00156997946e592b04c9f4d711e1bf703c6b3c6ce288e`**. Επιλέχθηκε μόνο environment pinning, χωρίς custom BERTScore ή manual tokenizer max_length override.

Encoding: Python 3.11.9, official bert-score distribution 0.3.13 (upstream internal version 0.3.12), transformers 4.30.2, tokenizers 0.13.3, huggingface-hub 0.25.2, torch 2.11.0. Χρησιμοποιήθηκε το υπάρχον isolated venv με system-site-packages για αμετάβλητες κοινές εξαρτήσεις. Ο venv δεν προστέθηκε στο Git. RF evaluation: το αρχικό shroom_ensemble runtime με scikit-learn 1.8.0, numpy 2.4.4, scipy 1.17.1, pandas 3.0.2 και την πλήρη configuration E6-v3.

Model/tokenizer: `microsoft/deberta-large-mnli@7296194b9009373def4f7c5dad292651e4b5cf4e`, το ίδιο pinned E3 checkpoint. Official mapping num_layers=18, idf=False, rescale_with_baseline=False, all_layers=False, use_fast_tokenizer=False, lang=None. Hash: `microsoft/deberta-large-mnli_L18_no-idf_version=0.3.12(hug_trans=4.30.2)`. CPU float32, batch=2, torch threads4/4. Το 512 προήλθε αυτόματα από την επίσημη mapping του tokenizer. Όλα τα assets υπήρχαν ήδη τοπικά· δεν έγινε λήψη μοντέλου.

Επαναλήφθηκαν έξι synthetic cases (identity, omission, addition, number change, negation added/removed). **PASS** για finite P/R/F1, κατεύθυνση precision/recall και deterministic structural contracts. Μηδενικές απόπειρες δικτύου, κανένα override. Τα αποτελέσματα και οι ακριβείς τιμές βρίσκονται στο `execution/synthetic_contract.json`.

Το pre-extraction manifest `execution/run_config.json` πάγωσε protocol/amendment/report hashes, πακέτα, model provenance, inputs/IDs/folds, schema, πλήρη RF configuration, extraction/evaluator/reporter source hashes. Οι σφραγισμένες ρυθμίσεις δεν άλλαξαν μετά το score.

## Phase 4 — final frozen E6-v4 execution

Ακριβώς 561 canonical rows (493 development_model_agnostic + 68 trial, η ήδη εγκεκριμένη canonical development δεξαμενή), ίδιοι locked folds, ίδια σειρά 36 αρχικών χαρακτηριστικών με αριθμητική ισότητα και επτά νέες στήλες. Reference=tgt για DM/MT, src για PG, candidate=hyp. Τα exact saved label-free strings πέρασαν στην επίσημη API με την κανονική εσωτερική strip/tokenization. Το unchanged structure.py εφαρμόστηκε αποκλειστικά στους τέσσερις deterministic δείκτες.

Η εξαγωγή δεν διάβασε labels ή OOF predictions ως inputs. Η μήτρα πάγωσε πριν γίνει join των ανθρώπινων targets για RF/evaluation. Βασικό baseline ελέγχθηκε ξανά ανά ID/fold και αναπαρήγαγε ακριβώς 474/561 και το καταγεγραμμένο Spearman, χωρίς fit.

Missing values=0, invalid values=0, NaN/Inf=0. Truncated references=0, hypotheses=0; empty references=0, hypotheses=0. Οι original/used token lengths ανά ID και πλευρά αποθηκεύτηκαν στο `features/truncation_audit.csv`. Επαληθεύτηκε used=min(original,512).

Πλήρης εξαγωγή και συμβόλαια: **295.188s**, περιλαμβάνει model load **9.490s**. RF/evaluation διαδικασία: **10.025s**. Οι χρόνοι δεν περιλαμβάνουν προηγούμενη διάγνωση ή ανθρώπινο χρόνο συγγραφής. 561/561 σειρές υπολογίστηκαν μία φορά και αποθηκεύτηκαν σε fixed chunks. Μία configuration, πέντε outer-fold RF fits, prediction clip [0,1], binary>=0.5. Δεν έγινε tuning ή δεύτερη variant.

| Νέο χαρακτηριστικό | Min | Max | Mean |
|---|---:|---:|---:|
| bertscore_ref_hyp_precision | 0.3054393828 | 1.0000000000 | 0.7280997422 |
| bertscore_ref_hyp_recall | 0.3444043994 | 1.0000001192 | 0.7329606282 |
| bertscore_ref_hyp_f1 | 0.3666705191 | 1.0000001192 | 0.7272025476 |
| structure_length_ratio | 0.0000000000 | 1.0000000000 | 0.7093755255 |
| structure_number_presence_mismatch | 0.0000000000 | 1.0000000000 | 0.0089126560 |
| structure_number_set_mismatch | 0.0000000000 | 1.0000000000 | 0.0089126560 |
| structure_negation_mismatch | 0.0000000000 | 1.0000000000 | 0.0695187166 |

## Ανά fold, task και evidence

| Ομάδα | N | v3 correct | v4 correct | v3 accuracy | v4 accuracy | v3 Spearman | v4 Spearman |
|---|---:|---:|---:|---:|---:|---:|---:|
| Fold 1 | 113 | 100 | 98 | 0.8849557522 | 0.8672566372 | 0.8161783605 | 0.8119182252 |
| Fold 2 | 112 | 91 | 90 | 0.8125000000 | 0.8035714286 | 0.7693547089 | 0.7779608527 |
| Fold 3 | 112 | 93 | 93 | 0.8303571429 | 0.8303571429 | 0.7703346139 | 0.7738754756 |
| Fold 4 | 112 | 92 | 91 | 0.8214285714 | 0.8125000000 | 0.7792654109 | 0.7798845702 |
| Fold 5 | 112 | 98 | 96 | 0.8750000000 | 0.8571428571 | 0.7840673179 | 0.7832118720 |
| DM | 211 | 169 | 166 | 0.8009478673 | 0.7867298578 | 0.6852178827 | 0.6865562590 |
| MT | 216 | 191 | 189 | 0.8842592593 | 0.8750000000 | 0.8327371481 | 0.8353706046 |
| PG | 134 | 114 | 113 | 0.8507462687 | 0.8432835821 | 0.7522106511 | 0.7485306917 |
| Evidence 0 | 368 | 317 | 314 | 0.8614130435 | 0.8532608696 | 0.8119705384 | 0.8129307917 |
| Evidence 1 | 193 | 157 | 154 | 0.8134715026 | 0.7979274611 | 0.6941425689 | 0.6948697844 |
| DM evidence 0 | 18 | 12 | 12 | 0.6666666667 | 0.6666666667 | 0.6056338446 | 0.5454925046 |
| DM evidence 1 | 193 | 157 | 154 | 0.8134715026 | 0.7979274611 | 0.6941425689 | 0.6948697844 |

Evidence 1=διαθέσιμος ορισμός, 0=χωρίς ορισμό. Οι εξωτερικοί ορισμοί αφορούν **αποκλειστικά DM** και εδώ χρησιμοποιούνται μόνο ως περιγραφική υποομάδα· δεν μπήκαν στα επτά νέα features. Το no-evidence σύνολο περιλαμβάνει επίσης MT/PG και δεν είναι αιτιώδης σύγκριση επίδρασης retrieval. Παρατίθεται επιπλέον DM-only διαχωρισμός.

## Paired diagnostics — descriptive exploratory statistics

**1 διορθώσεις**, **7 νέα λάθη**, net **-6**. Και τα δύο σωστά: 467. Και τα δύο λάθος: 86.

Exact two-sided McNemar: **p=0.0703125000**.

Paired-bootstrap 95% CI για accuracy(v4)-accuracy(v3): **[-0.0213903743, -0.0017825312]**, ή **[-2.139037, -0.178253] ποσοστιαίες μονάδες**.

Χρησιμοποιήθηκε ακριβώς η υπάρχουσα διαδικασία: binomtest(corrected, corrected+regressions,0.5), δύο όψεις· 10.000 paired resamples 561 κοινών row indices με numpy.default_rng(42), quantile 0.025/0.975. Το bootstrap αφορά παγωμένες OOF προβλέψεις και δεν επανεκπαιδεύει μοντέλα. Spearman: ανθρώπινο p_hallucination έναντι predictions rounded στα 12 δεκαδικά, accuracy με unrounded prediction>=0.5. Όλα τα IDs διορθώσεων/νέων λαθών βρίσκονται στο metrics JSON και οι 561 γραμμές στο paired_row_diagnostics.csv.

Το E6-v4 είχε χαμηλότερη accuracy από το E6-v3. Καταγράφεται το αρνητικό development-only αποτέλεσμα χωρίς redesign ή δεύτερο run. Η σύγκριση αφορά συνολικά τα επτά πρόσθετα χαρακτηριστικά και δεν απομονώνει τη συμβολή κάθε μέρους.

Η παρέμβαση επιλέχθηκε μετά την exploratory ανάλυση σφαλμάτων E6-v2/v3. **Adaptive exploratory development-only** σε επαναχρησιμοποιημένο σύνολο. McNemar και bootstrap είναι **descriptive exploratory statistics**, χωρίς ανεξάρτητη confirmatory ερμηνεία ή διόρθωση για την adaptive επιλογή. Δεν χρησιμοποιήθηκε official test. Δεν έγινε επόμενο πείραμα.

## Integrity, παραδοτέα και Git

Τελικό audit **PASS**: 1784/1784 προστατευμένα αρχεία, E6-v3, διάγνωση και αρχικό πρωτόκολλο/config ανέπαφα. Τα 108 παλαιά v4 hashes επαληθεύτηκαν πριν από την εξουσιοδοτημένη ενημέρωση της αναφοράς· ο μοναδικός παλαιός τροποποιημένος στόχος είναι το παρόν E6_V4_RESULTS.md, με byte-identical ιστορικό archive. Αμετάβλητα όλα τα υπόλοιπα 107. Network attempts=**0**, real feature rows=**561**, RF fits=**5**, baseline fits=**0**, OOF evaluations=**1**. Δεν έγινε official-test access, retrieval, API/LLM call, αλλαγή synthetic δεδομένων ή git add/commit/push/tag.

Νέα αρχεία: amendment, `execution/` κώδικας/config/manifests/smoke/cache/logs/audits και archive, `features/` επτά νέα features και πλήρης μήτρα 43, `evaluation/` 561 OOF predictions, fold caches, metrics και paired diagnostics. Τροποποιήθηκε μόνο η παρούσα τελική αναφορά. Τα ακριβή νέα paths/hashes καταγράφονται στο `execution/completion_manifest.json`. Ο venv της διάγνωσης επαναχρησιμοποιήθηκε χωρίς αλλαγή.

Branch `agentic-rag-e7`, git status:

```text
?? "Augmentation Pipeline.txt"
?? RAG/results/rag_e6_v2/
?? RAG/results/rag_e6_v3/
?? RAG/results/rag_e6_v4/
?? RAG/results/rag_e7_agentic_v1/
?? RAG/results/rag_e8_rf_tuning_v1/
```

Η ένδειξη Git παραμένει ίδια επειδή ο v4 φάκελος ήταν ήδη untracked. **STOP μετά το E6-v4.**
