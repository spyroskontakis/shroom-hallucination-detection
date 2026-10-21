"""Validate final CSV cell values, quantitative denominators and preserved artifacts."""
from pathlib import Path
import csv,json,hashlib,collections,math
from datetime import datetime,timezone
OUT=Path(__file__).resolve().parent;ROOT=OUT.parents[3]
def read(n):return json.loads((OUT/n).read_text(encoding='utf-8'))
def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(1<<20),b''):h.update(b)
    return h.hexdigest()
def main():
    data=read('diagnostic_table.json');columns=data['columns'];expected=data['rows']
    with (OUT/'E6_DIAGNOSTIC_TABLE.csv').open(encoding='utf-8',newline='') as f:
        reader=csv.DictReader(f);assert reader.fieldnames==columns;rows=list(reader)
    assert len(rows)==len(expected)==561 and len(columns)==67
    texts={'canonical_id','task','src','tgt','hyp','selected_external_definition','selected_evidence_id','reference_field',
           'human_votes_json','correctness_group','missing_fields','qualitative_tags','qualitative_note'}
    for actual,want in zip(rows,expected):
        for k,v in want.items():
            if v is None:assert actual[k]=='',(actual['canonical_id'],k)
            elif k in texts:assert actual[k]==v,(actual['canonical_id'],k)
            else:assert float(actual[k])==float(v),(actual['canonical_id'],k)
        for version in ['v2','v3']:
            p=float(actual[version+'_oof']);assert int(actual[version+'_binary'])==int(p>=.5)
            assert float(actual[version+'_distance_to_0_5'])==abs(p-.5)
    quant=read('quantitative_summary.json')
    def check(rs,s):
        assert len(rs)==s['n']
        for v in ['v2','v3']:
            n=sum(r[v+'_binary']!=r['frozen_binary_label'] for r in rs)
            assert n==s[v+'_errors'] and n/len(rs)==s[v+'_error_rate']
        counts=collections.Counter(r['correctness_group'] for r in rs)
        for g in ['both_correct','both_wrong','v3_corrected','v3_new_error']:assert counts[g]==s[g]
    check(rows,quant['overall'])
    for field,section in [('task','by_task'),('evidence_available','by_evidence'),('p_hallucination','by_human_probability'),
                           ('fold','by_fold'),('annotator_disagreement','by_disagreement')]:
        for value,s in quant[section].items():
            subset=[r for r in rows if (r[field]==value if field=='task' else float(r[field])==float(value))]
            check(subset,s)
        assert sum(s['n'] for s in quant[section].values())==561
    for key,s in quant['by_task_evidence'].items():
        task,ev=key.split(' / ');check([r for r in rows if r['task']==task and r['evidence_available']==ev],s)
    assert sum(r['selected_external_definition']=='' for r in rows)==368
    assert sum(r['qualitative_reviewed']=='1' for r in rows)==97
    ids={r['canonical_id'] for r in rows};review=read('qualitative_review_by_id.json')
    assert set(review)=={r['canonical_id'] for r in rows if r['correctness_group']!='both_correct'}
    report=(OUT/'E6_ERROR_ANALYSIS.md').read_text(encoding='utf-8')
    for cid in review:assert cid in report
    # Check near-duplicate observation from saved columns only.
    byid={r['canonical_id']:r for r in rows}
    x=byid['HDEV_0150_3f30690a6d38'];z=byid['HDEV_0498_901cecdbe33b']
    for k in columns:
        if k.startswith('nli2_'):assert float(x[k])==float(z[k])
        if k.startswith('hhem_'):
            tolerance=1.2e-7 if k.endswith('raw_logit') else 1.5e-8
            assert abs(float(x[k])-float(z[k]))<=tolerance
    protected=read('input_verification.json')['protected_sha256']
    for p,h in protected.items():assert sha(ROOT/p)==h,p
    assert not any(k in __import__('sys').modules for k in ['torch','transformers','sklearn'])
    result={'status':'PASS','completed_utc':datetime.now(timezone.utc).isoformat(),'csv_rows':561,'csv_columns':67,
            'all_csv_cells_verified':True,'qualitative_reviewed':97,'common_errors_reviewed':78,'changes_reviewed':19,
            'all_report_case_ids_validated':True,'quantitative_denominators_verified':True,'previous_files_unchanged':len(protected),
            'new_training_fits':0,'new_inference_pairs':0,'retrieval_or_network_calls':0,
            'analysis_runtime':'bundled Python stdlib for diagnostics; Artifact Tool for CSV, no model runtime',
            'files':{p.name:sha(p) for p in OUT.iterdir() if p.is_file() and p.name!='analysis_completion_manifest.json'}}
    with (OUT/'analysis_completion_manifest.json').open('x',encoding='utf-8') as f:json.dump(result,f,indent=2)
    print({k:v for k,v in result.items() if k!='files'})

if __name__=='__main__':main()
