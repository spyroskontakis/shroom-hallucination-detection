"""Fixed E6-v2 paths, integrity and offline execution helpers."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib, json, os, sys, socket, importlib.metadata

OUT=Path(__file__).resolve().parents[1]
ROOT=OUT.parents[2]
V1=ROOT/'RAG/results/rag_e6_v1'
E7=ROOT/'RAG/results/rag_e7_agentic_v1'
E8=ROOT/'RAG/results/rag_e8_rf_tuning_v1'
CANONICAL=ROOT/'codex/canonical_human_development_manifest.csv'
MIXED=ROOT/'codex/canonical_feature_outputs/canonical_human_14_features.csv'
FOLDS=ROOT/'codex/canonical_fold_assignments.csv'
MODEL_ID='MoritzLaurer/DeBERTa-v3-large-mnli-fever-anli-ling-wanli'
REVISION='b3546ea6b0346eb6f8d5d68b13c7dc6d0376b3d7'
LABELS=['entailment','neutral','contradiction']
PREFIXES=['nli2_ref_hyp_','nli2_hyp_ref_','nli2_definition_hyp_']
NEW=[p+label for p in PREFIXES for label in LABELS]


def now(): return datetime.now(timezone.utc).isoformat()


def sha(p):
    h=hashlib.sha256()
    with Path(p).open('rb') as f:
        for b in iter(lambda:f.read(1<<20),b''):h.update(b)
    return h.hexdigest()


def read_json(p): return json.loads(Path(p).read_text(encoding='utf-8'))


def write_json(p,data):
    p=Path(p);p.resolve().relative_to(OUT)
    p.parent.mkdir(parents=True,exist_ok=True)
    with p.open('x',encoding='utf-8',newline='\n') as f:
        json.dump(data,f,indent=2,sort_keys=True,ensure_ascii=False,allow_nan=False);f.write('\n')


def csv_write(p,df):
    p=Path(p);p.resolve().relative_to(OUT);p.parent.mkdir(parents=True,exist_ok=True)
    with p.open('x',encoding='utf-8',newline='') as f:df.to_csv(f,index=False,lineterminator='\n')


def offline(phase):
    for key in ['HF_HUB_OFFLINE','TRANSFORMERS_OFFLINE','HF_DATASETS_OFFLINE','HF_HUB_DISABLE_TELEMETRY','PYTHONDONTWRITEBYTECODE']:
        os.environ[key]='1'
    os.environ['JOBLIB_TEMP_FOLDER']=str(OUT/'runtime_tmp')
    log=OUT/f'config/network_attempts_{phase}.jsonl'
    with log.open('x',encoding='utf-8'):pass
    def blocked(*args,**kwargs):
        with log.open('a',encoding='utf-8') as f:f.write(json.dumps({'utc':now(),'status':'BLOCKED'})+'\n')
        raise RuntimeError('E6-v2 inference/evaluation network disabled')
    socket.socket.connect=blocked;socket.socket.connect_ex=blocked
    socket.create_connection=blocked;socket.getaddrinfo=blocked
    return log


def versions():
    keys=['torch','transformers','numpy','pandas','scipy','scikit-learn','tokenizers','sentencepiece','safetensors']
    v={k:importlib.metadata.version(k) for k in keys}
    accepted=read_json(V1/'config/run_config.json')
    for k in ['torch','transformers','numpy','pandas','scipy','scikit-learn']:
        assert v[k]==accepted['packages'][k],(k,v[k],accepted['packages'][k])
    assert sys.version_info[:3]==(3,11,9)
    return {'python':sys.version,'executable':sys.executable,'packages':v}


def verify_inputs():
    manifest=read_json(OUT/'config/input_manifest.json')
    for path,want in manifest['protected_sha256'].items():assert sha(ROOT/path)==want,path
    return manifest


def verify_models():
    acquisition=read_json(OUT/'provenance/acquisition.json')
    assert acquisition['revision']==REVISION and acquisition['model_id']==MODEL_ID
    for meta in acquisition['files'].values():assert sha(OUT/meta['path'])==meta['sha256']
    return acquisition


def verify_freeze():
    verify_inputs()
    lock=read_json(OUT/'config/run_config.json')
    for path,want in lock['frozen_files'].items():assert sha(OUT/path)==want,path
    return lock
