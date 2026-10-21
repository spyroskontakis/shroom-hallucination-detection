"""Lock configuration and provenance before E6 model execution."""
import importlib.metadata
import sys
from e6_common import *


def main():
    from sklearn.ensemble import RandomForestRegressor
    offline()
    old = read_json(OUT / 'config/preflight.json')
    paths = set(old['input_sha256']) | set(old['oof_sha256'])
    paths.update(str(p.relative_to(ROOT)).replace('\\', '/') for p in CONT.rglob('*') if p.is_file())
    paths.update(str(p.relative_to(ROOT)).replace('\\', '/') for p in (INPUTS, SNAPSHOT, FUSED))
    for p, expected in {**old['input_sha256'], **old['oof_sha256']}.items():
        assert sha(ROOT / p) == expected
    protected = {p: sha(ROOT / p) for p in sorted(paths)}
    accepted = read_json(REPLAY / 'runtime/feature_runtime_provenance.json')
    files = accepted['files']
    for group in files.values():
        for meta in group.values():
            assert sha(Path(meta['path'])) == meta['sha256'], meta['path']
    packages = {k: importlib.metadata.version(k) for k in
                ('torch', 'transformers', 'sentence-transformers', 'numpy', 'scipy', 'scikit-learn', 'pandas')}
    for k, version in accepted['packages'].items():
        assert packages[k] == version, (k, packages[k], version)
    for k, version in {'scikit-learn': '1.8.0', 'scipy': '1.17.1', 'pandas': '3.0.2'}.items():
        assert packages[k] == version, (k, packages[k], version)
    assert protected[str(INPUTS.relative_to(ROOT)).replace('\\', '/')] == accepted['inputs']['label_free_csv']['sha256']
    assert sha(SNAPSHOT) == accepted['inputs']['lexical_snapshot']['sha256']
    implementation = {str(p.relative_to(OUT)).replace('\\', '/'): sha(p)
                      for p in sorted((OUT / 'scripts').glob('*.py'))}
    implementation['E6_PROTOCOL.md'] = sha(OUT / 'E6_PROTOCOL.md')
    result = {
        'schema': 'rag-e6-v1-locked', 'locked_utc': now(), 'features': FEATURES,
        'python': sys.version, 'executable': sys.executable, 'packages': packages,
        'random_forest': RandomForestRegressor(n_estimators=500, random_state=42, n_jobs=-1).get_params(),
        'threshold': 0.5, 'clip': [0, 1], 'spearman_prediction_rounding_decimals': 12,
        'bootstrap': {'replicates': 10000, 'seed': 42, 'percentiles': [0.025, 0.975], 'unit': 'paired canonical row'},
        'model_files': files, 'accepted_runtime_sha256': sha(REPLAY / 'runtime/feature_runtime_provenance.json'),
        'protected_sha256': protected, 'implementation_sha256': implementation,
        'ranking': {'function': 'accepted pinned select_top5 unchanged', 'historical_ranking_available': False,
                    'query_fields': ['term', 'src'], 'top_k': 5, 'consistency_atol': 1e-12, 'consistency_rtol': 0},
        'new_features': {'definition_rank': 1, 'nli_premise': 'candidate_definition', 'nli_hypothesis': 'hyp',
                         'fallback': [0, 0, 0, 0], 'device': 'cpu', 'dtype': 'float32'},
    }
    write_json(OUT / 'config/run_config.json', result)
    print(json.dumps({'status': 'CONFIG_LOCKED', 'protected_files': len(protected), 'packages': packages}), flush=True)


if __name__ == '__main__':
    main()
