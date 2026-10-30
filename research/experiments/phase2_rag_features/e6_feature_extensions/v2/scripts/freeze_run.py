"""Freeze the smoke-tested E6-v2 before any bulk inference or RF fit."""
if "_H2_CTX" not in globals():
    raise RuntimeError("Historical source: use the pinned cross-experiment context; direct execution/import is disabled")
import io,unittest
import v2_common as c


def main():
    c.verify_inputs();c.verify_models();runtime=c.versions()
    smoke=c.read_json(c.OUT/'config/smoke.json')
    assert smoke['status']=='PASS' and not smoke['labels_accessed'] and not smoke['accuracy_computed']
    assert smoke['device']=='cpu' and smoke['dtype']=='float32' and smoke['batch_size']==2
    assert smoke['torch_threads']==4 and smoke['torch_interop_threads']==4
    assert not (c.OUT/'config/run_config.json').exists()
    suite=unittest.defaultTestLoader.discover(str(c.OUT/'tests'),pattern='test_v2.py')
    stream=io.StringIO();result=unittest.TextTestRunner(stream=stream,verbosity=2).run(suite)
    with (c.OUT/'config/contracts_output.txt').open('x',encoding='utf-8') as f:f.write(stream.getvalue())
    assert result.wasSuccessful(),stream.getvalue()
    c.write_json(c.OUT/'config/contracts.json',{'status':'PASS','tests_run':result.testsRun,
                 'rf_fits':0,'real_nli_inference':False,'completed_utc':c.now()})
    old=c.read_json(c.V1/'config/run_config.json');features=old['features']+c.NEW
    assert len(features)==len(set(features))==34
    from sklearn.ensemble import RandomForestRegressor
    params=old['random_forest'];assert RandomForestRegressor(**params).get_params()==params
    paths=[c.OUT/'E6_V2_PROTOCOL.md']+list((c.OUT/'scripts').glob('*.py'))+list((c.OUT/'tests').glob('*.py'))
    paths+=list((c.OUT/'inputs').glob('*'))
    paths+=[c.OUT/'config/smoke.json',c.OUT/'config/input_checks.json',c.OUT/'config/input_manifest.json',
            c.OUT/'config/contracts.json',c.OUT/'provenance/acquisition.json',c.OUT/'provenance/user_request.txt']
    c.write_json(c.OUT/'config/run_config.json',{'status':'FROZEN_BEFORE_BULK_INFERENCE_AND_EVALUATION',
                 'frozen_utc':c.now(),'features':features,'original_features':old['features'],'new_features':c.NEW,
                 'random_forest':params,'runtime':runtime,'model_id':c.MODEL_ID,'revision':c.REVISION,
                 'label_order':c.LABELS,'execution':{'device':'cpu','dtype':'float32','batch_size':2},
                 'tokenization':{'max_length':512,'truncation':'longest_first','padding':True,'return_attention_mask':True},
                 'bootstrap':{'seed':42,'resamples':10000,'percentiles':[.025,.975]},
                 'threshold':.5,'clip':[0,1],'spearman_prediction_rounding':12,
                 'contracts_passed':result.testsRun,'expected_rf_fits':5,'baseline_fits':0,
                 'frozen_files':{p.relative_to(c.OUT).as_posix():c.sha(p) for p in paths}})
    print({'freeze':'PASS','contracts':result.testsRun,'feature_count':34,'RF_fits_before_freeze':0},flush=True)


if __name__=='__main__':main()
