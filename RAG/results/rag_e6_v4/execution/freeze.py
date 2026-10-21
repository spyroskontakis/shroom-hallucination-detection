"""Seal fixed execution code/configuration after synthetic PASS and amendment."""
import common as c
import ast
def main():
 log=c.offline('freeze');env=c.runtime('encoding');c.protected();assets=c.assets()
 smoke=c.read(c.HERE/'synthetic_contract.json');assert smoke['status']=='PASS' and smoke['network_attempts']==0
 assert not (c.HERE/'extraction_started.json').exists() and not (c.HERE/'evaluation_started.json').exists()
 old=c.read(c.V4/'config/run_config.json');schema=c.read(c.V4/'config/feature_schema.json')
 import structure
 assert structure.SPEC==c.read(c.V4/'config/structure_spec.json') and structure.contracts()=='PASS'
 assert old['features']==schema['ordered_features'] and len(old['features'])==43
 assert old['random_forest']==c.read(c.V3/'config/run_config.json')['random_forest']
 for name in ['common.py','smoke.py','freeze.py','extract.py','evaluate.py','report.py']:
  ast.parse((c.HERE/name).read_text(encoding='utf-8'))
 # Explicit input/code inventory: none of these declarations reads labels for encoding.
 names=['E6_V4_PROTOCOL.md','E6_V4_PROTOCOL_AMENDMENT_01.md','config/run_config.json',
 'config/input_manifest.json','config/feature_schema.json','config/structure_spec.json','scripts/structure.py',
 'inputs/coverage_pairs_label_free.json','inputs/locked_outer_folds.csv','inputs/canonical_metadata_label_free.csv',
 'compatibility_analysis/E6_V4_COMPATIBILITY_ANALYSIS.md','compatibility_analysis/diagnosis_manifest.json',
 'execution/synthetic_contract.json','execution/initial_integrity.json','execution/user_request.txt']
 names += ['execution/'+n for n in ['common.py','smoke.py','freeze.py','extract.py','evaluate.py','report.py']]
 # Freeze exact official package files and existing pinned environment via their verified manifests.
 original=c.read(c.V4/'config/blocked_state_manifest.json')['files']
 names += [p for p in original if p.startswith('packages/')]
 external={p:c.sha(c.ROOT/p) for p in ['RAG/results/rag_e6_v3/features/e6_v3_36_features.csv',
  'RAG/results/rag_e6_v3/evaluation/e6_v3_oof_predictions.csv','RAG/results/rag_e6_v3/config/run_config.json',
  'codex/canonical_fold_assignments.csv','codex/canonical_human_development_manifest.csv',
  'codex/canonical_feature_outputs/canonical_human_14_features.csv']}
 pairs=c.read(c.V4/'inputs/coverage_pairs_label_free.json');ids=[x['canonical_id'] for x in pairs]
 assert len(ids)==len(set(ids))==561
 c.write(c.HERE/'canonical_ids.json',ids);names+=['execution/canonical_ids.json']
 config={'frozen_utc':c.now(),'execution_authorized':True,'amendment':'E6_V4_PROTOCOL_AMENDMENT_01.md',
  'real_features_at_freeze':0,'fits_at_freeze':0,'evaluations_at_freeze':0,
  'features':old['features'],'original_features':schema['original_features'],'new_features':schema['new_features'],
  'random_forest':old['random_forest'],'target':'p_hallucination','clip':[0,1],'threshold':.5,
  'expected_rows':561,'expected_RF_fits':5,'expected_evaluations':1,'baseline_fits':0,
  'encoding_runtime':env,'evaluation_runtime':c.read(c.V3/'config/run_config.json')['runtime'],
  'bertscore':{'model':c.MODEL,'revision':c.REV,'tokenizer_revision':c.REV,'num_layers':18,
    'idf':False,'rescale_with_baseline':False,'use_fast_tokenizer':False,'all_layers':False,'lang':None,
    'hash_string':smoke['hash_string'],'automatic_model_max_length':512,'manual_override':False,
    'device':'cpu','dtype':'float32','batch_size':2,'chunk_size':16,'torch_threads':4,'torch_interop_threads':4},
  'truncation_policy':'official tokenizer limit 512 including special tokens; log original/used lengths per side; require used=min(original,512)',
  'preprocessing':'exact frozen pairs; official internal strip only for BERTScore; unchanged structure.py for structural features',
  'bootstrap':old['bootstrap'],'spearman_round_decimals':12,'network_required':False,
  'model_files':assets['model_files'],'external_input_hashes':external,
  'frozen_files':{p:c.sha(c.V4/p) for p in names}}
 assert log.stat().st_size==0;c.write(c.HERE/'run_config.json',config)
 print('Pre-extraction execution freeze PASS; amendment '+c.sha(c.V4/'E6_V4_PROTOCOL_AMENDMENT_01.md'),flush=True)
if __name__=='__main__':main()
