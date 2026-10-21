"""Frozen seven-feature Module 4 pipeline; label-free inputs only."""
from __future__ import annotations
import argparse, csv, hashlib, json, math, os, random, re, unicodedata
from collections import defaultdict
from pathlib import Path
from typing import Any, Callable

FEATURES=["rag_evidence_available","rag_sense_count","rag_retrieval_top1_cosine","rag_target_definition_max_cosine","rag_target_definition_max_entailment","rag_target_definition_max_contradiction","rag_target_definition_max_lexical_overlap"]
TOP_K=5
MPNET_ID="sentence-transformers/all-mpnet-base-v2"
MPNET_REVISION="e8c3b32edf5434bc2275fc9bab85f82640a19130"
NLI_ID="microsoft/deberta-large-mnli"
NLI_REVISION="7296194b9009373def4f7c5dad292651e4b5cf4e"
NLI_LABELS={0:"CONTRADICTION",1:"NEUTRAL",2:"ENTAILMENT"}
TOKEN_RE=re.compile(r"[^\W_]+",re.UNICODE)
FORBIDDEN=re.compile(r"(?i)^(label|labels|label_bin|p[_ (]?hallucination\)?|p_hallucination|prediction|oof_prediction)$")

def sha256_file(path:Path)->str:
    h=hashlib.sha256()
    with path.open("rb") as f:
        for b in iter(lambda:f.read(1024*1024),b""):h.update(b)
    return h.hexdigest()

def tokens(text:Any)->set[str]:
    return set(TOKEN_RE.findall(unicodedata.normalize("NFKC",str(text or "")).casefold()))

def lexical_jaccard(a:Any,b:Any)->float:
    x,y=tokens(a),tokens(b)
    return len(x&y)/len(x|y) if x or y else 0.0

def candidate_text(row:dict[str,Any])->str:
    return f"{row['candidate_term']}\n{row['candidate_context']}"

def validate_input_schema(headers:list[str])->None:
    if headers != ["example_id","task","term","src","tgt","rag_applicable"]: raise ValueError(f"Unexpected input schema: {headers}")
    if any(FORBIDDEN.match(h) for h in headers): raise ValueError("Label-bearing input rejected")

def validate_snapshot(records:list[dict[str,Any]])->None:
    if any(r.get("source")!="enwiktionary" for r in records): raise ValueError("Non-Wiktionary evidence rejected")
    if len({r["evidence_id"] for r in records})!=len(records): raise ValueError("Duplicate evidence IDs")

def select_top5(query:str,candidates:list[dict[str,Any]],embed:Callable[[list[str]],Any])->list[tuple[dict[str,Any],float]]:
    if not candidates:return []
    import numpy as np
    matrix=np.asarray(embed([query]+[candidate_text(c) for c in candidates]),dtype=float)
    matrix=matrix/np.maximum(np.linalg.norm(matrix,axis=1,keepdims=True),1e-12)
    scores=matrix[1:]@matrix[0]
    ranked=sorted(zip(candidates,scores.tolist()),key=lambda x:(-x[1],x[0]["source_entry_id"],x[0]["evidence_id"]))
    return ranked[:TOP_K]

def row_features(row:dict[str,Any],candidates:list[dict[str,Any]],embed:Callable[[list[str]],Any],nli:Callable[[list[tuple[str,str]]],list[dict[str,float]]])->dict[str,Any]:
    zero={name:0 if name in ("rag_evidence_available","rag_sense_count") else 0.0 for name in FEATURES}
    if row["task"]!="DM" or str(row["rag_applicable"]) not in ("1","True","true"):return {"example_id":row["example_id"],**zero}
    selected=select_top5(f"{row['term']}\n{row['src']}",candidates,embed)
    if not selected:return {"example_id":row["example_id"],**zero}
    import numpy as np
    defs=[c["candidate_definition"] for c,_ in selected]
    target_matrix=np.asarray(embed([row["tgt"]]+defs),dtype=float);target_matrix=target_matrix/np.maximum(np.linalg.norm(target_matrix,axis=1,keepdims=True),1e-12)
    target_scores=(target_matrix[1:]@target_matrix[0]).tolist()
    nli_scores=nli([(definition,row["tgt"]) for definition in defs])
    result={"example_id":row["example_id"],"rag_evidence_available":1,"rag_sense_count":len(selected),"rag_retrieval_top1_cosine":float(selected[0][1]),"rag_target_definition_max_cosine":float(max(target_scores)),"rag_target_definition_max_entailment":float(max(s["entailment"] for s in nli_scores)),"rag_target_definition_max_contradiction":float(max(s["contradiction"] for s in nli_scores)),"rag_target_definition_max_lexical_overlap":float(max(lexical_jaccard(d,row["tgt"]) for d in defs))}
    if not all(math.isfinite(float(result[f])) for f in FEATURES):raise ValueError("Non-finite feature")
    return result

def build(rows:list[dict[str,Any]],records:list[dict[str,Any]],embed,nli)->list[dict[str,Any]]:
    validate_snapshot(records);by_term=defaultdict(list)
    for record in records:by_term[record["term_key"]].append(record)
    ids=[r["example_id"] for r in rows]
    if len(ids)!=561 or len(set(ids))!=561:raise ValueError("Expected 561 unique ordered row IDs")
    return [row_features(row,by_term.get(unicodedata.normalize("NFKC",row["term"]).strip().casefold(),[]),embed,nli) for row in rows]

def write_csv(path:Path,rows:list[dict[str,Any]])->None:
    path.parent.mkdir(parents=True,exist_ok=True);tmp=path.with_suffix(path.suffix+".part")
    with tmp.open("w",encoding="utf-8-sig",newline="") as f:
        w=csv.DictWriter(f,fieldnames=["example_id"]+FEATURES,lineterminator="\n");w.writeheader();w.writerows(rows)
    os.replace(tmp,path)

def real_backends(device:str):
    import numpy as np, torch
    from sentence_transformers import SentenceTransformer
    from transformers import AutoModelForSequenceClassification,AutoTokenizer
    random.seed(42);np.random.seed(42);torch.manual_seed(42)
    sim=SentenceTransformer(MPNET_ID,revision=MPNET_REVISION,device=device,local_files_only=True);sim.max_seq_length=256
    tokenizer=AutoTokenizer.from_pretrained(NLI_ID,revision=NLI_REVISION,local_files_only=True)
    model=AutoModelForSequenceClassification.from_pretrained(NLI_ID,revision=NLI_REVISION,local_files_only=True).to(device).eval()
    def embed(texts):return sim.encode(texts,batch_size=64,normalize_embeddings=True,convert_to_numpy=True,show_progress_bar=False,device=device)
    def nli(pairs):
        out=[]
        with torch.inference_mode():
            for start in range(0,len(pairs),8 if device.startswith("cuda") else 2):
                batch=pairs[start:start+(8 if device.startswith("cuda") else 2)];enc=tokenizer([x[0] for x in batch],[x[1] for x in batch],truncation=True,max_length=512,padding=True,return_tensors="pt");enc={k:v.to(device) for k,v in enc.items()};probs=torch.softmax(model(**enc).logits,dim=-1).cpu().numpy()
                for p in probs:out.append({"contradiction":float(p[0]),"neutral":float(p[1]),"entailment":float(p[2])})
        return out
    return embed,nli

def main():
    ap=argparse.ArgumentParser();ap.add_argument("--inputs",type=Path,required=True);ap.add_argument("--snapshot",type=Path,required=True);ap.add_argument("--output",type=Path,required=True);ap.add_argument("--device",default="cpu");args=ap.parse_args()
    with args.inputs.open("r",encoding="utf-8-sig",newline="") as f:r=csv.DictReader(f);validate_input_schema(r.fieldnames or []);rows=list(r)
    records=[json.loads(line) for line in args.snapshot.read_text(encoding="utf-8").splitlines() if line]
    embed,nli=real_backends(args.device);write_csv(args.output,build(rows,records,embed,nli))

if __name__=="__main__":main()
