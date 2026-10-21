"""Read-only diagnostics of frozen OOF results. No model imports, fits or inference."""
from pathlib import Path
import csv,json,hashlib,math,statistics,socket
from collections import Counter,defaultdict
from datetime import datetime,timezone
OUT=Path(__file__).resolve().parent
ROOT=OUT.parents[3]
V2=OUT.parent.parent/'rag_e6_v2';V3=OUT.parent
def sha(p):
    h=hashlib.sha256()
    with Path(p).open('rb') as f:
        for b in iter(lambda:f.read(1<<20),b''):h.update(b)
    return h.hexdigest()
def read(p):return json.loads(Path(p).read_text(encoding='utf-8'))
def write(name,data):
    with (OUT/name).open('x',encoding='utf-8') as f:json.dump(data,f,ensure_ascii=False,indent=2,allow_nan=False)
def csvrows(p):
    with Path(p).open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))
def index(rows):
    d={r['canonical_id']:r for r in rows};assert len(d)==len(rows)==561;return d
def blocked(*a,**k):raise RuntimeError('Network forbidden for saved-artifact analysis')
socket.socket.connect=blocked;socket.create_connection=blocked;socket.getaddrinfo=blocked

def main():
    protected=dict(read(V3/'config/input_manifest.json')['protected_sha256'])
    for folder in [V2,V3]:
        m=read(folder/'config/completion_manifest.json')
        for p,h in m['files'].items():
            key=(folder/p).relative_to(ROOT).as_posix()
            if key in protected:assert protected[key]==h
            protected[key]=h
        p=folder/'config/completion_manifest.json';protected[p.relative_to(ROOT).as_posix()]=sha(p)
    for p,h in protected.items():assert sha(ROOT/p)==h,p
    texts=index(csvrows(ROOT/'codex/canonical_human_development_manifest.csv'))
    folds=index(csvrows(ROOT/'codex/canonical_fold_assignments.csv'))
    f2=csvrows(V2/'features/e6_v2_34_features.csv');f3=csvrows(V3/'features/e6_v3_36_features.csv')
    ids=[r['canonical_id'] for r in f3];assert ids==[r['canonical_id'] for r in f2]
    cols2=read(V2/'config/run_config.json')['features'];cols3=read(V3/'config/run_config.json')['features']
    assert cols3[:34]==cols2 and len(cols3)==36
    old=index(f2);new=index(f3)
    p2=index(csvrows(V2/'evaluation/e6_v2_oof_predictions.csv'));p3=index(csvrows(V3/'evaluation/e6_v3_oof_predictions.csv'))
    paired=index(csvrows(V3/'evaluation/paired_row_diagnostics.csv'))
    mapping=index(read(V2/'inputs/definition_reference_mapping.json'))
    all_pairs=read(V2/'inputs/nli_pairs_label_free.json');pairs={p['pair_id']:p for p in all_pairs}
    hhem={r['pair_id']:r for r in csvrows(V3/'features/hhem_pair_scores.csv')}
    for d in [texts,folds,old,new,p2,p3,paired,mapping]:assert set(d)==set(ids)
    rows=[]
    for cid in ids:
        t=texts[cid];m=mapping[cid];a=old[cid];z=new[cid];q=paired[cid]
        assert all(float(a[k])==float(z[k]) for k in cols2)
        assert int(folds[cid]['fold_id'])==int(p2[cid]['fold_id'])==int(p3[cid]['fold_id'])==int(q['fold_id'])
        y=int(t['label_bin']);human=float(t['p_hallucination'])
        assert y==int(q['label_bin']) and human==float(q['p_hallucination']) and t['task']==q['task']==m['task']
        v2=float(p2[cid]['prediction']);v3=float(p3[cid]['prediction'])
        assert v2==float(q['E6-v2']) and v3==float(q['E6-v3'])
        assert all(math.isfinite(v) and 0<=v<=1 for v in [v2,v3,human])
        b2=int(v2>=.5);b3=int(v3>=.5);c2=b2==y;c3=b3==y
        group='both_correct' if c2 and c3 else 'both_wrong' if not c2 and not c3 else 'v3_corrected' if c3 else 'v3_new_error'
        ev=int(z['rag_evidence_available']);assert ev==m['evidence_available']
        ref=t['src'] if t['task']=='PG' else t['tgt']
        assert pairs[cid+':A']['premise']==ref and pairs[cid+':A']['hypothesis']==t['hyp']
        if ev:
            assert pairs[cid+':C']['premise']==m['definition'] and pairs[cid+':C']['hypothesis']==t['hyp']
            assert float(hhem[cid+':C']['consistency'])==float(z['hhem_definition_hyp_consistency'])
        else:assert m['definition'] is None and cid+':C' not in pairs and float(z['hhem_definition_hyp_consistency'])==0
        assert float(hhem[cid+':A']['consistency'])==float(z['hhem_ref_hyp_consistency'])
        votes=json.loads(t['labels']) if t['labels'] else []
        assert all(v in ['Hallucination','Not Hallucination'] for v in votes)
        n=len(votes);positive=votes.count('Hallucination')
        if n:assert abs(positive/n-human)<1e-12
        missing=[k for k in ['src','tgt','hyp'] if not t[k].strip()]
        if not ev:missing.append('selected_external_definition')
        row={'canonical_id':cid,'task':t['task'],'fold':int(q['fold_id']),
             'src':t['src'],'tgt':t['tgt'],'hyp':t['hyp'],'selected_external_definition':m['definition'],
             'selected_evidence_id':m['selected_evidence_id'],'reference_field':m['reference_field'],
             'evidence_available':ev,'p_hallucination':t['p_hallucination'],'frozen_binary_label':y,
             'human_votes_json':t['labels'],'annotator_count':n,'hallucination_vote_count':positive,
             'annotator_disagreement':int(0<positive<n),'v2_oof':p2[cid]['prediction'],'v3_oof':p3[cid]['prediction'],
             'v2_binary':b2,'v3_binary':b3,'correctness_group':group,
             'v2_distance_to_0_5':abs(v2-.5),'v3_distance_to_0_5':abs(v3-.5),'v3_minus_v2_prediction':v3-v2,
             'missing_fields':';'.join(missing),'tgt_is_period_placeholder':int(t['tgt'].strip()=='.'),
             **{k:z[k] for k in cols3},'hhem_ref_hyp_raw_logit':hhem[cid+':A']['logit'],
             'hhem_definition_hyp_raw_logit':hhem[cid+':C']['logit'] if ev else None}
        rows.append(row)
    counts=Counter(r['correctness_group'] for r in rows)
    assert counts=={'both_correct':464,'both_wrong':78,'v3_corrected':10,'v3_new_error':9}
    assert sum(r['v2_binary']==r['frozen_binary_label'] for r in rows)==473
    assert sum(r['v3_binary']==r['frozen_binary_label'] for r in rows)==474
    def stats(rs):
        n=len(rs);c=Counter(r['correctness_group'] for r in rs)
        e2=sum(r['v2_binary']!=r['frozen_binary_label'] for r in rs);e3=sum(r['v3_binary']!=r['frozen_binary_label'] for r in rs)
        return {'n':n,'v2_errors':e2,'v3_errors':e3,'v2_error_rate':e2/n,'v3_error_rate':e3/n,
                **{g:c[g] for g in ['both_correct','both_wrong','v3_corrected','v3_new_error']}}
    def groups(keys):
        grouped=defaultdict(list)
        for r in rows:grouped[' / '.join(str(r[k]) for k in keys)].append(r)
        return {k:stats(v) for k,v in sorted(grouped.items())}
    quant={'overall':stats(rows),'by_task':groups(['task']),'by_evidence':groups(['evidence_available']),
           'by_task_evidence':groups(['task','evidence_available']),'by_human_probability':groups(['p_hallucination']),
           'by_label':groups(['frozen_binary_label']),'by_votes':groups(['annotator_count']),
           'by_disagreement':groups(['annotator_disagreement']),'by_fold':groups(['fold'])}
    margins={}
    for version in ['v2','v3']:
        margin=version+'_distance_to_0_5';summ={}
        for name,rs in [('all',rows),('errors',[r for r in rows if r[version+'_binary']!=r['frozen_binary_label']])]+[(g,[r for r in rows if r['correctness_group']==g]) for g in counts]:
            vals=[r[margin] for r in rs]
            summ[name]={'n':len(vals),'min':min(vals),'median':statistics.median(vals),'max':max(vals),
                        'distance_le_0_05':sum(v<=.05 for v in vals),'distance_le_0_10':sum(v<=.10 for v in vals)}
        for label,low,high in [('0_to_0.05',0,.05),('0.05_to_0.10',.05,.1),('0.10_to_0.20',.1,.2),('above_0.20',.2,1)]:
            rs=[r for r in rows if (r[margin]>=low if low==0 else r[margin]>low) and r[margin]<=high]
            summ[label]=stats(rs) if rs else {'n':0}
        margins[version]=summ
    quant['margins']=margins
    quant['missing']={k:sum(r[k] is None or str(r[k]).strip()=='' for r in rows) for k in ['src','tgt','hyp','selected_external_definition','human_votes_json']}
    quant['period_placeholder_ids']=[r['canonical_id'] for r in rows if r['tgt_is_period_placeholder']]
    quant['definitions_equal_reference']=sum(r['evidence_available'] and r['selected_external_definition']==(r['src'] if r['task']=='PG' else r['tgt']) for r in rows)
    quant['common_errors_by_direction']={str(y):sum(r['correctness_group']=='both_wrong' and r['frozen_binary_label']==y for r in rows) for y in [0,1]}
    write('diagnostics_intermediate.json',rows);write('quantitative_summary.json',quant)
    write('input_verification.json',{'utc':datetime.now(timezone.utc).isoformat(),'status':'PASS','protected_sha256':protected,
          'counts':dict(counts),'rows':561,'labels_votes_alignment':'PASS','training_fits':0,'inference_pairs':0,'network_calls':0})
    selected=[r for r in rows if r['correctness_group']!='both_correct']
    with (OUT/'review_cases.txt').open('x',encoding='utf-8') as f:
        for i,r in enumerate(selected,1):
            f.write(f"\nCASE {i} | {r['canonical_id']} | {r['task']} | {r['correctness_group']} | human={r['p_hallucination']} label={r['frozen_binary_label']} | v2={float(r['v2_oof']):.6f} v3={float(r['v3_oof']):.6f}\n")
            for k in ['src','tgt','hyp','selected_external_definition']:f.write(f'{k}: {r[k]}\n')
            f.write('NLI2 ref E/N/C: '+','.join(f"{float(r['nli2_ref_hyp_'+k]):.3f}" for k in ['entailment','neutral','contradiction'])+'; HHEM ref/def: '+','.join(f"{float(r[k]):.3f}" for k in ['hhem_ref_hyp_consistency','hhem_definition_hyp_consistency'])+'\n')
    print(json.dumps(quant,ensure_ascii=False,indent=2))

if __name__=='__main__':main()
