"""Independently rehash saved Modal checkpoints using CPU only."""
import hashlib
import json
from pathlib import Path
import modal

app=modal.App('shroom-e11d-checkpoint-audit')
volume=modal.Volume.from_name('shroom-e11d-human-contrastive-results',create_if_missing=False)

@app.function(image=modal.Image.debian_slim(python_version='3.11'),cpu=2,timeout=1800,volumes={'/results':volume},retries=0)
def verify():
    result={}
    for f in range(1,6):
        folder=Path(f'/results/e11d-fixed-001/folds/fold_{f}/e11d-fold-{f:03d}')
        status=json.loads((folder/'FOLD_PASS.json').read_text())
        hashes={p.name:hashlib.file_digest(p.open('rb'),'sha256').hexdigest() for p in (folder/'final_checkpoint').iterdir() if p.is_file()}
        assert hashes['model.safetensors']==status['checkpoint_sha256']
        assert status['fold_id']==f and status['run_id']==f'e11d-fold-{f:03d}' and status['status']=='PASS'
        pred=hashlib.sha256((folder/'heldout_predictions.jsonl').read_bytes()).hexdigest()
        assert pred==status['heldout_predictions_sha256']
        result[str(f)]={'model_sha256':hashes['model.safetensors'],'checkpoint_files_sha256':hashes,'predictions_sha256':pred,'summary':status}
    return {'status':'PASS','folds':result,'fits_started_by_verifier':0}

@app.local_entrypoint()
def main():
    home=Path(__file__).resolve().parent
    result=verify.remote()
    for f in range(1,6):
        local=json.loads((home/f'private/returned/fold_{f}.json').read_text())
        assert local['summary']==result['folds'][str(f)]['summary']
        assert hashlib.sha256(local['predictions_jsonl'].encode()).hexdigest()==result['folds'][str(f)]['predictions_sha256']
    with (home/'CHECKPOINT_VERIFICATION.json').open('x',encoding='utf-8') as out:
        json.dump(result,out,indent=2);out.write('\n')
    print('PASS: five saved checkpoints and prediction hashes match five local returns; zero training fits.')
