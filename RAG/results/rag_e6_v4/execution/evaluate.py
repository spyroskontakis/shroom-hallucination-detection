"""Exactly five fixed RF fits after verified feature freeze; no baseline fits."""
import common as c
import time,traceback
import numpy as np,pandas as pd
from scipy.stats import spearmanr,binomtest
from sklearn.ensemble import RandomForestRegressor
def metric(df,col):
 p=df[col].to_numpy();y=df.label_bin.to_numpy();t=df.p_hallucination.to_numpy()
 assert len(df)>0 and np.isfinite(p).all() and ((p>=0)&(p<=1)).all()
 good=int(((p>=.5).astype(int)==y).sum());rank=np.round(p,12)
 rho=float(spearmanr(t,rank).statistic) if len(np.unique(t))>1 and len(np.unique(rank))>1 else None
 return {'n':len(df),'correct':good,'accuracy':good/len(df),'spearman':rho}
def paired(df):
 old=df['E6-v3_correct'].to_numpy(bool);new=df['E6-v4_correct'].to_numpy(bool)
 b=int((~old&new).sum());e=int((old&~new).sum());delta=new.astype(int)-old.astype(int)
 rng=np.random.default_rng(42)
 samples=np.array([delta[rng.integers(0,len(delta),len(delta))].mean() for _ in range(10000)])
 lo,hi=np.quantile(samples,[.025,.975]).tolist()
 return {'corrected':b,'regressions':e,'net_correct':b-e,'both_correct':int((old&new).sum()),'both_wrong':int((~old&~new).sum()),
  'accuracy_difference':float(delta.mean()),'mcnemar_exact_two_sided_p':float(binomtest(b,b+e,.5).pvalue) if b+e else 1.,
  'bootstrap':{'resamples':10000,'seed':42,'rng':'default_rng','percentile_95_ci':[lo,hi]},
  'corrected_ids':df.loc[~old&new,'canonical_id'].tolist(),'regression_ids':df.loc[old&~new,'canonical_id'].tolist()}
def main():
 log=c.offline('evaluation');env=c.runtime('evaluation');lock=c.verify_freeze();c.protected()
 freeze=c.read(c.HERE/'feature_freeze.json');assert freeze['status']=='PASS'
 for p,h in freeze['files'].items():assert c.sha(c.V4/p)==h,p
 assert not (c.HERE/'extraction_failure.json').exists()
 features=pd.read_csv(c.V4/'features/e6_v4_43_features.csv',float_precision='round_trip')
 base=pd.read_csv(c.V3/'features/e6_v3_36_features.csv',float_precision='round_trip')
 ids=features.canonical_id.tolist();cols=lock['features']
 assert len(ids)==len(set(ids))==561 and features.columns.tolist()==['canonical_id']+cols
 assert ids==base.canonical_id.tolist() and np.array_equal(features[lock['original_features']].to_numpy(),base.iloc[:,1:].to_numpy())
 assert np.isfinite(features[cols].to_numpy()).all()
 def align(path):
  x=pd.read_csv(path,float_precision='round_trip');assert len(x)==x.canonical_id.nunique()==561 and set(x.canonical_id)==set(ids)
  return x.set_index('canonical_id').loc[ids].reset_index()
 gold=align(c.ROOT/'codex/canonical_human_development_manifest.csv')
 mixed=align(c.ROOT/'codex/canonical_feature_outputs/canonical_human_14_features.csv')
 folds=align(c.V4/'inputs/locked_outer_folds.csv');approved=align(c.ROOT/'codex/canonical_fold_assignments.csv')
 old=align(c.V3/'evaluation/e6_v3_oof_predictions.csv');oldrows=align(c.V3/'evaluation/paired_row_diagnostics.csv')
 for df in [mixed,approved,old,oldrows]:assert np.array_equal(df.fold_id,folds.fold_id)
 for name in ['label_bin','p_hallucination','task']:
  assert np.array_equal(gold[name],mixed[name]) and np.array_equal(gold[name],oldrows[name])
 assert np.array_equal(old.prediction,oldrows['E6-v3'])
 assert gold.source_split.value_counts().to_dict()=={'development_model_agnostic':493,'trial':68}
 frame=gold[['canonical_id','task','label_bin','p_hallucination']].copy()
 frame['fold_id']=folds.fold_id;frame['rag_evidence_available']=features.rag_evidence_available
 frame['E6-v3']=old.prediction
 expected=c.read(c.V3/'evaluation/e6_v3_metrics.json')['diagnostics']['all_rows']['E6-v3']
 assert metric(frame,'E6-v3')==expected and expected['correct']==474
 assert (frame.loc[frame.rag_evidence_available==1,'task']=='DM').all()
 params=lock['random_forest'];assert params==c.read(c.V3/'config/run_config.json')['random_forest']
 assert RandomForestRegressor(**params).get_params()==params
 c.write(c.HERE/'baseline_verification_final.json',{'status':'PASS','metrics':expected,'IDs_folds_labels_predictions_exact':True,'baseline_fits':0})
 c.write(c.HERE/'evaluation_started.json',{'started_utc':c.now(),'planned_fits':5,'configuration_count':1,'feature_freeze_sha256':c.sha(c.HERE/'feature_freeze.json'),'baseline_fits':0})
 start=time.perf_counter();pred=np.full(561,np.nan);records=[]
 for fold in range(1,6):
  train=frame.fold_id.to_numpy()!=fold;valid=~train
  assert set(frame.loc[train,'canonical_id']).isdisjoint(frame.loc[valid,'canonical_id'])
  record={'fold':fold,'started_utc':c.now(),'train_ids':frame.loc[train,'canonical_id'].tolist(),'validation_ids':frame.loc[valid,'canonical_id'].tolist(),'parameters':params}
  c.write(c.HERE/f'fit_{fold}_started.json',record)
  model=RandomForestRegressor(**params)
  model.fit(features.loc[train,cols].to_numpy(float),frame.loc[train,'p_hallucination'].to_numpy(float))
  p=np.clip(model.predict(features.loc[valid,cols].to_numpy(float)),0,1)
  assert np.isfinite(p).all();pred[valid]=p
  record['completed_utc']=c.now();records.append(record);c.write(c.HERE/f'fit_{fold}_completed.json',record)
  # Cache each validation output immediately; never run a second fit to repair IO.
  c.csvwrite(c.V4/f'evaluation/fold_{fold}_predictions.csv',pd.DataFrame({'canonical_id':frame.loc[valid,'canonical_id'],'fold_id':fold,'prediction':p}))
  print(f'RF fold {fold}/5 completed',flush=True)
 assert np.isfinite(pred).all() and len(records)==5
 frame['E6-v4']=pred
 for name in ['E6-v3','E6-v4']:
  frame[name+'_binary']=(frame[name]>=.5).astype(int);frame[name+'_correct']=frame[name+'_binary']==frame.label_bin
 frame['change']=np.select([~frame['E6-v3_correct']&frame['E6-v4_correct'],frame['E6-v3_correct']&~frame['E6-v4_correct']],['correction','regression'],default='unchanged_correctness')
 c.csvwrite(c.V4/'evaluation/e6_v4_oof_predictions.csv',pd.DataFrame({'canonical_id':ids,'fold_id':frame.fold_id,'prediction':pred}))
 c.csvwrite(c.V4/'evaluation/paired_row_diagnostics.csv',frame)
 diagnostics={'all_rows':{n:metric(frame,n) for n in ['E6-v3','E6-v4']}}
 for name,column in [('per_fold','fold_id'),('per_task','task'),('per_evidence','rag_evidence_available')]:
  diagnostics[name]={str(k):{n:metric(g,n) for n in ['E6-v3','E6-v4']} for k,g in frame.groupby(column)}
 diagnostics['DM_evidence']={str(k):{n:metric(g,n) for n in ['E6-v3','E6-v4']} for k,g in frame[frame.task=='DM'].groupby('rag_evidence_available')}
 result={'status':'PASS','diagnostics':diagnostics,'paired':paired(frame),'RF_fits':5,'baseline_fits':0,'evaluations':1,
  'seconds':time.perf_counter()-start,'runtime':env,'statistics_scope':'adaptive exploratory development-only; descriptive exploratory statistics'}
 assert log.stat().st_size==0;c.verify_freeze();c.protected()
 c.write(c.V4/'evaluation/e6_v4_metrics.json',result)
 c.write(c.HERE/'evaluation_completed.json',{'status':'PASS','completed_utc':c.now(),'RF_fits':5,'OOF_evaluations':1,'rows':561,'network_attempts':0})
 print(result['diagnostics']['all_rows'],flush=True)
if __name__=='__main__':
 try:main()
 except Exception as e:
  c.write(c.HERE/'evaluation_failure.json',{'error':repr(e),'traceback':traceback.format_exc()});raise
