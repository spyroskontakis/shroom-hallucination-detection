"""Frozen development-only E3 reproduction and single E5 fusion evaluation."""
from __future__ import annotations
import argparse, hashlib, json
from pathlib import Path
import numpy as np
import pandas as pd
from scipy.stats import spearmanr
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import accuracy_score

E3 = ["src_ent","src_neu","src_con","tgt_ent","tgt_neu","tgt_con","sim_src_hyp","sim_tgt_hyp","sim_src_tgt","sim_max","sim_min","sim_mean","sim_gap_tgt_src","sim_hyp_distance_from_truth"]
RAG = ["rag_evidence_available","rag_sense_count","rag_retrieval_top1_cosine","rag_target_definition_max_cosine","rag_target_definition_max_entailment","rag_target_definition_max_contradiction","rag_target_definition_max_lexical_overlap"]
EXPECTED_ACC=0.7932263814616756
EXPECTED_SPEARMAN=0.7390395612811848

def sha256(path:Path)->str:
    h=hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda:f.read(1<<20),b""):h.update(block)
    return h.hexdigest()

def metric(frame:pd.DataFrame)->dict:
    y=frame.p_hallucination.to_numpy(float);p=frame.prediction.to_numpy(float)
    # Exact canonical evaluator behavior: rank predictions after 12-decimal rounding.
    return {"n":int(len(frame)),"accuracy":float(accuracy_score(frame.label_bin.to_numpy(int),(p>=.5).astype(int))),"spearman":float(spearmanr(y,np.round(p,12)).statistic)}

def run_cv(frame:pd.DataFrame,features:list[str])->pd.DataFrame:
    chunks=[]
    for fold in range(1,6):
        train=frame[frame.fold_id!=fold];valid=frame[frame.fold_id==fold]
        model=RandomForestRegressor(n_estimators=500,random_state=42,n_jobs=-1)
        model.fit(train[features].to_numpy(float),train.p_hallucination.to_numpy(float))
        pred=np.clip(model.predict(valid[features].to_numpy(float)),0,1)
        chunks.append(pd.DataFrame({"canonical_id":valid.canonical_id.to_numpy(),"fold_id":fold,"prediction":pred},index=valid.index))
    return pd.concat(chunks).sort_index()

def main():
    ap=argparse.ArgumentParser();ap.add_argument("--mixed",type=Path,required=True);ap.add_argument("--folds",type=Path,required=True);ap.add_argument("--rag",type=Path,required=True);ap.add_argument("--output-dir",type=Path,required=True);args=ap.parse_args()
    expected={args.mixed:"3038bd8752a94064e05389e03b063484a1191f9e9a6164f06d11b40688a6828b",args.folds:"f5a5964923806a23dd34a8bcc137f3cf489437e033d645e9d0845bf40792eb5d",args.rag:"708483b831430d876135d1484ad841bf6ba0d9c9a2d0a5f22df6280535fe3160"}
    for p,want in expected.items():
        got=sha256(p)
        if got!=want:raise ValueError(f"Frozen input hash mismatch: {p}: {got}")
    mixed=pd.read_csv(args.mixed);folds=pd.read_csv(args.folds);rag=pd.read_csv(args.rag)
    if list(rag.columns)!=["example_id"]+RAG:raise ValueError("RAG schema mismatch")
    if len(mixed)!=561 or mixed.canonical_id.nunique()!=561 or len(rag)!=561 or rag.example_id.nunique()!=561:raise ValueError("Expected 561 unique rows")
    if set(E3+RAG)&{"label","label_bin","p_hallucination","canonical_id","fold_id"}:raise ValueError("Forbidden predictor")
    fold_check=mixed[["canonical_id","fold_id"]].merge(folds[["canonical_id","fold_id"]],on="canonical_id",suffixes=("_mixed","_locked"),validate="one_to_one")
    if len(fold_check)!=561 or not (fold_check.fold_id_mixed==fold_check.fold_id_locked).all():raise ValueError("Fold mismatch")
    frame=mixed.merge(rag.rename(columns={"example_id":"canonical_id"}),on="canonical_id",validate="one_to_one",sort=False)
    if len(frame)!=561 or not np.isfinite(frame[E3+RAG].to_numpy(float)).all():raise ValueError("Join/finiteness failure")
    e3_pred=run_cv(frame,E3);e3=frame[["canonical_id","fold_id","task","label_bin","p_hallucination"]].join(e3_pred[["prediction"]])
    e3_metrics=metric(e3)
    if e3_metrics["accuracy"]!=EXPECTED_ACC or abs(e3_metrics["spearman"]-EXPECTED_SPEARMAN)>1e-15:raise RuntimeError(f"E3 reproduction mismatch: {e3_metrics}")
    e5_pred=run_cv(frame,E3+RAG);e5=frame[["canonical_id","fold_id","task","label_bin","p_hallucination","rag_evidence_available"]].join(e5_pred[["prediction"]])
    e5_metrics=metric(e5)
    args.output_dir.mkdir(parents=True,exist_ok=True)
    fused=args.output_dir.parent/"features"/"module4_fused_21_features.csv";fused.parent.mkdir(parents=True,exist_ok=True)
    frame[["canonical_id"]+E3+RAG].to_csv(fused,index=False,encoding="utf-8-sig",lineterminator="\n")
    e3_out=args.output_dir/"module4_e3_oof_predictions.csv";e5_out=args.output_dir/"module4_e5_oof_predictions.csv"
    e3_pred.to_csv(e3_out,index=False,encoding="utf-8-sig",lineterminator="\n");e5_pred.to_csv(e5_out,index=False,encoding="utf-8-sig",lineterminator="\n")
    diagnostics={
      "all_rows":{"E3":e3_metrics,"E5":e5_metrics},
      "evidence_rows":{"E3":metric(e3[e5.rag_evidence_available==1]),"E5":metric(e5[e5.rag_evidence_available==1])},
      "fallback_rows":{"E3":metric(e3[e5.rag_evidence_available==0]),"E5":metric(e5[e5.rag_evidence_available==0])},
      "per_task":{task:{"E3":metric(e3[e3.task==task]),"E5":metric(e5[e5.task==task])} for task in sorted(frame.task.unique())}
    }
    decision="E5_RAG_IMPROVES_DEVELOPMENT_SCORE" if e5_metrics["accuracy"]>e3_metrics["accuracy"] or (e5_metrics["accuracy"]==e3_metrics["accuracy"] and e5_metrics["spearman"]>e3_metrics["spearman"]) else "E5_RAG_NO_SCORE_GAIN_E3_REMAINS_FINAL"
    result={"schema_version":"module4-development-oof-v1","rows":561,"folds":5,"e3_features":E3,"rag_features":RAG,"random_forest":{"n_estimators":500,"random_state":42,"n_jobs":-1},"e3_reproduction":{"expected":{"accuracy":EXPECTED_ACC,"spearman":EXPECTED_SPEARMAN},"observed":e3_metrics,"result":"PASS"},"e5":e5_metrics,"diagnostics":diagnostics,"decision":decision,"input_sha256":{str(p):sha256(p) for p in expected},"output_sha256":{"fused_21_features":sha256(fused),"e3_oof_predictions":sha256(e3_out),"e5_oof_predictions":sha256(e5_out)}}
    metrics=args.output_dir/"module4_development_oof_metrics.json";metrics.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps({"e3":e3_metrics,"e5":e5_metrics,"decision":decision,"metrics_sha256":sha256(metrics)},sort_keys=True))
if __name__=="__main__":main()
