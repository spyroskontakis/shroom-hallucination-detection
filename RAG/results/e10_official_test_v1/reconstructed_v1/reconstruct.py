"""Acquire only missing terms using unchanged frozen acquisition/parser functions."""
import collections,csv,hashlib,json,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[3]
sys.path[:0]=[str(HERE.parent),str(ROOT/'RAG/results/rag_module4/continuation_v1/schannel_run_v1/scripts')]
import audit_data as audit
import module4_schannel_acquire as transport
wiki=transport.frozen_wiki
lex=wiki.frozen
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,obj):p.write_text(json.dumps(obj,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8')
def main():
    frozen=json.loads((HERE.parent/'E10_OFFICIAL_TEST_FEATURE_MANIFEST.json').read_text(encoding='utf-8'))
    for p,h in frozen['source_sha256'].items():assert sha(ROOT/p)==h,p
    rows,_=audit.sanitized_test(ROOT/'Labeled test/SHROOM_test-labeled/test.model-agnostic.json')
    rows=[{k:audit.norm(v) if k in ('src','tgt','hyp') else v for k,v in r.items()} for r in rows]
    assert len(rows)==len({r['id'] for r in rows})==1500
    assert all(set(r)=={'id','task','src','tgt','hyp'} for r in rows)
    save(HERE/'test_inputs_label_free.json',rows)
    query=[{'example_id':str(r['id']),'task':r['task'],'term':lex.extract_dm_term(r['src']) or '', 'src':r['src'],'tgt':r['tgt'],'rag_applicable':int(r['task']=='DM' and bool(lex.extract_dm_term(r['src'])))} for r in rows]
    terms=lex.build_term_rows(query)
    known_root=ROOT/'RAG/results/rag_module4/continuation_v1/schannel_run_v1'
    known={r['term_key']:r for r in csv.DictReader((known_root/'module4_dev_term_manifest.csv').open(encoding='utf-8-sig'))}
    missing=[t for t in terms if t['term_key'] not in known]
    assert len(missing)==557
    raw=HERE/'WIKTIONARY_RECONSTRUCTED_RAW';raw.mkdir(exist_ok=True)
    processed=HERE/'WIKTIONARY_RECONSTRUCTED_PROCESSED';processed.mkdir(exist_ok=True)
    save(HERE/'reconstruction_terms.json',missing)
    print('Retrieving 557 missing terms; two frozen test terms retained.',flush=True)
    failures=wiki.acquire(raw,missing,transport.SchannelFetcher(raw/'network_requests.jsonl',3))
    result=wiki.offline_build(raw,missing,processed/'new_snapshot.jsonl',processed/'term_manifest.csv')
    old_records=[json.loads(l) for l in (known_root/'module4_external_lexical_snapshot.jsonl').read_text(encoding='utf-8').splitlines()]
    new_records=[json.loads(l) for l in (processed/'new_snapshot.jsonl').read_text(encoding='utf-8').splitlines()]
    combined=old_records+new_records
    assert len({r['evidence_id'] for r in combined})==len(combined)
    (processed/'combined_snapshot.jsonl').write_text(''.join(json.dumps(r,ensure_ascii=False,sort_keys=True)+'\n' for r in combined),encoding='utf-8')
    acquired=list(csv.DictReader((processed/'term_manifest.csv').open(encoding='utf-8-sig')))
    events=[json.loads(l) for l in (raw/'network_requests.jsonl').read_text().splitlines()]
    for t in acquired:
        content=[r for r in new_records if r['term_key']==t['term_key']]
        target=processed/(wiki.stem_for(int(t['term_order']),t['term_key'])+'.json')
        save(target,content)
        t['processed_path']=str(target.relative_to(HERE));t['processed_sha256']=sha(target)
        t['requests']=[{k:e.get(k) for k in ['timestamp_utc','url','status','http_status','response_sha256']} for e in events if e['requested_term']==t['term_key']]
        t['resource_origin']='newly_retrieved_2026'
    usable={r['term_key'] for r in new_records};known_usable={r['term_key'] for r in old_records}
    dm=[r for r in query if r['task']=='DM']
    coverage={'reconstructed_terms_with_senses':len(usable),'unavailable_terms':557-len(usable),'confirmed_no_sense_terms':result['status_counts'].get('NO_SENSE_FOUND',0),'technical_failure_terms':result['status_counts'].get('SOURCE_REQUEST_FAILED',0),'DM_with_reconstructed_definitions':sum(lex.term_key(r['term']) in usable for r in dm),'DM_with_frozen_definitions':sum(lex.term_key(r['term']) in known_usable for r in dm),'DM_original_missing_definition_behavior':sum(lex.term_key(r['term']) not in usable|known_usable for r in dm)}
    save(HERE/'E10_RECONSTRUCTION_MANIFEST.json',{'evaluation_type':'reconstructed retrospective evaluation on the official labeled SHROOM test set','coverage':coverage,'terms':acquired,'failures':failures,'frozen_resources':{str(p.relative_to(ROOT)):sha(p) for p in [known_root/'module4_external_lexical_snapshot.jsonl',known_root/'module4_dev_term_manifest.csv']},'source_code':{str(p.relative_to(ROOT)):sha(p) for p in [Path(wiki.__file__),Path(transport.__file__),Path(lex.__file__)]},'test_inputs_sha256':sha(HERE/'test_inputs_label_free.json'),'combined_snapshot_sha256':sha(processed/'combined_snapshot.jsonl'),'procedure':'Unchanged frozen acquire/offline_build/parser/Schannel transport; missing-term population supplied instead of development-only count guard.','deviation':'Missing Wiktionary resources reconstructed in 2026; two existing frozen test terms retained.'})
    (HERE/'E10_RECONSTRUCTION_REPORT.md').write_text('# Wiktionary reconstruction\n\n'+json.dumps(coverage,indent=2)+'\n\nSame frozen Wiktionary acquisition and parser functions; new resources are separated from the existing snapshot. Explicit failed/no-sense terms receive only the original no-candidate zero behavior. No definition was manually corrected. Full per-term timestamps, URLs and raw/processed hashes are in the manifest and request log.\n',encoding='utf-8')
    files=[p for p in HERE.rglob('*') if p.is_file() and ('WIKTIONARY_' in str(p) or p.name.startswith('E10_RECONSTRUCTION_')) and p.suffix!='.txt']
    (HERE/'E10_RECONSTRUCTION_SHA256SUMS.txt').write_text(''.join(sha(p)+'  '+p.relative_to(HERE).as_posix()+'\n' for p in sorted(files)),encoding='utf-8')
    print(json.dumps(coverage),flush=True)
if __name__=='__main__':main()
