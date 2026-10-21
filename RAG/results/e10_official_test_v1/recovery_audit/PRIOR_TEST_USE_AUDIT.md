# Prior official-test exposure

Conclusion: any future result must be described as **retrospective evaluation on the official labeled test set**, not an independent or pristine test evaluation. This audit reads historical code and stored outputs; it does not recompute test metrics or generate predictions.

## Direct evidence

Cell indices below are zero-based notebook JSON indices, not execution counters.

| Evidence | What it establishes |
|---|---|
| `codex/data/shroom_ensemble.ipynb`, cells 2 and 4 (executions 29, 31) | Official model-agnostic and model-aware test paths were opened and loaded. |
| Same notebook, cells 6–8 (executions 32–34) | Gold label distributions, labels by task and gold probability difficulty bins were inspected. |
| Same notebook, cells 20–21 (executions 45–46) | `df = test_agnostic_df.copy()` and gold regression/binary targets were constructed and displayed. |
| Same notebook, cell 31 (execution 55), stored output cell 32 (56) | Five-fold supervised RF CV on test-derived rows/gold; stored OOF accuracy 0.7933333333333333 and Spearman 0.6738868983127707. This is not a held-out final benchmark. |
| Same notebook, cells 46 and 50 (executions 68, 72) | Another historical test-derived CV result, stored accuracy 0.806 and Spearman 0.7117582549660093. |
| `codex/data/7. Ablation Synthetic Data/7.Ablation_Synthetic_Data.ipynb`, cells 1–2 and 8 | Evaluation source is `4.nli_similarity_features_dataset.csv`; evaluation code reads official gold and computes accuracy/Spearman/MAE. |
| Same notebook, cell 27 (execution 28) and saved `ablation_synthetic_ratio_results.csv` | Ratios 0, .25, .5, .75, 1 were evaluated against this test-derived source. |
| Same notebook, cell 29 (execution 29) and saved `ablation_synthetic_weight_results.csv` | Synthetic weights .1, .25, .5, .75, 1 were evaluated against the same source. |
| Same notebook, cells 30–31 | Markdown explicitly discusses whether synthetic data should enter the final method; helper source sorts results by Spearman then accuracy. Cell 31 has no execution counter: this is evidence of intended selection logic, not proof that this particular helper executed or a particular choice was adopted. |

The 1,500 IDs and normalized `(task,src,tgt,hyp)` multiset in that historical feature CSV were compared with the official model-agnostic test inputs and match exactly. Only input columns were selected for this identity check. No gold-value comparison or scoring was needed.

## Timing and limits of chronology

The filesystem records `codex/data/shroom_ensemble.ipynb` modified at **2026-05-05T15:54:56.143536Z**; the historical test feature CSV at **2026-05-05T13:13:44.054770Z**; ratio and weight result CSVs at **2026-06-06T10:07:01.553929Z** and **2026-06-06T10:07:09.161844Z**. These are local artifact timestamps, not authenticated notebook execution dates. The precise first access and each original execution time cannot be established from these records. Execution counters and stored outputs prove prior execution, not wall-clock timing.

The local Git history subsequently records Module4/E5 work in August 2026 and E6/E7/E8 releases in September 2026. Thus the available local chronology places exploratory test use before the later development-only experiment sequence, subject to the timestamp limitation above. No claim of first access at the Git baseline date is made.

## Influence on later E6 / E9 / E10 / E11

`codex/evaluation_protocol_decision.md` explicitly documents historical labeled-test ratio/weight sweeps, excludes that protocol from authoritative model selection, and warns against calling the official test pristine or unbiased. Its later canonical CV procedure is development-only. `codex/chapter6_audit.md` records that the later development feature extraction did not take test feature/prediction artifacts as inputs.

There is nevertheless a direct **test-input-derived population influence**: `codex/canonical_evaluation_data_prep.py` used official test texts for overlap filtering, and the shared 561-row canonical development pool excludes four exact development/test overlaps. That pool feeds the later E6/E9/E10/E11 comparisons. The preparation script also historically loads/decorates test labels for its audit artifacts; this is additional exposure, not evidence that those labels were fit as E10 training targets. The newly proposed 547-row pool adds 14 source-pair exclusions and is explicitly test-input-informed.

The inspected lineage does **not** establish that historical test predictions, test metrics or test gold were direct feature/target inputs to the authoritative E6/E9/E10/E11 development CV fits. It does establish earlier test-driven exploration and subsequent design work. Neither local manifests nor a later clean CV flow can establish that the researchers' later methodological decisions were cognitively independent of previously viewed results. The exact causal influence of the sweeps on each later design choice is unrecorded; do not invent it or assert its absence.

Answers: test inputs accessed previously **yes**; gold inspected **yes**; performance computed **yes**; design/tuning after exposure **yes** (including test-evaluated synthetic sweeps); later artifact influence **yes for overlap-based pool construction**, with no demonstrated direct reuse of historical test predictions/gold as authoritative later model inputs. Required wording remains retrospective, even after strict overlap removal.
