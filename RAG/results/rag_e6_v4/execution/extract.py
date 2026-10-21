"""561 frozen label-free pairs, official BERTScore + unchanged structural code."""
import common as c
import time,traceback
def main():
 log=c.offline('extraction');env=c.runtime('encoding');lock=c.verify_freeze();c.protected();c.assets()
 import numpy as np,pandas as pd,torch
 import structure
 from bert_score.utils import sent_encode
 assert c.read(c.HERE/'synthetic_contract.json')['status']=='PASS'
 pairs=c.read(c.V4/'inputs/coverage_pairs_label_free.json')
 base=pd.read_csv(c.V3/'features/e6_v3_36_features.csv',float_precision='round_trip')
 ids=base.canonical_id.tolist();old=lock['original_features'];new=lock['new_features']
 assert len(ids)==len(set(ids))==len(pairs)==561
 assert base.columns.tolist()==['canonical_id']+old and len(old)==36
 assert [x['canonical_id'] for x in pairs]==ids
 assert all(set(x)=={'pair_id','canonical_id','group','premise','hypothesis'} for x in pairs)
 assert all(x['group']=='A' and isinstance(x['premise'],str) and isinstance(x['hypothesis'],str) for x in pairs)
 c.write(c.HERE/'extraction_started.json',{'started_utc':c.now(),'planned_rows':561,'freeze_sha256':c.sha(c.HERE/'run_config.json')})
 start=time.perf_counter();s=c.scorer();loadseconds=time.perf_counter()-start
 assert s.hash==lock['bertscore']['hash_string']
 trunc=[];rows=[]
 for offset in range(0,561,16):
  batch=pairs[offset:offset+16]
  for pair in batch:
   item={'canonical_id':pair['canonical_id']}
   for field,name in [('premise','reference'),('hypothesis','hyp')]:
    text=pair[field];untruncated=s._tokenizer.encode(text.strip(),add_special_tokens=True,truncation=False)
    actual=sent_encode(s._tokenizer,text)
    assert len(actual)==min(len(untruncated),512),(pair['canonical_id'],name)
    assert len(actual)<=512
    item[name+'_original_tokens']=len(untruncated);item[name+'_used_tokens']=len(actual)
    item[name+'_truncated']=len(untruncated)>512;item[name+'_empty_after_strip']=not bool(text.strip())
   trunc.append(item)
  with torch.inference_mode():P,R,F=s.score(cands=[x['hypothesis'] for x in batch],refs=[x['premise'] for x in batch],batch_size=2)
  assert torch.isfinite(torch.stack([P,R,F])).all(),'Non-finite BERTScore: stop'
  current=[]
  for i,pair in enumerate(batch):
   row={'canonical_id':pair['canonical_id'],new[0]:float(P[i]),new[1]:float(R[i]),new[2]:float(F[i]),
        **structure.features(pair['premise'],pair['hypothesis'])}
   assert list(row)==['canonical_id']+new
   current.append(row)
  c.write(c.HERE/f'chunks/chunk_{offset:04d}.json',current);rows+=current
  print(f'Extracted {len(rows)}/561',flush=True)
 features=pd.DataFrame(rows);combined=pd.concat([base,features[new]],axis=1)
 assert features.canonical_id.tolist()==ids and combined.columns.tolist()==['canonical_id']+lock['features']
 assert np.array_equal(combined[old].to_numpy(),base[old].to_numpy())
 assert np.isfinite(combined[lock['features']].to_numpy()).all()
 assert log.stat().st_size==0
 c.csvwrite(c.V4/'features/e6_v4_new_7_features.csv',features)
 c.csvwrite(c.V4/'features/e6_v4_43_features.csv',combined)
 c.csvwrite(c.V4/'features/truncation_audit.csv',pd.DataFrame(trunc))
 saved=pd.read_csv(c.V4/'features/e6_v4_43_features.csv',float_precision='round_trip')
 assert np.array_equal(saved[old].to_numpy(),base[old].to_numpy())
 assert np.array_equal(saved[lock['features']].to_numpy(),combined[lock['features']].to_numpy())
 audit=c.protected();c.verify_freeze()
 summary={'status':'PASS','rows':561,'features':43,'old_features_exact':True,'ordered_ids_exact':True,
  'no_labels_or_predictions_in_extraction_inputs':True,'nonfinite':0,'missing_values':0,'invalid_values':0,
  'reference_truncated':sum(x['reference_truncated'] for x in trunc),'hyp_truncated':sum(x['hyp_truncated'] for x in trunc),
  'empty_references':sum(x['reference_empty_after_strip'] for x in trunc),'empty_hyp':sum(x['hyp_empty_after_strip'] for x in trunc),
  'seconds_total':time.perf_counter()-start,'model_load_seconds':loadseconds,'network_attempts':0,'runtime':env,
  'statistics':{col:{'min':float(features[col].min()),'max':float(features[col].max()),'mean':float(features[col].mean())} for col in new},
  'integrity':audit}
 c.write(c.HERE/'extraction_contracts.json',summary)
 paths=['features/e6_v4_new_7_features.csv','features/e6_v4_43_features.csv','features/truncation_audit.csv','execution/extraction_contracts.json']
 c.write(c.HERE/'feature_freeze.json',{'status':'PASS','frozen_utc':c.now(),'files':{p:c.sha(c.V4/p) for p in paths},'rows':561,'features':43,'RF_fits':0})
 print('Feature matrix frozen: PASS',flush=True)
if __name__=='__main__':
 try:main()
 except Exception as e:
  c.write(c.HERE/'extraction_failure.json',{'error':repr(e),'traceback':traceback.format_exc(),'RF_evaluation_allowed':False});raise
