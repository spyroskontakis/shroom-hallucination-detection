"""Amended E6-v4 runtime and integrity gates. No implicit network fallback."""
import os,sys,json,hashlib,socket,importlib.metadata,datetime
from pathlib import Path
HERE=Path(__file__).resolve().parent;V4=HERE.parent;ROOT=V4.parents[2];V3=ROOT/'RAG/results/rag_e6_v3'
sys.path.insert(0,str(V4/'packages'));sys.path.insert(0,str(V4/'scripts'))
MODEL='microsoft/deberta-large-mnli';REV='7296194b9009373def4f7c5dad292651e4b5cf4e'
PINS={'transformers':'4.30.2','tokenizers':'0.13.3','huggingface-hub':'0.25.2','bert-score':'0.3.13'}
ENV={'HF_HUB_OFFLINE':'1','TRANSFORMERS_OFFLINE':'1','HF_DATASETS_OFFLINE':'1','HF_HUB_DISABLE_TELEMETRY':'1',
 'PYTHONDONTWRITEBYTECODE':'1','TOKENIZERS_PARALLELISM':'false','MPLBACKEND':'Agg',
 'MPLCONFIGDIR':str(HERE/'tmp/matplotlib'),'HF_MODULES_CACHE':str(HERE/'tmp/hf_modules'),
 'JOBLIB_TEMP_FOLDER':str(HERE/'tmp/joblib'),'TEMP':str(HERE/'tmp'),'TMP':str(HERE/'tmp')}
def now():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def read(p):return json.loads(Path(p).read_text(encoding='utf-8'))
def write(p,data):
 p=Path(p);p.resolve().relative_to(V4);p.parent.mkdir(parents=True,exist_ok=True)
 with p.open('x',encoding='utf-8') as f:json.dump(data,f,indent=2,ensure_ascii=False,allow_nan=False)
def csvwrite(p,frame):
 p=Path(p);p.resolve().relative_to(V4);p.parent.mkdir(parents=True,exist_ok=True)
 with p.open('x',encoding='utf-8',newline='') as f:frame.to_csv(f,index=False,lineterminator='\n')
def offline(phase):
 os.environ.update(ENV);(HERE/'tmp').mkdir(exist_ok=True)
 log=HERE/f'network_{phase}.jsonl';log.touch(exist_ok=False)
 def block(*a,**k):
  with log.open('a',encoding='utf-8') as f:f.write(json.dumps({'utc':now(),'attempt':'blocked'})+'\n')
  raise RuntimeError('Network forbidden in E6-v4 execution')
 socket.socket.connect=block;socket.socket.connect_ex=block;socket.create_connection=block;socket.getaddrinfo=block
 return log
def runtime(kind):
 expected=read(V3/'config/run_config.json')['runtime']['packages'].copy()
 if kind=='encoding':expected.update(PINS)
 actual={n:importlib.metadata.version(n) for n in expected}
 assert actual==expected,(actual,expected)
 assert sys.version_info[:3]==(3,11,9)
 if kind=='encoding':
  import transformers,tokenizers,huggingface_hub
  for mod in [transformers,tokenizers,huggingface_hub]:assert Path(mod.__file__).resolve().is_relative_to(V4/'compatibility_analysis/env')
 return {'python':sys.version,'executable':sys.executable,'packages':actual,'environment':ENV}
def protected(allow_updated_report=False):
 m=read(V4/'config/input_manifest.json')['protected_sha256']
 for p,h in m.items():assert sha(ROOT/p)==h,p
 old=read(V4/'config/blocked_state_manifest.json')['files']
 for p,h in old.items():
  target=HERE/'E6_V4_RESULTS_PHASE1_ARCHIVE.md' if p=='E6_V4_RESULTS.md' and allow_updated_report else V4/p
  assert sha(target)==h,p
 diagnosis=read(V4/'compatibility_analysis/diagnosis_manifest.json')['files']
 for p,h in diagnosis.items():assert sha(V4/'compatibility_analysis'/p)==h,p
 return {'protected_files':len(m),'old_v4_files':len(old),'diagnosis_files':len(diagnosis)}
def assets():
 m=read(V4/'provenance/compatibility.json')
 for asset in m['model_files'].values():assert sha(asset['path'])==asset['sha256']
 ref=Path(m['cache_ref_path']);assert ref.read_text().strip()==REV and sha(ref)==m['cache_ref_sha256']
 return m
def verify_freeze():
 m=read(HERE/'run_config.json')
 for p,h in m['frozen_files'].items():assert sha(V4/p)==h,p
 assert m['execution_authorized'] and m['real_features_at_freeze']==0 and m['fits_at_freeze']==0
 return m
def scorer():
 import torch,bert_score
 from bert_score.utils import model2layers
 torch.manual_seed(42);torch.set_num_threads(4);torch.set_num_interop_threads(4)
 s=bert_score.BERTScorer(model_type=MODEL,num_layers=None,batch_size=2,nthreads=4,all_layers=False,
    idf=False,idf_sents=None,device='cpu',lang=None,rescale_with_baseline=False,use_fast_tokenizer=False)
 assert s.num_layers==model2layers[MODEL]==18 and len(s._model.encoder.layer)==18
 assert s._tokenizer.model_max_length==512 and s._model.config.max_position_embeddings==512
 assert s._model.config._commit_hash==REV and not s._model.training
 assert {p.dtype for p in s._model.parameters()}=={torch.float32}
 return s
