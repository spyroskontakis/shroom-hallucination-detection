# SHROOM RAG E5 — Module 4: RAG-Assisted Fusion

## Phase 0 — Static Feasibility and Preregistration

**Ημερομηνία παγώματος:** 2026-08-29  
**Scope:** αποκλειστικά static inspection, development-only, χωρίς feature/model/retrieval execution  
**Phase 0 verdict:** `MODULE4_FEASIBLE_PROCEED_TO_FEATURE_PREPARATION`

## 1. Ενιαίο E5 και ερευνητικό ερώτημα

Το E5 αντιμετωπίζεται ως ενιαίο ελεγχόμενο πείραμα. Τα Modules 1–3 εξέτασαν retrieval feasibility, κάλυψη training-derived και external knowledge bases, ανθρώπινη word-sense relevance και τη δυνατότητα εφαρμογής selective gate. Το Module 3 παραμένει οριστικά κλειστό με τις αποφάσεις:

```text
MODULE3_CLOSED_DIAGNOSTIC_ONLY
FINAL_GATED_RAG_NOT_EXECUTED_INCOMPATIBLE_FROZEN_GATE
NO_GO_FOR_GEMINI
E3_NLI_similarity_REMAINS_FINAL
```

Το νέο Module 4 δεν αναιρεί αυτές τις αποφάσεις. Το ερευνητικό του ερώτημα είναι αν frozen external lexical evidence μπορεί, ως πρόσθετο feature branch, να βελτιώσει το canonical development-only OOF score του `E3_NLI_similarity` χωρίς label leakage. Δεν αποτελεί Gemini experiment, νέο safety gate ή αναδρομική επανερμηνεία των Modules 1–3.

## 2. Phase 0 Canonical Resolution

Οι δύο αποκλίσεις εντοπίστηκαν από static inspection πριν από οποιοδήποτε Module 4 execution. Δεν είχαν δημιουργηθεί Module 4 features, predictions ή metrics. Η τιμή Spearman διορθώθηκε ώστε να συμφωνεί ακριβώς με το canonical E3 artifact:

```text
Exact Overall OOF Spearman: 0.7390395612811848
Displayed to six decimals: 0.739040
```

Η exact τιμή είναι η μοναδική τιμή που επιτρέπεται σε μελλοντικούς υπολογισμούς· η τιμή έξι δεκαδικών χρησιμοποιείται μόνο για παρουσίαση. Παράλληλα, το retrieval `top_k` διορθώθηκε σε `top_k = 5`, ώστε να συμφωνεί με τη frozen Phase 2B configuration. Δεν πραγματοποιήθηκε ablation, tuning ή post-hoc επιλογή βάσει αποτελεσμάτων.

Το αρχικό blocked plan διατηρείται στο ιστορικό με:

```text
Original blocked plan size: 18,917 bytes
Original blocked plan SHA-256: d332c5e38498867c87f8274b1a61008fa8ad2954ca50984a7c6646866ae7f81b
Original verdict: MODULE4_BLOCKED_BASELINE_SPEARMAN_AND_TOP_K_MISMATCH
```

Μετά τη ρητή canonical επίλυση, δεν παραμένει unresolved static compatibility blocker. Δεν υπολογίστηκε νέο score και δεν προεπιλέχθηκε θετικό πειραματικό αποτέλεσμα.

## 3. Static compatibility revalidation

| Check | Canonical value | Result |
|---|---|---|
| E3 Overall OOF Accuracy | `0.7932263814616756` | PASS |
| E3 Overall OOF Spearman | exact `0.7390395612811848`; display `0.739040` | PASS |
| Eligible development rows | 561/561 | PASS |
| Outer-fold assignments | 5/5 | PASS |
| E3 predictor features | 14/14 | PASS |
| Classifier | frozen canonical Random Forest configuration | PASS |
| External-source manifests and hashes | frozen WordNet 3.1/Wiktionary artifacts | PASS |
| Retrieval candidate limit | frozen `top_k=5` | PASS |
| Fixed Module 4 RAG feature schema | 7/7 frozen features | PASS |
| Unresolved compatibility blockers | 0 | PASS |

## 4. Canonical E3 baseline που επαληθεύτηκε

Η authoritative canonical branch που εντοπίστηκε είναι η development-only Prompt 7E/7E-A branch:

- development rows: 561/561 unique `canonical_id` και 561/561 unique `exact_text_key`·
- folds: πέντε locked outer folds, μεγέθη validation 113/561, 112/561, 112/561, 112/561 και 112/561·
- training rows ανά fold: 448/561 στο fold 1 και 449/561 στα folds 2–5·
- E3 predictor schema: 6 NLI + 8 semantic-similarity features, 14/14 συνολικά·
- classifier: `sklearn.ensemble.RandomForestRegressor`·
- parameters: `n_estimators=500`, `random_state=42`, `n_jobs=-1`, με τα υπόλοιπα parameters όπως καταγράφονται στο canonical metadata·
- regression target: `p_hallucination`· prediction clipping `[0,1]`· binary threshold `0.5`· calibration `none`·
- Overall OOF Accuracy: `0.7932263814616756`·
- Overall OOF Spearman: `0.7390395612811848` (exact canonical value; `0.739040` μόνο για παρουσίαση)·
- eligible development rows: 561·
- outer folds: 5/5·
- E3 features: 14/14·
- classifier: frozen canonical Random Forest configuration.

Τα 14 frozen E3 features είναι:

```text
src_ent
src_neu
src_con
tgt_ent
tgt_neu
tgt_con
sim_src_hyp
sim_tgt_hyp
sim_src_tgt
sim_max
sim_min
sim_mean
sim_gap_tgt_src
sim_hyp_distance_from_truth
```

Η παλαιότερη 499-row branch στο `data/2. EDA/shroom_final_implementation` δεν είναι συμβατή με το Accuracy `0.793226` του ζητήματος και δεν επιλέγεται ως Module 4 baseline. Το `RAG/AGENTS.md` εξακολουθεί να αναφέρει 499 development samples, αλλά τα νεότερα canonical Prompt 7E artifacts παγώνουν 561 rows. Η Module 4 branch χρησιμοποιεί αποκλειστικά τις 561 canonical rows και τα frozen folds.

## 5. Exact allowed inputs και SHA-256

Μόνο τα παρακάτω non-protected artifacts επιθεωρήθηκαν και επιτρέπονται ως Phase 0 reproducibility evidence ή μελλοντικά frozen inputs:

| Artifact | Bytes | SHA-256 | Ρόλος |
|---|---:|---|---|
| `RAG/AGENTS.md` | 3,244 | `8dc147df8c11ef967ccc5b9af44f68b9c76ac2c43b67186c021bb78523c83594` | project constraints |
| `RAG/MODULE2_FINAL_RESULTS.md` | 14,619 | `574a75f7e0a2bef4ad2ac1b4c68e2892e8356fd9134a885293549e2773c82d92` | Module 2 aggregate result |
| `RAG/results/rag_module3/MODULE3_FINAL_RESULTS.md` | 13,113 | `5fa251d03f9940d0749443346fc02de8370cd61a2825a8c6b4574d78dcee14e7` | Module 3 closure |
| `RAG/results/rag_module3/phase2b/MODULE3_PHASE2B_RESULTS.md` | 9,190 | `82701d12b8fd6d1a7645275b7f417df4a4bbd471e836239e053868c576decff4` | aggregate external-KB findings |
| `RAG/results/rag_module3/phase2b/MODULE3_PHASE2B_PLAN.md` | 13,297 | `966e0ce44296429c9d5b2f147b485a1a3e29d49693bdfa41b0f3fb5d327d7733` | frozen Phase 2B procedure |
| `RAG/results/rag_module3/phase2b/external_kb/MODULE3_PHASE2B_SOURCE_MANIFEST.json` | 16,758 | `9d91c599fabbd6782e92b13cb7f8fa6e2f984c464242b02a578792d1de893ece` | source/configuration manifest |
| `RAG/results/rag_module3/phase2b/external_kb/module3_phase2b_external_kb_snapshot.jsonl` | 39,483 | `87356e9c2d6ae8893767c55c66901ce9449f15605d5eb8b5c7c25b687ddd4825` | frozen lexical snapshot |
| `codex/canonical_development_cv.py` | 36,688 | `cde3f829ea68ee35ded568953b5d59ffabbd854a9da6e11d9436ed01403b49d2` | canonical E1–E4 CV implementation |
| `codex/canonical_feature_outputs/canonical_feature_extraction_metadata.json` | 7,295 | `a35217c423697064ac03b102ae7ab8983758355283081dc83d730203dbd2d446` | model/schema metadata |
| `codex/canonical_feature_outputs/canonical_human_14_features.csv` | 193,134 | `3038bd8752a94064e05389e03b063484a1191f9e9a6164f06d11b40688a6828b` | 561 canonical development rows and E3 features |
| `codex/canonical_fold_assignments.csv` | 57,282 | `f5a5964923806a23dd34a8bcc137f3cf489437e033d645e9d0845bf40792eb5d` | locked outer folds |
| `codex/canonical_cv_outputs/canonical_cv_metadata.json` | 10,098 | `9477c46a28c8e79b49f85b35cd517bec7a672d7d064e4e03914b11cf57f320c0` | classifier/configuration metadata |
| `codex/canonical_cv_outputs/canonical_cv_overall_metrics.csv` | 1,614 | `3f20f975a9051aba712787173d926a1c2e0971ab2708453d9cb78e8580641852` | canonical development metrics |
| `codex/canonical_cv_outputs/canonical_cv_model_selection.csv` | 275 | `598907d29203950414f5285732e98fb80f0751baae7c00fcd0c7b2c5de3ea597` | selected E3 baseline |
| `codex/canonical_cv_outputs/canonical_cv_selection_decision.json` | 3,464 | `a7e54fd892cfe037b847f979a03b9c88a408040ea477c8a2909b017a2350ad01` | frozen E1–E3 selection rule/result |
| `codex/canonical_cv_outputs/canonical_cv_results_summary.md` | 4,318 | `23c22618ec31146fc6db3587cf10a8ac9b503be6ace018e4298832b3375d84c3` | canonical aggregate report |

Το notebook δεν εκτελέστηκε. Η canonical implementation επαληθεύτηκε από το standalone script και τα structured artifacts παραπάνω.

## 6. Frozen external-source status

Οι μόνες επιτρεπόμενες external lexical sources είναι:

- Princeton WordNet 3.1 archive: 16,358,468 bytes, SHA-256 `3f7d8be8ef6ecc7167d39b10d66954ec734280b5bdcd57f7d9eafe429d11c22a`, WordNet License.
- English Wiktionary exact pages: οι επτά immutable revision IDs, timestamps και raw-response hashes που καταγράφονται στο source manifest, υπό CC BY-SA 4.0 και GFDL.

Δεν επιτρέπεται νέα λήψη, νεότερο revision, διαφορετικό λεξικό ή συμπλήρωση από web search. Το local MPNet snapshot είναι `sentence-transformers/all-mpnet-base-v2`, commit `e8c3b32edf5434bc2275fc9bab85f82640a19130`, CPU, `local_files_only=true`, `max_seq_length=256`.

## 7. Frozen retrieval configuration

Τα κοινά, συμβατά στοιχεία παγώνουν ως εξής:

1. Exact lexical lookup του normalized `term` στις frozen WordNet/Wiktionary sources.
2. Query fields αποκλειστικά `term + "\n" + src`.
3. Candidate representation: term, part of speech, definition και usage example.
4. Dense ranking: normalized MPNet embeddings και cosine similarity.
5. Deterministic tie-breaking: WordNet-before-Wiktionary source priority, original sense order, stable evidence ID.
6. Απαγορεύονται πριν από το ordered-list lock: `tgt`, hallucination label, `p_hallucination`, E3 prediction/probability και fold outcome.
7. Μοναδικό frozen candidate limit: `top_k = 5`.

Το Module 4 επαναχρησιμοποιεί ακριβώς τη frozen Phase 2B lexical candidate construction, τα frozen WordNet 3.1/Wiktionary snapshots, την frozen MPNet configuration, το query `term + src`, το deterministic tie-breaking και `top_k=5`. Δεν επιτρέπεται ablation ή tuning του candidate limit και ειδικά δεν επιτρέπεται σύγκριση `top_k ∈ {1, 3, 5}`. Η τιμή 5 δεν αλλάζει μετά την εξέταση αποτελεσμάτων. Δεν επαναχρησιμοποιείται το ασύμβατο Module 2 BM25 hard gate και δεν σχεδιάζεται νέο post-hoc gate.

## 8. Fixed RAG-assisted feature schema

Μετά και μόνο μετά το immutable ordered candidate-list lock, επιτρέπεται η χρήση του `tgt` για evidence comparison. Δεν επιτρέπεται feature addition μετά την εξέταση αποτελεσμάτων. Το schema παγώνει σε επτά features:

```text
rag_evidence_available
rag_sense_count
rag_retrieval_top1_cosine
rag_target_definition_max_cosine
rag_target_definition_max_entailment
rag_target_definition_max_contradiction
rag_target_definition_max_lexical_overlap
```

Ο normalized diagnostic flag `candidate_definition == tgt` καταγράφεται σε ξεχωριστό audit πεδίο και απαγορεύεται ως classifier feature.

Για cosine χρησιμοποιείται το frozen MPNet snapshot. Για entailment/contradiction χρησιμοποιείται αποκλειστικά το canonical E3 NLI model `microsoft/deberta-large-mnli`, frozen cached snapshot `7296194b9009373def4f7c5dad292651e4b5cf4e`, label mapping 0=`CONTRADICTION`, 1=`NEUTRAL`, 2=`ENTAILMENT`, truncation enabled και max length 512. Δεν επιτρέπεται model substitution.

### Missing-evidence policy

Όταν δεν υπάρχει exact external evidence:

```text
rag_evidence_available = 0
rag_sense_count = 0
rag_retrieval_top1_cosine = 0.0
rag_target_definition_max_cosine = 0.0
rag_target_definition_max_entailment = 0.0
rag_target_definition_max_contradiction = 0.0
rag_target_definition_max_lexical_overlap = 0.0
```

Όταν υπάρχει evidence, `rag_evidence_available=1`, `rag_sense_count` είναι ο αριθμός candidates στην τελικά εγκεκριμένη ordered list και τα υπόλοιπα πεδία υπολογίζονται μόνο πάνω σε αυτή. Η availability indicator διαχωρίζει deterministic missing zeros από πραγματικές τιμές. Δεν επιτρέπεται mean/median imputation ή fold/global label-dependent imputation.

## 9. Fusion και leakage protocol

Η μοναδική intended primary comparison είναι:

```text
E3_NLI_similarity: frozen 14 E3 features
vs
E5_MODULE4_RAG_ASSISTED_FUSION: frozen 14 E3 features + frozen 7 RAG features
```

Η fusion branch χρησιμοποιεί τον ίδιο `RandomForestRegressor` και ακριβώς τα ίδια frozen parameters. Δεν γίνεται feature scaling ή νέα preprocessing επιλογή. Αν μελλοντικά προκύψει τεχνικά αναγκαίο hyperparameter, απαιτείται nested inner CV μέσα σε κάθε training fold· η προτιμώμενη και προεγγεγραμμένη επιλογή είναι κανένα νέο hyperparameter.

Η μελλοντική execution πρέπει να εγγυάται:

- 561/561 ίδιες canonical development rows και τα ίδια five outer folds·
- 1/1 OOF prediction ανά eligible row και πλήρες canonical ID join·
- training μόνο στις training rows κάθε fold και validation αποκλειστικά στο αντίστοιχο fold·
- retrieval/order lock χωρίς validation labels ή outcomes·
- καμία χρήση hallucination labels/probabilities, E3 outputs ή fold outcomes στην retrieval και feature preparation·
- fold-local εφαρμογή κάθε learned preprocessing, αν ποτέ εγκριθεί·
- κανένα official-test input.

## 10. Frozen score-selection rule και uncertainty diagnostics

Η primary σύγκριση θα γίνει στις ίδιες 561 rows και folds:

1. μεγαλύτερο Overall OOF Accuracy·
2. αν και μόνο αν το Accuracy είναι ακριβώς ίσο, μεγαλύτερο Overall OOF Spearman.

Fold-level Accuracy/Spearman, per-task και per-track metrics, paired prediction comparison, paired bootstrap confidence interval και McNemar test όπου εφαρμόζεται είναι diagnostics. Δεν αλλάζουν τον selection rule και δεν επιτρέπουν post-hoc configuration selection.

Οι μόνες επιτρεπόμενες τελικές αποφάσεις είναι:

```text
E5_RAG_IMPROVES_DEVELOPMENT_SCORE
E5_RAG_LEXICAL_COVERAGE_GAIN_ONLY
E5_RAG_NO_SCORE_GAIN_E3_REMAINS_FINAL
MODULE4_BLOCKED_INSUFFICIENT_REPRODUCIBILITY
```

## 11. Υποχρεωτικό overlap audit

Το future results report πρέπει να παρουσιάσει χωριστά:

1. metrics στις 561/561 development rows·
2. metrics στις rows με external evidence·
3. metrics μετά την αφαίρεση rows με exact normalized definition–`tgt` match·
4. gains/losses που αποδίδονται στις exact-match rows·
5. evidence coverage ανά task και track·
6. fallback performance στις rows χωρίς evidence.

Η Phase 2B είχε 6/21 exact normalized definition–`tgt` overlaps, τα οποία ήταν και τα 6/6 strict rows, όλα από English Wiktionary. Αν οποιοδήποτε Module 4 gain προέρχεται μόνο από exact overlap, η ισχυρότερη επιτρεπόμενη ερμηνεία είναι `external lexical coverage improvement`, όχι γενική RAG generalization ή downstream safety.

## 12. Frozen holdout protocol

Το υπάρχον 10-example holdout παραμένει κλειστό. Η μοναδική επιτρεπόμενη ακολουθία είναι:

1. development-only OOF execution και report·
2. κλείδωμα μίας και μόνο final Module 4 configuration·
3. δημιουργία και SHA-256 hashing των holdout predictions χωρίς label access·
4. ξεχωριστή ρητή έγκριση από τον owner·
5. μία μοναδική unblinded holdout evaluation.

Το holdout θα παρουσιαστεί μόνο ως descriptive sanity check λόγω 10 examples. Το official test παραμένει εκτός ορίων.

## 13. Expected future artifacts — δεν δημιουργούνται στη Phase 0

Ένα ξεχωριστά εγκεκριμένο execution στάδιο πρέπει να καθορίσει περιορισμένο artifact set που θα περιλαμβάνει κατ’ ελάχιστο frozen retrieval/configuration metadata, immutable ordered candidates, RAG feature matrix, OOF predictions, metric/overlap audits και results report. Κανένα από αυτά δεν δημιουργήθηκε στη Phase 0.

## 14. Stop conditions

Η execution σταματά χωρίς features/predictions/metrics αν ισχύει οποιοδήποτε από τα παρακάτω:

- άλλαξε hash canonical E3 input, fold assignment, external source manifest ή snapshot·
- δεν υπάρχει πλήρες 561/561 canonical row/fold join·
- απαιτείται νέο model/source/download ή νέο retrieval/gate design·
- χρησιμοποιήθηκε forbidden field πριν από candidate-list lock·
- προτείνεται post-hoc feature, threshold, gate ή configuration·
- απαιτείται holdout-label ή official-test access πριν από τα προβλεπόμενα locks/approvals.

## 15. Protected exclusions και Phase 0 accounting

Δεν ανοίχτηκαν, διαβάστηκαν, έγιναν parse ή hash:

- official SHROOM test data ή official-test-derived predictions/submissions·
- AI-completed ή AI-independent annotations·
- row-level human annotation CSVs·
- labels του frozen 10-example holdout·
- credential-like files.

Phase 0 counters:

| Counter | Value |
|---|---:|
| Outputs created | 1 |
| Existing artifacts modified | 0 |
| Protected content accesses | 0 |
| Holdout-label accesses | 0 |
| Official-test accesses | 0 |
| Notebook/model/retrieval executions | 0 |
| Feature/prediction/metric rows produced | 0 |
| Network/API calls | 0 |
| Installations/downloads | 0 |

Το recovery quarantine `_cleanup_quarantine_20260829` δεν τροποποιήθηκε, διαβάστηκε ή διαγράφηκε. Η feature preparation δεν έχει ξεκινήσει.
