"""One frozen five-fold E7 evaluation, exactly five E3 and five E6 RF fits."""
from e7_common import *


def main():
    import numpy as np
    import pandas as pd
    from scipy.stats import rankdata
    from sklearn.ensemble import RandomForestRegressor
    from router import USE, FALLBACK, choose_route, finish_prediction, OBSERVATIONS
    from evaluation_common import verify_evaluation_freeze, audited_cv, metric, paired

    frozen = verify_evaluation_freeze()
    assert read_json(OUT / 'config/security_prepare_evaluation_v1.json')['operational_violations']==[]
    started = OUT / 'evaluation/evaluation_started.json'
    if started.exists():
        raise FileExistsError('E7 evaluation already started; no rerun allowed')
    features, metadata, predictors, evaluator = aligned_label_free()
    routes = pd.read_csv(OUT/'routing/routes.csv',float_precision='round_trip')
    thresholds = read_json(OUT/'config/fold_thresholds.json')
    assert routes.canonical_id.tolist()==metadata.canonical_id.tolist()
    assert routes.fold_id.tolist()==metadata.fold_id.tolist()
    assert len(routes)==routes.canonical_id.nunique()==561
    for row in routes.to_dict('records'):
        threshold = thresholds[str(row['fold_id'])]['threshold']
        assert row['threshold']==threshold
        assert row['route']==choose_route({k:row[k] for k in OBSERVATIONS},threshold)
        assert row['decision_count']==1
    # First label/baseline projections occur only after the hashes above establish frozen actions.
    labels = pd.read_csv(CANONICAL,usecols=['canonical_id','task','label_bin','p_hallucination'])
    mixed_labels = pd.read_csv(MIXED,usecols=['canonical_id','fold_id','task','label_bin','p_hallucination'])
    assert labels.canonical_id.nunique()==len(labels)==561
    labels = labels.set_index('canonical_id').loc[metadata.canonical_id].reset_index()
    assert mixed_labels.canonical_id.tolist()==metadata.canonical_id.tolist()
    for col in ['task','label_bin','p_hallucination']:
        assert np.array_equal(labels[col],mixed_labels[col])
    assert np.array_equal(metadata.fold_id,mixed_labels.fold_id)
    assert set(labels.label_bin)=={0,1}
    assert np.isfinite(labels.p_hallucination).all() and labels.p_hallucination.between(0,1).all()
    frame = metadata.join(features.drop(columns='canonical_id'))
    frame = frame.join(labels[['label_bin','p_hallucination']])
    frame['route'] = routes.route
    frame['evidence_available'] = routes.evidence_available
    baseline_expected = {'E3':(445,.7390395612811848),'E5':(446,.7421719692110536),
                         'E6':(453,.7444205394)}
    baseline_metrics = {}
    for name in ['E3','E5','E6']:
        path = E6/'evaluation/e6_oof_predictions.csv' if name=='E6' else RUN/f'evaluation/module4_{name.lower()}_oof_predictions.csv'
        pred = pd.read_csv(path)
        assert len(pred)==pred.canonical_id.nunique()==561
        assert pred.canonical_id.tolist()==metadata.canonical_id.tolist()
        assert np.array_equal(pred.fold_id,metadata.fold_id)
        frame[name] = pred.prediction.to_numpy(float)
        baseline_metrics[name] = metric(frame,name)
        expected_correct,expected_rho = baseline_expected[name]
        assert baseline_metrics[name]['correct']==expected_correct
        expected_exact = (read_json(E6/'evaluation/e6_metrics.json')['diagnostics']['all_rows']['E6']['spearman']
                          if name=='E6' else expected_rho)
        assert abs(baseline_metrics[name]['spearman']-expected_exact)<=1e-12
    write_json(OUT/'evaluation/baseline_verification.json',{
        'checked_utc':now(),'status':'PASS','metrics':baseline_metrics,
        'routes_frozen_before_label_projection':True,'routes_freeze_sha256':sha(OUT/'config/routes_freeze.json')})
    verify_evaluation_freeze()
    import e7_common
    assert not e7_common.GUARD.events
    write_json(started,{'started_utc':now(),'expected_evaluation_count':1,'expected_outer_folds':5,
                        'expected_rf_fits':10,'evaluation_freeze_sha256':sha(OUT/'config/evaluation_freeze.json'),
                        'protocol_sha256':frozen['protocol_sha256']})
    reproduction = {}
    for name,cols in [('E3',frozen['e3_predictors']),('E6',frozen['e6_predictors'])]:
        pred = audited_cv(evaluator,frame,cols,name,RandomForestRegressor,frozen['random_forest'])
        csv_write(OUT/f'evaluation/{name.lower()}_fresh_oof_predictions.csv',pred)
        fresh = pred.prediction.to_numpy(float)
        saved = frame[name].to_numpy(float)
        maxdiff = float(np.abs(fresh-saved).max())
        assert np.allclose(fresh,saved,rtol=0,atol=1e-12), (name,maxdiff)
        assert np.array_equal(fresh>=.5,saved>=.5)
        assert np.array_equal(rankdata(np.round(fresh,12)),rankdata(np.round(saved,12)))
        frame[name+'_fresh'] = fresh
        fresh_metrics = metric(frame,name+'_fresh')
        assert fresh_metrics['correct']==baseline_metrics[name]['correct']
        assert abs(fresh_metrics['spearman']-baseline_metrics[name]['spearman'])<=1e-12
        reproduction[name]={'status':'PASS','max_absolute_prediction_difference':maxdiff,
                            'binary_equal':True,'rounded_rank_equal':True,'metrics':fresh_metrics}
    completed = list((OUT/'evaluation/fits').glob('*_completed.json'))
    assert len(completed)==10
    trajectories=[]
    for row in frame.to_dict('records'):
        result=finish_prediction(row['route'],{'E3':row['E3_fresh'],'E6':row['E6_fresh']})
        trajectories.append({'canonical_id':row['canonical_id'],'fold_id':row['fold_id'],
                             'route':row['route'],**result})
    frame['E7']=[r['prediction'] for r in trajectories]
    assert np.isfinite(frame.E7).all() and frame.E7.between(0,1).all()
    assert (frame.loc[frame.evidence_available==0,'route']==FALLBACK).all()
    csv_write(OUT/'evaluation/e7_oof_predictions.csv',frame[['canonical_id','fold_id','route','E7']].rename(columns={'E7':'prediction'}))
    write_json(OUT/'evaluation/agent_trajectories.json',trajectories)
    for name in ['E3','E5','E6','E7']:
        frame[name+'_correct']=(frame[name]>=.5).astype(int)==frame.label_bin
    for name in ['E6','E3']:
        frame['E7_vs_'+name]=np.select([~frame[name+'_correct']&frame.E7_correct,
                                      frame[name+'_correct']&~frame.E7_correct],
                                     ['corrected','regressed'],default='unchanged_correctness')
    csv_write(OUT/'evaluation/paired_row_diagnostics.csv',frame[
        ['canonical_id','fold_id','task','evidence_available','route','label_bin','p_hallucination',
         'E3','E5','E6','E3_fresh','E6_fresh','E7','E7_vs_E6','E7_vs_E3']])
    diagnostics={
        'overall':{n:metric(frame,n) for n in ['E3','E5','E6','E7']},
        'per_task':{str(k):metric(g,'E7') for k,g in frame.groupby('task')},
        'by_evidence':{str(int(k)):metric(g,'E7') for k,g in frame.groupby('evidence_available')},
        'by_route':{str(k):metric(g,'E7') for k,g in frame.groupby('route')},
        'per_fold':{str(int(k)):{**metric(g,'E7'),'threshold':thresholds[str(int(k))]['threshold'],
                               'route_counts':{str(r):int(n) for r,n in g.route.value_counts().items()}}
                    for k,g in frame.groupby('fold_id')},
        'paired':{n:paired(frame,n) for n in ['E6','E3']},
        'route_counts':{str(k):int(v) for k,v in frame.route.value_counts().items()},
        'routes_by_task':{str(k):{str(r):int(n) for r,n in g.route.value_counts().items()}
                          for k,g in frame.groupby('task')},
        'routes_by_evidence':{str(int(k)):{str(r):int(n) for r,n in g.route.value_counts().items()}
                              for k,g in frame.groupby('evidence_available')},
    }
    verify_evaluation_freeze()
    assert not e7_common.GUARD.events
    write_json(OUT/'evaluation/e7_metrics.json',{
        'status':'COMPLETED','completed_utc':now(),'development_only':True,'e7_evaluation_count':1,
        'outer_folds':5,'rf_fits':10,'inner_fits':0,'reproduction':reproduction,
        'protocol_sha256':frozen['protocol_sha256'],'diagnostics':diagnostics})
    print('COMPLETED: '+str(diagnostics['overall']['E7']),flush=True)


if __name__ == '__main__':
    guard=offline('evaluate_e7_v1')
    try:
        main()
    finally:
        guard.save()
