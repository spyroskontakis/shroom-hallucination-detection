"""One pinned FactCG extraction; only label-free request rows reach Modal."""
import hashlib,json,sys
from pathlib import Path
import modal
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[3] if len(HERE.parents)>3 else Path('/opt/SHROOM/SHROOM2024')
SOURCE=ROOT/'RAG/results/phase3_e9_claim_verification/factcg_gpu'
REMOTE='/opt/SHROOM/SHROOM2024/RAG/results/phase3_e9_claim_verification/factcg_gpu'
app=modal.App('shroom-e10-retrospective-factcg-v1')
volume=modal.Volume.from_name('shroom-e10-retrospective-v1',create_if_missing=True)
image=(modal.Image.debian_slim(python_version='3.11')
       .pip_install_from_requirements(str(SOURCE/'requirements_gpu.lock.txt'))
       .run_commands('python -m pip check')
       .add_local_file(str(SOURCE/'factcg_backend.py'),REMOTE+'/factcg_backend.py')
       .add_local_file(str(SOURCE/'factcg_common.py'),REMOTE+'/factcg_common.py')
       .add_local_dir(str(SOURCE/'nltk_data'),REMOTE+'/nltk_data')) if modal.is_local() else modal.Image.debian_slim(python_version='3.11')
def digest(value):return hashlib.sha256(json.dumps(value,sort_keys=True,ensure_ascii=False,allow_nan=False).encode()).hexdigest()

@app.function(image=image,gpu='A100-80GB',cpu=4,memory=32768,timeout=14400,volumes={'/results':volume},max_containers=1,retries=0)
def extract(rows,identity,expected_dependencies,source_hashes):
    import importlib.metadata,math,os,time
    started=time.time()
    assert len(rows)==len({r['canonical_id'] for r in rows})==1500
    assert all(set(r)=={'canonical_id','task','reference_text','whole_hypothesis'} for r in rows)
    assert digest(rows)==identity
    sys.path.insert(0,REMOTE)
    from factcg_backend import load,score
    from factcg_common import MODEL,REVISION,SETTINGS
    for name,h in source_hashes.items():assert hashlib.sha256((Path(REMOTE)/name).read_bytes()).hexdigest()==h
    versions={n:importlib.metadata.version(n).split('+')[0] for n in expected_dependencies}
    assert versions==expected_dependencies,(versions,expected_dependencies)
    import torch,nltk
    assert torch.cuda.is_available() and torch.version.cuda=='12.1'
    torch.manual_seed(42);torch.backends.cuda.matmul.allow_tf32=False
    nltk.data.path.insert(0,REMOTE+'/nltk_data')
    out=Path('/results')/identity
    out.mkdir(exist_ok=False) # Duplicate launch is rejected rather than repeated.
    (out/'STARTED.json').write_text(json.dumps({'input_identity':identity,'rows':1500,'model':MODEL,'revision':REVISION,'settings':SETTINGS,'versions':versions,'gpu':torch.cuda.get_device_name(0),'started_unix':started}),encoding='utf-8');volume.commit()
    tokenizer,model=load(Path('/tmp/factcg_model_cache'))
    scores=[]
    with (out/'scores.partial.jsonl').open('x',encoding='utf-8') as handle:
        for i,row in enumerate(rows):
            probability,audit=score(tokenizer,model,row['reference_text'],row['whole_hypothesis'])
            assert math.isfinite(probability) and 0<=probability<=1
            item={'id':row['canonical_id'],'factcg_support_probability':probability,'input_row_sha256':digest(row),'audit':audit}
            scores.append(item);handle.write(json.dumps(item,ensure_ascii=False)+'\n');handle.flush()
            if (i+1)%25==0:
                os.fsync(handle.fileno());volume.commit();print(f'FactCG {i+1}/1500',flush=True)
    (out/'scores.partial.jsonl').rename(out/'scores.jsonl')
    report={'status':'PASS','rows':1500,'input_identity':identity,'model':MODEL,'revision':REVISION,'settings':SETTINGS,'dependencies':versions,'gpu':torch.cuda.get_device_name(0),'seconds':time.time()-started,'scores_sha256':hashlib.sha256((out/'scores.jsonl').read_bytes()).hexdigest()}
    (out/'REPORT.json').write_text(json.dumps(report,indent=2),encoding='utf-8');volume.commit()
    return {'scores':scores,'report':report}

@app.local_entrypoint()
def main():
    inputs=json.loads((HERE/'test_inputs_label_free.json').read_text(encoding='utf-8'))
    assert all(set(r)=={'id','task','src','tgt','hyp'} for r in inputs)
    rows=[{'canonical_id':str(r['id']),'task':r['task'],'reference_text':r['src'] if r['task']=='PG' else r['tgt'],'whole_hypothesis':r['hyp']} for r in inputs]
    m=json.loads((SOURCE/'GPU_RUN_MANIFEST.json').read_text(encoding='utf-8'))
    identity=digest(rows)
    launch=HERE/'FACTCG_LAUNCH.json'
    with launch.open('x',encoding='utf-8') as f:json.dump({'identity':identity,'volume':'shroom-e10-retrospective-v1','remote_output':'/results/'+identity,'rows':1500},f,indent=2)
    result=extract.remote(rows,identity,m['dependency_versions'],{name:hashlib.sha256((SOURCE/name).read_bytes()).hexdigest() for name in ['factcg_backend.py','factcg_common.py']})
    with (HERE/'factcg_return.json').open('x',encoding='utf-8') as f:json.dump(result,f,ensure_ascii=False,indent=2,allow_nan=False)
    print('FactCG 1500-row return saved and verified',flush=True)
