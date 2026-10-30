"""Five independent two-stage E11-E jobs; exactly ten fits, automatic retries off."""
import json
import sys
from pathlib import Path
import modal

REMOTE='/opt/e11e'
LOCAL=Path(__file__).resolve().parent if modal.is_local() else Path(REMOTE)
if str(LOCAL) not in sys.path:sys.path.insert(0,str(LOCAL))
from train_stages import execute,require,sha_file


def image_definition():
    import shutil
    e11=LOCAL.parent
    require(json.loads((LOCAL/'E11E_PRETRAINING_AUDIT.json').read_text())['status']=='PASS','pretraining audit')
    spec=json.loads((LOCAL/'E11E_TRAINING_PROTOCOL.json').read_text())
    manifest=json.loads((LOCAL/'RUNTIME_MANIFEST.json').read_text())
    bundle=LOCAL/'private/runtime_bundle'
    require(not bundle.exists(),'runtime bundle already staged; reconcile prior launch')
    bundle.mkdir(parents=True)
    for name,digest in manifest.items():
        require(sha_file(LOCAL/name)==digest,'frozen runtime source drift')
        shutil.copyfile(LOCAL/name,bundle/name)
    shutil.copyfile(LOCAL/'RUNTIME_MANIFEST.json',bundle/'RUNTIME_MANIFEST.json')
    for fold in range(1,6):
        for name,digest in spec['folds'][str(fold)]['files_sha256'].items():
            relative=Path(f'private/fold_{fold}')/name
            require(sha_file(LOCAL/relative)==digest,'prepared split drift')
            (bundle/relative).parent.mkdir(parents=True,exist_ok=True)
            shutil.copyfile(LOCAL/relative,bundle/relative)
    require(sha_file(e11/'E11A_REQUIREMENTS.lock.txt')==spec['requirements_sha256'],'dependency lock')
    image=modal.Image.debian_slim(python_version='3.11')
    image=image.add_local_file(str(e11/'E11A_REQUIREMENTS.lock.txt'),f'{REMOTE}/requirements.txt',copy=True)
    image=image.run_commands(f'python -m pip install --no-cache-dir -r {REMOTE}/requirements.txt','python -m pip check')
    image=image.add_local_dir(str(bundle),REMOTE,copy=True)
    return image.add_local_dir(str(e11.parents[2]/spec['model']['local_mirror_dir']),f'{REMOTE}/model',copy=True)


image=image_definition() if modal.is_local() else modal.Image.debian_slim(python_version='3.11')
app=modal.App('shroom-e11e-fixed-two-stage-contrastive')
volume=modal.Volume.from_name('shroom-e11e-fixed-two-stage-contrastive-results',create_if_missing=True)


@app.function(image=image,gpu='A100-80GB',cpu=8,memory=65536,ephemeral_disk=524288,
              timeout=14400,volumes={'/results':volume},max_containers=5,retries=0)
def train(fold_id):
    bundle=Path(REMOTE);output=Path('/results/e11e-fixed-001')
    manifest=json.loads((bundle/'RUNTIME_MANIFEST.json').read_text())
    for name,digest in manifest.items():require(sha_file(bundle/name)==digest,'runtime integrity')
    summaries=[]
    for stage in (1,2):
        model=bundle/'model' if stage==1 else output/f'fold_{fold_id}/stage_1/final_checkpoint'
        summary=execute(fold_id,stage,bundle,model,output)
        volume.commit();summaries.append(summary)
        print(f'E11-E fold {fold_id} stage {stage} saved; rows {summary["training_rows_used"]}',flush=True)
    predictions=(output/f'fold_{fold_id}/stage_2/heldout_predictions.jsonl').read_text()
    return {'fold_id':fold_id,'stages':summaries,'predictions_jsonl':predictions}


@app.local_entrypoint()
def main():
    target=LOCAL/'private/returned'
    require(not target.exists(),'previous launch exists; reconcile jobs instead of duplicating fits')
    target.mkdir(parents=True)
    for result in train.map(range(1,6)):
        with (target/f'fold_{result["fold_id"]}.json').open('x',encoding='utf-8') as out:
            json.dump(result,out,indent=2);out.write('\n')
        print('Completed E11-E fold',result['fold_id'],'both stages',flush=True)
