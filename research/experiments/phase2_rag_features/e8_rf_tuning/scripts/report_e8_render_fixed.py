"""Audit saved nested predictions without fits and write the final E8 report."""
import json
import hashlib
import e8_common as c
from evaluate_e8 import verify_execution


def main():
    guard=c.offline('report_v1')
    try:
        import numpy as np
        import pandas as pd
        from nested_rf import metrics, paired, select, validate_splits
        from e8_data import load_data, baseline, runtime
        lock=verify_execution(); rt=runtime()
        frame,columns=load_data(); base,basecheck=baseline(frame)
        result=c.read_json(c.OUT/'evaluation/e8_metrics.json')
        assert result['status']=='COMPLETED'
        f=pd.read_csv(c.OUT/'evaluation/paired_row_diagnostics.csv',float_precision='round_trip')
        oof=pd.read_csv(c.OUT/'evaluation/e8_oof_predictions.csv',float_precision='round_trip')
        assert c.sha(c.OUT/'evaluation/e8_oof_predictions.csv')==result['outer_oof_sha256']
        assert f.canonical_id.tolist()==oof.canonical_id.tolist()==frame.canonical_id.tolist()
        assert len(oof)==oof.canonical_id.nunique()==561
        for key in ['fold_id','task','label_bin','p_hallucination','rag_evidence_available']:
            assert np.array_equal(f[key],frame[key]),key
        assert np.array_equal(f.E8,oof.prediction) and np.array_equal(f.E6,base.prediction)
        d=result['diagnostics']
        for groups,saved in [([('all',f)],{'all':d['all_rows']}),(f.groupby('fold_id'),d['per_fold']),
                             (f.groupby('task'),d['per_task']),(f.groupby('rag_evidence_available'),d['by_evidence'])]:
            for key,g in groups:
                for name in ['E6','E8']:
                    assert metrics(g.label_bin,g.p_hallucination,g[name])==saved[str(key)][name]
        recomputed=paired(f.label_bin,f.E6,f.E8)
        for key,value in recomputed.items(): assert value==result['paired_vs_e6'][key],key
        splits=c.read_json(c.OUT/'splits/nested_splits.json')['outer_folds']
        validate_splits(splits,frame.canonical_id.tolist())
        configs=c.read_json(c.OUT/'config/configurations.json')['configurations']
        selections=c.read_json(c.OUT/'evaluation/selected_configurations.json')
        events=[json.loads(line) for line in (c.OUT/'evaluation/fit_events.jsonl').read_text().splitlines()]
        starts=[e for e in events if e['event']=='fit_started']
        ends=[e for e in events if e['event']=='fit_completed']
        assert len(events)==190 and len(starts)==len(ends)==95
        assert [e['fit_number'] for e in starts]==[e['fit_number'] for e in ends]==list(range(1,96))
        indexed=frame.set_index('canonical_id')
        for start,end in zip(starts,ends):
            assert start['utc']<=end['utc']
            assert {k:v for k,v in start.items() if k not in ('event','utc')}=={k:v for k,v in end.items() if k not in ('event','utc')}
            outer=splits[end['outer_fold']-1]
            expected=outer['inner'][end['inner_fold']-1] if end['stage']=='inner' else outer
            assert end['train_ids']==expected['train_ids'] and end['prediction_ids']==expected['validation_ids']
            cfg=next(z for z in configs if z['id']==end['configuration'])
            assert cfg['parameters']==end['parameters']
            ti,vi=end['train_ids'],end['prediction_ids']
            arrays={'train_x_sha256':indexed.loc[ti,columns].to_numpy(float),
                    'train_y_sha256':indexed.loc[ti,'p_hallucination'].to_numpy(float),
                    'predict_x_sha256':indexed.loc[vi,columns].to_numpy(float)}
            for key,array in arrays.items(): assert hashlib.sha256(array.tobytes()).hexdigest()==end[key]
            if end['stage']=='outer_selected':
                assert end['configuration']==selections[end['outer_fold']-1]['selected_configuration']
                assert selections[end['outer_fold']-1]['selected_utc']<=start['utc']
        inner_metrics_verified=0
        for split,selection in zip(splits,selections):
            fold=split['outer_fold']; training=indexed.loc[split['train_ids']]
            inner=pd.read_csv(c.OUT/f'evaluation/inner_oof_fold_{fold}.csv',float_precision='round_trip')
            scores=[]
            for cfg in configs:
                part=inner[inner.configuration==cfg['id']]
                assert part.canonical_id.tolist()==split['train_ids']
                score={'configuration':cfg['id'],'order':cfg['order'],
                       **metrics(training.label_bin,training.p_hallucination,part.prediction),'outer_fold':fold}
                scores.append(score); inner_metrics_verified+=1
                relevant=[e for e in ends if e['outer_fold']==fold and e['configuration']==cfg['id'] and e['stage']=='inner']
                assert [e['inner_fold'] for e in relevant]==[1,2,3]
            assert scores==selection['inner_scores']
            assert select(scores)==selection['selected_configuration']
            rows=oof[oof.fold_id==fold]
            assert rows.selected_configuration.eq(selection['selected_configuration']).all()
        assert sum(e['stage']=='inner' for e in ends)==90
        assert sum(e['stage']=='outer_selected' for e in ends)==5
        assert result['configuration_frequency']=={cfg['id']:sum(s['selected_configuration']==cfg['id'] for s in selections) for cfg in configs}
        for phase in ['prepare_v1','evaluate_v1']:
            assert not c.read_json(c.OUT/f'config/security_{phase}.json')['operational_violations']
        verify_execution(); assert not guard.events
        audit={'status':'PASS','verified_utc':c.now(),'protected_files_unchanged':lock['protected_count'],
               'inner_metrics_recomputed':inner_metrics_verified,'selected_configurations_verified':5,
               'outer_rows':561,'fits_started':95,'fits_completed':95,'inner_fits':90,'outer_fits':5,
               'baseline_verification_fits':0,'paired_statistics_recomputed':True,
               'train_target_prediction_array_hashes_verified':285,'operational_guard_violations':0,
               'contracts_passed':c.read_json(c.OUT/'config/contracts.json')['tests_run']}
        c.write_json(c.OUT/'config/final_integrity.json',audit)
        text=render_report(result,selections,splits,rt,audit,basecheck,lock)
        with (c.OUT/'E8_RESULTS.md').open('x',encoding='utf-8',newline='\n') as handle: handle.write(text)
    finally:
        guard.save()
    c.write_json(c.OUT/'config/completion_manifest.json',{
        'status':'COMPLETED','completed_utc':c.now(),'nested_evaluations':1,
        'files':{p.relative_to(c.OUT).as_posix():c.sha(p) for p in sorted(c.OUT.rglob('*'))
                 if p.is_file() and 'runtime_tmp' not in p.parts and '__pycache__' not in p.parts}})
    print(json.dumps({'status':'COMPLETED','audit':audit,'report':str(c.OUT/'E8_RESULTS.md')}),flush=True)


def render_report(result,selections,splits,runtime,audit,baseline,lock):
    d=result['diagnostics']; comparison=result['paired_vs_e6']; b=comparison['bootstrap']
    def num(v): return 'undefined' if v is None else f'{v:.10f}'
    lines=['# E8 v1 — Random Forest tuning on frozen E6 features','',
           '**COMPLETED — EXPLORATORY DEVELOPMENT-ONLY.** One frozen nested evaluation; 95 E8 fits and zero additional baseline verification fits. '
           'No configuration, feature, threshold or selection rule was changed after seeing results.','',
           '## Overall result','',
           '| Procedure | Correct / N | Outer OOF accuracy | Outer OOF Spearman |',
           '|---|---:|---:|---:|']
    for name in ['E6','E8']:
        m=d['all_rows'][name];lines.append(f"| {name} | {m['correct']}/{m['n']} | {m['accuracy']:.10f} ({m['accuracy']*100:.4f}%) | {num(m['spearman'])} |")
    net=comparison['net_correct']
    direction='improved' if net>0 else ('reduced' if net<0 else 'matched')
    lines+=['',f"Nested tuning {direction} the E6 development correct count: net {net:+d}/561; accuracy difference {b['accuracy_difference_pp']:+.6f} percentage points.",
            '', '## Fixed inputs, estimator and baseline','',
            'Exactly the 25 frozen E6 columns, same ordered 561 canonical IDs and locked five outer folds; all samples use the E6 feature path, with no E7 router. '
            'Target is p_hallucination; binary strata use the approved label_bin. No features were recomputed or transformed. '
            'E6 features were parsed with float_precision="round_trip"; exact arrays, ID order, labels and folds were validated against canonical artifacts.', '',
            'C0 is identical to all 18 accepted E6 RF parameters. Every fit receives an explicit full dictionary: '
            'n_estimators=500, criterion="squared_error", max_depth=None, min_samples_split=2, min_weight_fraction_leaf=0.0, '
            'max_leaf_nodes=None, min_impurity_decrease=0.0, bootstrap=True, oob_score=False, n_jobs=-1, random_state=42, verbose=0, '
            'warm_start=False, ccp_alpha=0.0, max_samples=None, monotonic_cst=None, plus the candidate min_samples_leaf and max_features below. '
            'Predictions are clipped to [0,1]; classification uses >=0.5. Full machine-readable dictionaries and runtime are in config/configurations.json.', '',
            'Runtime matches E6: Python 3.11.9, scikit-learn 1.8.0, NumPy 2.4.4, pandas 3.0.2, SciPy 1.17.1. '
            'The saved E6 baseline reproduces 453/561, accuracy 0.8074866310160428 and Spearman 0.744420539373989. '
            f"E7's existing fresh E6 predictions agree per ID within 1e-12 (actual maximum difference {baseline['fresh_e7_e6_max_absolute_difference']:.17g}), "
            'with identical binary and 12-decimal-rounded predictions. This verification required zero new baseline fits.','',
            '## Predefined configurations and selection frequency','',
            '| ID | min_samples_leaf | max_features | Selected outer folds | Frequency |',
            '|---|---:|---:|---|---:|']
    for i,(leaf,mf) in enumerate([(1,1.0),(3,1.0),(5,1.0),(1,.5),(3,.5),(5,.5)]):
        config=f'C{i}'; folds=[str(s['outer_fold']) for s in selections if s['selected_configuration']==config]
        lines.append(f"| {config} | {leaf} | {mf} | {', '.join(folds) or 'none'} | {result['configuration_frequency'][config]}/5 |")
    lines+=['','## Nested selection and leakage checks','',
            'Within each canonical-ordered outer-training set, a fresh StratifiedKFold(n_splits=3, shuffle=True, random_state=42) uses task + "_" + str(label_bin). '
            'All six candidates share those three saved splits. Minimum outer-training stratum counts by outer fold are '
            f"{[min(s['stratum_counts'].values()) for s in splits]}; all strata have at least three rows. "
            'The frozen split JSON records the training and validation IDs and all stratum counts; the inner assignment CSV has 2,244 rows.', '',
            'For each candidate, the three inner predictions cover the entire outer-training set once. Selection uses pooled inner OOF accuracy, '
            'then pooled inner OOF Spearman, then earliest C0–C5. Undefined Spearman ranks below defined values at equal accuracy. '
            'No R² or average-of-fold scores enter selection. Spearman uses unrounded target and predictions rounded to 12 decimals.', '',
            'The tuning function receives only outer-training rows, inner splits, feature names and configurations. Inner train/validation IDs are disjoint from outer validation. '
            'Each selection and all six inner scores were saved before selected outer-model fitting/prediction. Outer-validation labels enter scoring only after '
            'all five selections and outer OOF predictions exist. This evaluates a selection procedure, not a globally chosen RF configuration.', '',
            '| Outer fold | Selected | Selected inner correct / N | Selected inner accuracy | Selected inner Spearman |',
            '|---|---|---:|---:|---:|']
    for s in selections:
        m=next(x for x in s['inner_scores'] if x['configuration']==s['selected_configuration'])
        lines.append(f"| {s['outer_fold']} | {s['selected_configuration']} | {m['correct']}/{m['n']} | {m['accuracy']:.10f} | {num(m['spearman'])} |")
    lines+=['','All 30 candidate/outer-fold scores are in evaluation/inner_scores.csv; all candidate inner OOF predictions are saved separately for each outer fold.','',
            '## Outer OOF results by fold, task and evidence','',
            '| Group | N | E6 correct | E8 correct | E6 accuracy | E8 accuracy | E6 Spearman | E8 Spearman |',
            '|---|---:|---:|---:|---:|---:|---:|---:|']
    groups=[(f'Fold {k}',g) for k,g in d['per_fold'].items()]+list(d['per_task'].items())
    groups+=[('With definition',d['by_evidence']['1']),('Without definition',d['by_evidence']['0'])]
    for title,g in groups:
        a,z=g['E6'],g['E8']
        lines.append(f"| {title} | {z['n']} | {a['correct']} | {z['correct']} | {a['accuracy']:.10f} | {z['accuracy']:.10f} | {num(a['spearman'])} | {num(z['spearman'])} |")
    lo,hi=b['percentile_95_ci'];lop,hip=b['percentile_95_ci_pp']
    lines+=['','## Paired comparison against E6','',
            f"Corrections: **{comparison['corrected']}**. New errors: **{comparison['introduced_errors']}**. Net: **{net:+d}**. "
            f"Exact two-sided McNemar p = **{comparison['mcnemar_exact_two_sided_p']:.10f}**.", '',
            f"Accuracy difference E8 minus E6: **{b['accuracy_difference']:+.10f}**, or **{b['accuracy_difference_pp']:+.6f} percentage points**. "
            f"Paired-bootstrap 95% percentile interval: **[{lo:+.10f}, {hi:+.10f}]**, or **[{lop:+.6f}, {hip:+.6f}] percentage points**.", '',
            'The existing procedure is preserved: exact binomtest(corrections, discordant total, 0.5), p=1 for no discordance; '
            '10,000 paired row resamples with numpy.default_rng(42), sample size 561 and percentile 2.5/97.5. '
            'Bootstrap conditions on fixed OOF correctness and omits retraining/selection variability. '
            'Every correction and new-error canonical ID is in evaluation/e8_metrics.json; evaluation/paired_row_diagnostics.csv covers all rows.', '',
            '## Freeze chronology, fit accounting and integrity','',
            f"Existing protocol freeze: {c.read_json(c.OUT/'config/protocol_freeze.json')['frozen_utc']}. "
            f"Complete code/configuration/split freeze: {lock['frozen_utc']}. "
            f"First-suite marker: {c.read_json(c.OUT/'evaluation/evaluation_started.json')['started_utc']}. "
            f"Evaluation completed: {result['completed_utc']}.", '',
            'The directory initially contained only E8_PROTOCOL.md, initial_integrity.json, protocol_freeze.json and e8_common.py. '
            'No prior E8 fit or result was present. Those files were retained; the incomplete implementation was completed without changing the frozen protocol.', '',
            f"Pre-fit contracts: **{audit['contracts_passed']} PASS**, plus real data alignment, runtime, C0 identity, saved baseline and thread-execution checks. "
            '**90 inner fits + 5 selected outer fits = 95 E8 fits**. Additional baseline verification fits: **0**. '
            'No final all-data fit or second nested run occurred.', '',
            f"Final read-only audit: 95 fit-start/fit-completion pairs; 285 training/target/prediction array hashes; "
            'all inner/outer ID partitions; all 30 pooled inner scores and five selections recomputed; 561 unique finite outer OOF predictions; '
            f"all subgroup and paired statistics verified; **{audit['protected_files_unchanged']} protected E3/E5/E6/E7 files unchanged**. "
            'Operational network/access violations: zero. Process-local guards are defense-in-depth, not OS isolation.', '',
            '## Interpretation and limitations','',
            ('The paired 95% interval includes zero; this run does not establish an accuracy advantage over E6.' if lo<=0<=hi else
             'The paired interval excludes zero for these fixed development OOF predictions; this alone does not establish generalization.'), '',
            '**Exploratory development-only on a reused development pool.** Nested CV keeps each outer-validation label out of its hyperparameter selection, '
            'but does not erase prior experiment/design exposure or turn the pool into an independent test. '
            'No globally best configuration is inferred from selection frequency or aggregate outer results. '
            'Subgroups are descriptive, no adaptive-research correction is claimed, and non-significance does not establish equivalence. '
            'The inherited E6 reference-assisted features, DM-only definition coverage and Module 4 provenance limitations remain.', '',
            'All new files are under RAG/results/rag_e8_rf_tuning_v1/. E3/E5/E6/E7 and existing user changes, including untracked E7, were preserved. '
            'No retrieval, MPNet/NLI extraction, external data, LLM/API calls, synthetic-data edits, official-test access, package changes, '
            'commit, push, tag or next experiment occurred.', '',
            '## Artifact map','',
            '- E8_PROTOCOL.md: unchanged preregistered protocol; config/configurations.json: full six parameter dictionaries and runtime.',
            '- splits/: canonical outer assignments, 2,244 inner assignments, full inner/outer ID lists and stratum counts.',
            '- config/execution_freeze.json: pre-fit source/test/input-reference/config/split hashes; config/final_integrity.json and completion_manifest.json: final audits.',
            '- scripts/: data checks, nested selector, preparation, one-shot evaluation and report/audit; tests/test_e8.py: pre-fit contracts.',
            '- evaluation/: 30 inner score rows, all inner OOF predictions, five selection records, 561 final OOF predictions, paired row diagnostics and metrics.',
            '- evaluation/fit_events.jsonl: 190 start/completion records for 95 fits, full parameters/IDs and array hashes.','']
    lines += ['## Report-rendering repair', '', 'The originally frozen report_e8.py had an unterminated display string at line 138 and stopped at parsing, before any audit/report execution. It remains unchanged. report_e8_render_fixed.py fixes only that closing quote and adds this disclosure. All experiment inputs, splits, candidate settings, selection code, training code, OOF predictions and scores remain frozen. No fit was repeated. See config/report_render_repair.json for both source hashes.', '']
    return '\n'.join(lines)


if __name__=='__main__': main()
