"""Label-free 36-feature extraction using the original CPU backends/functions."""
import argparse,collections,hashlib,importlib.util,json,os,sys,time
from pathlib import Path
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[3]
sys.path.insert(0,str(HERE/'vendor'))
os.environ['HF_HUB_OFFLINE']='1'
os.environ['TRANSFORMERS_OFFLINE']='1'
sys.path[:0]=[str(ROOT/'codex'),str(ROOT/'RAG/results/rag_e6_v1/scripts'),str(ROOT/'RAG/results/rag_e6_v2/scripts'),str(ROOT/'RAG/results/rag_e6_v3/scripts'),str(ROOT/'RAG/scripts')]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def write(p,x):
    data=json.dumps(x,ensure_ascii=False,sort_keys=True,indent=2,allow_nan=False)+'\n'
    if p.exists():assert p.read_text(encoding='utf-8')==data,p
    else:
        tmp=p.with_suffix('.part');tmp.write_text(data,encoding='utf-8');os.replace(tmp,p)
def digest(x):return hashlib.sha256(json.dumps(x,ensure_ascii=False,sort_keys=True).encode()).hexdigest()
def main(stage):
    import numpy as np,pandas as pd,torch
    torch.set_num_threads(4);torch.set_num_interop_threads(4)
    torch.manual_seed(42);np.random.seed(42)
    contract=read(HERE.parent/'E10_OFFICIAL_TEST_FEATURE_MANIFEST.json')
    for p,h in contract['source_sha256'].items():assert sha(ROOT/p)==h,p
    rows=read(HERE/'test_inputs_label_free.json')
    assert len(rows)==len({r['id'] for r in rows})==1500
    assert all(set(r)=={'id','task','src','tgt','hyp'} for r in rows)
    reconstruction=read(HERE/'E10_RECONSTRUCTION_MANIFEST.json')
    assert sha(HERE/'test_inputs_label_free.json')==reconstruction['test_inputs_sha256']
    frame=pd.DataFrame(rows).rename(columns={'id':'example_id'});frame['example_id']=frame.example_id.astype(str)
    dest=HERE/'cpu_features';dest.mkdir(exist_ok=True)
    import v3_common
    environment=v3_common.versions()
    write(dest/(stage+'_input_lock.json'),{'input_sha256':sha(HERE/'test_inputs_label_free.json'),'contract_sha256':sha(HERE.parent/'E10_OFFICIAL_TEST_FEATURE_MANIFEST.json'),'adapter_sha256':sha(Path(__file__)),'environment':environment})
    done=dest/(stage+'_complete.json')
    if done.exists():
        meta=read(done)
        for p,h in meta['outputs'].items():assert sha(HERE/p)==h
        print(stage+' already completed and verified; no inference',flush=True);return
    started=time.time();outputs=[]
    if stage=='base14':
        import canonical_feature_extraction as base
        from transformers import AutoTokenizer,AutoModelForSequenceClassification
        from sentence_transformers import SentenceTransformer
        tokenizer=AutoTokenizer.from_pretrained(**{'pretrained_model_name_or_path':contract['models']['NLI1']['model'],'revision':contract['models']['NLI1']['revision'],'local_files_only':True})
        model=AutoModelForSequenceClassification.from_pretrained(contract['models']['NLI1']['model'],revision=contract['models']['NLI1']['revision'],local_files_only=True).to('cpu').eval()
        nli=base.extract_nli(frame,'example_id',tokenizer,model,torch.device('cpu'),2,dest/'base_nli.csv')
        del model,tokenizer
        simmodel=SentenceTransformer(contract['models']['MPNet']['model'],revision=contract['models']['MPNet']['revision'],local_files_only=True,device='cpu')
        # Base14 keeps the original checkpoint default; RAG separately uses 256.
        assert simmodel.max_seq_length==384
        sim=base.extract_similarity(frame,'example_id',simmodel,'cpu',64,dest/'base_similarity.csv')
        nli['example_id']=nli.example_id.astype(str);sim['example_id']=sim.example_id.astype(str)
        merged=nli.merge(sim,on='example_id',validate='one_to_one',sort=False)
        assert merged.example_id.tolist()==frame.example_id.tolist()
        merged[['example_id']+contract['ordered_features'][:14]].to_csv(dest/'base14.csv',index=False)
        outputs=[dest/'base14.csv',dest/'base_nli.csv',dest/'base_similarity.csv']
    elif stage=='rag11':
        import build_features as e6
        import module4_build_external_lexicon as lex
        frozen=e6.frozen
        records=[json.loads(l) for l in (HERE/'WIKTIONARY_RECONSTRUCTED_PROCESSED/combined_snapshot.jsonl').read_text(encoding='utf-8').splitlines()]
        assert sha(HERE/'WIKTIONARY_RECONSTRUCTED_PROCESSED/combined_snapshot.jsonl')==reconstruction['combined_snapshot_sha256']
        query=[{'example_id':str(r['id']),'task':r['task'],'term':lex.extract_dm_term(r['src']) or '', 'src':r['src'],'rag_applicable':int(r['task']=='DM' and bool(lex.extract_dm_term(r['src'])))} for r in rows]
        embed,nli=frozen.real_backends('cpu')
        byterm=collections.defaultdict(list)
        for r in records:byterm[r['term_key']].append(r)
        chunks=dest/'rag_chunks';chunks.mkdir(exist_ok=True)
        rankings=[];scores=[]
        for i,(q,r) in enumerate(zip(query,rows)):
            path=chunks/f'{i:04d}.json';identity=digest({'q':q,'r':r,'snapshot':reconstruction['combined_snapshot_sha256']})
            if path.exists():
                cached=read(path);assert cached['identity']==identity
            else:
                rank=e6.reconstruct([q],records,embed)[0]
                # Freeze the ranking record before providing hyp to definition scoring.
                write(chunks/f'{i:04d}_ranking.json',{'identity':identity,'ranking':rank})
                definition=rank['selected'][0]['candidate_definition'] if rank['selected'] else None
                f=frozen.row_features({**q,'tgt':r['tgt']},byterm.get(lex.term_key(q['term']),[]),embed,nli)
                f.update(e6.compare_hyp(definition,r['hyp'],embed,nli))
                cached={'identity':identity,'ranking':rank,'features':f};write(path,cached)
            rankings.append(cached['ranking']);scores.append(cached['features'])
            if (i+1)%50==0:print(f'RAG/definition {i+1}/1500',flush=True)
        write(dest/'rankings.json',rankings)
        pd.DataFrame(scores)[['example_id']+contract['ordered_features'][14:25]].to_csv(dest/'rag11.csv',index=False)
        outputs=[dest/'rankings.json',dest/'rag11.csv']
    elif stage in ('nli2','hhem'):
        import nli_backend,hhem_backend
        backend=nli_backend if stage=='nli2' else hhem_backend
        backend.c.verify_models()
        rankings=read(dest/'rankings.json');assert [str(r['canonical_id']) for r in rankings]==frame.example_id.tolist()
        pairs=[]
        for r,ranking in zip(rows,rankings):
            cid=str(r['id']);ref=r['src'] if r['task']=='PG' else r['tgt']
            items=[('A',ref,r['hyp'])]
            if stage=='nli2':items.append(('B',r['hyp'],ref))
            if ranking['selected']:items.append(('C',ranking['selected'][0]['candidate_definition'],r['hyp']))
            pairs.extend({'pair_id':cid+':'+g,'canonical_id':cid,'group':g,'premise':p,'hypothesis':h} for g,p,h in items)
        write(dest/(stage+'_pairs.json'),pairs)
        chunks=dest/(stage+'_chunks');chunks.mkdir(exist_ok=True)
        loaded=None;all_scores=[];all_audits=[]
        for begin in range(0,len(pairs),2):
            batch=pairs[begin:begin+2];p=chunks/f'{begin//2:04d}.json';identity=digest(batch)
            if p.exists():cached=read(p);assert cached['identity']==identity
            else:
                if loaded is None:loaded=backend.load_backend()
                s,a=backend.infer_batch(*loaded,batch)
                cached={'identity':identity,'scores':s,'audits':a};write(p,cached)
            all_scores+=cached['scores'];all_audits+=cached['audits']
            if (begin+2)%100==0:print(f'{stage} {begin+len(batch)}/{len(pairs)}',flush=True)
        lookup={s['pair_id']:s for s in all_scores};out=[]
        for r in rows:
            cid=str(r['id']);result={'example_id':cid}
            if stage=='nli2':
                for g,prefix in [('A','nli2_ref_hyp_'),('B','nli2_hyp_ref_'),('C','nli2_definition_hyp_')]:
                    score=lookup.get(cid+':'+g)
                    for label in ['entailment','neutral','contradiction']:result[prefix+label]=score[label] if score else 0.
            else:
                result['hhem_ref_hyp_consistency']=lookup[cid+':A']['consistency']
                result['hhem_definition_hyp_consistency']=lookup.get(cid+':C',{}).get('consistency',0.)
            out.append(result)
        pd.DataFrame(out).to_csv(dest/(stage+'.csv'),index=False)
        write(dest/(stage+'_truncation.json'),all_audits)
        outputs=[dest/(stage+'.csv'),dest/(stage+'_pairs.json'),dest/(stage+'_truncation.json')]
    write(done,{'stage':stage,'input_sha256':sha(HERE/'test_inputs_label_free.json'),'device':'cpu','dtype':'float32','threads':4,'seconds':time.time()-started,'outputs':{p.relative_to(HERE).as_posix():sha(p) for p in outputs}})
    print(stage+' PASS',flush=True)
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('stage',choices=['base14','rag11','nli2','hhem']);main(p.parse_args().stage)
