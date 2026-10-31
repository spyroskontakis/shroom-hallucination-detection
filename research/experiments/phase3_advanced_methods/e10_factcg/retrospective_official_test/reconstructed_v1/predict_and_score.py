"""Separate one-fit prediction freeze and guarded one-time gold scoring."""
import argparse,collections,hashlib,json,sys,time
from pathlib import Path
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[3]
OFFICIAL_TEST_SHA256='c5c5fe0ce9c402186990b0dde05c0274ac90d10906b169f28d2f2c0cf669f299'
sys.path.insert(0,str(ROOT/'RAG/results/phase3_e9_claim_verification/scripts'))
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,data):
    with p.open('x',encoding='utf-8') as f:json.dump(data,f,ensure_ascii=False,indent=2,allow_nan=False);f.write('\n')
def contract():
    c=read(HERE.parent/'E10_OFFICIAL_TEST_FEATURE_MANIFEST.json')
    for p,h in c['source_sha256'].items():assert sha(ROOT/p)==h,p
    assert sha(ROOT/'Labeled test/SHROOM_test-labeled/test.model-agnostic.json')==OFFICIAL_TEST_SHA256
    return c
def validated_predictions():
    p=HERE/'E10_OFFICIAL_TEST_PREDICTIONS.json'
    expected=(HERE/'E10_OFFICIAL_TEST_PREDICTIONS_SHA256.txt').read_text().split()[0]
    assert sha(p)==expected
    data=read(p);inputs=read(HERE/'test_inputs_label_free.json')
    assert len(data['predictions'])==len({str(r['id']) for r in data['predictions']})==1500
    assert [str(r['id']) for r in data['predictions']]==[str(r['id']) for r in inputs]
    assert all(0<=r['prediction']<=1 for r in data['predictions'])
    assert data['test_inputs_sha256']==sha(HERE/'test_inputs_label_free.json')
    return data,expected
def freeze():
    import numpy as np,pandas as pd,joblib,sklearn
    from sklearn.ensemble import RandomForestRegressor
    c=contract();names=c['ordered_features'];assert len(names)==37
    inputs=read(HERE/'test_inputs_label_free.json');ids=[str(r['id']) for r in inputs]
    assert len(ids)==len(set(ids))==1500
    assert all(set(r)=={'id','task','src','tgt','hyp'} for r in inputs)
    all_columns={};stage_hashes={}
    for stage,file in [('base14','base14.csv'),('rag11','rag11.csv'),('nli2','nli2.csv'),('hhem','hhem.csv')]:
        meta=read(HERE/'cpu_features'/f'{stage}_complete.json')
        assert meta['input_sha256']==sha(HERE/'test_inputs_label_free.json')
        for p,h in meta['outputs'].items():assert sha(HERE/p)==h
        path=HERE/'cpu_features'/file
        frame=pd.read_csv(path,dtype={'example_id':str},float_precision='round_trip')
        assert frame.example_id.tolist()==ids
        for name in frame.columns[1:]:assert name not in all_columns;all_columns[name]=frame[name].to_numpy(float)
        stage_hashes[file]=sha(path)
    fact=read(HERE/'factcg_return.json');assert fact['report']['status']=='PASS'
    assert fact['report']['revision']==c['models']['FactCG']['revision'] and fact['report']['settings']==c['models']['FactCG']['settings']
    assert [str(r['id']) for r in fact['scores']]==ids
    for r,s in zip(inputs,fact['scores']):
        projected={'canonical_id':str(r['id']),'task':r['task'],'reference_text':r['src'] if r['task']=='PG' else r['tgt'],'whole_hypothesis':r['hyp']}
        expected=hashlib.sha256(json.dumps(projected,sort_keys=True,ensure_ascii=False,allow_nan=False).encode()).hexdigest()
        assert s['input_row_sha256']==expected
    all_columns['factcg_support_probability']=np.array([r['factcg_support_probability'] for r in fact['scores']])
    assert list(all_columns)==names
    matrix=pd.DataFrame(all_columns);assert matrix.shape==(1500,37) and np.isfinite(matrix.to_numpy()).all()
    for name in names:
        if any(x in name for x in ['entailment','neutral','contradiction','consistency','support_probability']) or name in ['src_ent','src_neu','src_con','tgt_ent','tgt_neu','tgt_con']:
            assert ((matrix[name]>=0)&(matrix[name]<=1)).all(),name
    definition_columns=names[14:25]+names[31:34]+[names[35]]
    assert len(definition_columns)==15
    unavailable=matrix.rag_evidence_available.to_numpy()==0
    assert (matrix.loc[unavailable,definition_columns].to_numpy()==0).all()
    assert set(matrix.rag_evidence_available)<= {0,1} and matrix.rag_sense_count.between(0,5).all()
    result=matrix.copy();result.insert(0,'id',ids)
    with (HERE/'E10_OFFICIAL_TEST_FEATURES.csv').open('x',encoding='utf-8',newline='') as f:result.to_csv(f,index=False)
    counts=dict(collections.Counter(r['task'] for r in inputs));assert counts=={'DM':563,'MT':562,'PG':375}
    write(HERE/'E10_OFFICIAL_TEST_FEATURES_MANIFEST.json',{'status':'PASS_FROZEN_BEFORE_TEST_GOLD','rows':1500,'ordered_features':names,'task_counts':counts,'test_inputs_sha256':sha(HERE/'test_inputs_label_free.json'),'features_sha256':sha(HERE/'E10_OFFICIAL_TEST_FEATURES.csv'),'stage_sha256':stage_hashes,'factcg_return_sha256':sha(HERE/'factcg_return.json'),'unexpected_missing_values':0,'feature_failures':0,'definition_zero_rows':int(unavailable.sum()),'models':c['models'],'cache_policy':'Reused frozen 561-row training feature matrix. Historical test feature files lack verified complete matching pinned E10 provenance; no such cache substituted. Stage checkpoints verified by input identity.'})
    training_path=ROOT/'RAG/results/phase3_e9_claim_verification/features/e10_return/E10.csv'
    train=pd.read_csv(training_path,float_precision='round_trip')
    metadata=pd.read_csv(ROOT/'codex/canonical_human_development_manifest.csv',keep_default_na=False)
    assert train.columns.tolist()==['canonical_id']+names and len(train)==561
    assert train.canonical_id.tolist()==metadata.canonical_id.tolist()
    assert np.isfinite(train[names].to_numpy(float)).all()
    model=RandomForestRegressor(**c['rf_parameters']);assert model.get_params()==c['rf_parameters']
    write(HERE/'PRESCORING_CODE_LOCK.json',{'files':{p.name:sha(p) for p in sorted(HERE.glob('*.py'))},'locked_unix':time.time()})
    write(HERE/'E10_OFFICIAL_TEST_TRAIN_MANIFEST.json',{'training_examples':561,'source_counts':dict(collections.Counter(metadata.source_split)),'task_counts':dict(collections.Counter(metadata.task)),'training_ids':metadata.canonical_id.tolist(),'training_matrix_sha256':sha(training_path),'training_manifest_sha256':c['source_sha256']['codex/canonical_human_development_manifest.csv'],'RF_parameters':c['rf_parameters'],'target':'p_hallucination','threshold':0.5,'clip':[0,1],'sklearn_version':sklearn.__version__,'expected_fits':1,'exact_test_overlap':0,'MT_source_target_overlaps_retained':14,'strict_547_pool_used':False,'limitation':'Shared MT source/target pairs have differing hypotheses. Prior exploratory official test use exists.'})
    write(HERE/'RF_FIT_STARTED.json',{'started_unix':time.time(),'fits_authorized':1})
    model.fit(train[names].to_numpy(float),metadata.p_hallucination.to_numpy(float))
    joblib.dump(model,HERE/'E10_FINAL_RF.joblib')
    predictions=np.clip(model.predict(matrix[names].to_numpy(float)),0,1)
    assert len(predictions)==1500 and np.isfinite(predictions).all()
    write(HERE/'RF_FIT_COMPLETED.json',{'completed_unix':time.time(),'actual_fits':1,'model_sha256':sha(HERE/'E10_FINAL_RF.joblib')})
    write(HERE/'E10_OFFICIAL_TEST_PREDICTIONS.json',{'evaluation_type':'reconstructed retrospective evaluation on the official labeled SHROOM test set','training_examples':561,'test_inputs_sha256':sha(HERE/'test_inputs_label_free.json'),'features_sha256':sha(HERE/'E10_OFFICIAL_TEST_FEATURES.csv'),'frozen_unix':time.time(),'predictions':[{'id':r['id'],'task':r['task'],'prediction':float(p),'predicted_label':'Hallucination' if p>=.5 else 'Not Hallucination'} for r,p in zip(inputs,predictions)]})
    (HERE/'E10_OFFICIAL_TEST_PREDICTIONS_SHA256.txt').write_text(sha(HERE/'E10_OFFICIAL_TEST_PREDICTIONS.json')+'  E10_OFFICIAL_TEST_PREDICTIONS.json\n',encoding='utf-8')
    _,hash_value=validated_predictions()
    coverage=read(HERE/'E10_RECONSTRUCTION_MANIFEST.json')['coverage']
    print('PREDICTIONS FROZEN: YES\nTraining examples: 561\nTest examples: 1500\nDM: 563\nMT: 562\nPG: 375',flush=True)
    print(json.dumps({'Reconstructed Wiktionary terms':coverage['reconstructed_terms_with_senses'],'Unavailable Wiktionary terms':coverage['unavailable_terms'],'Prediction SHA256':hash_value,'Any feature failures':0,'Any deviations from E10':'Wiktionary material reconstructed in 2026'},indent=2),flush=True)
def score():
    import numpy as np
    import e9_common as evaluator
    contract();data,prediction_hash=validated_predictions()
    for name,h in read(HERE/'PRESCORING_CODE_LOCK.json')['files'].items():assert sha(HERE/name)==h
    assert read(HERE/'RF_FIT_COMPLETED.json')['actual_fits']==1
    assert not (HERE/'E10_OFFICIAL_TEST_METRICS.json').exists()
    write(HERE/'SCORING_STARTED.json',{'prediction_sha256':prediction_hash,'started_unix':time.time(),'one_scoring_run':True})
    # First access to official gold in this evaluation, after prediction hash verification.
    gold=read(ROOT/'Labeled test/SHROOM_test-labeled/test.model-agnostic.json')
    byid={str(r['id']):r for r in gold};assert len(byid)==1500
    ordered=[byid[str(r['id'])] for r in data['predictions']]
    assert all(r['task']==p['task'] for r,p in zip(ordered,data['predictions']))
    assert set(r['label'] for r in ordered)=={'Hallucination','Not Hallucination'}
    y=np.array([int(r['label']=='Hallucination') for r in ordered]);target=np.array([r['p(Hallucination)'] for r in ordered],float)
    probabilities=np.array([r['prediction'] for r in data['predictions']]);pred=(probabilities>=.5).astype(int)
    def one(indices):
        indices=np.array(indices,dtype=int)
        metrics=evaluator.metric(y[indices],target[indices],probabilities[indices])
        cm=[[int(((y[indices]==a)&(pred[indices]==b)).sum()) for b in [0,1]] for a in [0,1]]
        return {**metrics,'confusion_matrix_NH_H':cm,'gold_counts':{'H':int(y[indices].sum()),'NH':int(len(indices)-y[indices].sum())},'predicted_counts':{'H':int(pred[indices].sum()),'NH':int(len(indices)-pred[indices].sum())}}
    metrics={'evaluation_type':'reconstructed retrospective evaluation on the official labeled SHROOM test set','overall':one(range(1500)),'by_task':{t:one([i for i,r in enumerate(ordered) if r['task']==t]) for t in ['DM','MT','PG']},'prediction_sha256':prediction_hash,'spearman_prediction_rounding_decimals':12,'RF_fits':1,'no_tuning_after_scoring':True,'scoring_completed_unix':time.time()}
    write(HERE/'E10_OFFICIAL_TEST_METRICS.json',metrics)
    assert sha(HERE/'E10_OFFICIAL_TEST_PREDICTIONS.json')==prediction_hash
    print(json.dumps(metrics,indent=2),flush=True)
if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('action',choices=['freeze','score']);args=parser.parse_args()
    freeze() if args.action=='freeze' else score()
