"""Independent CPU-only verification of all ten E11-E saved checkpoints."""
import hashlib
import json
from pathlib import Path
import modal

app=modal.App('shroom-e11e-checkpoint-audit')
volume=modal.Volume.from_name('shroom-e11e-fixed-two-stage-contrastive-results',create_if_missing=False)


def sha(path):
    with path.open('rb') as handle:return hashlib.file_digest(handle,'sha256').hexdigest()


@app.function(image=modal.Image.debian_slim(python_version='3.11'),cpu=2,timeout=1800,volumes={'/results':volume},retries=0)
def verify():
    stages={}
    root=Path('/results/e11e-fixed-001')
    assert sorted(p.name for p in root.iterdir())==[f'fold_{f}' for f in range(1,6)]
    for f in range(1,6):
        assert sorted(p.name for p in (root/f'fold_{f}').iterdir())==['stage_1','stage_2']
        for stage in (1,2):
            folder=root/f'fold_{f}/stage_{stage}'
            s=json.loads((folder/'STAGE_PASS.json').read_text())
            hashes={p.name:sha(p) for p in (folder/'final_checkpoint').iterdir() if p.is_file()}
            assert s['status']=='PASS' and s['fold_id']==f and s['stage']==stage and s['run_id']==f'e11e-fold-{f:03d}-stage-{stage}'
            assert hashes['model.safetensors']==s['checkpoint_sha256']
            config=json.loads((folder/'final_checkpoint/config.json').read_text())
            assert config['label2id']=={'not_hallucination':0,'hallucination':1}
            record={'summary':s,'checkpoint_files_sha256':hashes,'status_sha256':sha(folder/'STAGE_PASS.json')}
            if stage==1:assert not (folder/'heldout_predictions.jsonl').exists()
            else:
                assert s['initial_model_weights_sha256']==stages[f'{f}:1']['summary']['checkpoint_sha256']
                record['predictions_sha256']=sha(folder/'heldout_predictions.jsonl')
                assert record['predictions_sha256']==s['heldout_predictions_sha256']
            stages[f'{f}:{stage}']=record
    return {'status':'PASS','stages':stages,'saved_stage1_fits':5,'saved_stage2_fits':5,'fits_started_by_verifier':0}


@app.local_entrypoint()
def main():
    home=Path(__file__).resolve().parent
    result=verify.remote()
    for f in range(1,6):
        local=json.loads((home/f'private/returned/fold_{f}.json').read_text())
        for stage in (1,2):assert local['stages'][stage-1]==result['stages'][f'{f}:{stage}']['summary']
        assert hashlib.sha256(local['predictions_jsonl'].encode()).hexdigest()==result['stages'][f'{f}:2']['predictions_sha256']
    with (home/'CHECKPOINT_VERIFICATION.json').open('x',encoding='utf-8') as handle:
        json.dump(result,handle,indent=2);handle.write('\n')
    print('PASS: ten saved checkpoints, five OOF returns and five Stage-1 to Stage-2 chains independently verified.')
