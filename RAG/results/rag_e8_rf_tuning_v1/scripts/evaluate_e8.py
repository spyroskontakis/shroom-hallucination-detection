"""Execute the one frozen 95-fit nested E8 suite; no outer-label selection."""
import json
import hashlib
import e8_common as c


def verify_execution():
    c.verify_integrity()
    lock=c.read_json(c.OUT/'config/execution_freeze.json')
    for path,want in lock['files'].items():
        assert c.sha(c.OUT/path)==want,f'Pre-fit file changed: {path}'
    return lock


def main():
    guard=c.offline('evaluate_v1')
    try:
        import numpy as np
        import pandas as pd
        from sklearn.ensemble import RandomForestRegressor
        from e8_data import load_data, runtime, baseline
        from nested_rf import tune_training_only, metrics, paired, validate_splits
        lock=verify_execution()
        runtime()
        frame,columns=load_data()
        configs=c.read_json(c.OUT/'config/configurations.json')['configurations']
        assert columns==c.read_json(c.OUT/'config/configurations.json')['features']
        split_file=c.read_json(c.OUT/'splits/nested_splits.json')
        assert split_file['canonical_ids']==frame.canonical_id.tolist()
        splits=split_file['outer_folds']
        validate_splits(splits,frame.canonical_id.tolist())
        # Explicitly check frozen outer assignments against the canonical fold mapping.
        for s in splits:
            assert s['validation_ids']==frame.loc[frame.fold_id==s['outer_fold'],'canonical_id'].tolist()
        assert not guard.events
        c.write_json(c.OUT/'evaluation/evaluation_started.json',{'started_utc':c.now(),
                     'execution_freeze_sha256':c.sha(c.OUT/'config/execution_freeze.json'),
                     'expected_e8_fits':95,'baseline_verification_fits':0})
        fit_path=c.OUT/'evaluation/fit_events.jsonl'
        with fit_path.open('x',encoding='utf-8'): pass
        completed=[]

        def audited_fit(x,y,v,cfg,train_ids,valid_ids,stage,outer,inner,reference):
            assert not guard.events
            assert set(train_ids).isdisjoint(valid_ids)
            np.testing.assert_array_equal(x,reference.loc[train_ids,columns].to_numpy(float))
            np.testing.assert_array_equal(y,reference.loc[train_ids,'p_hallucination'].to_numpy(float))
            assert x.shape==(len(train_ids),25) and v.shape==(len(valid_ids),25)
            assert np.isfinite(x).all() and np.isfinite(v).all() and np.isfinite(y).all()
            record={'fit_number':len(completed)+1,'stage':stage,'outer_fold':outer,'inner_fold':inner,
                    'configuration':cfg['id'],'parameters':cfg['parameters'],
                    'train_ids':train_ids,'prediction_ids':valid_ids,
                    'train_x_sha256':hashlib.sha256(x.tobytes()).hexdigest(),
                    'train_y_sha256':hashlib.sha256(y.tobytes()).hexdigest(),
                    'predict_x_sha256':hashlib.sha256(v.tobytes()).hexdigest()}
            with fit_path.open('a',encoding='utf-8') as handle:
                handle.write(json.dumps({**record,'event':'fit_started','utc':c.now()},sort_keys=True)+'\n')
                handle.flush()
            estimator=RandomForestRegressor(**cfg['parameters'])
            assert estimator.get_params()==cfg['parameters']
            estimator.fit(x,y)
            assert not guard.events
            prediction=np.clip(estimator.predict(v),0,1)
            assert prediction.shape==(len(valid_ids),) and np.isfinite(prediction).all()
            assert not guard.events
            with fit_path.open('a',encoding='utf-8') as handle:
                handle.write(json.dumps({**record,'event':'fit_completed','utc':c.now()},sort_keys=True)+'\n')
                handle.flush()
            completed.append(record)
            return prediction

        predictions=[]; selections=[]; all_scores=[]
        features_only=frame.set_index('canonical_id')[columns]
        for outer in splits:
            fold=outer['outer_fold']
            training=frame.loc[frame.fold_id!=fold,['canonical_id','task','label_bin','p_hallucination']+columns].copy()
            assert training.canonical_id.tolist()==outer['train_ids']
            ref=training.set_index('canonical_id')

            def inner_fit(x,y,v,cfg,ti,vi,k):
                assert set(ti)|set(vi)==set(outer['train_ids'])
                assert (set(ti)|set(vi)).isdisjoint(outer['validation_ids'])
                np.testing.assert_array_equal(v,ref.loc[vi,columns].to_numpy(float))
                result=audited_fit(x,y,v,cfg,ti,vi,'inner',fold,k,ref)
                if k==3: print(f'Outer {fold}/5: {cfg["id"]} inner fits complete ({len(completed)}/95 fits)',flush=True)
                return result

            scores,selected,inner_oof=tune_training_only(training,outer['inner'],configs,columns,inner_fit)
            for row in scores: row['outer_fold']=fold
            inner_oof.insert(0,'outer_fold',fold)
            c.csv_write(c.OUT/f'evaluation/inner_oof_fold_{fold}.csv',inner_oof)
            selected_cfg=next(cfg for cfg in configs if cfg['id']==selected)
            decision={'outer_fold':fold,'selected_configuration':selected,'parameters':selected_cfg['parameters'],
                      'selected_utc':c.now(),'training_ids':outer['train_ids'],'inner_scores':scores}
            # Persist tuning decision before accessing outer-validation predictor arrays.
            c.write_json(c.OUT/f'evaluation/selection_fold_{fold}.json',decision)
            selections.append(decision); all_scores.extend(scores)
            ti,vi=outer['train_ids'],outer['validation_ids']
            out=audited_fit(ref.loc[ti,columns].to_numpy(float),ref.loc[ti,'p_hallucination'].to_numpy(float),
                            features_only.loc[vi,columns].to_numpy(float),selected_cfg,ti,vi,'outer_selected',fold,None,ref)
            predictions.append(pd.DataFrame({'canonical_id':vi,'fold_id':fold,'prediction':out,
                                             'selected_configuration':selected}))
            print(f'Outer {fold}/5 predictions saved; selected {selected}; fits {len(completed)}/95',flush=True)
            c.csv_write(c.OUT/f'evaluation/outer_oof_fold_{fold}.csv',predictions[-1])
        assert len(completed)==95 and sum(r['stage']=='inner' for r in completed)==90
        ids=frame.canonical_id.tolist()
        oof=pd.concat(predictions).set_index('canonical_id').loc[ids].reset_index()
        assert len(oof)==oof.canonical_id.nunique()==561 and np.array_equal(oof.fold_id,frame.fold_id)
        c.csv_write(c.OUT/'evaluation/e8_oof_predictions.csv',oof)
        c.csv_write(c.OUT/'evaluation/inner_scores.csv',pd.DataFrame(all_scores))
        c.write_json(c.OUT/'evaluation/selected_configurations.json',selections)
        # First E8 outer score computation: all five decisions and OOF predictions now exist.
        frozen,_=baseline(frame)
        f=frame[['canonical_id','fold_id','task','rag_evidence_available','label_bin','p_hallucination']].copy()
        f['E6']=frozen.prediction.to_numpy(); f['E8']=oof.prediction.to_numpy()
        f['selected_configuration']=oof.selected_configuration.to_numpy()
        for name in ['E6','E8']:
            f[name+'_binary']=(f[name]>=.5).astype(int)
            f[name+'_correct']=f[name+'_binary']==f.label_bin
        f['change']=np.select([~f.E6_correct&f.E8_correct,f.E6_correct&~f.E8_correct],
                              ['corrected','introduced_error'],default='unchanged_correctness')
        c.csv_write(c.OUT/'evaluation/paired_row_diagnostics.csv',f)
        def both(g): return {name:metrics(g.label_bin,g.p_hallucination,g[name]) for name in ['E6','E8']}
        diagnostics={'all_rows':both(f),
                     'per_fold':{str(k):both(g) for k,g in f.groupby('fold_id')},
                     'per_task':{str(k):both(g) for k,g in f.groupby('task')},
                     'by_evidence':{str(k):both(g) for k,g in f.groupby('rag_evidence_available')}}
        comparison=paired(f.label_bin,f.E6,f.E8)
        comparison['corrected_ids']=f.loc[f.change=='corrected','canonical_id'].tolist()
        comparison['introduced_error_ids']=f.loc[f.change=='introduced_error','canonical_id'].tolist()
        verify_execution(); assert not guard.events
        result={'status':'COMPLETED','completed_utc':c.now(),'exploratory_development_only':True,
                'reused_development_pool':True,'independent_test':False,'diagnostics':diagnostics,
                'paired_vs_e6':comparison,'configuration_frequency':
                {cfg['id']:sum(s['selected_configuration']==cfg['id'] for s in selections) for cfg in configs},
                'fit_counts':{'inner':90,'outer_selected':5,'total_e8':95,'additional_baseline_verification':0},
                'protected_unchanged':lock['protected_count'],'outer_oof_sha256':c.sha(c.OUT/'evaluation/e8_oof_predictions.csv')}
        c.write_json(c.OUT/'evaluation/e8_metrics.json',result)
        print(json.dumps({'all_rows':diagnostics['all_rows'],'configuration_frequency':result['configuration_frequency'],
                          'fit_counts':result['fit_counts']}),flush=True)
    finally:
        guard.save()


if __name__=='__main__': main()
