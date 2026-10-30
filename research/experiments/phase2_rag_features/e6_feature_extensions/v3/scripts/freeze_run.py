"""Run pre-bulk contracts, write protocol and freeze all choices and code."""
if "_H2_CTX" not in globals():
    raise RuntimeError("Historical source: use the pinned cross-experiment context; direct execution/import is disabled")
import io,sys,unittest,json
import v3_common as c

def main():
    log=c.offline('contracts');runtime=c.versions();c.verify_inputs();c.verify_models()
    smoke=c.read_json(c.OUT/'config/smoke.json');assert smoke['status']=='PASS'
    assert smoke['model_class']=='DebertaV2ForSequenceClassification' and smoke['tokenizer_fast']
    assert smoke['torch_threads']==smoke['torch_interop_threads']==4
    assert smoke['device']=='cpu' and smoke['dtype']=='float32' and smoke['batch_size']==2
    suite=unittest.defaultTestLoader.discover(str(c.OUT/'tests'),pattern='test_v3.py')
    stream=io.StringIO();result=unittest.TextTestRunner(stream=stream,verbosity=2).run(suite)
    print(stream.getvalue(),flush=True)
    assert result.wasSuccessful() and result.testsRun==7
    c.write_json(c.OUT/'config/contracts.json',{'status':'PASS','tests':result.testsRun,'output':stream.getvalue(),'completed_utc':c.now()})
    old=c.read_json(c.V2/'config/run_config.json');params=old['random_forest']
    from sklearn.ensemble import RandomForestRegressor
    assert RandomForestRegressor(**params).get_params()==params and len(params)==18
    features=old['features']+c.NEW;assert len(features)==36 and len(set(features))==36
    protocol='''# E6-v3 protocol — fixed HHEM-1.0 feature block

Frozen before real-pair inference and E6-v3 scoring. One predetermined experiment only.
Research question: does the entire additional frozen factual-consistency block complement E6-v2?
Inspired by the evaluator-combination idea of Halu-NLP/MetaCheckGPT; this is not a full reproduction.

## Inputs and baseline

Use the exact saved 34 E6-v2 columns, order and values (CSV float_precision=round_trip),
the same 561 canonical IDs and five locked folds (113/112/112/112/112).
Primary saved baseline E6-v2: 473/561, accuracy 0.8431372549019608, Spearman 0.7775058304756869.
Verify OOF per ID/fold and row diagnostics before fitting; zero baseline fits. Stop and investigate any mismatch.
config/input_manifest.json protects all prior experiment artifacts including untracked E6-v2/E7/E8.
No earlier files are modified. Read-only integrity hashes include canonical development sources.

## Model and scoring

vectara/hallucination_evaluation_model at immutable revision
58383384656cbaec2949a75a41f20e891e90a73b (historical hhem-1.0-open).
Model/tokenizer/config/card downloaded only from this revision; local_files_only=True,
trust_remote_code=False. DebertaV2ForSequenceClassification, one output logit.
Apply torch.sigmoid to raw logits exactly once; never single-logit softmax or a second sigmoid.
The pinned model card's Transformers implementation explicitly uses 1/(1+exp(-logits)).
High score means supported by premise, low means unsupported; do not invert the feature.
eval(), requires_grad_(False), inference_mode(), no training/finetuning/autocast.
CPU float32, batch size 2, seed 42, torch intra/inter-op threads 4/4, eager attention.
Fast tokenizer; separate premise/hypothesis inputs; longest_first truncation, max_length=512,
per-batch padding and attention_mask. Audit original/used length and removed tokens by side.
Store raw logits and sigmoid scores without intentional rounding, in JSON caches and CSV outputs.
The artificial four-pair technical smoke includes long text and precedes this freeze; no development labels used.
provenance/acquisition.json records model/tokenizer URLs, SHA-256, sizes and declared datasets:
MultiNLI, SNLI, FEVER, Vitamin C, PAWS; base microsoft/deberta-v3-base. These author claims
do not independently establish absence of pretraining or fine-tuning contamination.

## Exactly two new features

1. hhem_ref_hyp_consistency: saved E6-v2 A, reference premise → hyp hypothesis, all 561.
   Reference=tgt for DM/MT, src for PG.
2. hhem_definition_hyp_consistency: saved E6-v2 C, selected definition premise → hyp hypothesis, 193.
   Exact zero for the 368 missing-definition rows, preserving rag_evidence_available.

Use the exact saved A/C text strings; 754 real pairs, 34+2=36 features. No reverse B pairs,
new retrieval/reranking/replacement or manual feature rules. Definitions are inherited from E6-v1's
locally reconstructed frozen Module 4 ranking. No historical complete ranking exists for direct
comparison; aggregate consistency with E5 does not by itself prove the entire historical ordering.
The extraction input schema has only pair ID, canonical ID, group, premise and hypothesis.
No labels, hallucination targets or OOF predictions enter extraction.

## Resumption and feature freeze

377 atomic JSON batch checkpoints. Each stores exact pair/text digest, configuration digest,
ordered pair IDs, scores, truncation, duration and a payload digest. On resume validate every
completed cache and reuse it without model inference; load the model only for missing batches.
Use a unique network-attempt log and extraction-session record per invocation. Completed features
are verified and skipped. Do not run concurrent extraction invocations. CSV outputs already present
must equal reconstructed results. Never overwrite completed cache/results. Resume after a technical
failure only, with identical frozen code, inputs, execution settings and revision.
After all caches validate: verify finite scores in [0,1], missing-definition zeros, 34 unchanged
base columns, canonical order/folds, then hash/freeze the full matrix before joining evaluation labels.

## Single fixed evaluation

Five RandomForestRegressor fits, each trained only on its outer-training fold and predicting only
its outer-validation fold. No tuning, router, ablation or threshold search. Exactly one configuration.
Regression target p_hallucination, clip predictions [0,1], binary prediction >=0.5.
All 18 explicit accepted E6-v2 parameters:

```json
'''+json.dumps(params,indent=2,sort_keys=True)+'''
```

Accuracy uses unrounded predictions and approved label_bin. Spearman is scipy.stats.spearmanr
of p_hallucination versus numpy.round(prediction,12); undefined for constant/singleton cases.
Report overall, fold, DM/MT/PG, and evidence availability results for E6-v2/E6-v3.
Report corrected and new-error IDs, exact two-sided binomtest(corrected,discordant_count,0.5),
with p=1 if no discordance. Paired bootstrap uses 10,000 canonical-row resamples of size 561,
numpy.default_rng(42), differences in correctness, numpy.quantile([.025,.975]); no retraining.
Do not change features, model, RF or protocol once real results appear.

## Integrity and reporting

Verify input/model/code hashes, old feature equality, cache reassembly, all OOF metrics/paired statistics,
five disjoint training/validation partitions and 15 fit input/target array hashes. Record fit counts,
extraction elapsed time and per-batch inference time, truncation, dependencies and network attempts.
All writes are within rag_e6_v3. No paid API, remote inference, MPNet/NLI extraction, synthetic changes,
official-test access, commit/push/tag or subsequent experiment. Only the authorized pinned model
download uses network; smoke/extraction/evaluation/report deny network connections.

Results are exploratory development-only on a reused set, regardless of their direction.
OOF evaluation is not an independent test. The conclusion concerns the entire HHEM feature block,
not attribution to individual new features. Bootstrap conditions on these fixed OOF predictions;
it does not correct for previous experiment selection or repeated development use.

Full ordered columns, runtime and hashes are frozen in config/run_config.json.
'''
    with (c.OUT/'E6_V3_PROTOCOL.md').open('x',encoding='utf-8',newline='\n') as f:f.write(protocol)
    paths=[c.OUT/'E6_V3_PROTOCOL.md']
    for folder in ['scripts','tests','inputs','provenance']:
        paths+=sorted(p for p in (c.OUT/folder).rglob('*') if p.is_file())
    paths += [c.OUT/'config'/n for n in ['input_manifest.json','input_checks.json','smoke.json','contracts.json']]
    c.write_json(c.OUT/'config/run_config.json',{'frozen_utc':c.now(),'features':features,'original_features':old['features'],
                 'new_features':c.NEW,'random_forest':params,'runtime':runtime,'model_id':c.MODEL_ID,'revision':c.REVISION,
                 'execution':{'device':'cpu','dtype':'float32','batch_size':2},
                 'torch_threads':4,'torch_interop_threads':4,'activation':'sigmoid(raw logit) once',
                 'tokenization':{'max_length':512,'truncation':'longest_first','padding':True,'attention_mask':True},
                 'bootstrap':old['bootstrap'],'clip':old['clip'],'threshold':.5,'spearman_round_decimals':12,
                 'expected_rf_fits':5,'baseline_fits':0,'contracts_passed':result.testsRun,
                 'frozen_files':{p.relative_to(c.OUT).as_posix():c.sha(p) for p in paths}})
    assert log.stat().st_size==0
    print({'protocol_frozen':True,'features':36,'parameters':len(params)},flush=True)

if __name__=='__main__':main()
