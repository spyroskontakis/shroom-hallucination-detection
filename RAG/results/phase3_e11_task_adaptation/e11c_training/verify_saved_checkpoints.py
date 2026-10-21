"""Read-only CPU verification of existing checkpoints; never trains a model."""
import hashlib
import json
from pathlib import Path
import modal

app=modal.App('shroom-e11c-checkpoint-audit')
volume=modal.Volume.from_name('shroom-e11c-fixed-two-stage-results',create_if_missing=False)


@app.function(image=modal.Image.debian_slim(python_version='3.11'),cpu=2,
              timeout=1800,volumes={'/results':volume},retries=0)
def verify():
    root=Path('/results/e11c-fixed-001')
    evidence={}
    for fold in range(1,6):
        for stage in (1,2):
            folder=root/f'fold_{fold}/stage_{stage}'
            status=json.loads((folder/'STAGE_PASS.json').read_text())
            with (folder/'final_checkpoint/model.safetensors').open('rb') as f:
                digest=hashlib.file_digest(f,'sha256').hexdigest()
            assert status['checkpoint_sha256']==digest
            assert status['fold_id']==fold and status['stage']==stage and status['status']=='PASS'
            evidence[f'{fold}:{stage}']={'checkpoint_sha256':digest,'status':status}
            if stage==2:
                data=(folder/'heldout_predictions.jsonl').read_bytes()
                assert hashlib.sha256(data).hexdigest()==status['heldout_predictions_sha256']
                evidence[f'{fold}:{stage}']['predictions_sha256']=hashlib.sha256(data).hexdigest()
    return evidence


@app.local_entrypoint()
def main():
    home=Path(__file__).resolve().parent
    evidence=verify.remote()
    for fold in range(1,6):
        local=json.loads((home/f'private/returned/fold_{fold}.json').read_text())
        for stage in (1,2):
            assert local['stages'][stage-1]==evidence[f'{fold}:{stage}']['status']
        assert hashlib.sha256(local['predictions_jsonl'].encode()).hexdigest()==evidence[f'{fold}:2']['predictions_sha256']
    target=home/'CHECKPOINT_VERIFICATION.json'
    with target.open('x',encoding='utf-8') as f:
        json.dump({'status':'PASS','training_reruns':0,'original_five_jobs_completed':True,
                   'stage1_fits':5,'stage2_fits':5,'evidence':evidence},f,indent=2)
        f.write('\n')
    print('PASS: all ten saved checkpoint hashes and all five local returns match the persistent volume.')
