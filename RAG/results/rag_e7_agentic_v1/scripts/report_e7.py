"""Read completed OOF files, verify integrity, and report without any training."""
from e7_common import *


def main():
    import numpy as np
    import pandas as pd
    from router import USE, FALLBACK, OBSERVATIONS, plan_routes, finish_prediction
    from evaluation_common import verify_evaluation_freeze, metric, paired
    frozen = verify_evaluation_freeze()
    result = read_json(OUT/'evaluation/e7_metrics.json')
    assert result['status']=='COMPLETED' and result['rf_fits']==10 and result['e7_evaluation_count']==1
    for phase in ('e7_contracts_v1','prepare_evaluation_v1','evaluate_e7_v1'):
        security = read_json(OUT/f'config/security_{phase}.json')
        assert security['operational_violations']==[] and security['operational_network_attempts']==0
    start = read_json(OUT/'evaluation/evaluation_started.json')
    route_freeze = read_json(OUT/'config/routes_freeze.json')
    assert start['evaluation_freeze_sha256']==sha(OUT/'config/evaluation_freeze.json')
    assert route_freeze['frozen_utc'] < frozen['frozen_utc'] < start['started_utc'] < result['completed_utc']
    metadata = pd.read_csv(MIXED,usecols=['canonical_id','fold_id','task'])
    signals = retrieval_metadata(metadata.canonical_id.tolist())
    expected_routes, thresholds = plan_routes(metadata,signals)
    routes = pd.read_csv(OUT/'routing/routes.csv',float_precision='round_trip')
    pd.testing.assert_frame_equal(routes,expected_routes,check_dtype=False)
    assert thresholds == read_json(OUT/'config/fold_thresholds.json')
    diag = pd.read_csv(OUT/'evaluation/paired_row_diagnostics.csv',float_precision='round_trip')
    oof = pd.read_csv(OUT/'evaluation/e7_oof_predictions.csv',float_precision='round_trip')
    assert len(oof)==oof.canonical_id.nunique()==561
    assert oof.canonical_id.tolist()==metadata.canonical_id.tolist()==diag.canonical_id.tolist()
    assert np.array_equal(oof.fold_id,metadata.fold_id)
    assert np.array_equal(oof.route,routes.route) and np.array_equal(diag.route,routes.route)
    assert np.array_equal(oof.prediction,diag.E7)
    expected_predictions=np.where(routes.route==USE,diag.E6_fresh,diag.E3_fresh)
    assert np.array_equal(expected_predictions,oof.prediction)
    assert np.isfinite(oof.prediction).all() and oof.prediction.between(0,1).all()
    trajectories=read_json(OUT/'evaluation/agent_trajectories.json')
    assert len(trajectories)==561
    for i,trajectory in enumerate(trajectories):
        row=diag.iloc[i]
        assert trajectory['canonical_id']==row.canonical_id and trajectory['fold_id']==int(row.fold_id)
        expected=finish_prediction(row.route,{'E3':row.E3_fresh,'E6':row.E6_fresh})
        for key,value in expected.items():
            assert trajectory[key]==value
    for name in ('E3','E6'):
        for fold in range(1,6):
            fit=read_json(OUT/f'evaluation/fits/{name}_fold{fold}_started.json')
            done=read_json(OUT/f'evaluation/fits/{name}_fold{fold}_completed.json')
            assert fit['train_ids']==metadata.loc[metadata.fold_id!=fold,'canonical_id'].tolist()
            assert fit['validation_ids']==metadata.loc[metadata.fold_id==fold,'canonical_id'].tolist()
            assert done['fit_count']==done['predict_count']==1
            assert start['started_utc']<=fit['started_utc']<=done['completed_utc']<=result['completed_utc']
    assert len(list((OUT/'evaluation/fits').glob('*_started.json')))==10
    assert len(list((OUT/'evaluation/fits').glob('*_completed.json')))==10
    d=result['diagnostics']
    for name in ('E3','E5','E6','E7'):
        assert metric(diag,name)==d['overall'][name]
    for name in ('E3','E6'):
        assert paired(diag,name)==d['paired'][name]
    for key,col in [('per_task','task'),('by_evidence','evidence_available'),('by_route','route')]:
        for group,rows in diag.groupby(col):
            k=str(int(group)) if key=='by_evidence' else str(group)
            assert metric(rows,'E7')==d[key][k]
    for fold,rows in diag.groupby('fold_id'):
        for k,v in metric(rows,'E7').items():
            assert d['per_fold'][str(fold)][k]==v

    # Post-execution ceiling diagnostic only. No oracle decisions are used by E7.
    truth=diag.label_bin.to_numpy(int)
    c3=(diag.E3.to_numpy()>=.5).astype(int)==truth
    c6=(diag.E6.to_numpy()>=.5).astype(int)==truth
    no=diag.evidence_available.to_numpy()==0
    gains=c3 & ~c6
    losses=~c3 & c6
    forced_net=int(c3[no].sum()-c6[no].sum())
    loose=int(c6.sum())+forced_net+int(gains.sum())
    tight=int(c3[no].sum())+int((c3[~no] | c6[~no]).sum())
    ceiling={
        'scope':'Post-hoc descriptive ceiling on these fixed OOF binary predictions only; not a trained router',
        'frozen_e6_correct':int(c6.sum()),'no_evidence_e3_correct':int(c3[no].sum()),
        'no_evidence_e6_correct':int(c6[no].sum()),'forced_no_evidence_net_change':forced_net,
        'e3_correct_e6_wrong_total':int(gains.sum()),'e3_correct_e6_wrong_no_evidence':int((gains&no).sum()),
        'e3_correct_e6_wrong_with_evidence':int((gains&~no).sum()),
        'e3_wrong_e6_correct_no_evidence':int((losses&no).sum()),
        'loose_upper_bound_correct':loose,'tight_oracle_upper_bound_correct':tight,
        'tight_oracle_upper_bound_accuracy':tight/561,
        'gain_ids_total':diag.loc[gains,'canonical_id'].tolist(),
        'gain_ids_with_evidence':diag.loc[gains&~no,'canonical_id'].tolist(),
    }
    assert d['overall']['E7']['correct']<=tight<=loose
    write_json(OUT/'evaluation/routing_ceiling_analysis.json',ceiling)
    freeze=verify_integrity()
    import e7_common
    assert not e7_common.GUARD.events
    audit={'status':'PASS','checked_utc':now(),'protocol_sha256':freeze['protocol_sha256'],
           'protected_files_unchanged':len(freeze['protected_sha256']),'evaluation_freeze_verified':True,
           'implementation_hashes_verified':True,'e7_evaluation_suites':1,'outer_folds':5,'rf_fits':10,
           'oof_rows':561,'unique_ids':561,'one_route_per_id':True,'all_trajectories_end':True,
           'no_evidence_all_fallback':True,'predictions_in_unit_interval':True,
           'routes_frozen_before_labels_and_fit':True,'router_inputs':list(OBSERVATIONS),
           'operational_network_attempts':0,'official_test_access':False,
           'security_scope':'Python audit guard and explicit development inputs, not OS isolation',
           'reproduction':result['reproduction']}
    write_json(OUT/'config/final_integrity_audit.json',audit)

    def fmt(x):
        return 'undefined' if x is None else f'{x:.10f}'

    def table_metrics(groups):
        lines=['| Group | Correct / N | Accuracy | Spearman |','|---|---:|---:|---:|']
        for name,m in groups.items():
            lines.append(f"| {name} | {m['correct']}/{m['n']} | {fmt(m['accuracy'])} | {fmt(m['spearman'])} |")
        return '\n'.join(lines)

    report=[
        '# E7 v1 — Selective / Agentic RAG without LLM',
        '**COMPLETED — DEVELOPMENT-ONLY.** One frozen five-fold OOF evaluation; no post-score redesign or rerun.',
        '## Actual result',table_metrics(d['overall']),
        ('The frozen selective policy did not improve E6 on this development pool.'
         if d['overall']['E7']['correct']<d['overall']['E6']['correct'] else
         'The frozen selective policy improved development accuracy over E6.'
         if d['overall']['E7']['correct']>d['overall']['E6']['correct'] else
         'E7 matched E6 development accuracy; equal accuracy does not establish statistical equivalence.'),
        '## Frozen architecture and training',
        'A deterministic controller loads cached E6 ranking metadata. Each sample follows START → RETRIEVE → ASSESS_EVIDENCE → one routing action → PREDICT → END. There is exactly one decision. RETRIEVE performs no external request.',
        'For each outer fold, tau is numpy.quantile(top1_cosine of evidence-bearing outer-training rows, 0.5, method="linear"). Evidence available and score >= tau selects USE_EXTERNAL_EVIDENCE (fresh E6 path); all other rows select FALLBACK_TO_BASE (fresh E3 path). Inference receives only evidence_available and top1_cosine. No labels, hypothesis, correctness or predictions determine routing. No inner search, tuning, retry or supervised router target exists.',
        'The accepted Module 4 run_cv code ran unchanged, with an estimator wrapper checking and logging train/validation arrays and IDs. E3 uses 14 predictors; E6 uses the frozen 25. Each RF uses 500 trees, random_state=42, n_jobs=-1 and all frozen defaults, target p_hallucination, clipping [0,1], binary threshold >=0.5. Exactly ten RF fits (5 E3 + 5 E6); zero MPNet/DeBERTa extraction or pretrained-model training. Both paths were computed for this audit; no inference-cost saving is claimed.',
        '## Training-fold medians and fold results',
        '| Fold | Train evidence N | Median tau | E6 route | E3 fallback | Correct / N | Accuracy | Spearman |',
        '|---|---:|---:|---:|---:|---:|---:|---:|',
    ]
    for f in range(1,6):
        k=str(f);m=d['per_fold'][k];t=thresholds[k]
        report.append(f"| {f} | {len(t['train_evidence_ids'])} | {t['threshold']!r} | {m['route_counts'].get(USE,0)} | {m['route_counts'].get(FALLBACK,0)} | {m['correct']}/{m['n']} | {fmt(m['accuracy'])} | {fmt(m['spearman'])} |")
    report += ['## Route distribution',
               '| Group | E6 route | E3 fallback |','|---|---:|---:|']
    route_groups={'All rows':d['route_counts'],**d['routes_by_task'],
                  'With evidence':d['routes_by_evidence']['1'],'Without evidence':d['routes_by_evidence']['0']}
    for group,count in route_groups.items():
        report.append(f'| {group} | {count.get(USE,0)} | {count.get(FALLBACK,0)} |')
    report += ['## Task, evidence and route metrics',table_metrics(d['per_task']),
               table_metrics({'With evidence':d['by_evidence']['1'],'Without evidence':d['by_evidence']['0']}),
               table_metrics(d['by_route']),
               'Spearman uses target p_hallucination and predictions rounded to 12 decimals. It is undefined for fewer than two observations or a constant target/rounded prediction. Subgroup metrics are descriptive.',
               '## Paired comparisons',
               '| Baseline | Corrections | Regressions | Net correct | Δ accuracy (pp) | Exact McNemar p | Bootstrap 95% CI (pp) |',
               '|---|---:|---:|---:|---:|---:|---|']
    for name in ('E6','E3'):
        p=d['paired'][name];ci=p['paired_bootstrap']['percentile_95_ci']
        report.append(f"| {name} | {p['corrections']} | {p['regressions']} | {p['net_correct']:+d} | {p['accuracy_difference']*100:+.6f} | {fmt(p['mcnemar_exact_two_sided_p'])} | [{ci[0]*100:+.6f}, {ci[1]*100:+.6f}] |")
    p=d['paired']['E6']
    report += [
        'E6 is the primary baseline; E3 is secondary. Exact two-sided McNemar uses binomtest(b,b+c,0.5), or p=1 for no discordance. Paired bootstrap uses 10,000 resamples of 561 paired correctness differences, default_rng(42) freshly initialized per baseline, percentile 2.5/97.5. No multiple-comparison or research-selection correction is claimed.',
        f"E7 vs E6 corrections from fallback: {p['changes_by_route'][FALLBACK]['corrections']}; regressions from fallback: {p['changes_by_route'][FALLBACK]['regressions']}. E6-route rows retain the reproduced E6 predictions. IDs of every correction/regression are in e7_metrics.json; paired_row_diagnostics.csv covers all 561 rows.",
        '## Post-execution numerical ceiling',
        f"Actual saved OOF files show no-evidence E3={ceiling['no_evidence_e3_correct']}/368 versus E6={ceiling['no_evidence_e6_correct']}/368, hence mandatory fallback changes the correct count by {forced_net:+d}. Globally there are {ceiling['e3_correct_e6_wrong_total']} E3-correct/E6-wrong rows. These establish the loose bound {int(c6.sum())} {forced_net:+d} + {int(gains.sum())} = {loose}/561.",
        f"The tighter bound is {tight}/561 ({tight/561:.10f}): {int((gains&no).sum())} of those potential corrections already occurs in the mandatory no-evidence fallback and is included in its net change. Only {int((gains&~no).sum())} additional E3-only correct row is in the evidence group. Equivalently, sum E3 correctness on no-evidence rows and max(E3 correctness,E6 correctness) on evidence rows. This oracle ceiling is an after-the-fact descriptive limit on these fixed OOF predictions, not a deployable router, not a tuned experiment and not a generalization bound. It was never used to change thresholds or actions.",
        '## Technical history and execution chronology',
        'The initial preflight stopped with three blocked writes and no fit/score. A separately authorized import-only diagnostic traced them to Windows NUL stdio for platform.py shell probes (ver / command /c ver / cmd /c ver). The process-local adapter suppresses that optional probe and uses the native Windows fallback; no filesystem allowlist was widened. ACCESS_REPAIR_REPORT.md and historical failure/security records remain. The original failure report is preserved at history/INITIAL_PREFLIGHT_FAILURE.md.',
        f"Protocol freeze: {read_json(OUT/'config/protocol_freeze.json')['frozen_utc']}. Routes frozen: {route_freeze['frozen_utc']}. Evaluation/source freeze: {frozen['frozen_utc']}. First-suite marker: {start['started_utc']}. Completed: {result['completed_utc']}.",
        f"Full E7 contracts: {read_json(OUT/'config/e7_contracts.json')['tests_run']} PASS. The later pre-evaluation preflight passed with no operational guard violation. Labels and saved predictions were projected only after the routing freeze; prior integrity reads hashed frozen bytes without using their contents for decisions.",
        '## Reproduction and final integrity',
        f"Protocol SHA-256 unchanged: `{frozen['protocol_sha256']}`. All {len(freeze['protected_sha256'])} protected E3/E5/E6/Module 4 files are unchanged. Evaluation source/config hashes, exact ID/fold alignment, all trajectories, 561 valid OOF values and ten completed fit records passed final audit. Network attempts during contracts/preparation/evaluation/reporting: zero; no official-test dataset access. The guard is process-local defense-in-depth, not OS isolation.",
    ]
    for name,r in result['reproduction'].items():
        report.append(f"{name}: fresh vs frozen predictions match per canonical ID within 1e-12; actual max absolute difference {r['max_absolute_prediction_difference']:.17g}. Binary predictions and ranks after 12-decimal rounding are identical; metrics reproduce. This goes beyond aggregate-count agreement.")
    report += [
        '## Interpretation and limitations',
        'The experiment adds explicit evidence assessment and a conditional action to the E6 retrieval-plus-semantic-verification pipeline. A training-only median is interpretable, but it is a relative cosine cutoff, not a calibrated estimate that evidence will improve prediction. The same development pool informed earlier experiments; fold-safe threshold fitting does not erase adaptive research history. Bootstrap intervals condition on fixed OOF values and omit retraining uncertainty. Non-significance is not evidence of equivalence.',
        'Evidence is DM-only. E6 retains reference-assisted E5 features and historical provenance/label-exposure caveats. Reconstructed aggregate consistency does not establish the historical complete ranking. E6 can improve no-evidence predictions through a different RF feature space; mandatory E3 fallback discards those improvements. No independent official-test generalization claim is made.',
        'The repository clone is not self-contained: authorized local canonical inputs, fold/feature/OOF files and ranking are required. E7 did not load MPNet or DeBERTa; it reused verified frozen matrices. No E8, synthetic-data change, thesis/PowerPoint edit, commit, push or tag occurred.',
        '## Artifacts',
        'scripts/: controller, guarded preflight, freeze preparation, accepted-evaluator audit wrapper, one-shot evaluation and read-only reporting. tests/: router, data-alignment, runtime and access contracts. routing/: label-free observations and frozen actions. config/: hashes, thresholds, contracts, security logs and final integrity/completion manifests. evaluation/: fresh E3/E6 predictions, E7 OOF predictions, 561 agent trajectories, paired diagnostics, metrics, ceiling analysis and ten fit-start/fit-completion pairs. Existing history/repair logs remain; earlier manifests describe their historical snapshots.',
        'Branch: agentic-rag-e7, originating at frozen rag-e6-v1 commit 0a1ef3e792867796c412070087095274b0206849. STOP after this single E7 execution.'
    ]
    target=OUT/'E7_RESULTS.md'
    assert sha(target)==frozen['source_report_before_completion_sha256'], 'Report already replaced; no overwrite'
    target.write_text('\n\n'.join(report)+'\n',encoding='utf-8',newline='\n')
    print('PASS: completed report, per-ID outputs, statistical checks and numerical ceiling verified.',flush=True)
    print(str(ceiling),flush=True)


if __name__ == '__main__':
    guard=offline('report_e7_v1')
    try:
        main()
        assert not guard.events
    finally:
        guard.save()
    from evaluation_common import verify_evaluation_freeze
    verify_evaluation_freeze()
    paths=sorted(p for p in OUT.rglob('*') if p.is_file())
    files={p.relative_to(OUT).as_posix():{'bytes':p.stat().st_size,'sha256':sha(p)} for p in paths}
    write_json(OUT/'config/completion_manifest.json',{
        'status':'COMPLETED','verified_utc':now(),'files':files,'self_excluded':True,
        'e7_evaluations':1,'rf_fits':10,'protocol_sha256':sha(OUT/'E7_PROTOCOL.md')})
