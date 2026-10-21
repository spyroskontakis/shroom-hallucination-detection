"""Verified frozen E6 arrays, approved development labels and saved baseline."""
import sys
import importlib.metadata
import numpy as np
import pandas as pd
import e8_common as common
from nested_rf import metrics, configurations, RandomForestRegressor


def runtime():
    expected = {'numpy': '2.4.4', 'pandas': '3.0.2', 'scipy': '1.17.1', 'scikit-learn': '1.8.0'}
    actual = {k: importlib.metadata.version(k) for k in expected}
    assert actual == expected and sys.version_info[:3] == (3, 11, 9), actual
    old = common.read_json(common.E6 / 'config/run_config.json')
    assert all(old['packages'][k] == v for k, v in actual.items())
    configs = configurations()
    assert configs[0]['parameters'] == old['random_forest']
    for config in configs:
        assert RandomForestRegressor(**config['parameters']).get_params() == config['parameters']
    return {'executable': sys.executable, 'python': sys.version, 'packages': actual,
            'c0_exact_e6_configuration': True}


def load_data():
    features, meta, columns, _ = common.aligned_label_free()
    ids = meta.canonical_id.tolist()
    canonical = pd.read_csv(common.CANONICAL, usecols=['canonical_id','task','label_bin','p_hallucination'])
    mixed = pd.read_csv(common.MIXED, usecols=['canonical_id','task','label_bin','p_hallucination'])
    for df in [canonical, mixed]:
        assert len(df) == df.canonical_id.nunique() == 561 and set(df.canonical_id) == set(ids)
    canonical = canonical.set_index('canonical_id').loc[ids].reset_index()
    mixed = mixed.set_index('canonical_id').loc[ids].reset_index()
    for key in ['task','label_bin','p_hallucination']:
        assert np.array_equal(canonical[key], mixed[key]), key
    assert np.array_equal(canonical.task, meta.task)
    assert set(canonical.label_bin) == {0,1}
    assert np.isfinite(canonical.p_hallucination).all() and canonical.p_hallucination.between(0,1).all()
    frame = meta.merge(canonical[['canonical_id','label_bin','p_hallucination']],
                       on='canonical_id', validate='one_to_one', sort=False).merge(
        features, on='canonical_id', validate='one_to_one', sort=False)
    assert frame.canonical_id.tolist() == ids
    return frame, columns


def baseline(frame):
    frozen = pd.read_csv(common.E6 / 'evaluation/e6_oof_predictions.csv')
    fresh = pd.read_csv(common.ROOT / 'RAG/results/rag_e7_agentic_v1/evaluation/e6_fresh_oof_predictions.csv')
    old = common.read_json(common.E6 / 'evaluation/e6_metrics.json')['diagnostics']['all_rows']['E6']
    ids = frame.canonical_id.tolist()
    for df in [frozen, fresh]:
        assert len(df) == df.canonical_id.nunique() == 561
        assert set(df.canonical_id) == set(ids)
    frozen = frozen.set_index('canonical_id').loc[ids].reset_index()
    fresh = fresh.set_index('canonical_id').loc[ids].reset_index()
    assert np.array_equal(frame.fold_id, frozen.fold_id) and np.array_equal(frame.fold_id, fresh.fold_id)
    assert np.isfinite(frozen.prediction).all() and frozen.prediction.between(0,1).all()
    assert np.allclose(frozen.prediction, fresh.prediction, atol=1e-12, rtol=0)
    assert np.array_equal(frozen.prediction >= .5, fresh.prediction >= .5)
    assert np.array_equal(np.round(frozen.prediction,12), np.round(fresh.prediction,12))
    m = metrics(frame.label_bin, frame.p_hallucination, frozen.prediction)
    assert m['correct'] == 453 and m['accuracy'] == 453/561
    assert abs(m['spearman'] - 0.744420539373989) < 1e-15
    assert m == old
    return frozen, {'status': 'PASS', 'metrics': m, 'fresh_e7_e6_max_absolute_difference':
                    float(np.abs(frozen.prediction - fresh.prediction).max()),
                    'binary_and_rounded_predictions_equal': True, 'additional_baseline_verification_fits': 0}
