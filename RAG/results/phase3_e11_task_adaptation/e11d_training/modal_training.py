"""Exactly five frozen E11-D folds; isolated durable volume, no teacher clients."""
import json
import sys
from pathlib import Path
import modal

REMOTE = '/opt/e11d'
LOCAL = Path(__file__).resolve().parent if modal.is_local() else Path(REMOTE)
if str(LOCAL) not in sys.path: sys.path.insert(0, str(LOCAL))
if modal.is_local(): sys.path.insert(0, str(LOCAL.parent))
from scoring_common import require, sha_file


def make_image():
    e11 = LOCAL.parent
    audit = json.loads((LOCAL/'E11D_PRETRAINING_AUDIT.json').read_text())
    require(audit['status'] == 'PASS', 'pretraining audit')
    manifest = json.loads((LOCAL/'RUNTIME_MANIFEST.json').read_text())
    image = modal.Image.debian_slim(python_version='3.11')
    for name, entry in manifest.items():
        source = LOCAL/entry['local_path']
        require(sha_file(source) == entry['sha256'], 'runtime source drift: '+name)
        image = image.add_local_file(str(source), f'{REMOTE}/{name}', copy=True)
    image = image.add_local_file(str(LOCAL/'RUNTIME_MANIFEST.json'), f'{REMOTE}/RUNTIME_MANIFEST.json', copy=True)
    spec = json.loads((e11/'E11A_TRAINING_PROTOCOL.json').read_text())
    image = image.add_local_dir(str(e11.parents[2]/spec['model']['local_mirror_dir']), f'{REMOTE}/model', copy=True)
    return image.run_commands(f'python -m pip install --no-cache-dir -r {REMOTE}/E11A_REQUIREMENTS.lock.txt', 'python -m pip check')


image = make_image() if modal.is_local() else modal.Image.debian_slim(python_version='3.11')
app = modal.App('shroom-e11d-human-contrastive')
volume = modal.Volume.from_name('shroom-e11d-human-contrastive-results', create_if_missing=True)


@app.function(image=image, gpu='A100-80GB', cpu=8, memory=65536, ephemeral_disk=524288,
              timeout=14400, volumes={'/results':volume}, max_containers=5, retries=0)
def train(fold_id):
    from train_fold import execute
    bundle = Path(REMOTE)
    manifest = json.loads((bundle/'RUNTIME_MANIFEST.json').read_text())
    for name, entry in manifest.items(): require(sha_file(bundle/name) == entry['sha256'], 'runtime integrity')
    result = execute(fold_id, 'fold', bundle, bundle/'model', Path('/results/e11d-fixed-001'), f'e11d-fold-{fold_id:03d}', True)
    volume.commit()
    folder = Path(result['checkpoint_path']).parent
    return {'fold_id':fold_id, 'summary':result, 'predictions_jsonl':(folder/'heldout_predictions.jsonl').read_text()}


@app.local_entrypoint()
def main():
    target = LOCAL/'private/returned'
    require(not target.exists(), 'already launched; reconcile existing jobs before any rerun')
    target.mkdir(parents=True)
    for result in train.map(range(1,6)):
        (target/f"fold_{result['fold_id']}.json").write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
        print('Completed E11-D fold',result['fold_id'],flush=True)
