"""One fixed five-fold E6-v3 RF evaluation against saved E6-v2 predictions."""
import numpy as np
import pandas as pd
from scipy.stats import spearmanr,binomtest
from sklearn.ensemble import RandomForestRegressor
import v3_common as c


def metric(frame,column):
    y=frame.label_bin.to_numpy(int);p=frame[column].to_numpy(float);target=frame.p_hallucination.to_numpy(float)
    assert len(p)>0 and np.isfinite(p).all() and ((p>=0)&(p<=1)).all()
    correct=int(((p>=.5).astype(int)==y).sum());ranked=np.round(p,12)
    rho=None
    if len(p)>1 and len(np.unique(target))>1 and len(np.unique(ranked))>1:
        value=float(spearmanr(target,ranked).statistic)
        if np.isfinite(value):rho=value
    return {'n':len(p),'correct':correct,'accuracy':correct/len(p),'spearman':rho}


def paired(frame):
    y=frame.label_bin.to_numpy(int)
    old=(frame['E6-v2'].to_numpy()>=.5).astype(int)==y
    new=(frame['E6-v3'].to_numpy()>=.5).astype(int)==y
    b=int((~old&new).sum());e=int((old&~new).sum());delta=new.astype(int)-old.astype(int)
    rng=np.random.default_rng(42)
    bootstrap=np.array([delta[rng.integers(0,len(delta),len(delta))].mean() for _ in range(10000)])
    lo,hi=[float(v) for v in np.quantile(bootstrap,[.025,.975])]
    return {'corrected':b,'introduced_errors':e,'net_correct':b-e,
            'both_correct':int((old&new).sum()),'both_wrong':int((~old&~new).sum()),
            'mcnemar_exact_two_sided_p':float(binomtest(b,b+e,.5).pvalue) if b+e else 1.,
            'bootstrap':{'resamples':10000,'seed':42,'accuracy_difference':float(delta.mean()),
                         'percentile_95_ci':[lo,hi],'accuracy_difference_pp':float(delta.mean()*100),
                         'percentile_95_ci_pp':[lo*100,hi*100]},
            'corrected_ids':frame.loc[~old&new,'canonical_id'].tolist(),
            'introduced_error_ids':frame.loc[old&~new,'canonical_id'].tolist()}


def load_evaluation():
    lock=c.verify_freeze();freeze=c.read_json(c.OUT/'config/feature_freeze.json')
    for path,want in freeze['files'].items():assert c.sha(c.OUT/path)==want,path
    features=pd.read_csv(c.OUT/'features/e6_v3_36_features.csv',float_precision='round_trip')
    base=pd.read_csv(c.V2/'features/e6_v2_34_features.csv',float_precision='round_trip')
    assert features.columns.tolist()==['canonical_id']+lock['features']
    assert features.canonical_id.tolist()==base.canonical_id.tolist()
    assert np.array_equal(features.iloc[:,:35].to_numpy(),base.to_numpy())
    assert len(features)==features.canonical_id.nunique()==561
    metadata=pd.read_csv(c.MIXED,usecols=['canonical_id','fold_id','task','label_bin','p_hallucination'])
    canonical=pd.read_csv(c.CANONICAL,usecols=['canonical_id','task','label_bin','p_hallucination'])
    folds=pd.read_csv(c.FOLDS,usecols=['canonical_id','fold_id'])
    ids=features.canonical_id.tolist()
    for df in [metadata,canonical,folds]:
        assert len(df)==df.canonical_id.nunique()==561 and set(df.canonical_id)==set(ids)
    assert metadata.canonical_id.tolist()==ids
    canonical=canonical.set_index('canonical_id').loc[ids].reset_index()
    folds=folds.set_index('canonical_id').loc[ids].reset_index()
    for key in ['task','label_bin','p_hallucination']:assert np.array_equal(metadata[key],canonical[key])
    assert np.array_equal(metadata.fold_id,folds.fold_id)
    f=metadata.merge(features,on='canonical_id',validate='one_to_one',sort=False)
    saved=pd.read_csv(c.V2/'evaluation/e6_v2_oof_predictions.csv',float_precision='round_trip')
    assert len(saved)==saved.canonical_id.nunique()==561 and set(saved.canonical_id)==set(ids)
    saved=saved.set_index('canonical_id').loc[ids].reset_index()
    assert np.array_equal(saved.fold_id,f.fold_id)
    f['E6-v2']=saved.prediction.to_numpy()
    observed=metric(f,'E6-v2');expected=c.read_json(c.V2/'evaluation/e6_v2_metrics.json')['diagnostics']['all_rows']['E6-v2']
    assert observed==expected and observed['correct']==473
    baseline_rows=pd.read_csv(c.V2/'evaluation/paired_row_diagnostics.csv',float_precision='round_trip')
    assert baseline_rows.canonical_id.tolist()==ids
    for key in ['fold_id','label_bin','p_hallucination','E6-v2']:
        assert np.array_equal(baseline_rows[key],f[key]),key
    check={'status':'PASS','metrics':observed,'canonical_ids_folds':'exact match',
           'e6_v2_features_unchanged':True,'new_baseline_fits':0,
           'prediction_and_row_diagnostics_exact':True}
    return f,lock,check


def main():
    log=c.offline('evaluate');c.versions()
    f,lock,check=load_evaluation();features=lock['features'];params=lock['random_forest']
    assert RandomForestRegressor(**params).get_params()==params
    assert params==c.read_json(c.V2/'config/run_config.json')['random_forest']
    c.write_json(c.OUT/'evaluation/baseline_verification.json',check)
    c.write_json(c.OUT/'evaluation/evaluation_started.json',{'started_utc':c.now(),'expected_rf_fits':5,
                 'baseline_fits':0,'configuration_count':1,'run_config_sha256':c.sha(c.OUT/'config/run_config.json'),
                 'feature_freeze_sha256':c.sha(c.OUT/'config/feature_freeze.json')})
    outputs=[];fit_records=[]
    for fold in range(1,6):
        train=f[f.fold_id!=fold];valid=f[f.fold_id==fold]
        assert set(train.canonical_id).isdisjoint(valid.canonical_id)
        model=RandomForestRegressor(**params)
        x=train[features].to_numpy(float);y=train.p_hallucination.to_numpy(float);v=valid[features].to_numpy(float)
        record={'fold':fold,'train_ids':train.canonical_id.tolist(),'validation_ids':valid.canonical_id.tolist(),
                'parameters':params,'started_utc':c.now(),'train_x_sha256':c.hashlib.sha256(x.tobytes()).hexdigest(),
                'train_y_sha256':c.hashlib.sha256(y.tobytes()).hexdigest(),'validation_x_sha256':c.hashlib.sha256(v.tobytes()).hexdigest()}
        c.write_json(c.OUT/f'evaluation/fit_{fold}_started.json',record)
        model.fit(x,y)
        pred=np.clip(model.predict(v),0,1)
        assert np.isfinite(pred).all() and len(pred)==len(valid)
        record['completed_utc']=c.now();fit_records.append(record)
        c.write_json(c.OUT/f'evaluation/fit_{fold}_completed.json',record)
        outputs.append(pd.DataFrame({'canonical_id':valid.canonical_id.to_numpy(),'fold_id':fold,'prediction':pred},index=valid.index))
        print(f'RF fits {fold}/5 complete',flush=True)
    predictions=pd.concat(outputs).sort_index()
    assert predictions.canonical_id.tolist()==f.canonical_id.tolist() and len(predictions)==561
    c.csv_write(c.OUT/'evaluation/e6_v3_oof_predictions.csv',predictions)
    f['E6-v3']=predictions.prediction.to_numpy()
    def both(g):return {name:metric(g,name) for name in ['E6-v2','E6-v3']}
    diagnostics={'all_rows':both(f),'per_fold':{str(k):both(g) for k,g in f.groupby('fold_id')},
                 'per_task':{k:both(g) for k,g in f.groupby('task')},
                 'by_evidence':{str(k):both(g) for k,g in f.groupby('rag_evidence_available')}}
    for name in ['E6-v2','E6-v3']:
        f[name+'_binary']=(f[name]>=.5).astype(int);f[name+'_correct']=f[name+'_binary']==f.label_bin
    f['change']=np.select([~f['E6-v2_correct']&f['E6-v3_correct'],f['E6-v2_correct']&~f['E6-v3_correct']],
                          ['corrected','introduced_error'],default='unchanged_correctness')
    c.csv_write(c.OUT/'evaluation/paired_row_diagnostics.csv',f[['canonical_id','fold_id','task','rag_evidence_available',
                'label_bin','p_hallucination','E6-v2','E6-v3','E6-v2_binary','E6-v3_binary','E6-v2_correct','E6-v3_correct','change']])
    c.verify_freeze();assert log.stat().st_size==0
    c.write_json(c.OUT/'evaluation/e6_v3_metrics.json',{'status':'COMPLETED','completed_utc':c.now(),
                 'exploratory_development_only':True,'diagnostics':diagnostics,'paired_vs_e6_v2':paired(f),
                 'rf_fits':5,'additional_baseline_fits':0,'configurations_evaluated':1,
                 'oof_sha256':c.sha(c.OUT/'evaluation/e6_v3_oof_predictions.csv')})
    print(diagnostics['all_rows'],flush=True)


if __name__=='__main__':main()
