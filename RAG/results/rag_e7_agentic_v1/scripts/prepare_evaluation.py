"""Freeze label-free actions, tests, source and configuration before first RF fit."""
from e7_common import *


def main():
    import numpy as np
    from router import plan_routes, USE, FALLBACK, OBSERVATIONS
    freeze = verify_integrity()
    for name in ('evaluation_freeze.json', 'routes_freeze.json'):
        if (OUT / 'config' / name).exists():
            raise FileExistsError('Pre-evaluation outputs already frozen')
    assert not (OUT / 'evaluation/evaluation_started.json').exists()
    contracts = read_json(OUT / 'config/e7_contracts.json')
    assert contracts['status'] == 'PASS'
    assert read_json(OUT / 'config/security_e7_contracts_v1.json')['operational_violations'] == []
    preflight = initial_preflight()
    features, metadata, predictors, ev = aligned_label_free()
    signals = retrieval_metadata(metadata.canonical_id.tolist())
    routes, thresholds = plan_routes(metadata, signals)
    assert len(routes) == routes.canonical_id.nunique() == 561
    assert set(routes.route) == {USE, FALLBACK}
    for fold, record in thresholds.items():
        rows = (metadata.fold_id != int(fold)) & (signals.evidence_available == 1)
        assert record['train_evidence_ids'] == metadata.loc[rows, 'canonical_id'].tolist()
        assert record['threshold'] == float(np.quantile(signals.loc[rows,'top1_cosine'],.5,method='linear'))
        assert not set(record['train_ids']) & set(record['validation_ids'])
    csv_write(OUT / 'routing/router_inputs.csv', signals)
    csv_write(OUT / 'routing/routes.csv', routes)
    write_json(OUT / 'config/fold_thresholds.json', thresholds)
    route_files = ['routing/router_inputs.csv','routing/routes.csv','config/fold_thresholds.json']
    write_json(OUT / 'config/routes_freeze.json', {
        'frozen_utc':now(),'rows':561,'router_inputs':list(OBSERVATIONS),'labels_loaded':False,
        'saved_predictions_loaded':False,'files':{p:sha(OUT / p) for p in route_files}})
    import e7_common
    assert e7_common.GUARD is not None and not e7_common.GUARD.events
    write_json(OUT / 'config/pre_evaluation_preflight.json', preflight)
    implementations = sorted(p for folder in ('scripts','tests') for p in (OUT/folder).glob('*.py'))
    implementation_hashes = {p.relative_to(OUT).as_posix():sha(p) for p in implementations}
    assert implementation_hashes == contracts['implementation_sha256']
    config_paths = route_files + ['config/routes_freeze.json','config/e7_contracts.json',
                                  'config/security_e7_contracts_v1.json','config/pre_evaluation_preflight.json']
    write_json(OUT / 'config/evaluation_freeze.json', {
        'frozen_utc':now(),'protocol_sha256':freeze['protocol_sha256'],
        'protocol_freeze_sha256':sha(OUT / 'config/protocol_freeze.json'),
        'implementation_sha256':implementation_hashes,'protected_sha256':freeze['protected_sha256'],
        'fold_sha256':sha(FOLDS),'e3_predictors':ev.E3,'e6_predictors':predictors,
        'router_inputs':list(OBSERVATIONS),'router_quantile':.5,
        'routing_rule':'evidence_available and top1_cosine >= outer_train_evidence_median -> E6; else E3',
        'random_forest':read_json(E6 / 'config/run_config.json')['random_forest'],
        'packages':preflight['packages'],'python':preflight['python'],
        'expected_evaluation_count':1,'expected_outer_folds':5,'expected_rf_fits':10,
        'config_sha256':{p:sha(OUT / p) for p in config_paths},
        'source_report_before_completion_sha256':sha(OUT / 'E7_RESULTS.md'),
    })
    print('PASS: protocol, implementation, all routing decisions and thresholds frozen before labels/fits.',flush=True)


if __name__ == '__main__':
    guard = offline('prepare_evaluation_v1')
    try:
        main()
        assert not guard.events
    finally:
        guard.save()
