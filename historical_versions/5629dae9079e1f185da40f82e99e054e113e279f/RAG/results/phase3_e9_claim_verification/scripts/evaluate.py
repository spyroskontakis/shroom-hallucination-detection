"""Fixed five-fit evaluation component. Call only after validated features exist."""
import importlib.metadata
import numpy as np
from sklearn.ensemble import RandomForestRegressor
import e9_common as c
from verify_baseline import verify


def evaluate(matrix, variant):
    c.require(variant in ['E9-A', 'E9-B'], 'predefined variants only')
    metadata, baseline, old, lock, _ = verify()
    config = c.read_json(c.OUT / 'config/run_config.json')
    names = config['e9_a_features' if variant == 'E9-A' else 'e9_b_features']
    c.require(matrix.columns.tolist() == ['canonical_id'] + names, 'feature schema')
    c.require(matrix.canonical_id.tolist() == baseline.canonical_id.tolist(), '561 canonical IDs')
    c.require(np.array_equal(matrix[baseline.columns].to_numpy(), baseline.to_numpy()), '36 frozen columns differ')
    c.require(np.isfinite(matrix[names].to_numpy(float)).all(), 'finite features')
    c.require(config['random_forest'] == lock['random_forest'], 'RF configuration changed')
    for package, version in lock['runtime']['packages'].items():
        c.require(importlib.metadata.version(package) == version, 'runtime changed')
    if variant == 'E9-B':
        prior = c.read_json(c.OUT / 'evaluation/E9-A_metrics.json')
        c.require(prior['status'] == 'COMPLETED', 'E9-A must complete first')
        import pandas as pd
        a = pd.read_csv(c.OUT / 'features/E9-A.csv', float_precision='round_trip')
        c.require(np.array_equal(matrix[a.columns].to_numpy(), a.to_numpy()), '44 E9-A columns differ')
    # Exclusive run marker prevents accidental duplicate fits or rerunning observed results.
    c.write_json(c.OUT / f'evaluation/{variant}_started.json', {'expected_rf_fits': 5, 'feature_count': len(names)})
    predictions = np.full(561, np.nan)
    for fold in range(1, 6):
        train = metadata.fold_id.to_numpy() != fold
        valid = ~train
        c.require(set(metadata.loc[train, 'canonical_id']).isdisjoint(metadata.loc[valid, 'canonical_id']), 'training leakage')
        model = RandomForestRegressor(**config['random_forest'])
        c.require(model.get_params() == lock['random_forest'], 'RF defaults changed')
        # No fitted preprocessing or corpus statistics; train targets are indexed explicitly.
        model.fit(matrix.loc[train, names].to_numpy(float), metadata.loc[train, 'p_hallucination'].to_numpy(float))
        predictions[valid] = np.clip(model.predict(matrix.loc[valid, names].to_numpy(float)), 0, 1)
        c.write_json(c.OUT / f'evaluation/fit_{variant}_{fold}.json', {'fold': fold, 'completed': True})
    result = old[['canonical_id', 'fold_id']].copy()
    result['prediction'] = predictions
    with (c.OUT / f'evaluation/{variant}_oof.csv').open('x', newline='', encoding='utf-8') as handle:
        result.to_csv(handle, index=False)
    report = {'status': 'COMPLETED', 'rf_fits': 5, 'feature_count': len(names),
              'metrics': c.diagnostics(metadata, predictions),
              'paired_vs_e6_v3': c.paired(metadata.label_bin, old.prediction, predictions)}
    verify()
    c.write_json(c.OUT / f'evaluation/{variant}_metrics.json', report)
    return report


if __name__ == '__main__':
    import argparse
    import pandas as pd
    parser = argparse.ArgumentParser()
    parser.add_argument('--variant', choices=['E9-A', 'E9-B'], required=True)
    args = parser.parse_args()
    matrix = pd.read_csv(c.OUT / f'features/{args.variant}.csv', float_precision='round_trip')
    print(evaluate(matrix, args.variant))
