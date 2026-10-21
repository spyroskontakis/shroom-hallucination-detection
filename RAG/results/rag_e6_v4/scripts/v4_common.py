"""Fixed paths, immutable input verification and offline runtime for E6-v4."""
from pathlib import Path
from datetime import datetime,timezone
import sys,os,json,hashlib,socket,uuid,importlib.metadata
OUT=Path(__file__).resolve().parents[1];ROOT=OUT.parents[2]
V1=ROOT/'RAG/results/rag_e6_v1';V2=ROOT/'RAG/results/rag_e6_v2';V3=ROOT/'RAG/results/rag_e6_v3'
ANALYSIS=V3/'error_analysis'
CANONICAL=ROOT/'codex/canonical_human_development_manifest.csv'
MIXED=ROOT/'codex/canonical_feature_outputs/canonical_human_14_features.csv'
FOLDS=ROOT/'codex/canonical_fold_assignments.csv'
MODEL_ID='microsoft/deberta-large-mnli';REVISION='7296194b9009373def4f7c5dad292651e4b5cf4e'
NEW=['bertscore_ref_hyp_precision','bertscore_ref_hyp_recall','bertscore_ref_hyp_f1',
     'structure_length_ratio','structure_number_presence_mismatch','structure_number_set_mismatch','structure_negation_mismatch']
sys.path.insert(0,str(OUT/'packages'))
def now():return datetime.now(timezone.utc).isoformat()
def sha(p):
    h=hashlib.sha256()
    with Path(p).open('rb') as f:
        for b in iter(lambda:f.read(1<<20),b''):h.update(b)
    return h.hexdigest()
def read_json(p):return json.loads(Path(p).read_text(encoding='utf-8'))
def write_json(p,data):
    p=Path(p);p.resolve().relative_to(OUT);p.parent.mkdir(parents=True,exist_ok=True)
    with p.open('x',encoding='utf-8',newline='\n') as f:json.dump(data,f,indent=2,ensure_ascii=False,sort_keys=True,allow_nan=False)
def csv_write(p,df):
    p=Path(p);p.resolve().relative_to(OUT);p.parent.mkdir(parents=True,exist_ok=True)
    with p.open('x',encoding='utf-8',newline='') as f:df.to_csv(f,index=False,lineterminator='\n')
def offline(phase):
    for key in ['HF_HUB_OFFLINE','TRANSFORMERS_OFFLINE','HF_DATASETS_OFFLINE','HF_HUB_DISABLE_TELEMETRY','PYTHONDONTWRITEBYTECODE']:os.environ[key]='1'
    os.environ['MPLCONFIGDIR']=str(OUT/'runtime_tmp/matplotlib');os.environ['MPLBACKEND']='Agg'
    os.environ['TOKENIZERS_PARALLELISM']='false';os.environ['JOBLIB_TEMP_FOLDER']=str(OUT/'runtime_tmp')
    log=OUT/f'config/network_attempts_{phase}_{uuid.uuid4().hex}.jsonl';log.touch(exist_ok=False)
    def blocked(*a,**k):
        with log.open('a',encoding='utf-8') as f:f.write('{"blocked":true}\n')
        raise RuntimeError('E6-v4 execution is offline')
    socket.socket.connect=blocked;socket.socket.connect_ex=blocked;socket.create_connection=blocked;socket.getaddrinfo=blocked
    return log
def versions():
    expected=read_json(V3/'config/run_config.json')['runtime']['packages']
    actual={k:importlib.metadata.version(k) for k in expected}
    assert actual==expected and sys.version_info[:3]==(3,11,9)
    assert importlib.metadata.version('bert-score')=='0.3.13'
    return {'python':sys.version,'executable':sys.executable,'packages':{**actual,'bert-score':'0.3.13'}}
def verify_inputs():
    m=read_json(OUT/'config/input_manifest.json')
    for p,h in m['protected_sha256'].items():assert sha(ROOT/p)==h,p
    return m
def verify_models():
    m=read_json(OUT/'provenance/compatibility.json');assert m['status']=='PASS'
    for name,meta in m['model_files'].items():assert sha(meta['path'])==meta['sha256'],name
    p=Path(m['cache_ref_path']);assert p.read_text().strip()==REVISION and sha(p)==m['cache_ref_sha256']
    return m
def verify_freeze():
    verify_inputs();verify_models();m=read_json(OUT/'config/run_config.json')
    for p,h in m['frozen_files'].items():assert sha(OUT/p)==h,p
    return m
