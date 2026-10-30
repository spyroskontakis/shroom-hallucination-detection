"""Freeze the explicit runtime file allowlist after the pretraining audit."""
from prepare import HERE, E11, save, sha_file, require
import json

def main():
    require(json.loads((HERE/'E11D_PRETRAINING_AUDIT.json').read_text())['status']=='PASS', 'audit')
    files = {}
    for name in ('scoring_common.py','e11a_prepare_data.py','validate_e11a_protocol.py','E11A_TRAINING_PROTOCOL.json','E11A_PREPARATION_MANIFEST.json','E11A_REQUIREMENTS.lock.txt'):
        files[name]={'local_path':'../'+name,'sha256':sha_file(E11/name)}
    for f in range(1,6):
        for split in ('train','heldout'):
            name=f'e11a_prepared/fold_{f}/{split}.jsonl'
            files[name]={'local_path':'../'+name,'sha256':sha_file(E11/name)}
    for name in ('train_fold.py','contrastive.py','E11D_LOSS_PROTOCOL.json','E11D_PRETRAINING_AUDIT.json'):
        files[name]={'local_path':name,'sha256':sha_file(HERE/name)}
    save(HERE/'RUNTIME_MANIFEST.json', files)
    print('PASS: runtime allowlist frozen; only E11-A human split files uploaded.')

if __name__=='__main__': main()
