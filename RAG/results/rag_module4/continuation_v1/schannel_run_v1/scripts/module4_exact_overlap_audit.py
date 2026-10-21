"""Label-free exact normalized definition-target overlap audit for frozen top-5."""
from __future__ import annotations
import argparse,csv,json,os,sys,unicodedata
from collections import defaultdict
from pathlib import Path
import numpy as np

CONT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(CONT/'scripts'))
import module4_build_rag_features as frozen

def norm(x):return " ".join(unicodedata.normalize("NFKC",str(x or "")).casefold().split())

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--inputs',type=Path,required=True);ap.add_argument('--snapshot',type=Path,required=True);ap.add_argument('--output',type=Path,required=True);args=ap.parse_args()
 from sentence_transformers import SentenceTransformer
 model=SentenceTransformer(frozen.MPNET_ID,device='cpu',local_files_only=True);model.max_seq_length=256
 def embed(texts):return model.encode(texts,batch_size=64,normalize_embeddings=True,convert_to_numpy=True,show_progress_bar=False,device='cpu')
 with args.inputs.open('r',encoding='utf-8-sig',newline='') as f: rows=list(csv.DictReader(f))
 records=[json.loads(x) for x in args.snapshot.read_text(encoding='utf-8').splitlines() if x];frozen.validate_snapshot(records);by=defaultdict(list)
 for r in records:by[r['term_key']].append(r)
 out=[]
 for row in rows:
  candidates=by.get(norm(row['term']),[]) if row['task']=='DM' and str(row['rag_applicable'])=='1' else []
  top=frozen.select_top5(f"{row['term']}\n{row['src']}",candidates,embed) if candidates else []
  matches=sum(norm(c['candidate_definition'])==norm(row['tgt']) for c,_ in top)
  out.append({'example_id':row['example_id'],'top5_count':len(top),'exact_normalized_definition_tgt_match':int(matches>0),'exact_match_count':matches})
 args.output.parent.mkdir(parents=True,exist_ok=True);tmp=args.output.with_suffix('.csv.part')
 with tmp.open('w',encoding='utf-8-sig',newline='') as f:
  w=csv.DictWriter(f,fieldnames=list(out[0]),lineterminator='\n');w.writeheader();w.writerows(out)
 os.replace(tmp,args.output)
 print(json.dumps({'rows':len(out),'exact_match_rows':sum(r['exact_normalized_definition_tgt_match'] for r in out),'exact_matches':sum(r['exact_match_count'] for r in out)},sort_keys=True))
if __name__=='__main__':main()
