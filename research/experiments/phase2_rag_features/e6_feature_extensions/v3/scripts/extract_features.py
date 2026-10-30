"""Frozen HHEM inference with verified, atomic per-batch checkpoints."""
if "_H2_CTX" not in globals():
    raise RuntimeError("Historical source: use the pinned cross-experiment context; direct execution/import is disabled")
import json, time, os, uuid
import numpy as np
import pandas as pd
from scipy.special import expit
import v3_common as c

def digest(value):
    return c.hashlib.sha256(json.dumps(value,sort_keys=True,ensure_ascii=False,allow_nan=False).encode('utf-8')).hexdigest()

def validate_cache(cache,batch,config_sha):
    assert cache['config_sha256']==config_sha and cache['pairs_sha256']==digest(batch)
    assert cache['pair_ids']==[p['pair_id'] for p in batch]
    assert cache['payload_sha256']==digest({k:v for k,v in cache.items() if k!='payload_sha256'})
    scores,audits=cache['scores'],cache['truncation']
    assert len(scores)==len(audits)==len(batch)
    for p,s,a in zip(batch,scores,audits):
        for key in ['pair_id','canonical_id','group']:assert p[key]==s[key]==a[key]
        assert set(s)=={'pair_id','canonical_id','group','logit','consistency'}
        assert np.isfinite(s['logit']) and np.isfinite(s['consistency']) and 0<=s['consistency']<=1
        assert abs(expit(s['logit'])-s['consistency'])<=1e-7
        assert a['encoded_tokens']==min(a['original_tokens'],512)
        assert a['truncated']==(a['original_tokens']>512)
        assert a['premise_tokens_removed']>=0 and a['hypothesis_tokens_removed']>=0
        assert a['original_tokens']-a['encoded_tokens']==a['premise_tokens_removed']+a['hypothesis_tokens_removed']
        assert a['encoded_tokens']<=a['batch_padded_length']<=512
    return scores,audits

def persist_cache(path,payload):
    assert not path.exists()
    payload={**payload,'payload_sha256':digest(payload)}
    temporary=path.with_name(path.name+'.pending_'+uuid.uuid4().hex)
    temporary.resolve().relative_to(c.OUT)
    with temporary.open('x',encoding='utf-8',newline='\n') as f:
        json.dump(payload,f,sort_keys=True,indent=2,ensure_ascii=False,allow_nan=False)
        f.write('\n');f.flush();os.fsync(f.fileno())
    assert not path.exists();os.replace(temporary,path)
    return payload

def assemble(base,pairs,scores):
    assert len(pairs)==len(scores) and len({s['pair_id'] for s in scores})==len(scores)
    lookup={s['pair_id']:s for s in scores}
    assert set(lookup)=={r['pair_id'] for r in pairs}
    added=[]
    for row in base.to_dict('records'):
        cid=row['canonical_id'];a=lookup[cid+':A']['consistency']
        if row['rag_evidence_available']==0:
            assert cid+':C' not in lookup;d=0.
        else:d=lookup[cid+':C']['consistency']
        assert np.isfinite([a,d]).all() and 0<=a<=1 and 0<=d<=1
        added.append({'canonical_id':cid,c.NEW[0]:a,c.NEW[1]:d})
    new=pd.DataFrame(added)
    full=base.merge(new,on='canonical_id',validate='one_to_one',sort=False)
    assert full.canonical_id.tolist()==base.canonical_id.tolist()
    assert np.array_equal(full[base.columns].to_numpy(),base.to_numpy())
    assert np.isfinite(full.iloc[:,1:].to_numpy(float)).all()
    return new,full

def csv_checkpoint(path,df):
    if path.exists():
        saved=pd.read_csv(path,float_precision='round_trip')
        assert saved.columns.tolist()==df.columns.tolist()
        np.testing.assert_array_equal(saved.to_numpy(),df.to_numpy())
    else:c.csv_write(path,df)

def main():
    log=c.offline('extract');lock=c.verify_freeze();c.verify_models();c.versions()
    frozen=c.OUT/'config/feature_freeze.json'
    if frozen.exists():
        for p,want in c.read_json(frozen)['files'].items():assert c.sha(c.OUT/p)==want
        print('Features already frozen and verified; no inference');return
    from hhem_backend import load_backend,infer_batch
    import torch
    assert torch.get_num_threads()==4 and torch.get_num_interop_threads()==4
    pairs=c.read_json(c.OUT/'inputs/hhem_pairs_label_free.json');assert len(pairs)==754
    assert lock['execution']=={'device':'cpu','dtype':'float32','batch_size':2}
    start=c.now();t0=time.perf_counter();session=uuid.uuid4().hex
    c.write_json(c.OUT/f'config/extraction_sessions/{session}_started.json',{'utc':start,'pid':os.getpid()})
    all_scores=[];all_audits=[];reused=0;inferred=0;batch_seconds=0.;backend=None
    config_sha=c.sha(c.OUT/'config/run_config.json')
    chunks=c.OUT/'features/chunks';chunks.mkdir(parents=True,exist_ok=True)
    for begin in range(0,len(pairs),2):
        batch=pairs[begin:begin+2];path=chunks/f'batch_{begin//2:04d}.json'
        if path.exists():
            cache=c.read_json(path);scores,audits=validate_cache(cache,batch,config_sha);reused+=len(batch)
        else:
            if backend is None:backend=load_backend()
            tick=time.perf_counter();scores,audits=infer_batch(*backend,batch)
            payload={'config_sha256':config_sha,'pairs_sha256':digest(batch),'pair_ids':[p['pair_id'] for p in batch],
                     'scores':scores,'truncation':audits,'completed_utc':c.now(),'inference_seconds':time.perf_counter()-tick}
            cache=persist_cache(path,payload);validate_cache(cache,batch,config_sha);inferred+=len(batch)
        batch_seconds+=cache['inference_seconds'];all_scores+=scores;all_audits+=audits
        if (begin+2)%100==0 or begin+2==len(pairs):print(f'HHEM pairs {begin+len(batch)}/{len(pairs)}',flush=True)
    base=pd.read_csv(c.V2/'features/e6_v2_34_features.csv',float_precision='round_trip')
    new,full=assemble(base,pairs,all_scores)
    assert len(full)==561 and full.columns.tolist()==['canonical_id']+lock['features']
    for name,df in [('hhem_pair_scores',pd.DataFrame(all_scores)),('truncation_audit',pd.DataFrame(all_audits)),
                    ('e6_v3_added_2_features',new),('e6_v3_36_features',full)]:csv_checkpoint(c.OUT/f'features/{name}.csv',df)
    restored=pd.read_csv(c.OUT/'features/e6_v3_36_features.csv',float_precision='round_trip')
    np.testing.assert_array_equal(restored.iloc[:,:35].to_numpy(),base.to_numpy())
    audit=pd.DataFrame(all_audits)
    summary={'pairs':len(pairs),'truncated_pairs':int(audit.truncated.sum()),
             'truncated_canonical_rows':int(audit.loc[audit.truncated,'canonical_id'].nunique()),
             'by_group':{g:{'pairs':len(d),'truncated':int(d.truncated.sum()),'max_original_tokens':int(d.original_tokens.max())}
                         for g,d in audit.groupby('group')}}
    c.verify_freeze();assert log.stat().st_size==0
    seconds=time.perf_counter()-t0
    c.write_json(c.OUT/f'config/extraction_sessions/{session}_completed.json',{'started_utc':start,'completed_utc':c.now(),
                 'duration_seconds':seconds,'inferred':inferred,'reused':reused})
    c.write_json(frozen,{'status':'FROZEN_BEFORE_EVALUATION_LABEL_JOIN','started_utc':start,'completed_utc':c.now(),
                 'duration_seconds':seconds,'summed_batch_inference_seconds':batch_seconds,
                 'rows':561,'old_features_unchanged':34,'new_features':2,'total_features':36,
                 'pairs_inferred_this_execution':inferred,'pairs_reused_from_cache':reused,'verified_completed_batches':377,
                 'truncation':summary,'network_attempts':0,
                 'files':{p.relative_to(c.OUT).as_posix():c.sha(p) for p in (c.OUT/'features').rglob('*') if p.is_file()}})
    print({'feature_freeze':'PASS','truncation':summary,'seconds':seconds},flush=True)

if __name__=='__main__':main()
