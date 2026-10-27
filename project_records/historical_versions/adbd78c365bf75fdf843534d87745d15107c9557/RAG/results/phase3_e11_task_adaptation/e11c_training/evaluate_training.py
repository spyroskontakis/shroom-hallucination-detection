"""Final E11-C evaluation using the authoritative E11-A metric implementation."""
import json
import math
import subprocess
from collections import Counter
import prepare_training as p

c=p.c


def evaluate():
    p.preserve()
    spec=c.read_json(p.HERE/'E11C_TRAINING_PROTOCOL.json')
    original=p.a.load_protocol()
    human_rows=p.a.csv_rows(c.root()/original['data']['canonical_path'])
    human={r['canonical_id']:r for r in human_rows}
    fold_of={r['canonical_id']:int(r['fold_id']) for r in p.a.csv_rows(c.root()/original['data']['folds_path'])}
    rows=[];summaries={};sanity={};hashes={}
    for f in range(1,6):
        path=p.PRIVATE/f'returned/fold_{f}.json'
        data=c.read_json(path)
        c.require(data['fold_id']==f,'returned fold identity')
        stages=data['stages'];c.require(len(stages)==2,'two fits per fold')
        for stage,report in enumerate(stages,1):
            c.require(report['status']=='PASS' and report['stage']==stage and report['fold_id']==f and
                report['protocol_sha256']==spec['protocol_sha256'] and report['losses_all_finite'], 'stage provenance')
            c.require(len(report['loss_by_epoch'])==(1 if stage==1 else 5),'fixed epochs')
        c.require(stages[1]['initial_model_weights_sha256']==stages[0]['checkpoint_sha256'],'stage checkpoint transfer')
        raw=data['predictions_jsonl'].encode()
        c.require(c.digest(raw)==stages[1]['heldout_predictions_sha256'],'returned OOF hash')
        predictions=[c.strict_json(line) for line in data['predictions_jsonl'].splitlines()]
        c.require(len(predictions)==(113 if f==1 else 112),'heldout count')
        for r in predictions:
            c.require(r['sample_id'] in human and r['fold_id']==f==fold_of[r['sample_id']] and
                r['task']==human[r['sample_id']]['task'] and math.isfinite(r['p_H']) and 0<=r['p_H']<=1
                and r['predicted_class']==int(r['p_H']>=0.5),'OOF identity/probability')
        rows.extend(predictions)
        summaries[str(f)]={'stages':stages,'metrics':p.ev.metric(predictions,human)}
        sanity[str(f)]={'min_probability':min(r['p_H'] for r in predictions),
            'max_probability':max(r['p_H'] for r in predictions),
            'predicted_class_counts':dict(Counter(str(r['predicted_class']) for r in predictions)),
            'one_class_collapse':len({r['predicted_class'] for r in predictions})==1,
            'nan_inf':False,'selected_epoch':{'stage1':1,'stage2':5}}
        hashes[str(path.relative_to(p.HERE))]=c.sha(path)
    c.require(len(rows)==len({r['sample_id'] for r in rows})==561 and {r['sample_id'] for r in rows}==set(human),'complete OOF')
    byid={r['sample_id']:r for r in rows};rows=[byid[r['canonical_id']] for r in human_rows]
    c.write_once(p.PRIVATE/'E11C_OOF_PREDICTIONS.jsonl',c.rows_bytes(rows))
    metrics=p.ev.metric(rows,human)
    pre=c.read_json(p.HERE/'PRETRAINING_AUDIT.json')
    comparisons={name:{'baseline':pre[name],
        'delta_correct':metrics['correct']-pre[name]['correct'],
        'delta_accuracy':metrics['accuracy']-pre[name]['accuracy'],
        'delta_spearman':metrics['spearman']-pre[name]['spearman']} for name in ('E11A','E10')}
    results={'status':'PASS','experiment':'E11-C','protocol_sha256':spec['protocol_sha256'],
        'overall':metrics,'per_task':{t:p.ev.metric([r for r in rows if r['task']==t],human) for t in c.POLICY},
        'folds':summaries,'sanity':sanity,'comparisons':comparisons,'statistical_significance_tested':False,
        'model_fits':10,'seed':42,'architecture':spec['architecture'],
        'teacher_pool':11887,'duplicate_input_exclusions':pre['duplicate_input_exclusions'],
        'synthetic_rows_by_fold':{f:s['synthetic_rows'] for f,s in spec['folds'].items()},
        'leakage_exclusions_by_fold':{f:s['leakage_exclusions'] for f,s in spec['folds'].items()}}
    c.save(p.HERE/'E11C_RESULTS.json',results)
    report=['# E11-C controlled result','',
        '| Experiment | Supervision | Contrastive | Correct/561 | Accuracy | Spearman |',
        '|---|---|---|---:|---:|---:|']
    for name,supervision,m in [('E11-A','Human only',pre['E11A']),('E11-C','Synthetic then human',metrics),('E10','Feature-based',pre['E10'])]:
        report.append(f"| {name} | {supervision} | No | {m['correct']}/561 | {m['accuracy']:.9f} | {m['spearman']:.9f} |")
    report+=['','```json',json.dumps(results,indent=2),'```','',
             'No statistical significance claim is made. No hyperparameter or threshold tuning was performed.','']
    c.write_once(p.HERE/'E11C_RESULTS.md','\n'.join(report).encode())
    training_audit={'status':'PASS','model_fits':10,'protocol':spec,'sanity':sanity,
        'all_prior_artifacts_unchanged':True,'human_stage_matches_E11A':True,
        'Azure_rescue_excluded':True,'uncertain_excluded':True,'failures_excluded':True,
        'official_test_access':False,'teacher_API_calls':0,'commit':False,'push':False,
        'gpu':'one A100-80GB per fold job; five independent fold jobs',
        'training_seconds_sum':sum(s['elapsed_seconds'] for f in summaries.values() for s in f['stages']),
        'tests':c.read_json(p.HERE/'FINAL_TEST_REPORT.json'),
        'git_status_short':subprocess.run(['git','status','--short'],capture_output=True,text=True,check=True).stdout.splitlines()}
    c.save(p.HERE/'E11C_TRAINING_AUDIT.json',training_audit)
    c.write_once(p.HERE/'E11C_TRAINING_AUDIT.md',('# E11-C training audit\n\n```json\n'+json.dumps(training_audit,indent=2)+'\n```\n').encode())
    for path in list(p.HERE.glob('*.py'))+list(p.HERE.glob('*.json'))+list(p.HERE.glob('*.md'))+[p.PRIVATE/'E11C_OOF_PREDICTIONS.jsonl']:
        if path.name!='E11C_MANIFEST.json':hashes[str(path.relative_to(p.HERE))]=c.sha(path)
    c.save(p.HERE/'E11C_MANIFEST.json',{'status':'PASS','files_sha256':hashes,
        'checkpoints':'Persisted on Modal volume shroom-e11c-fixed-two-stage-results; hashes in fold summaries',
        'teacher_protocol_sha256':spec['teacher_protocol_sha256'],'protocol_sha256':spec['protocol_sha256']})
    p.preserve()
    print(json.dumps({'overall':metrics,'per_task':results['per_task'],'comparisons':comparisons},indent=2))


if __name__=='__main__':evaluate()
