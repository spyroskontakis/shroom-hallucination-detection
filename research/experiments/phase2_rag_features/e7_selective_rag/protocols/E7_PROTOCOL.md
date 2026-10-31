# E7 v1 — Selective / Agentic RAG without LLM

## 1. Motivation and research question

E3 uses 14 NLI/similarity predictors. E5 retains these and adds seven reference-assisted lexical/RAG predictors (21). E6 retains all 21 and adds definition-to-hypothesis cosine and NLI entailment/neutral/contradiction (25). Frozen development counts are E3=445/561, E5=446/561, E6=453/561. E7 tests conditional use of these existing prediction paths; it adds no predictor or knowledge source.

**Research question:** "Can a selective evidence-routing mechanism improve or preserve hallucination-detection performance by dynamically deciding when retrieved lexical evidence should be used and when the system should fall back to the base model?"

Μπορεί ένας evidence-routing μηχανισμός να αποφασίζει επιλεκτικά πότε η ανακτημένη εξωτερική γνώση είναι αρκετά αξιόπιστη ώστε να χρησιμοποιηθεί και πότε είναι προτιμότερο το σύστημα να επιστρέφει στη βασική model-agnostic μέθοδο;

## 2. Agent and scope

This is a bounded deterministic controller, not a general autonomous agent. One trajectory per canonical ID:

START -> RETRIEVE -> ASSESS_EVIDENCE -> USE_EXTERNAL_EVIDENCE or FALLBACK_TO_BASE -> PREDICT -> END.

RETRIEVE loads the frozen E6 reconstructed ranking. There is exactly one routing action, no loop, no new retrieval, and no generative model. Non-LLM design keeps the controller offline, interpretable, inexpensive and reproducible. No API, web search, new corpus, embedding/NLI inference, pretrained-model training, synthetic-data experiment or E8 is authorized.

## 3. Available observations, inspected without labels

The frozen ranking contains 561 unique canonical IDs, candidate_count, query hash, and ordered selected records with rank, score, evidence ID and provenance. There are 193 evidence-bearing rows and 368 empty lists; selected counts are 117 singletons, 36 pairs, 9 triples, 8 quadruples and 23 lists of five. Candidate count ranges from 0 to 34.

Derived label-free audit metadata: evidence_available = bool(selected); selected_sense_count = len(selected); top1_cosine = selected[0].score when available; top2_cosine and top1_minus_top2 only when at least two selections exist. Missing top scores/margin are null, never invented zeros. Top-2 and margin exist for only 76 rows, so the first router does not use them. Candidate count and sense count are reported but not used as extra decision criteria. Cosine is a relative retrieval similarity signal, not a calibrated probability of evidence truth/usefulness.

## 4. Frozen router rule and training-only parameters

Choose ONE deterministic threshold router. For each locked outer fold f, compute tau_f = numpy.quantile(top1_cosine for evidence-bearing outer_train rows, 0.5, method='linear'). The quantile level 0.5 is fixed here a priori as a simple relative-quality split, not selected from scores. The rule is:

- If evidence_available is true and top1_cosine >= tau_f: USE_EXTERNAL_EVIDENCE.
- Otherwise: FALLBACK_TO_BASE.

If the training fold has no evidence, tau_f is null and every validation row falls back. Equality uses >=, with no epsilon. Non-finite available scores or inconsistent metadata fail preflight. Router inference accepts exactly evidence_available and top1_cosine; IDs/folds/tasks are bookkeeping outside the decision function. No hyp, tgt, labels, target probability, correctness, OOF scores or model predictions enter router fitting or inference. No supervised router target exists.

There is NO threshold search, learned classifier, inner CV, RF tuning or performance-based selection. Only the training-fold empirical median is fitted; no validation observation contributes to it. All 561 actions and five thresholds are written and hashed BEFORE evaluation labels or baseline predictions are loaded. These thresholds are relative cutoffs, not validated optimal usefulness boundaries. Both actions must occur globally; otherwise STOP without redesign.

## 5. Frozen prediction paths and outer evaluation

Use the same 561 ordered canonical development IDs and locked folds (113/112/112/112/112). E3 predictors are the accepted Module 4 evaluator's E3 list (14); E6 predictors are the E6 feature_freeze list (25), in frozen order. Validate E6's first 21 columns against original E3 plus accepted seven RAG features. Load E6 CSV with float_precision='round_trip', matching E6 evaluation. Read original E3 features with the accepted parser behavior. Validate exact IDs, folds, finite values, and zero new features for missing evidence. No labels are projected in preflight/router construction.

Retrain both RF paths using the unchanged accepted Module 4 run_cv function: five fits for E3 and five for E6, each on outer_train only. RandomForestRegressor(n_estimators=500, random_state=42, n_jobs=-1), all remaining defaults identical to E6's recorded configuration and runtime. Target p_hallucination, clipping [0,1], binary prediction >=0.5. MPNet/DeBERTa remain unused inference-only historical feature extractors. No expensive feature extraction is repeated.

The E7 prediction is the freshly computed outer-validation prediction from the chosen E3/E6 path. Frozen saved OOF predictions are loaded only after actions are locked, for alignment/reproduction checks and comparison. Check freshly trained E3/E6 against saved predictions with absolute tolerance 1e-12, rtol=0; binary predictions must match exactly, and rounded-12-decimal ranks and baseline metrics must reproduce within 1e-12. If any compatibility check fails, STOP before interpreting E7. This is not unchecked mixing of global scores.

Training labels are available only to the RF training split. Outer-validation labels are not passed to fitting or routing. The accepted run_cv explicitly splits by fold before fit. Validation labels are used only for post-prediction evaluation; fold partitions and IDs are recorded for audit.

## 6. Metrics and statistics

Primary comparison E7 versus frozen E6 (accuracy 0.8074866310, Spearman 0.7444205394). Secondary reference E3 (0.7932263815, 0.7390395613); E5 descriptive reference (0.7950089127, 0.7421719692).

Report overall, DM/MT/PG, evidence/no-evidence, route-specific and fold-specific accuracy, correct/N, and Spearman using prediction rounding to 12 decimals. Undefined Spearman for tiny/constant groups is null with explanation. Report route counts overall, per task and per evidence status, and actual tau_f and train-evidence sample counts.

For E6 (primary) and E3 (secondary), report corrected/regressed IDs and counts, net correct, exact two-sided McNemar binomtest(b,b+c,0.5), p=1 when b+c=0. Paired bootstrap E7 minus baseline: 10,000 resamples of 561 paired correctness differences, numpy default_rng(42) initialized independently per comparison, percentile 2.5/97.5 using numpy.quantile. Same iteration/order as E6. Report raw accuracy difference and percentage-point CI. No multiplicity correction or selection-adjusted inference is claimed. Subgroup results are descriptive.

## 7. Freeze, preflight, failures and stop conditions

Freeze this protocol hash with UTC timestamp before evaluation or label join. Preserve original hashes of all 447 E6-protected files plus all E6 files and release/source documentation. Preflight must verify those hashes and all input schemas/alignment. Synthetic contracts test no labels in router schema, training-only threshold, unavailable evidence fallback, threshold equality, one action, deterministic termination, selected prediction/range, network block, restricted data access and frozen-write rejection. All fixtures stay inside this E7 directory. Full preflight plus contracts must PASS before final evaluation starts.

Use a Python process-local audit guard: block network operations, child processes and file writes outside this E7 directory; allow repository reads only from the explicit preflight frozen-file allowlist and E7. E7 data loaders allow only named development files and explicit projections. No official-test datasets are on the allowlist. Runtime/library reads outside the repository are restricted to the Python environment and system software directories. Guards are defense-in-depth for this code, not OS isolation. Synthetic guard probes are explicitly marked and counted separately from operational attempts; any operational network/forbidden access causes STOP. Git fetch is an explicitly authorized setup operation outside the offline experiment.

Outputs use exclusive creation. Write a single evaluation_started marker before any RF fit; if it already exists, refuse rerun. Lock source/test hashes before final evaluation. One E7 evaluation suite, five outer folds, exactly ten RF fits, no inner fits. On critical preflight/contract failure, input mutation, baseline incompatibility, non-finite prediction, network/access violation or execution failure: STOP and report; do not tune or rerun to improve a result. Preserve protocol and original artifacts regardless of score. No commit, push or tag.

## 8. Limitations and interpretation

**DEVELOPMENT-ONLY.** The same development pool informed prior experiments and the motivation for this design. Fold-local threshold fitting does not erase this adaptive research history. Accuracy preservation cannot be inferred as equivalence from a non-significant test. Bootstrap intervals condition on fixed OOF predictions and omit retraining uncertainty. Evidence is DM-only, reference-assisted E5 features remain in E6, and historical Module 4 provenance/label-exposure caveats remain. Reconstructed aggregate consistency does not prove the complete historical ranking. Routing to E3 without evidence can lose E6 benefits from its globally different RF feature space. Computing both paths for this audit is not a claim of inference-cost savings.

A GitHub clone is not self-contained: private canonical inputs, frozen per-row matrices/predictions and reconstructed ranking are local-only. Reproduction requires authorized inputs matching hashes and the pinned Python runtime. Historical extractors: MPNet sentence-transformers/all-mpnet-base-v2@e8c3b32edf5434bc2275fc9bab85f82640a19130 and DeBERTa microsoft/deberta-large-mnli@7296194b9009373def4f7c5dad292651e4b5cf4e. They are not loaded in E7. Sources: frozen E6 protocol/results/reproducibility guide, Module 4 release documentation, accepted evaluator and pinned ranking code.

After the single run, record the outcome even if E7 is worse. Do not redesign, start E8, modify thesis files or touch frozen artifacts.
