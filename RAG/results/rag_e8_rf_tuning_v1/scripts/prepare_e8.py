"""Validate and freeze all E8 inputs/splits/code before any estimator fit."""
import sys
import unittest
import io
import e8_common as c


def main():
    guard = c.offline('prepare_v1')
    try:
        from e8_data import runtime, load_data, baseline
        from nested_rf import configurations, generate_splits, validate_splits
        from joblib import Parallel, delayed
        import numpy as np
        import pandas as pd
        freeze=c.verify_integrity()
        assert not (c.OUT/'config/execution_freeze.json').exists()
        assert not (c.OUT/'evaluation/evaluation_started.json').exists()
        rt=runtime()
        frame, columns=load_data()
        _, baseline_check=baseline(frame)
        splits=generate_splits(frame[['canonical_id','fold_id','task','label_bin']])
        validate_splits(splits,frame.canonical_id.tolist())
        # Direct policy probes never perform actual denied operations.
        assert guard.probe('socket.connect',(None,('example.invalid',443)))
        assert guard.probe('open',(str(c.E6/'E6_RESULTS.md'),'w',0))
        assert guard.probe('open',(str(c.ROOT/'FORBIDDEN_FAKE_DATASET.csv'),'r',0))
        assert guard.probe('subprocess.Popen',('unused',[],None,None))
        thread_result=Parallel(n_jobs=-1,prefer='threads')(delayed(abs)(i) for i in [-2,-1,0,1])
        assert thread_result==[2,1,0,1]
        suite=unittest.defaultTestLoader.discover(str(c.OUT/'tests'),pattern='test_e8.py')
        output=io.StringIO()
        result=unittest.TextTestRunner(stream=output,verbosity=2).run(suite)
        (c.OUT/'config/contracts_output.txt').write_text(output.getvalue(),encoding='utf-8')
        assert result.wasSuccessful(),output.getvalue()
        assert not guard.events
        c.write_json(c.OUT/'config/contracts.json',{'status':'PASS','tests_run':result.testsRun,
                     'real_estimator_fits':0,'runtime_thread_smoke':'PASS','completed_utc':c.now(),
                     'real_input_alignment':'PASS','c0_identity':'PASS','baseline':baseline_check})
        c.write_json(c.OUT/'config/configurations.json',{'runtime':rt,'features':columns,
                     'candidate_order':[x['id'] for x in configurations()],'configurations':configurations(),
                     'threshold':.5,'clip':[0,1],'selection':['pooled_inner_accuracy_desc','pooled_inner_spearman_desc_defined_first','candidate_order_asc']})
        c.write_json(c.OUT/'splits/nested_splits.json',{'canonical_ids':frame.canonical_id.tolist(),
                     'outer_folds':splits,'inner_generator':{'n_splits':3,'shuffle':True,'random_state':42}})
        c.csv_write(c.OUT/'splits/outer_assignments.csv',frame[['canonical_id','fold_id']])
        assignments=[]
        for outer in splits:
            for inner in outer['inner']:
                for cid in inner['validation_ids']:
                    assignments.append({'canonical_id':cid,'outer_fold':outer['outer_fold'],
                                        'inner_validation_fold':inner['inner_fold']})
        c.csv_write(c.OUT/'splits/inner_assignments.csv',pd.DataFrame(assignments))
        assert len(assignments)==2244
        c.write_json(c.OUT/'config/baseline_verification.json',baseline_check)
        c.verify_integrity()
        paths=[c.OUT/'E8_PROTOCOL.md',c.OUT/'config/protocol_freeze.json',c.OUT/'config/configurations.json',
               c.OUT/'config/contracts.json',c.OUT/'config/baseline_verification.json']
        paths+=list((c.OUT/'scripts').glob('*.py'))+list((c.OUT/'tests').glob('*.py'))+list((c.OUT/'splits').glob('*'))
        c.write_json(c.OUT/'config/execution_freeze.json',{'frozen_utc':c.now(),'status':'READY_BEFORE_ANY_E8_FIT',
                     'e8_fits_before_freeze':0,'expected_inner_fits':90,'expected_outer_fits':5,
                     'additional_baseline_fits':0,'protected_count':len(freeze['protected_sha256']),
                     'files':{p.relative_to(c.OUT).as_posix():c.sha(p) for p in paths},
                     'continued_partial_preparation':True})
        print({'status':'READY','contracts_passed':result.testsRun,'protected_files':len(freeze['protected_sha256']),
               'inner_assignment_rows':len(assignments),'stratum_minima':[min(s['stratum_counts'].values()) for s in splits]},flush=True)
    finally:
        guard.save()


if __name__=='__main__': main()
