"""Hash prior artifacts and project exact saved A/C pairs without evaluation labels."""
import shutil
import numpy as np
import pandas as pd
import v3_common as c

def select_pairs(pairs):
    selected=[p for p in pairs if p['group'] in ['A','C']]
    assert all(set(p)=={'pair_id','canonical_id','group','premise','hypothesis'} for p in selected)
    assert len({p['pair_id'] for p in selected})==len(selected)
    assert all(p['pair_id']==p['canonical_id']+':'+p['group'] for p in selected)
    assert all(isinstance(p[k],str) and p[k].strip() for p in selected for k in ['premise','hypothesis'])
    return selected

def main():
    original=c.read_json(c.V2/'config/input_manifest.json')['protected_sha256']
    for path,want in original.items():assert c.sha(c.ROOT/path)==want,path
    protected=dict(original)
    for folder in [c.V1,c.V2,c.E7,c.E8]:
        complete=c.read_json(folder/'config/completion_manifest.json')
        for path,meta in complete['files'].items():
            want=meta['sha256'] if isinstance(meta,dict) else meta
            assert c.sha(folder/path)==want,(folder,path)
        for p in folder.rglob('*'):
            if p.is_file():
                key=p.relative_to(c.ROOT).as_posix();actual=c.sha(p)
                if key in protected:assert protected[key]==actual
                protected[key]=actual
    c.write_json(c.OUT/'config/input_manifest.json',{'created_utc':c.now(),'protected_sha256':protected,
                 'baseline':'E6-v2','mode':'hash only; no label projection'})
    base=pd.read_csv(c.V2/'features/e6_v2_34_features.csv',float_precision='round_trip')
    columns=c.read_json(c.V2/'config/run_config.json')['features']
    assert base.columns.tolist()==['canonical_id']+columns and len(columns)==34
    assert len(base)==base.canonical_id.nunique()==561 and np.isfinite(base[columns].to_numpy()).all()
    ids=base.canonical_id.tolist()
    assert c.sha(c.V2/'features/e6_v2_34_features.csv')=='9d130665cd48ece1a75ca313c2f1220012fd9e935f1df678cb082bdf65811531'
    for name in ['canonical_metadata_label_free.csv','locked_outer_folds.csv','definition_reference_mapping.json']:
        dest=c.OUT/'inputs'/name
        assert not dest.exists();shutil.copyfile(c.V2/'inputs'/name,dest)
        assert c.sha(dest)==c.sha(c.V2/'inputs'/name)
    metadata=pd.read_csv(c.OUT/'inputs/canonical_metadata_label_free.csv')
    folds=pd.read_csv(c.OUT/'inputs/locked_outer_folds.csv')
    canonical_folds=pd.read_csv(c.FOLDS,usecols=['canonical_id','fold_id']).set_index('canonical_id').loc[ids].reset_index()
    saved=pd.read_csv(c.V2/'evaluation/e6_v2_oof_predictions.csv',usecols=['canonical_id','fold_id'])
    for df in [metadata,folds,canonical_folds,saved]:
        assert df.canonical_id.tolist()==ids and df.canonical_id.nunique()==561
        assert np.array_equal(df.fold_id,folds.fold_id)
    assert folds.fold_id.value_counts().sort_index().tolist()==[113,112,112,112,112]
    pairs=select_pairs(c.read_json(c.V2/'inputs/nli_pairs_label_free.json'))
    mapping=c.read_json(c.OUT/'inputs/definition_reference_mapping.json')
    assert [m['canonical_id'] for m in mapping]==ids
    lookup={p['pair_id']:p for p in pairs}
    assert len(pairs)==754 and sum(p['group']=='A' for p in pairs)==561 and sum(p['group']=='C' for p in pairs)==193
    for m,row in zip(mapping,base.to_dict('records')):
        cid=row['canonical_id'];assert m['evidence_available']==row['rag_evidence_available']
        assert m['reference_field']==('src' if m['task']=='PG' else 'tgt')
        a=lookup[cid+':A']
        if m['evidence_available']:
            d=lookup[cid+':C'];assert d['premise']==m['definition'] and d['hypothesis']==a['hypothesis']
        else:assert cid+':C' not in lookup and m['definition'] is None
    c.write_json(c.OUT/'inputs/hhem_pairs_label_free.json',pairs)
    c.write_json(c.OUT/'config/input_checks.json',{'status':'PASS','rows':561,'original_features':columns,
                 'new_features':c.NEW,'total_features':36,'pairs':{'A':561,'C':193},'missing_definition_rows':368,
                 'saved_pairs_reused_verbatim':True,'baseline_ids_folds_verified':True,'labels_projected':False,
                 'protected_files':len(protected)})
    print({'inputs':'PASS','protected':len(protected),'pairs':len(pairs)},flush=True)

if __name__=='__main__':main()
