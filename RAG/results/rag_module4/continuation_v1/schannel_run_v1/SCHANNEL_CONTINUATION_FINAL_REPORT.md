# E5 Module 4 — Verified Schannel Continuation Final Report

**Ημερομηνία:** 2026-08-30  
**Scope:** development-only OOF, frozen single configuration, official test/holdout κλειστά  
**Final run verdict:** `MODULE4_SCHANNEL_CONTINUATION_COMPLETE_DEVELOPMENT_OOF_EVALUATED_WITH_DISCLOSED_DEVIATION`

## 1. Scientific status

Η ακριβής root cause της προηγούμενης Python/OpenSSL TLS αποτυχίας παραμένει **unresolved**. Δεν τροποποιήθηκαν Python/Windows trust stores, ώρα συστήματος, proxy policy ή source semantics και δεν χρησιμοποιήθηκε TLS bypass. Η παρούσα συνέχεια αποδεικνύει μόνο ότι το ήδη εγκατεστημένο Windows `curl.exe` με Schannel ολοκλήρωσε επιτυχώς το συγκεκριμένο frozen English Wiktionary acquisition με κανονική certificate και hostname verification.

Το ιστορικό label-exposure incident δεν μηδενίζεται: πριν από αυτή τη συνέχεια είχε ήδη εμφανιστεί μία πρώτη γραμμή του mixed E3 CSV. Στην παρούσα συνέχεια υπήρξαν **0 νέες development-label accesses πριν από το 561×7 feature lock**. Το mixed E3 artifact ανοίχτηκε μόνο μετά την καταγραφή:

```text
RAG_7_FEATURES_LOCKED_BEFORE_ANY_NEW_DEVELOPMENT_LABEL_ACCESS
```

## 2. Transport validation and disclosed deviation

- Client: `external-artifacts/local-0dd4264ef6a3/curl.exe`, curl 8.21.0/libcurl 8.21.0, Schannel.
- Executable: 818,512 bytes; SHA-256 `73d24149ff289afc49ec41f08918ef9faa727d39ad993e929757dc2ddafab805`.
- Invocation: argument list, `shell=False`, `-q` first, HTTPS-only, no redirects, no insecure/revocation-bypass options.
- Preflight: curl exit 0, HTTP 200, `ssl_verify_result=0`, valid `query.general` JSON; response 3,102 bytes, SHA-256 `ad95053cd8af58f48431ca819f3fd0e227cc0d3145cc13e4a80dca11c4c8b685`.
- Server Date `2026-08-30T07:27:45Z` and local completion `2026-08-30T07:27:47.961074Z` were consistent to approximately 3 seconds. This is a consistency check, not independent proof of clock correctness.
- Tests: 28/28 PASS across frozen parser fixtures, orchestration, seven-feature logic and Schannel transport tests.

Κατά την πρώτη model-runtime προσπάθεια, το default Python σταμάτησε πριν από output λόγω torch/NumPy ABI mismatch. Χρησιμοποιήθηκε στη συνέχεια το ήδη εγκατεστημένο canonical `shroom_ensemble` environment, χωρίς package changes. Σε μία απορριφθείσα model-load προσπάθεια, το `transformers 5.5.4` εκκίνησε background safetensors-conversion hub-resolution helper παρά το `local_files_only=True`. Ο helper απέτυχε και η διεργασία διακόπηκε πριν δημιουργήσει accepted feature artifact. Η τελική και η deterministic-repeat inference εκτελέστηκαν με `HF_HUB_OFFLINE=1`, `TRANSFORMERS_OFFLINE=1`, `HF_DATASETS_OFFLINE=1` και telemetry disabled. Το συμβάν δηλώνεται ως protocol deviation και δεν αποκρύπτεται.

## 3. Acquisition and snapshot lock

- Locked terms: 206/206 canonical normalized DM terms.
- Logical failed terms: 0/206.
- Request-log events: 434 attempts: 395/434 accepted HTTP 200 responses και 39/434 HTTP 429 transient attempts.
- TLS/certificate failures: 0/434.
- Accepted response με non-200 ή nonzero SSL verification: 0/395.
- Frozen revision files: 206; frozen parse files: 188. Οι 18 χωρίς parse ήταν έγκυρα missing/no-revision pages.
- Offline term statuses: `SENSES_FOUND` 188/206, `NO_SENSE_FOUND` 18/206, `SOURCE_REQUEST_FAILED` 0/206.
- Raw extracted senses: 462; deterministic unique senses/evidence IDs: 462/462.
- Snapshot source values: `enwiktionary` μόνο.
- Δύο offline snapshot/manifest builds: byte-identical PASS.

## 4. Frozen seven-feature lock

Η frozen pipeline διατήρησε `term + src`, MPNet revision `e8c3b32edf5434bc2275fc9bab85f82640a19130`, `top_k=5`, deterministic tie-breaking, DeBERTa-large-MNLI revision `7296194b9009373def4f7c5dad292651e4b5cf4e`, την ίδια NLI direction/aggregation και deterministic missing-evidence zeros.

- Rows: 561/561, unique canonical identities: 561/561.
- Columns: 1 identity + 7/7 frozen RAG features.
- DM rows: 211/561; MT/PG fallback rows: 350/561 και 350/350 με επτά μηδενικά features.
- Evidence-available rows: 193/561; zero-evidence rows: 368/561.
- Non-finite values: 0.
- Forbidden label/prediction/fold columns: 0.
- Δύο πλήρεις offline reconstructions: byte-identical PASS.
- Locked RAG feature SHA-256: `708483b831430d876135d1484ad841bf6ba0d9c9a2d0a5f22df6280535fe3160`.

## 5. Authorized E3 reproduction gate

Μετά το feature lock χρησιμοποιήθηκαν ρητή allowlist 14/14 E3 predictors, οι locked 5/5 outer folds και η canonical `RandomForestRegressor(n_estimators=500, random_state=42, n_jobs=-1)`. Labels, row IDs, fold IDs και OOF predictions δεν χρησιμοποιήθηκαν ως predictors. Η canonical 12-decimal prediction rounding εφαρμόστηκε μόνο στον Spearman evaluator.

| Metric | Expected | Observed | Result |
|---|---:|---:|---|
| Overall OOF Accuracy | 445/561 (0.7932263814616756) | 445/561 (0.7932263814616756) | PASS |
| Overall OOF Spearman | 0.7390395612811848 | 0.7390395612811848 | PASS |

## 6. Single frozen E5 development-only OOF result

Δεν έγινε tuning, ablation, source comparison ή δεύτερη E5 configuration.

| Scope | E3 Accuracy | E5 Accuracy | E3 Spearman | E5 Spearman |
|---|---:|---:|---:|---:|
| All development rows | 445/561 (79.3226%) | 446/561 (79.5009%) | 0.7390395613 | 0.7421719692 |
| Evidence rows | 143/193 (74.0933%) | 145/193 (75.1295%) | 0.6486587710 | 0.6534407273 |
| No-evidence fallback | 302/368 (82.0652%) | 301/368 (81.7935%) | 0.7662242801 | 0.7692661676 |
| DM | 155/211 (73.4597%) | 157/211 (74.4076%) | 0.6400104693 | 0.6427316315 |
| MT | 185/216 (85.6481%) | 185/216 (85.6481%) | 0.7960447809 | 0.7972150618 |
| PG | 105/134 (78.3582%) | 104/134 (77.6119%) | 0.6961810929 | 0.6949901408 |

Η E5 διόρθωσε 5/561 rows και εισήγαγε 4/561 νέες αστοχίες: net +1/561 σωστή binary prediction. Exact McNemar two-sided `p=1.0`. Η paired bootstrap Accuracy διαφορά ήταν `+0.0017825312`, με 10,000 fixed-seed replicates και percentile 95% CI `[-0.0089126560, 0.0124777184]`. Άρα η παρατηρούμενη μικρή development gain είναι συμβατή με μηδενική διαφορά και δεν αποτελεί αξιόπιστη ένδειξη γενίκευσης.

## 7. Reference-overlap audit

Υπήρχαν 18/561 rows με exact normalized candidate-definition–`tgt` match μέσα στο frozen top-5. Στις 18 exact rows, E3 και E5 είχαν αμφότερα 13/18 Accuracy· η E5 δεν διόρθωσε ούτε εισήγαγε binary error (0/18 και 0/18). Μετά την αφαίρεσή τους, E3: 432/543 (79.5580%), Spearman 0.7398237523· E5: 433/543 (79.7422%), Spearman 0.7433186589. Οι 5 διορθώσεις και 4 νέες αστοχίες προήλθαν όλες από non-exact rows.

Αυτό αποκλείει την απλή εξήγηση ότι το net +1 Accuracy προήλθε αποκλειστικά από exact reference copying. Δεν αποδεικνύει, όμως, general RAG generalization ή downstream safety: το `tgt` χρησιμοποιείται reference-assisted για feature comparison, το sample είναι development-only και η lexical πηγή μπορεί να παραμένει ισχυρά συναφής με τις references.

## 8. Frozen decision and limitations

Με τον προκαθορισμένο κανόνα—primary Overall OOF Accuracy, secondary Spearman μόνο σε Accuracy tie—η μοναδική επιτρεπόμενη score-based απόφαση είναι:

```text
E5_RAG_IMPROVES_DEVELOPMENT_SCORE
```

Η απόφαση σημαίνει μόνο measured improvement στο συγκεκριμένο frozen development OOF experiment. Δεν αποτελεί external validation, benchmark improvement claim, Gemini approval ή τελική holdout απόδειξη. Το official test, το frozen holdout, annotations, protected και quarantine content παρέμειναν κλειστά. Δεν δημιουργήθηκαν holdout predictions.

Κύριοι περιορισμοί: development-only sample 561 rows, RAG εφαρμογή σε 211 DM rows, evidence σε 193 rows, 18 exact reference overlaps, πολύ μικρό net Accuracy gain, bootstrap interval που περιλαμβάνει το μηδέν, διαφορετική συμπεριφορά ανά task/fold, historical label-exposure incident και το νέο αποκαλυμμένο background hub-resolution deviation.

## 9. Key artifact integrity

| Artifact | Bytes | SHA-256 |
|---|---:|---|
| `SCHANNEL_TRANSPORT_ADDENDUM.md` | 2,487 | `b74d8b8caddd914ad066085cb6987c390932f1c7963509e8d72d31098f6bb41c` |
| `raw_sources/network_requests.jsonl` | 345,639 | `1e5f0d7657bd683a50123e80b3a40472750334e501b0bdd62560c3d52fda808c` |
| `module4_external_lexical_snapshot.jsonl` | 381,385 | `7677937ace64644afa4f39d8745f54711640a578f1387d9e389008b1e0440d40` |
| `module4_dev_term_manifest.csv` | 61,152 | `b5002d09df7ed8559aaea0ec60a8367dcd35edf36e22b11e0f59f0154aa4e062` |
| `features/module4_rag_features.csv` | 38,385 | `708483b831430d876135d1484ad841bf6ba0d9c9a2d0a5f22df6280535fe3160` |
| `features/module4_fused_21_features.csv` | 149,500 | `402e28b19239779980bce50db80f06bf726f6a07967b313e39ce07289d93cfd3` |
| `features/module4_exact_overlap_audit.csv` | 16,350 | `0fab92f6907da36ae1be609d26230f8b7db054b42bff1f02b578b8719bba714a` |
| `evaluation/module4_e3_oof_predictions.csv` | 24,799 | `942d4c5d69411d7b496286d108f3347192f69224535938e335d94b7f67e237f1` |
| `evaluation/module4_e5_oof_predictions.csv` | 24,843 | `6532425e38d66391e579c414e4ec07482f100f2dee7b4ce0531d502d034e6ea5` |
| `evaluation/module4_development_oof_metrics.json` | 6,480 | `4fca6c5c72e79a9da593e97fc4f4612e51aa89509626ae10e12a0aec915ed712` |
| `scripts/module4_schannel_acquire.py` | 6,816 | `f44171f65ce18528ce51eef13bbc6285fb273fe139f75e9ede4ab112224fbe89` |
| `scripts/module4_evaluate_fusion.py` | 6,233 | `ef127e98c8a71b64abec6986cb6baf852b9521ff480142517ef0bc00e40b919e` |
| `scripts/module4_exact_overlap_audit.py` | 2,238 | `5912c0a838d9f4ac8c8f92163c268656a1588fb7c873dd35260f2df6c20dfb14` |
| `scripts/module4_finalize_diagnostics.py` | 3,197 | `becc5d0ed0dbfa425ba42402bb7d04854d83778a8ab3066cfc07f4fd328f1460` |

Το transport-only diff περιορίστηκε στην έγχυση `SchannelFetcher.get()` στο υπάρχον frozen orchestration interface: raw bytes επιστρέφονται στον αμετάβλητο parser και η αποθήκευση/atomic promotion παραμένει στο frozen orchestration layer. Δεν έγινε semantic parser ή feature-definition change.

No official test, holdout labels, human/AI annotation content, protected data or Gemini/LLM API was accessed. No previous Module 4 artifact, E1–E4 artifact, Module 1–3 artifact, dataset or incident report was modified. Package changes/installations: 0. Notebook executions: 0. Official-test accesses: 0. Holdout-label accesses: 0.
