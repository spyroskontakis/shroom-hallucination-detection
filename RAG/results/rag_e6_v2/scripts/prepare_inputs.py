"""Prepare label-free text pairs from E6-v1's already selected definition."""
import json
import numpy as np
import pandas as pd
import v2_common as c


def pair_rows(text_rows,ranking,base):
    allowed={'canonical_id','task','src','tgt','hyp'}
    evidence={r['canonical_id']:r for r in ranking}
    assert len(evidence)==len(ranking)
    old=base.set_index('canonical_id')
    pairs=[];mapping=[]
    for row in text_rows:
        assert set(row)==allowed,'Unexpected fields in NLI input; labels forbidden'
        cid=row['canonical_id'];task=row['task']
        assert task in ['DM','MT','PG']
        for field in ['src','tgt','hyp']:assert isinstance(row[field],str) and row[field].strip(),(cid,field)
        reference=row['src'] if task=='PG' else row['tgt']
        selected=evidence[cid]['selected']
        assert bool(selected)==bool(old.loc[cid,'rag_evidence_available'])
        assert len(selected)==int(old.loc[cid,'rag_sense_count'])
        if selected:
            assert selected[0]['rank']==1
            assert abs(float(selected[0]['score'])-float(old.loc[cid,'rag_retrieval_top1_cosine']))<=1e-12
        mapping.append({'canonical_id':cid,'task':task,'reference_field':'src' if task=='PG' else 'tgt',
                        'evidence_available':int(bool(selected)),
                        'selected_evidence_id':selected[0]['evidence_id'] if selected else None,
                        'definition':selected[0]['candidate_definition'] if selected else None})
        definitions=[('A',reference,row['hyp']),('B',row['hyp'],reference)]
        if selected:
            definition=selected[0]['candidate_definition']
            assert isinstance(definition,str) and definition.strip()
            definitions.append(('C',definition,row['hyp']))
        for group,premise,hypothesis in definitions:
            pairs.append({'pair_id':f'{cid}:{group}','canonical_id':cid,'group':group,
                          'premise':premise,'hypothesis':hypothesis})
    return pairs,mapping


def main():
    if (c.OUT/'config/input_manifest.json').exists():raise FileExistsError('Input preparation already exists')
    original=c.read_json(c.E8/'config/protocol_freeze.json')['protected_sha256']
    protected=dict(original)
    for folder in [c.V1,c.E7,c.E8]:
        for path in folder.rglob('*'):
            if path.is_file():protected[path.relative_to(c.ROOT).as_posix()]=c.sha(path)
    for path,want in original.items():assert c.sha(c.ROOT/path)==want,path
    # Validate completed artifacts, including the originally frozen E6-v1 outputs.
    for folder in [c.V1,c.E7,c.E8]:
        completion=c.read_json(folder/'config/completion_manifest.json')
        for path,meta in completion['files'].items():
            want=meta['sha256'] if isinstance(meta,dict) else meta
            assert c.sha(folder/path)==want,(folder,path)
    for path in [c.CANONICAL,c.MIXED,c.FOLDS]:
        key=path.relative_to(c.ROOT).as_posix();assert key in protected
    c.write_json(c.OUT/'config/input_manifest.json',{'created_utc':c.now(),'protected_sha256':protected,
                 'mode':'hash verification only; no evaluation labels projected',
                 'new_feature_names':c.NEW,'primary_baseline':'E6-v1'})
    base=pd.read_csv(c.V1/'features/e6_25_features.csv',float_precision='round_trip')
    old_columns=c.read_json(c.V1/'config/feature_freeze.json')['predictors']
    assert base.columns.tolist()==['canonical_id']+old_columns and len(old_columns)==25
    assert len(base)==base.canonical_id.nunique()==561
    assert np.isfinite(base[old_columns].to_numpy()).all()
    ids=base.canonical_id.tolist()
    text=pd.read_csv(c.CANONICAL,usecols=['canonical_id','task','src','tgt','hyp'],keep_default_na=False)
    assert len(text)==text.canonical_id.nunique()==561 and set(text.canonical_id)==set(ids)
    text=text.set_index('canonical_id').loc[ids].reset_index()
    metadata=pd.read_csv(c.MIXED,usecols=['canonical_id','task','fold_id'])
    folds=pd.read_csv(c.FOLDS,usecols=['canonical_id','fold_id'])
    for df in [metadata,folds]:
        assert len(df)==df.canonical_id.nunique()==561 and set(df.canonical_id)==set(ids)
    metadata=metadata.set_index('canonical_id').loc[ids].reset_index()
    folds=folds.set_index('canonical_id').loc[ids].reset_index()
    assert np.array_equal(metadata.fold_id,folds.fold_id) and np.array_equal(metadata.task,text.task)
    assert folds.fold_id.value_counts().sort_index().tolist()==[113,112,112,112,112]
    saved=pd.read_csv(c.V1/'evaluation/e6_oof_predictions.csv')
    assert len(saved)==saved.canonical_id.nunique()==561 and set(saved.canonical_id)==set(ids)
    saved=saved.set_index('canonical_id').loc[ids].reset_index()
    assert np.array_equal(folds.fold_id,saved.fold_id)
    ranking=[json.loads(line) for line in (c.V1/'ranking/reconstructed_top5.jsonl').read_text(encoding='utf-8').splitlines()]
    assert len(ranking)==561 and {r['canonical_id'] for r in ranking}==set(ids)
    pairs,mapping=pair_rows(text.to_dict('records'),ranking,base)
    assert len(pairs)==561*2+193==1315
    c.write_json(c.OUT/'inputs/nli_pairs_label_free.json',pairs)
    c.write_json(c.OUT/'inputs/definition_reference_mapping.json',mapping)
    c.csv_write(c.OUT/'inputs/canonical_metadata_label_free.csv',metadata)
    c.csv_write(c.OUT/'inputs/locked_outer_folds.csv',folds)
    c.write_json(c.OUT/'config/input_checks.json',{'status':'PASS','rows':561,'old_features':old_columns,
                 'new_features':c.NEW,'total_features':34,'pairs':{'A':561,'B':561,'C':193},
                 'missing_definition_rows':368,'baseline_ids_folds_hashes':'PASS',
                 'no_labels_in_nli_inputs':True,'new_retrieval_or_reranking':False,
                 'created_utc':c.now(),'inputs_sha256':{p.relative_to(c.OUT).as_posix():c.sha(p)
                    for p in (c.OUT/'inputs').glob('*')}})
    print({'input_checks':'PASS','pairs':len(pairs),'protected_files':len(protected)},flush=True)


if __name__=='__main__':main()
