"""Official BERTScore in isolated pinned dependencies; synthetic inputs only."""
import sys,os,json,time,traceback,socket,hashlib,importlib.metadata
from pathlib import Path
HERE=Path(__file__).resolve().parent;V4=HERE.parent
sys.path.insert(0,str(V4/'packages'))
for k in ['HF_HUB_OFFLINE','TRANSFORMERS_OFFLINE','HF_DATASETS_OFFLINE','HF_HUB_DISABLE_TELEMETRY','PYTHONDONTWRITEBYTECODE']:os.environ[k]='1'
os.environ['MPLCONFIGDIR']=str(HERE/'tmp/matplotlib');os.environ['MPLBACKEND']='Agg'
os.environ['HF_MODULES_CACHE']=str(HERE/'tmp/hf_modules')
network=[]
def blocked(*a,**k):network.append('blocked');raise RuntimeError('Offline synthetic test')
socket.socket.connect=blocked;socket.socket.connect_ex=blocked;socket.getaddrinfo=blocked;socket.create_connection=blocked
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
result={'status':'STARTED','real_features_extracted':0,'rf_fits':0,'evaluations':0,'model_max_length_override':False}
try:
 import torch,transformers,bert_score
 from bert_score.utils import sent_encode,model2layers
 assert transformers.__version__=='4.30.2'
 assert Path(transformers.__file__).resolve().is_relative_to(HERE/'env')
 result['runtime']={'python':sys.version,'executable':sys.executable,'packages':{n:importlib.metadata.version(n) for n in ['bert-score','transformers','tokenizers','huggingface-hub','torch','numpy','pandas','scipy','scikit-learn','safetensors','regex','packaging']}}
 frozen=json.loads((V4/'provenance/compatibility.json').read_text())
 for asset in frozen['model_files'].values():assert sha(asset['path'])==asset['sha256']
 assert Path(frozen['cache_ref_path']).read_text().strip()==frozen['revision']
 torch.manual_seed(42);torch.set_num_threads(4);torch.set_num_interop_threads(4)
 start=time.perf_counter()
 scorer=bert_score.BERTScorer(model_type=frozen['model_id'],num_layers=None,batch_size=2,nthreads=4,
         all_layers=False,idf=False,device='cpu',lang=None,rescale_with_baseline=False,use_fast_tokenizer=False)
 assert scorer._model.config._commit_hash==frozen['revision']
 assert scorer.num_layers==model2layers[frozen['model_id']]==18
 assert scorer._tokenizer.model_max_length==512
 assert {p.dtype for p in scorer._model.parameters()}=={torch.float32}
 result.update(model_id=frozen['model_id'],checkpoint_revision=frozen['revision'],num_layers=scorer.num_layers,
               tokenizer_class=type(scorer._tokenizer).__name__,tokenizer_max_length=scorer._tokenizer.model_max_length,
               hash_string=scorer.hash,model_max_position_embeddings=scorer._model.config.max_position_embeddings,
               load_seconds=time.perf_counter()-start,model_class=type(scorer._model).__name__)
 # Two short pairs exercise finite matching and unequal-length batch padding.
 refs=['a','A cat sleeps.'];cands=['a','A cat.']
 start=time.perf_counter()
 with torch.inference_mode():p,r,f=scorer.score(cands=cands,refs=refs,batch_size=2)
 assert torch.isfinite(torch.stack([p,r,f])).all()
 result['score_seconds']=time.perf_counter()-start
 result['synthetic_scores']=[{'reference':ref,'candidate':hyp,'P':float(p[i]),'R':float(r[i]),'F1':float(f[i]),
     'reference_tokens':sent_encode(scorer._tokenizer,ref),'candidate_tokens':sent_encode(scorer._tokenizer,hyp)} for i,(ref,hyp) in enumerate(zip(refs,cands))]
 # Tokenizer-only boundary check, no long-sequence inference and no real texts.
 long='a '*600
 result['synthetic_truncation_check']={'untruncated_tokens':len(scorer._tokenizer.encode(long.strip(),truncation=False)),
                                     'official_sent_encode_tokens':len(sent_encode(scorer._tokenizer,long))}
 assert result['synthetic_truncation_check']=={'untruncated_tokens':602,'official_sent_encode_tokens':512}
 assert scorer._tokenizer.model_max_length==512 and not network
 result['status']='PASS'
except Exception as error:
 result.update(status='FAIL',error=repr(error),traceback=traceback.format_exc())
result['network_attempts']=network
with (HERE/'official_pinned_test.json').open('x',encoding='utf-8') as f:json.dump(result,f,indent=2)
print(json.dumps(result,indent=2),flush=True)
if result['status']!='PASS':raise SystemExit(2)
