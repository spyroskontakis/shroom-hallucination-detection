"""Offline experiment helpers. Importing performs no fitting or artifact writes."""
import hashlib
import importlib.util
import json
import sys
from pathlib import Path

HERE=Path(__file__).resolve().parent
E11=HERE.parent
C=E11/'e11c_training'
D=E11/'e11d_training'
sys.path[:0]=[str(E11),str(E11/'e11a_results')]
from scoring_common import ROOT,require,sha_file
from e11a_prepare_data import load_protocol
from validate_e11a_protocol import read_jsonl,validate_local
from assemble_e11a_results import metric,baseline,rows_csv


def read(path): return json.loads(path.read_text(encoding='utf-8'))
def encoded(value): return json.dumps(value,sort_keys=True,ensure_ascii=False,separators=(',',':'),allow_nan=False).encode()
def digest(value): return hashlib.sha256(value).hexdigest()


def write_once(path,data):
    path.parent.mkdir(parents=True,exist_ok=True)
    if path.exists(): require(path.read_bytes()==data,'refusing overwrite: '+str(path))
    else: path.write_bytes(data)


def save(path,value):
    write_once(path,(json.dumps(value,indent=2,ensure_ascii=False,allow_nan=False)+'\n').encode())


def load_module(name,path):
    spec=importlib.util.spec_from_file_location(name,path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module


def baselines():
    a=load_protocol()
    require(sha_file(ROOT/a['data']['canonical_path'])==a['data']['canonical_sha256'] and sha_file(ROOT/a['data']['folds_path'])==a['data']['folds_sha256'],'human source integrity')
    human={r['canonical_id']:r for r in rows_csv(ROOT/a['data']['canonical_path'])}
    folds={r['canonical_id']:int(r['fold_id']) for r in rows_csv(ROOT/a['data']['folds_path'])}
    result={}
    for name,folder,oof_name in [('E11-A',E11/'e11a_results','E11A_OOF_PREDICTIONS.jsonl'),('E11-C',C,'private/E11C_OOF_PREDICTIONS.jsonl'),('E11-D',D,'private/E11D_OOF_PREDICTIONS.jsonl')]:
        report=folder/(name.replace('-','')+'_RESULTS.json');oof=folder/oof_name
        rows=read_jsonl(oof);validate_rows(rows,human,folds)
        computed=metric(rows,human)
        require(computed==read(report)['overall'],name+' exact evaluator replay')
        result[name]={**computed,'results_sha256':sha_file(report),'oof_sha256':sha_file(oof)}
    folder=ROOT/'RAG/results/phase3_e9_claim_verification/evaluation/E10'
    expected=read(folder/'E10_metrics.json')['metrics']['overall']
    base=baseline('E10',folder/'E10_oof.csv',folder/'E10_metrics.json',expected,human,folds)
    base.pop('scores');result['E10']=base
    return result,human,folds


def validate_rows(rows,human,folds,fold_id=None):
    import math
    expected={sid for sid in human if fold_id is None or folds[sid]==fold_id}
    ids=[r['sample_id'] for r in rows]
    require(len(ids)==len(set(ids))==len(expected) and set(ids)==expected,'OOF unique complete IDs')
    for r in rows:
        sid=r['sample_id'];p=r['p_H']
        require(r['fold_id']==folds[sid] and r['task']==human[sid]['task'] and r['gold_label']==int(human[sid]['label_bin']),'OOF row identity')
        require(isinstance(p,(int,float)) and math.isfinite(p) and 0<=p<=1 and r['predicted_class']==int(p>=.5),'OOF probability/class')
    for f in {r['fold_id'] for r in rows}:
        require({r['predicted_class'] for r in rows if r['fold_id']==f}=={0,1},'fold class collapse')


def protected_files():
    roots=[E11/'e11a_results',E11/'e11a_prepared',E11/'e11c',C,D,ROOT/'RAG/results/phase3_e9_claim_verification/evaluation/E10']
    paths=[p for root in roots for p in root.rglob('*') if p.is_file() and '__pycache__' not in p.parts]
    paths += [p for p in E11.iterdir() if p.is_file()]
    return {p.relative_to(ROOT).as_posix():sha_file(p) for p in sorted(set(paths))}


def verify_manifest(folder,name):
    manifest=read(folder/name)
    for relative,sha in manifest['files_sha256'].items(): require(sha_file(folder/relative)==sha,'manifest mismatch: '+str(folder/relative))
