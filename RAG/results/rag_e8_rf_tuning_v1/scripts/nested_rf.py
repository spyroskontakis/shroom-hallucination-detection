"""Fixed E8 candidate grid, pooled metrics and training-only nested selector."""
import numpy as np
import pandas as pd
from scipy.stats import spearmanr, binomtest
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import StratifiedKFold

PARAMETERS = {
    'n_estimators': 500, 'criterion': 'squared_error', 'max_depth': None,
    'min_samples_split': 2, 'min_samples_leaf': 1, 'min_weight_fraction_leaf': 0.0,
    'max_features': 1.0, 'max_leaf_nodes': None, 'min_impurity_decrease': 0.0,
    'bootstrap': True, 'oob_score': False, 'n_jobs': -1, 'random_state': 42,
    'verbose': 0, 'warm_start': False, 'ccp_alpha': 0.0, 'max_samples': None,
    'monotonic_cst': None,
}
GRID = [(1, 1.0), (3, 1.0), (5, 1.0), (1, 0.5), (3, 0.5), (5, 0.5)]


def configurations():
    return [{'id': f'C{i}', 'order': i,
             'parameters': {**PARAMETERS, 'min_samples_leaf': leaf, 'max_features': features}}
            for i, (leaf, features) in enumerate(GRID)]


def metrics(labels, target, prediction):
    y = np.asarray(labels, dtype=int)
    target = np.asarray(target, dtype=float)
    prediction = np.asarray(prediction, dtype=float)
    assert len(y) == len(target) == len(prediction) and len(y) > 0
    assert np.isfinite(target).all() and np.isfinite(prediction).all()
    assert np.isin(y, [0, 1]).all() and ((prediction >= 0) & (prediction <= 1)).all()
    correct = int(((prediction >= .5).astype(int) == y).sum())
    rounded = np.round(prediction, 12)
    corr = None
    if len(y) >= 2 and len(np.unique(target)) > 1 and len(np.unique(rounded)) > 1:
        value = float(spearmanr(target, rounded).statistic)
        corr = value if np.isfinite(value) else None
    return {'n': len(y), 'correct': correct, 'accuracy': correct / len(y), 'spearman': corr}


def select(scores):
    assert len(scores) == 6 and [r['configuration'] for r in scores] == [f'C{i}' for i in range(6)]
    def key(row):
        value = row['spearman']
        rank = float(value) if value is not None and np.isfinite(value) else -np.inf
        return -row['accuracy'], -rank, row['order']
    return min(scores, key=key)['configuration']


def generate_splits(metadata):
    """Freeze canonical-ordered train/validation IDs and training-only strata."""
    assert len(metadata) == metadata.canonical_id.nunique() == 561
    assert set(metadata.fold_id) == {1, 2, 3, 4, 5}
    assert set(metadata.label_bin) == {0, 1}
    results = []
    for fold in range(1, 6):
        train = metadata.loc[metadata.fold_id != fold].copy()
        valid = metadata.loc[metadata.fold_id == fold]
        strata = train.task.astype(str) + '_' + train.label_bin.astype(str)
        counts = strata.value_counts().sort_index().to_dict()
        assert min(counts.values()) >= 3
        inner = []
        cv = StratifiedKFold(n_splits=3, shuffle=True, random_state=42)
        for k, (it, iv) in enumerate(cv.split(np.zeros(len(train)), strata), 1):
            inner.append({'inner_fold': k,
                          'train_ids': train.iloc[it].canonical_id.tolist(),
                          'validation_ids': train.iloc[iv].canonical_id.tolist(),
                          'train_strata': strata.iloc[it].value_counts().sort_index().to_dict(),
                          'validation_strata': strata.iloc[iv].value_counts().sort_index().to_dict()})
        results.append({'outer_fold': fold, 'train_ids': train.canonical_id.tolist(),
                        'validation_ids': valid.canonical_id.tolist(), 'stratum_counts': counts,
                        'inner': inner})
    validate_splits(results, metadata.canonical_id.tolist())
    return results


def validate_splits(splits, canonical_ids):
    universe = set(canonical_ids)
    assert len(universe) == len(canonical_ids)
    assert [s['outer_fold'] for s in splits] == [1, 2, 3, 4, 5]
    outer_coverage = []
    for split in splits:
        train, valid = split['train_ids'], split['validation_ids']
        st, sv = set(train), set(valid)
        assert len(st) == len(train) and len(sv) == len(valid)
        assert not st & sv and st | sv == universe
        assert train == [i for i in canonical_ids if i in st]
        assert valid == [i for i in canonical_ids if i in sv]
        inner_coverage = []
        assert [s['inner_fold'] for s in split['inner']] == [1, 2, 3]
        for inn in split['inner']:
            a, b = inn['train_ids'], inn['validation_ids']
            sa, sb = set(a), set(b)
            assert len(sa) == len(a) and len(sb) == len(b)
            assert not sa & sb and sa | sb == st
            assert not (sa | sb) & sv
            assert a == [i for i in train if i in sa] and b == [i for i in train if i in sb]
            inner_coverage.extend(b)
        assert len(inner_coverage) == len(st) and set(inner_coverage) == st
        outer_coverage.extend(valid)
    assert len(outer_coverage) == len(universe) and set(outer_coverage) == universe


def tune_training_only(training, inner_splits, configs, columns, fit_predict):
    """No outer-validation data or baseline predictions enter this function."""
    assert training.columns.tolist() == ['canonical_id', 'task', 'label_bin', 'p_hallucination'] + columns
    assert [c['id'] for c in configs] == [f'C{i}' for i in range(6)]
    assert training.canonical_id.nunique() == len(training)
    index = training.set_index('canonical_id', drop=False)
    ids = training.canonical_id.tolist()
    scores, oof = [], []
    for cfg in configs:
        predictions = pd.Series(np.nan, index=ids, dtype=float)
        for inner in inner_splits:
            ti, vi = inner['train_ids'], inner['validation_ids']
            assert set(ti).isdisjoint(vi) and set(ti) | set(vi) == set(ids)
            assert predictions.loc[vi].isna().all()
            pred = fit_predict(
                index.loc[ti, columns].to_numpy(float), index.loc[ti, 'p_hallucination'].to_numpy(float),
                index.loc[vi, columns].to_numpy(float), cfg, ti, vi, inner['inner_fold'])
            predictions.loc[vi] = np.clip(np.asarray(pred, dtype=float), 0, 1)
        assert predictions.notna().all()
        values = predictions.loc[ids].to_numpy()
        m = metrics(training.label_bin, training.p_hallucination, values)
        scores.append({'configuration': cfg['id'], 'order': cfg['order'], **m})
        oof.append(pd.DataFrame({'canonical_id': ids, 'configuration': cfg['id'], 'prediction': values}))
    return scores, select(scores), pd.concat(oof, ignore_index=True)


def paired(labels, baseline, prediction):
    y = np.asarray(labels, dtype=int)
    before = (np.asarray(baseline) >= .5).astype(int) == y
    after = (np.asarray(prediction) >= .5).astype(int) == y
    b = int((~before & after).sum()); c = int((before & ~after).sum())
    delta = after.astype(int) - before.astype(int)
    rng = np.random.default_rng(42)
    boot = np.array([delta[rng.integers(0, len(y), len(y))].mean() for _ in range(10000)])
    lo, hi = [float(v) for v in np.quantile(boot, [.025, .975])]
    return {'corrected': b, 'introduced_errors': c, 'net_correct': b-c,
            'both_correct': int((before & after).sum()), 'both_wrong': int((~before & ~after).sum()),
            'mcnemar_exact_two_sided_p': float(binomtest(b, b+c, .5).pvalue) if b+c else 1.0,
            'bootstrap': {'resamples': 10000, 'seed': 42, 'accuracy_difference': float(delta.mean()),
                          'percentile_95_ci': [lo, hi], 'accuracy_difference_pp': float(delta.mean()*100),
                          'percentile_95_ci_pp': [lo*100, hi*100]}}
