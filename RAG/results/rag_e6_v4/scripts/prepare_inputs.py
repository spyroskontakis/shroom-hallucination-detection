"""Reuse exact frozen A pairs; no labels, predictions or definitions projected."""
import numpy as np
import pandas as pd
import v4_common as c
def main():
    original=c.read_json(c.ANALYSIS/'input_verification.json')['protected_sha256'];protected=dict(original)
    for p,h in original.items():assert c.sha(c.ROOT/p)==h,p
    completed=c.read_json(c.ANALYSIS/'analysis_completion_manifest.json')
    for p,h in completed['files'].items():
        actual=c.ANALYSIS/p;assert c.sha(actual)==h,p
        protected[actual.relative_to(c.ROOT).as_posix()]=h
    manifest=c.ANALYSIS/'analysis_completion_manifest.json';protected[manifest.relative_to(c.ROOT).as_posix()]=c.sha(manifest)
    # Do not walk the analysis node_modules junction; it is not an experiment artifact.
    c.write_json(c.OUT/'config/input_manifest.json',{'created_utc':c.now(),'protected_sha256':protected,
                 'source':'E6-v3 and completed diagnostic analysis manifests','labels_projected':False})
    base=pd.read_csv(c.V3/'features/e6_v3_36_features.csv',float_precision='round_trip')
    cols=c.read_json(c.V3/'config/run_config.json')['features']
    assert base.columns.tolist()==['canonical_id']+cols and len(cols)==36
    assert len(base)==base.canonical_id.nunique()==561 and np.isfinite(base[cols].to_numpy()).all()
    ids=base.canonical_id.tolist()
    pairs=[p for p in c.read_json(c.V2/'inputs/nli_pairs_label_free.json') if p['group']=='A']
    v3pairs=[p for p in c.read_json(c.V3/'inputs/hhem_pairs_label_free.json') if p['group']=='A']
    assert pairs==v3pairs and [p['canonical_id'] for p in pairs]==ids
    assert all(set(p)=={'pair_id','canonical_id','group','premise','hypothesis'} for p in pairs)
    metadata=pd.read_csv(c.V3/'inputs/canonical_metadata_label_free.csv')
    folds=pd.read_csv(c.V3/'inputs/locked_outer_folds.csv')
    approved=pd.read_csv(c.FOLDS,usecols=['canonical_id','fold_id']).set_index('canonical_id').loc[ids].reset_index()
    for d in [metadata,folds,approved]:
        assert d.canonical_id.tolist()==ids and np.array_equal(d.fold_id,approved.fold_id)
    assert folds.fold_id.value_counts().sort_index().tolist()==[113,112,112,112,112]
    reference_mapping=c.read_json(c.V2/'inputs/definition_reference_mapping.json')
    assert [r['canonical_id'] for r in reference_mapping]==ids
    for r,meta in zip(reference_mapping,metadata.to_dict('records')):
        assert r['reference_field']==('src' if meta['task']=='PG' else 'tgt')
    c.write_json(c.OUT/'inputs/coverage_pairs_label_free.json',pairs)
    c.csv_write(c.OUT/'inputs/locked_outer_folds.csv',folds)
    c.csv_write(c.OUT/'inputs/canonical_metadata_label_free.csv',metadata)
    c.write_json(c.OUT/'config/input_checks.json',{'status':'PASS','rows':561,'old_features':cols,'new_features':c.NEW,
                 'exact_pair_text_reuse':True,'definitions_in_new_features':False,'total_features':43,
                 'no_labels_in_extraction_inputs':True,'protected_files':len(protected)})
    print({'inputs':'PASS','protected':len(protected)},flush=True)
if __name__=='__main__':main()
