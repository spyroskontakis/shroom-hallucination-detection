"""Single E6 OOF evaluation and fixed paired development-only diagnostics."""
import numpy as np
import pandas as pd
from scipy.stats import binomtest
from sklearn.ensemble import RandomForestRegressor
from e6_common import *


def metric(frame, prediction):
    scored = frame[['label_bin', 'p_hallucination']].copy()
    scored['prediction'] = frame[prediction]
    result = evaluator.metric(scored)
    result['correct'] = int(((frame[prediction] >= .5).astype(int) == frame.label_bin).sum())
    return result


def paired(frame, baseline):
    c6 = (frame.E6 >= .5).astype(int) == frame.label_bin
    cb = (frame[baseline] >= .5).astype(int) == frame.label_bin
    corrected = ~cb & c6
    introduced = cb & ~c6
    b, c = int(corrected.sum()), int(introduced.sum())
    d = (c6.astype(int) - cb.astype(int)).to_numpy()
    rng = np.random.default_rng(42)
    boots = np.array([d[rng.integers(0, len(d), len(d))].mean() for _ in range(10000)])
    return {
        'corrected': b, 'introduced_errors': c, 'net_correct': b - c,
        'both_correct': int((cb & c6).sum()), 'both_wrong': int((~cb & ~c6).sum()),
        'mcnemar_exact_two_sided_p': float(binomtest(b, b + c, .5).pvalue) if b + c else 1.0,
        'paired_bootstrap_accuracy_difference_e6_minus_baseline': {
            'replicates': 10000, 'seed': 42, 'observed': float(d.mean()),
            'percentile_95_ci': [float(np.quantile(boots, .025)), float(np.quantile(boots, .975))]},
        'corrected_ids': frame.loc[corrected, 'canonical_id'].tolist(),
        'introduced_error_ids': frame.loc[introduced, 'canonical_id'].tolist(),
    }


def main():
    offline()
    lock = verify_lock()
    assert RandomForestRegressor(n_estimators=500, random_state=42, n_jobs=-1).get_params() == lock['random_forest']
    freeze = read_json(OUT / 'config/feature_freeze.json')
    for p, expected in freeze['files'].items():
        assert sha(OUT / p) == expected
    assert sha(OUT / 'ranking/reconstructed_top5.jsonl') == freeze['ranking_sha256']
    assert read_json(OUT / 'config/ranking_consistency.json')['status'] == 'PASS'
    if (OUT / 'evaluation/evaluation_started.json').exists():
        raise FileExistsError('Evaluation already started; inspect prior artifacts instead of rerunning')
    # This is the first E6 evaluation label join, after feature freeze.
    mixed = pd.read_csv(MIXED)
    folds = pd.read_csv(FOLDS, usecols=['canonical_id', 'fold_id'])
    canonical = pd.read_csv(CANONICAL, usecols=['canonical_id', 'task', 'label_bin', 'p_hallucination'])
    features = pd.read_csv(OUT / 'features/e6_25_features.csv', float_precision='round_trip')
    assert features.columns.tolist() == ['canonical_id'] + FEATURES
    assert len(features) == features.canonical_id.nunique() == 561
    assert features.canonical_id.tolist() == mixed.canonical_id.tolist()
    cross = mixed[['canonical_id', 'fold_id', 'task', 'label_bin', 'p_hallucination']].merge(
        folds, on='canonical_id', suffixes=('_mixed', '_locked'), validate='one_to_one')
    assert len(cross) == 561 and (cross.fold_id_mixed == cross.fold_id_locked).all()
    check = mixed[['canonical_id', 'task', 'label_bin', 'p_hallucination']].merge(
        canonical, on='canonical_id', suffixes=('_mixed', '_manifest'), validate='one_to_one')
    assert len(check) == 561
    for col in ['task', 'label_bin', 'p_hallucination']:
        assert (check[col + '_mixed'] == check[col + '_manifest']).all(), col
    frame = mixed[['canonical_id', 'fold_id', 'task', 'label_bin', 'p_hallucination']].merge(
        features, on='canonical_id', validate='one_to_one', sort=False)
    assert frame.canonical_id.tolist() == mixed.canonical_id.tolist()
    # Exact preservation of the numeric feature arrays supplied to the accepted E5 estimator.
    original = mixed.merge(pd.read_csv(RAG).rename(columns={'example_id': 'canonical_id'}),
                           on='canonical_id', validate='one_to_one', sort=False)
    assert np.array_equal(frame[evaluator.E3 + evaluator.RAG].to_numpy(float),
                          original[evaluator.E3 + evaluator.RAG].to_numpy(float))
    saved = read_json(RUN / 'evaluation/module4_development_oof_metrics.json')
    baseline_metrics = {}
    for name, correct in [('E3', 445), ('E5', 446)]:
        pred = pd.read_csv(RUN / f'evaluation/module4_{name.lower()}_oof_predictions.csv')
        assert len(pred) == pred.canonical_id.nunique() == 561
        frame = frame.merge(pred.rename(columns={'prediction': name}),
                            on=['canonical_id', 'fold_id'], validate='one_to_one', sort=False)
        assert len(frame) == 561 and frame.canonical_id.tolist() == mixed.canonical_id.tolist()
        observed = metric(frame, name)
        expected = saved['diagnostics']['all_rows'][name]
        assert observed['correct'] == correct and observed['accuracy'] == expected['accuracy']
        assert abs(observed['spearman'] - expected['spearman']) <= 1e-15, (name, observed, expected)
        baseline_metrics[name] = observed
    write_json(OUT / 'evaluation/baseline_compatibility.json', {
        'status': 'PASS', 'checked_utc': now(), 'metrics': baseline_metrics,
        'ids_and_folds': '561 one-to-one matches in canonical order',
        'e5_predictor_arrays_equal': True, 'retrained_baselines': False,
        'runtime_matches_documented_canonical': lock['packages'],
    })
    write_json(OUT / 'evaluation/evaluation_started.json', {
        'started_utc': now(), 'config_sha256': sha(OUT / 'config/run_config.json'),
        'feature_freeze_sha256': sha(OUT / 'config/feature_freeze.json'), 'configuration_count': 1,
    })
    print(json.dumps({'baseline_compatibility': 'PASS', 'metrics': baseline_metrics}), flush=True)
    pred = evaluator.run_cv(frame, FEATURES)
    assert pred.canonical_id.tolist() == frame.canonical_id.tolist()
    assert pred.fold_id.tolist() == frame.fold_id.tolist()
    frame['E6'] = pred.prediction.to_numpy()
    csv_write(OUT / 'evaluation/e6_oof_predictions.csv', pred)
    diagnostics = {
        'all_rows': {name: metric(frame, name) for name in ['E3', 'E5', 'E6']},
        'per_task': {task: {name: metric(g, name) for name in ['E3', 'E5', 'E6']}
                     for task, g in frame.groupby('task')},
        'by_evidence': {str(int(flag)): {name: metric(g, name) for name in ['E3', 'E5', 'E6']}
                        for flag, g in frame.groupby('rag_evidence_available')},
        'per_fold': {str(int(fold)): {name: metric(g, name) for name in ['E3', 'E5', 'E6']}
                     for fold, g in frame.groupby('fold_id')},
        'paired': {name: paired(frame, name) for name in ['E3', 'E5']},
    }
    for name in ['E3', 'E5', 'E6']:
        frame[name + '_binary'] = (frame[name] >= .5).astype(int)
        frame[name + '_correct'] = frame[name + '_binary'] == frame.label_bin
    for name in ['E3', 'E5']:
        frame['E6_vs_' + name] = np.select([
            ~frame[name + '_correct'] & frame.E6_correct,
            frame[name + '_correct'] & ~frame.E6_correct], ['corrected', 'introduced_error'], default='unchanged_correctness')
    csv_write(OUT / 'evaluation/paired_row_diagnostics.csv', frame[
        ['canonical_id', 'fold_id', 'task', 'rag_evidence_available', 'label_bin', 'p_hallucination',
         'E3', 'E5', 'E6', 'E3_binary', 'E5_binary', 'E6_binary', 'E3_correct', 'E5_correct',
         'E6_correct', 'E6_vs_E3', 'E6_vs_E5']])
    # Descriptive subgroup correction counts; inference is only on the full paired sample.
    diagnostics['corrections_by_group'] = {}
    for key, groups in [('task', frame.groupby('task')), ('evidence', frame.groupby('rag_evidence_available'))]:
        diagnostics['corrections_by_group'][key] = {
            str(group): {name: {'corrected': int((g['E6_vs_' + name] == 'corrected').sum()),
                                'introduced_errors': int((g['E6_vs_' + name] == 'introduced_error').sum())}
                        for name in ['E3', 'E5']} for group, g in groups}
    verify_lock()
    assert (OUT / 'config/network_attempts.jsonl').stat().st_size == 0
    write_json(OUT / 'evaluation/e6_metrics.json', {
        'status': 'COMPLETED', 'completed_utc': now(), 'development_only': True,
        'rows': 561, 'features': FEATURES, 'configuration_count': 1,
        'diagnostics': diagnostics, 'protected_artifacts_unchanged': True,
        'oof_sha256': sha(OUT / 'evaluation/e6_oof_predictions.csv'),
        'baseline_retraining_runs': 0, 'e6_cv_runs': 1, 'e6_fitted_forests': 5,
    })
    print(json.dumps(diagnostics['all_rows']), flush=True)


if __name__ == '__main__':
    main()
