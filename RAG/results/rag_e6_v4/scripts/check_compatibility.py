"""Official unmodified BERTScore compatibility gate, artificial text only."""
from pathlib import Path
import sys,os,json,hashlib,traceback,time,socket,base64,csv,importlib.metadata
OUT=Path(__file__).resolve().parents[1];ROOT=OUT.parents[2]
sys.path.insert(0,str(OUT/'packages'))
for key in ['HF_HUB_OFFLINE','TRANSFORMERS_OFFLINE','HF_DATASETS_OFFLINE','HF_HUB_DISABLE_TELEMETRY']:os.environ[key]='1'
os.environ['MPLCONFIGDIR']=str(OUT/'runtime_tmp/matplotlib');os.environ['MPLBACKEND']='Agg'
os.environ['TOKENIZERS_PARALLELISM']='false';os.environ['PYTHONDONTWRITEBYTECODE']='1'
MODEL='microsoft/deberta-large-mnli';REV='7296194b9009373def4f7c5dad292651e4b5cf4e'
def sha(p):
    h=hashlib.sha256()
    with Path(p).open('rb') as f:
        for b in iter(lambda:f.read(1<<20),b''):h.update(b)
    return h.hexdigest()
def write(n,v):
    with (OUT/n).open('x',encoding='utf-8') as f:json.dump(v,f,indent=2,ensure_ascii=False,allow_nan=False)
network=[]
def blocked(*a,**k):network.append('blocked');raise RuntimeError('Network disabled')
socket.socket.connect=blocked;socket.create_connection=blocked;socket.getaddrinfo=blocked

def main():
    result={'status':'CHECKING','real_pairs_scored':0,'rf_fits':0,'model_id':MODEL,'revision':REV}
    try:
        # Verify each unpacked official wheel RECORD entry; never patch this package.
        record=OUT/'packages/bert_score-0.3.13.dist-info/RECORD';verified=0
        with record.open(encoding='utf-8',newline='') as f:
            for name,digest,size in csv.reader(f):
                if not digest:continue
                p=OUT/'packages'/name;want=base64.urlsafe_b64decode(digest.split('=',1)[1]+'==').hex()
                assert sha(p)==want and p.stat().st_size==int(size);verified+=1
        assert importlib.metadata.version('bert-score')=='0.3.13'
        frozen=json.loads((ROOT/'RAG/results/rag_e6_v1/config/run_config.json').read_text(encoding='utf-8'))
        assets=frozen['model_files']['nli']
        snapshot=Path(assets['config.json']['path']).parent
        assert snapshot.name==REV
        ref=snapshot.parent.parent/'refs/main';assert ref.read_text().strip()==REV
        for name,m in assets.items():assert sha(m['path'])==m['sha256'],name
        import bert_score,torch,transformers
        from bert_score.utils import model2layers,get_hash,greedy_cos_idf,sent_encode
        assert MODEL in model2layers
        layers=model2layers[MODEL]
        result.update(distribution_version=importlib.metadata.version('bert-score'),internal_version=bert_score.__version__,
                      wheel_sha256=sha(OUT/'provenance/bert_score-0.3.13-py3-none-any.whl'),record_entries_verified=verified,
                      num_layers=layers,official_hash=get_hash(MODEL,layers,False,False,False,False),
                      model_files=assets,cache_ref_path=str(ref),cache_ref_sha256=sha(ref),
                      packages={k:importlib.metadata.version(k) for k in ['torch','transformers','numpy','pandas','scipy','scikit-learn','tokenizers','bert-score']})
        torch.manual_seed(42);assert torch.get_num_threads()==torch.get_num_interop_threads()==4
        t0=time.perf_counter()
        scorer=bert_score.BERTScorer(model_type=MODEL,num_layers=None,batch_size=2,nthreads=4,
                   all_layers=False,idf=False,device='cpu',lang=None,rescale_with_baseline=False,use_fast_tokenizer=False)
        assert scorer.num_layers==layers and len(scorer._model.encoder.layer)==layers
        assert scorer._model.config._commit_hash==REV
        assert not scorer._model.training
        assert {p.dtype for p in scorer._model.parameters()}=={torch.float32}
        result.update(model_class=type(scorer._model).__name__,tokenizer_class=type(scorer._tokenizer).__name__,
                      tokenizer_name_or_path=scorer._tokenizer.name_or_path,tokenizer_max_length=scorer._tokenizer.model_max_length,
                      model_max_position_embeddings=scorer._model.config.max_position_embeddings,
                      observed_commit=scorer._model.config._commit_hash,scorer_hash=scorer.hash,
                      device='cpu',dtype='float32',batch_size=2,torch_threads=4,torch_interop_threads=4)
        # Direction test calls the official matching function on artificial orthogonal embeddings.
        eye=torch.eye(5);ref_emb=eye[[3,0,1,2,4]].unsqueeze(0);hyp_emb=eye[[3,0,1,4]].unsqueeze(0)
        P,R,F=greedy_cos_idf(ref_emb.clone(),torch.ones(1,5),torch.tensor([[0.,1.,1.,1.,0.]]),
                            hyp_emb.clone(),torch.ones(1,4),torch.tensor([[0.,1.,1.,0.]]))
        assert torch.allclose(P,torch.tensor([1.])) and torch.allclose(R,torch.tensor([2/3]))
        samples=[('identical','A red cat sleeps.','A red cat sleeps.'),
                 ('omission','A red cat sleeps and a blue dog runs.','A red cat sleeps.'),
                 ('addition','A red cat sleeps.','A red cat sleeps and a blue dog runs.'),
                 ('number_change','There are 12 apples.','There are 13 apples.'),
                 ('negation_added','The train is running.','The train is not running.'),
                 ('negation_removed','The train is not running.','The train is running.')]
        with torch.inference_mode():
            p,r,f=scorer.score(cands=[s[2] for s in samples],refs=[s[1] for s in samples],batch_size=2)
        assert torch.isfinite(torch.stack([p,r,f])).all()
        assert torch.allclose(torch.stack([p[0],r[0],f[0]]),torch.ones(3),atol=2e-5,rtol=0)
        assert p[1]>r[1] and r[2]>p[2]
        assert abs(float(p[1]-r[2]))<2e-5 and abs(float(r[1]-p[2]))<2e-5
        result.update(status='PASS',smoke=[{'kind':s[0],'reference':s[1],'hyp':s[2],
                      'precision':float(p[i]),'recall':float(r[i]),'f1':float(f[i])} for i,s in enumerate(samples)],
                      direction_contract='official greedy matching P=1, R=2/3 for partial candidate coverage',
                      smoke_seconds=time.perf_counter()-t0)
        assert ref.read_text().strip()==REV and not network
    except Exception as error:
        result.update(status='BLOCKED_COMPATIBILITY',error=repr(error),traceback=traceback.format_exc())
    result['network_attempts']=network
    write('provenance/compatibility.json',result)
    print(json.dumps({k:v for k,v in result.items() if k not in ['model_files','smoke']},ensure_ascii=False,indent=2),flush=True)
    if result['status']!='PASS':raise SystemExit(2)

if __name__=='__main__':main()
