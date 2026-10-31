"""Offline filesystem/archive/Git evidence search; no inference or network."""
import collections, csv, hashlib, importlib.util, io, json, os, re, subprocess, sys, tarfile, unicodedata, zipfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(HERE.parent))
import audit_data as audit

def sha(data): return hashlib.sha256(data).hexdigest()
def norm(s): return ' '.join(unicodedata.normalize('NFKC', str(s)).split()).casefold()
def save(name, value): (HERE/name).write_text(json.dumps(value, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
def git(*args): return subprocess.check_output(['git',*args],cwd=ROOT)

test, _ = audit.sanitized_test(ROOT/'Labeled test/SHROOM_test-labeled/test.model-agnostic.json')
spec=importlib.util.spec_from_file_location('lexicon',ROOT/'RAG/scripts/module4_build_external_lexicon.py')
lex=importlib.util.module_from_spec(spec);sys.modules[spec.name]=lex;spec.loader.exec_module(lex)
canonical_path=ROOT/'codex/canonical_human_development_manifest.csv'
canonical=list(csv.DictReader(canonical_path.open(encoding='utf-8-sig')))
test_pairs=collections.defaultdict(list)
for i,t in enumerate(test):test_pairs[audit.key(t,('task','src','tgt'))].append((i,t))
removed=[];kept=[]
for i,r in enumerate(canonical):
    matches=test_pairs.get(audit.key(r,('task','src','tgt')),[])
    if matches:
        assert r['task']=='MT'
        assert all(audit.key(r)!=audit.key(t) and audit.norm(r['hyp'])!=audit.norm(t['hyp']) for _,t in matches)
        removed.append({'canonical_id':r['canonical_id'],'canonical_index':i,'original_source_index':int(r['original_row_index']),'source':r['source_split'],'task':r['task'],'test_ids':[t['id'] for _,t in matches],'test_indices':[j for j,_ in matches],'hypotheses_differ':True,'exact_example_shared':False})
    else:kept.append(r)
assert len(removed)==14 and len(kept)==547
assert not any(audit.key(r) in {audit.key(t) for t in test} for r in canonical)
save('E10_OFFICIAL_TEST_STRICT_TRAIN_MANIFEST.json',{'status':'PROPOSED_NOT_FITTED','rows':547,'parent_rows':561,'parent_manifest':str(canonical_path),'parent_sha256':sha(canonical_path.read_bytes()),'exclusion_policy':'Remove every canonical row whose normalized (task,src,tgt) occurs in official test; independent of labels and predictions.','source_counts':dict(collections.Counter(r['source_split'] for r in kept)),'task_counts':dict(collections.Counter(r['task'] for r in kept)),'excluded':removed,'retained_rows':kept,'model_fits':0,'test_gold_decoded':False})
required=collections.defaultdict(list)
for t in test:
    if t['task']=='DM':required[lex.term_key(lex.extract_dm_term(t['src']))].append(t['id'])
manifest_path=ROOT/'RAG/results/rag_module4/continuation_v1/schannel_run_v1/module4_dev_term_manifest.csv'
known={r['term_key']:r for r in csv.DictReader(manifest_path.open(encoding='utf-8-sig'))}
missing=set(required)-set(known)
assert len(missing)==557
save('REQUIRED_TERMS.json',{'all_DM_terms':dict(required),'missing_terms':sorted(missing),'already_acquired':{k:v for k,v in known.items() if k in required}})

EXT={'.json','.jsonl','.ndjson','.csv','.tsv','.txt','.md','.html','.htm','.xml','.ipynb','.py','.log','.yaml','.yml','.toml','.rst','.js'}
SKIPDIR={'.git','site-packages','node_modules','__pycache__','.venv','venv'}
records=[];candidates=[];inventory=[];errors=[];counts=collections.Counter();seen={}

def walk(obj):
    if isinstance(obj,dict):
        yield obj
        for v in obj.values():yield from walk(v)
    elif isinstance(obj,list):
        for v in obj:yield from walk(v)

def scan(data,path,stamp=None):
    counts['text_objects_examined']+=1
    lower=data.lower()
    if not any(x in lower for x in [b'wiktionary',b'candidate_definition',b'"term_key"',b'definition',b'mediawiki']):return
    digest=sha(data)
    records.append({'path':path,'sha256':digest,'bytes':len(data),'timestamp':stamp})
    if digest in seen:
        for hit in seen[digest]:candidates.append({**hit,'source_path':path,'original_timestamp_if_available':stamp})
        return
    hits=[];seen[digest]=hits
    text=data.decode('utf-8-sig',errors='replace')
    objects=[]
    try:objects=[json.loads(text)]
    except (ValueError,RecursionError):
        if path.lower().endswith(('.jsonl','.ndjson')):
            for line in text.splitlines():
                try:objects.append(json.loads(line))
                except ValueError:pass
    for obj in objects:
        for row in walk(obj):
            term=row.get('term_key',row.get('candidate_term',row.get('surface_term',row.get('term',row.get('title')))))
            definition=row.get('candidate_definition',row.get('definition'))
            if term and norm(term) in missing and isinstance(definition,str) and definition.strip():
                hits.append({'term':norm(term),'hash':digest,'kind':'candidate_definition','source_path':path,'original_timestamp_if_available':stamp,'source':row.get('source'),'provenance':row.get('provenance'),'evidence_id':row.get('evidence_id'),'definition_sha256':sha(definition.encode())})
            parsed=row.get('parse')
            if isinstance(parsed,dict) and norm(parsed.get('title','')) in missing and isinstance(parsed.get('text'),str):
                hits.append({'term':norm(parsed['title']),'hash':digest,'kind':'revision_html','revision_id':parsed.get('revid'),'source_path':path,'original_timestamp_if_available':stamp})
    # CSV mappings, including term/title/source provenance; candidate definitions only.
    if path.lower().endswith('.csv'):
        try:
            for row in csv.DictReader(io.StringIO(text)):
                term=row.get('term_key',row.get('candidate_term',row.get('term','')))
                if norm(term) in missing and any(row.get(k) for k in ['candidate_definition','definition','raw_parse_reference']):
                    hits.append({'term':norm(term),'hash':digest,'kind':'csv_mapping_or_pointer','source_path':path,'original_timestamp_if_available':row.get('revision_timestamp') or stamp,'source':row.get('source'),'referenced_file':row.get('raw_parse_reference')})
        except (csv.Error,TypeError):pass
    if path.lower().endswith(('.html','.htm')):
        title=re.search(r'<title[^>]*>(.*?)</title>',text,re.I|re.S)
        if title:
            term=norm(re.sub(r'\s*[-–].*Wiktionary.*','',title.group(1),flags=re.I))
            if term in missing:hits.append({'term':term,'hash':digest,'kind':'html_page_candidate','source_path':path,'original_timestamp_if_available':stamp})
    candidates.extend(hits)

def archive(data,path,depth=0):
    if depth>3:errors.append({'path':path,'error':'nested_archive_depth_limit'});return
    counts['archives_examined']+=1
    try:
        if zipfile.is_zipfile(io.BytesIO(data)):
            with zipfile.ZipFile(io.BytesIO(data)) as z:
                for item in z.infolist():
                    if item.is_dir():continue
                    member=path+'!'+item.filename;counts['archive_members_inventoried']+=1
                    if item.file_size>100_000_000:continue
                    suffix=Path(item.filename).suffix.lower()
                    if suffix in EXT:scan(z.read(item),member,str(item.date_time))
                    elif suffix=='.zip':archive(z.read(item),member,depth+1)
        else:
            with tarfile.open(fileobj=io.BytesIO(data),mode='r:*') as z:
                for item in z:
                    if not item.isfile():continue
                    counts['archive_members_inventoried']+=1
                    if item.size<=100_000_000 and Path(item.name).suffix.lower() in EXT:scan(z.extractfile(item).read(),path+'!'+item.name,str(item.mtime))
    except Exception as e:errors.append({'path':path,'error':type(e).__name__+': '+str(e)[:200]})

for directory,dirs,files in os.walk(ROOT):
    dirs[:]=[d for d in dirs if d not in SKIPDIR and (Path(directory)/d).resolve()!=HERE]
    for name in files:
        p=Path(directory)/name;rel=p.relative_to(ROOT).as_posix()
        try:
            stat=p.stat();inventory.append({'path':rel,'size':stat.st_size,'mtime_ns':stat.st_mtime_ns})
            if any(x in name.lower() for x in ['credential','service-account','service_account','.env','token.json']):counts['credential_files_excluded']+=1;continue
            if stat.st_size>100_000_000:counts['large_binary_or_resource_files_not_decoded']+=1;continue
            if p.suffix.lower() in EXT:scan(p.read_bytes(),rel,str(stat.st_mtime))
            elif p.suffix.lower() in {'.zip','.tar','.tgz','.gz'}:archive(p.read_bytes(),rel)
            elif p.suffix.lower() in {'.7z','.rar'}:errors.append({'path':rel,'error':'archive_format_requires_additional_reader'})
        except Exception as e:errors.append({'path':rel,'error':type(e).__name__})
print('Filesystem search complete',dict(counts),flush=True)
refs=git('for-each-ref','--format=%(refname) %(objectname)').decode().splitlines()
objects=git('rev-list','--all','--reflog','--objects').decode(errors='replace').splitlines()
blobs=[]
for line in objects:
    if ' ' not in line:continue
    oid,path=line.split(' ',1)
    if Path(path).suffix.lower() not in EXT|{'.zip','.tar','.gz','.tgz'}:continue
    if any(x in path.lower() for x in ['credential','service-account','service_account','/.env']):continue
    blobs.append((oid,path))
if blobs:
    info=git('cat-file','--batch-check=%(objectname) %(objecttype) %(objectsize)') if False else subprocess.check_output(['git','cat-file','--batch-check=%(objectname) %(objecttype) %(objectsize)'],input=('\n'.join(x[0] for x in blobs)+'\n').encode(),cwd=ROOT).decode().splitlines()
    for (oid,path),meta in zip(blobs,info):
        fields=meta.split()
        if len(fields)!=3 or fields[1]!='blob' or int(fields[2])>100_000_000:continue
        data=git('cat-file','blob',oid);counts['git_blobs_examined']+=1
        if Path(path).suffix.lower() in EXT:scan(data,'git:'+oid+':'+path)
        else:archive(data,'git:'+oid+':'+path)
save('SEARCH_INVENTORY.json',{'scope':str(ROOT),'refs':refs,'reachable_and_reflog_objects':len(objects),'counts':dict(counts),'errors':errors,'excluded_dependency_directories':sorted(SKIPDIR),'file_inventory':inventory,'wiktionary_or_definition_objects':records,'recovery_candidates':candidates})
with (HERE/'WIKTIONARY_RECOVERY_TABLE.csv').open('w',encoding='utf-8-sig',newline='') as f:
    fields=['term','required_by_test_ids','frozen_content_found','source_path','original_timestamp_if_available','hash','status']
    writer=csv.DictWriter(f,fieldnames=fields);writer.writeheader()
    for term in sorted(missing):
        found=[r for r in candidates if r['term']==term]
        writer.writerow({'term':term,'required_by_test_ids':json.dumps(required[term]),'frozen_content_found':'candidate_requires_verification' if found else 'false','source_path':'; '.join(r['source_path'] for r in found),'original_timestamp_if_available':'; '.join(str(r.get('original_timestamp_if_available') or '') for r in found),'hash':'; '.join(r['hash'] for r in found),'status':'REVIEW_CANDIDATE' if found else 'NOT_RECOVERED'})
print(json.dumps({'counts':dict(counts),'wiktionary_objects':len(records),'candidate_terms':len({r['term'] for r in candidates}),'candidates':candidates,'errors':errors},ensure_ascii=False),flush=True)
