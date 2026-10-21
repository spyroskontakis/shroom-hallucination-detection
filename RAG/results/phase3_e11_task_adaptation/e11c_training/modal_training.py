"""Isolated E11-C A100 training; no secrets and no teacher API clients."""
import json
import sys
from pathlib import Path
import modal

REMOTE='/opt/e11c'
LOCAL=Path(__file__).resolve().parent if modal.is_local() else Path(REMOTE)
if str(LOCAL) not in sys.path:sys.path.insert(0,str(LOCAL))
from train_stages import execute,require,sha_file


def image_definition():
    e11=LOCAL.parent
    audit=json.loads((LOCAL/'PRETRAINING_AUDIT.json').read_text())
    require(audit['status']=='PASS','pretraining audit must PASS')
    spec=json.loads((LOCAL/'E11C_TRAINING_PROTOCOL.json').read_text())
    image=modal.Image.debian_slim(python_version='3.11')
    for name in ('train_stages.py','E11C_TRAINING_PROTOCOL.json','PRETRAINING_AUDIT.json','RUNTIME_MANIFEST.json'):
        image=image.add_local_file(str(LOCAL/name),f'{REMOTE}/{name}',copy=True)
    image=image.add_local_file(str(e11/'E11A_REQUIREMENTS.lock.txt'),f'{REMOTE}/requirements.txt',copy=True)
    for fold in range(1,6):
        for name in spec['folds'][str(fold)]['files_sha256']:
            image=image.add_local_file(str(LOCAL/f'private/fold_{fold}'/name),f'{REMOTE}/private/fold_{fold}/{name}',copy=True)
    # Explicit model path from the verified E11-A protocol; no other data uploaded.
    root=e11.parents[2]
    image=image.add_local_dir(str(root/spec['model']['local_mirror_dir']),f'{REMOTE}/model',copy=True)
    return image.run_commands(f'python -m pip install --no-cache-dir -r {REMOTE}/requirements.txt','python -m pip check')


image=image_definition() if modal.is_local() else modal.Image.debian_slim(python_version='3.11')
app=modal.App('shroom-e11c-fixed-two-stage')
volume=modal.Volume.from_name('shroom-e11c-fixed-two-stage-results',create_if_missing=True)


@app.function(image=image,gpu='A100-80GB',cpu=8,memory=65536,ephemeral_disk=524288,
              timeout=14400,volumes={'/results':volume},max_containers=5,retries=0)
def train(fold_id):
    bundle=Path(REMOTE);output=Path('/results/e11c-fixed-001')
    manifest=json.loads((bundle/'RUNTIME_MANIFEST.json').read_text())
    for name,digest in manifest.items():require(sha_file(bundle/name)==digest,'runtime integrity')
    summaries=[]
    for stage in (1,2):
        model=bundle/'model' if stage==1 else output/f'fold_{fold_id}/stage_1/final_checkpoint'
        summary=execute(fold_id,stage,bundle,model,output)
        volume.commit()
        summaries.append(summary)
    predictions=(output/f'fold_{fold_id}/stage_2/heldout_predictions.jsonl').read_text()
    return {'fold_id':fold_id,'stages':summaries,'predictions_jsonl':predictions}


@app.local_entrypoint()
def main():
    target=LOCAL/'private/returned'
    require(not target.exists(),'existing return directory; do not duplicate fits')
    target.mkdir(parents=True)
    # All jobs use independent fold-scoped data/checkpoints; exactly ten fits.
    for result in train.map(range(1,6)):
        fold=result['fold_id']
        (target/f'fold_{fold}.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
        print('Completed fold',fold,'both stages; heldout rows',result['stages'][1]['heldout_predictions'],flush=True)
