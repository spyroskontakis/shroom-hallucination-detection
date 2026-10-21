"""Read-only baseline reconciliation and one-time E11-D freeze. No training."""
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
E11 = HERE.parent
sys.path.insert(0, str(E11))
sys.path.insert(0, str(E11 / 'e11a_results'))
from scoring_common import ROOT, sha_file, require
from e11a_prepare_data import load_protocol
from validate_e11a_protocol import validate_local, read_jsonl
from assemble_e11a_results import metric, baseline, rows_csv


def save(path, value):
    data = json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + '\n'
    if path.exists():
        require(path.read_text(encoding='utf-8') == data, 'refusing artifact overwrite: ' + str(path))
    else:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(data, encoding='utf-8', newline='\n')


def baselines():
    spec = load_protocol()
    require(sha_file(ROOT/spec['data']['canonical_path']) == spec['data']['canonical_sha256'] and
            sha_file(ROOT/spec['data']['folds_path']) == spec['data']['folds_sha256'], 'canonical/fold source integrity')
    human = {r['canonical_id']: r for r in rows_csv(ROOT / spec['data']['canonical_path'])}
    folds = {r['canonical_id']: int(r['fold_id']) for r in rows_csv(ROOT / spec['data']['folds_path'])}
    result = {}
    for name, result_path, oof in (
        ('E11-A', E11/'e11a_results/E11A_RESULTS.json', E11/'e11a_results/E11A_OOF_PREDICTIONS.jsonl'),
        ('E11-C', E11/'e11c_training/E11C_RESULTS.json', E11/'e11c_training/private/E11C_OOF_PREDICTIONS.jsonl')):
        saved = json.loads(result_path.read_text())
        rows = read_jsonl(oof)
        require(len(rows) == len({r['sample_id'] for r in rows}) == 561 and {r['sample_id'] for r in rows} == set(human), name+' IDs')
        require(all(r['fold_id'] == folds[r['sample_id']] for r in rows), name+' folds')
        computed = metric(rows, human)
        for key in ('correct', 'accuracy', 'spearman'):
            require(abs(computed[key] - saved['overall'][key]) < 1e-14, name+' metric mismatch')
        result[name] = {**computed, 'result_sha256': sha_file(result_path), 'oof_sha256': sha_file(oof)}
    folder = ROOT/'RAG/results/phase3_e9_claim_verification/evaluation/E10'
    saved = json.loads((folder/'E10_metrics.json').read_text())['metrics']['overall']
    expected = {'correct': round(saved['accuracy'] * 561), 'accuracy': saved['accuracy'], 'spearman': saved['spearman']}
    result['E10'] = baseline('E10', folder/'E10_oof.csv', folder/'E10_metrics.json', expected, human, folds)
    result['E10'].pop('scores')
    return result, human, folds


def protected_files():
    # Hash prior experiments, excluding only interpreter caches; no official-test files.
    roots = [E11/'e11a_results', E11/'e11a_prepared', E11/'e11c', E11/'e11c_training', ROOT/'RAG/results/phase3_e9_claim_verification/evaluation/E10']
    paths = [p for folder in roots for p in folder.rglob('*') if p.is_file() and '__pycache__' not in p.parts]
    paths += [p for p in E11.iterdir() if p.is_file()]
    return {str(p.relative_to(ROOT)).replace('\\', '/'): sha_file(p) for p in sorted(set(paths))}


def main():
    require(not (HERE/'private/returned').exists(), 'training already launched')
    checked = validate_local()
    bases, human, folds = baselines()
    spec = load_protocol()
    design = {
        'experiment': 'E11-D', 'status': 'FROZEN_BEFORE_TRAINING',
        'classification': 'Identical E11-A fold-weighted torch.nn.CrossEntropyLoss',
        'formula': 'mean_i[(1-y_i)*(1-cos(a_i,b_i)) + y_i*max(0,cos(a_i,b_i)-margin)]',
        'total_loss': 'weighted_CE + lambda * contrastive', 'lambda': 0.1, 'margin': 0.0,
        'temperature': None, 'normalization': 'cosine L2 normalization, eps=1e-8, float32',
        'representation': 'Final encoder layer; mean pool each paired sequence using fast-tokenizer sequence_ids; exclude special and padding tokens; include frozen textual prefixes.',
        'contextualization': 'Both representations are contextualized jointly by the original cross-encoder pair; no independent encoder passes.',
        'positive': 'label 0 not_hallucination: minimize 1-cos',
        'negative': 'label 1 hallucination: penalize cosine above zero',
        'rationale': 'Simple standard pairwise cosine embedding objective with modest fixed auxiliary weight; no projection head, mined pairs, alternatives or parameter selection.',
        'e11a_protocol_sha256': spec['protocol_sha256'], 'fits': 5, 'seed': 42,
        'data': spec['data'], 'model': spec['model'], 'input': spec['input'],
        'reference_policy': spec['reference_policy'], 'training': spec['training'], 'output': spec['output'],
        'synthetic_rows': 0, 'hyperparameter_search': False,
    }
    save(HERE/'E11D_LOSS_PROTOCOL.json', design)
    from transformers import AutoTokenizer
    from contrastive import sequence_masks
    tok = AutoTokenizer.from_pretrained(str(ROOT/spec['model']['local_mirror_dir']), local_files_only=True, use_fast=True)
    rows = [r for f in range(1,6) for r in read_jsonl(E11/f'e11a_prepared/fold_{f}/heldout.jsonl')]
    encoded = tok([r['text'] for r in rows], [r['text_pair'] for r in rows], add_special_tokens=True, truncation='longest_first', max_length=512, padding=False)
    masks = sequence_masks(encoded)
    require(len(masks) == 561, 'tokenizer coverage')
    tests = json.loads((HERE/'PRETRAINING_TESTS.json').read_text())
    require(tests['status'] == 'PASS', 'tests must pass')
    protected = protected_files()
    save(HERE/'private/PRESERVED_SHA256.json', protected)
    audit = {'status': 'PASS', 'frozen_utc': datetime.now(timezone.utc).isoformat(), 'e11a_validation': checked,
             'baselines': bases, 'human_rows': 561, 'synthetic_rows': 0, 'same_folds_and_text_bytes': True,
             'official_test_access': False, 'teacher_calls': 0, 'fits_before_freeze': 0,
             'tokenizer_masks_checked': len(masks), 'minimum_sequence_tokens': min(sum(m) for pair in masks for m in pair),
             'loss_protocol_sha256': sha_file(HERE/'E11D_LOSS_PROTOCOL.json'), 'tests': tests,
             'protected_files': len(protected), 'preservation_snapshot_sha256': sha_file(HERE/'private/PRESERVED_SHA256.json'),
             'evaluator_sha256': sha_file(E11/'e11a_results/assemble_e11a_results.py'),
             'changes_from_A': ['Additional fixed contrastive objective; same paired forward, architecture and classifier.'],
             'training_configuration': spec['training']}
    save(HERE/'E11D_PRETRAINING_AUDIT.json', audit)
    (HERE/'E11D_PRETRAINING_AUDIT.md').write_text('# E11-D pretraining audit: PASS\n\nHuman-only: same 561 rows, exact E11-A input bytes and five folds. No synthetic examples or official test access. Baselines recomputed from repository OOF artifacts.\n\nCosine embedding loss, lambda 0.1, margin 0; mean pooled final-layer paired-sequence representations, excluding padding/special tokens and including existing text prefixes. Joint cross-encoder context; no projection or extra model forward.\n\nAll E11-A model/revision, tokenizer, 512-token limit, seed 42, AdamW, LR 1e-5, weighted CE, batch 8/accumulation 2, five epochs, BF16, scheduler, final checkpoint and probability extraction settings are unchanged. Full configuration and hashes are in the JSON audit and loss protocol.\n\nOffline tests passed before freezing. Exactly five fits authorized. No search or extra smoke fit.\n', encoding='utf-8')
    print('PASS: pretraining frozen; human-only 561 rows; baselines verified; no fits started.')


if __name__ == '__main__':
    main()
