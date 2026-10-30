"""One frozen NLI block extraction, with resumable per-batch label-free scores."""
if "_H2_CTX" not in globals():
    raise RuntimeError("Historical source: use the pinned cross-experiment context; direct execution/import is disabled")
import time
import numpy as np
import pandas as pd
import v2_common as c


def assemble(base,pairs,scores):
    assert len(pairs)==len(scores) and len({s['pair_id'] for s in scores})==len(scores)
    lookup={s['pair_id']:s for s in scores}
    expected={(r['canonical_id'],r['group']) for r in pairs}
    assert set(lookup)=={r['pair_id'] for r in pairs}
    added=[]
    for _,row in base.iterrows():
        values={'canonical_id':row.canonical_id}
        for group,prefix in zip(['A','B','C'],c.PREFIXES):
            if group=='C' and row.rag_evidence_available==0:
                assert (row.canonical_id,'C') not in expected
                values.update({prefix+label:0.0 for label in c.LABELS})
                continue
            score=lookup[f'{row.canonical_id}:{group}']
            probs=np.array([score[label] for label in c.LABELS],dtype=float)
            assert np.isfinite(probs).all() and ((probs>=0)&(probs<=1)).all()
            assert abs(probs.sum()-1)<=2e-7
            values.update({prefix+label:score[label] for label in c.LABELS})
        added.append(values)
    new=pd.DataFrame(added)
    assert new.columns.tolist()==['canonical_id']+c.NEW
    full=base.merge(new,on='canonical_id',validate='one_to_one',sort=False)
    assert full.canonical_id.tolist()==base.canonical_id.tolist()
    assert np.array_equal(full[base.columns[1:]].to_numpy(),base.iloc[:,1:].to_numpy())
    assert np.isfinite(full.iloc[:,1:].to_numpy(float)).all()
    return new,full


def main():
    log=c.offline('extract')
    lock=c.verify_freeze();c.verify_models();c.versions()
    if (c.OUT/'config/feature_freeze.json').exists():raise FileExistsError('Features already frozen')
    from nli_backend import load_backend,infer_batch
    import torch
    assert torch.get_num_threads()==4 and torch.get_num_interop_threads()==4
    pairs=c.read_json(c.OUT/'inputs/nli_pairs_label_free.json')
    assert len(pairs)==1315
    start=c.now();t0=time.perf_counter()
    tokenizer,model=load_backend()
    assert lock['execution']=={'device':'cpu','dtype':'float32','batch_size':2}
    all_scores=[];all_audits=[];reused=0;inferred=0
    chunk_dir=c.OUT/'features/chunks';chunk_dir.mkdir(parents=True,exist_ok=True)
    for begin in range(0,len(pairs),2):
        end=min(begin+2,len(pairs));batch=pairs[begin:end]
        path=chunk_dir/f'batch_{begin//2:04d}.json'
        if path.exists():
            cache=c.read_json(path)
            assert cache['config_sha256']==c.sha(c.OUT/'config/run_config.json')
            assert cache['pair_ids']==[r['pair_id'] for r in batch]
            scores,audits=cache['scores'],cache['truncation'];reused+=len(batch)
        else:
            scores,audits=infer_batch(tokenizer,model,batch);inferred+=len(batch)
            c.write_json(path,{'pair_ids':[r['pair_id'] for r in batch],'scores':scores,'truncation':audits,
                         'config_sha256':c.sha(c.OUT/'config/run_config.json'),'completed_utc':c.now()})
        all_scores+=scores;all_audits+=audits
        if end%100==0 or end==len(pairs):print(f'NLI pairs {end}/{len(pairs)}',flush=True)
    base=pd.read_csv(c.V1/'features/e6_25_features.csv',float_precision='round_trip')
    new,full=assemble(base,pairs,all_scores)
    assert len(full)==561 and full.columns.tolist()==['canonical_id']+lock['features']
    c.csv_write(c.OUT/'features/nli2_pair_scores.csv',pd.DataFrame(all_scores))
    c.csv_write(c.OUT/'features/truncation_audit.csv',pd.DataFrame(all_audits))
    c.csv_write(c.OUT/'features/e6_v2_added_9_features.csv',new)
    c.csv_write(c.OUT/'features/e6_v2_34_features.csv',full)
    check=pd.read_csv(c.OUT/'features/e6_v2_34_features.csv',float_precision='round_trip')
    assert np.array_equal(check.iloc[:,:26].to_numpy(),base.to_numpy())
    audit=pd.DataFrame(all_audits)
    summary={'pairs':len(pairs),'truncated_pairs':int(audit.truncated.sum()),
             'truncated_canonical_rows':int(audit.loc[audit.truncated,'canonical_id'].nunique()),
             'by_group':{g:{'pairs':len(d),'truncated':int(d.truncated.sum()),
                           'max_original_tokens':int(d.original_tokens.max())} for g,d in audit.groupby('group')}}
    c.verify_freeze();assert log.stat().st_size==0
    c.write_json(c.OUT/'config/feature_freeze.json',{'status':'FROZEN_BEFORE_EVALUATION_LABEL_JOIN',
                 'started_utc':start,'completed_utc':c.now(),'duration_seconds':time.perf_counter()-t0,
                 'rows':561,'old_features_unchanged':25,'new_features':9,'total_features':34,
                 'pairs_inferred_this_execution':inferred,'pairs_reused_from_cache':reused,
                 'truncation':summary,'network_attempts':0,
                 'files':{p.relative_to(c.OUT).as_posix():c.sha(p) for p in (c.OUT/'features').rglob('*') if p.is_file()}})
    print({'feature_freeze':'PASS','truncation':summary,'seconds':time.perf_counter()-t0},flush=True)


if __name__=='__main__':main()
