"""Offline provenance launcher for the authorized pinned Module 4 replay."""
from __future__ import annotations
import argparse, hashlib, importlib.metadata, json, os, runpy, sys, time
from datetime import datetime, timezone
from pathlib import Path

FLAGS=("HF_HUB_OFFLINE","TRANSFORMERS_OFFLINE","HF_DATASETS_OFFLINE","HF_HUB_DISABLE_TELEMETRY","PYTHONDONTWRITEBYTECODE")
MPNET_ID="sentence-transformers/all-mpnet-base-v2";MPNET_REV="e8c3b32edf5434bc2275fc9bab85f82640a19130"
NLI_ID="microsoft/deberta-large-mnli";NLI_REV="7296194b9009373def4f7c5dad292651e4b5cf4e"
MP_FILES=("model.safetensors","config.json","modules.json","config_sentence_transformers.json","sentence_bert_config.json","tokenizer.json","tokenizer_config.json","vocab.txt","special_tokens_map.json","1_Pooling/config.json")
NLI_FILES=("pytorch_model.bin","config.json","tokenizer_config.json","merges.txt","vocab.json")

def sha(path):
    h=hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda:f.read(1<<20),b""):h.update(block)
    return h.hexdigest()
def inventory(root,names):
    out={}
    for name in names:
        p=root/name
        if not p.is_file():raise FileNotFoundError(p)
        out[name]={"path":str(p.resolve()),"bytes":p.stat().st_size,"sha256":sha(p)}
    return out
def resolve(repo,revision):
    from huggingface_hub import snapshot_download
    return Path(snapshot_download(repo_id=repo,revision=revision,local_files_only=True)).resolve()
def main():
    ap=argparse.ArgumentParser();ap.add_argument("--mode",choices=("preflight","features","overlap"),required=True);ap.add_argument("--replay-root",type=Path,required=True);ap.add_argument("--inputs",type=Path,required=True);ap.add_argument("--snapshot",type=Path,required=True);ap.add_argument("--output",type=Path);ap.add_argument("--provenance",type=Path,required=True);ap.add_argument("--feature-script",type=Path,required=True);ap.add_argument("--overlap-script",type=Path,required=True);a=ap.parse_args()
    if any(os.environ.get(k)!="1" for k in FLAGS):raise RuntimeError("OFFLINE_FLAG_MISSING")
    network_log=Path(os.environ["PINNED_REPLAY_NETWORK_LOG"])
    if network_log.exists() and network_log.stat().st_size:raise RuntimeError("PREEXISTING_NETWORK_ATTEMPT")
    start=time.perf_counter();started=datetime.now(timezone.utc).isoformat()
    mp=resolve(MPNET_ID,MPNET_REV);nli=resolve(NLI_ID,NLI_REV)
    expected_mp=Path.home()/".cache"/"huggingface"/"hub"/f"models--sentence-transformers--all-mpnet-base-v2"/"snapshots"/MPNET_REV
    expected_nli=Path.home()/".cache"/"huggingface"/"hub"/"models--microsoft--deberta-large-mnli"/"snapshots"/NLI_REV
    if mp!=expected_mp.resolve() or nli!=expected_nli.resolve():raise RuntimeError("RESOLVED_SNAPSHOT_MISMATCH")
    prov={"mode":a.mode,"started_utc":started,"offline_flags":{k:os.environ[k] for k in FLAGS},"python":{"executable":sys.executable,"version":sys.version.split()[0]},"packages":{k:importlib.metadata.version(k) for k in ("torch","transformers","sentence-transformers","numpy")},"device":"cpu","dtype_policy":"model defaults; MPNet/NLI float32 CPU as frozen specification","requested":{"mpnet":{"model":MPNET_ID,"revision":MPNET_REV},"nli":{"model":NLI_ID,"revision":NLI_REV}},"observed_resolution":{"mpnet_snapshot":str(mp),"nli_snapshot":str(nli)},"files":{"mpnet":inventory(mp,MP_FILES),"nli":inventory(nli,NLI_FILES)},"inputs":{"label_free_csv":{"path":str(a.inputs.resolve()),"sha256":sha(a.inputs)},"lexical_snapshot":{"path":str(a.snapshot.resolve()),"sha256":sha(a.snapshot)}},"scripts":{"feature":{"path":str(a.feature_script.resolve()),"sha256":sha(a.feature_script)},"overlap":{"path":str(a.overlap_script.resolve()),"sha256":sha(a.overlap_script)},"launcher":{"path":str(Path(__file__).resolve()),"sha256":sha(Path(__file__))}}}
    if a.mode!="preflight":
        if a.output is None:raise ValueError("--output required")
        a.output.resolve().relative_to(a.replay_root.resolve())
        target=a.feature_script if a.mode=="features" else a.overlap_script
        sys.argv=[str(target),"--inputs",str(a.inputs),"--snapshot",str(a.snapshot),"--output",str(a.output)]
        if a.mode=="features":sys.argv.extend(["--device","cpu"])
        runpy.run_path(str(target),run_name="__main__")
        prov["output"]={"path":str(a.output.resolve()),"bytes":a.output.stat().st_size,"sha256":sha(a.output)}
    if network_log.exists() and network_log.stat().st_size:raise RuntimeError("NETWORK_ATTEMPT_DETECTED")
    prov.update({"completed_utc":datetime.now(timezone.utc).isoformat(),"duration_seconds":round(time.perf_counter()-start,6),"blocked_network_attempts":0})
    a.provenance.parent.mkdir(parents=True,exist_ok=True);a.provenance.write_text(json.dumps(prov,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps({"mode":a.mode,"mpnet_snapshot":str(mp),"nli_snapshot":str(nli),"blocked_network_attempts":0,"duration_seconds":prov["duration_seconds"]},sort_keys=True))
if __name__=="__main__":main()
