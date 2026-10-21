"""Reuse the exact E6-v2 NLI backend locally. No inference occurs on import."""
import json
import os
import sys
import pandas as pd
import e9_common as c
from aggregates import nli, append_features
from verify_baseline import verify
from decomposer import MODEL, VERSION, cache_key, validate


def main():
    metadata, baseline, _, _, _ = verify()
    from run_decomposition import frozen_check
    frozen_check()
    stats = c.read_json(c.OUT / 'reports/full_decomposition_stats.json')
    c.require(stats['status'] == 'PASS' and stats['samples'] == 561, 'decomposition incomplete')
    c.require(c.sha(c.OUT / 'claims/full_claims.jsonl') == stats['full_claims_sha256'], 'claims hash changed')
    c.require(not (c.OUT / 'features/E9-A.csv').exists(), 'E9-A features already exist; no rerun')
    claims = [json.loads(line) for line in (c.OUT / 'claims/full_claims.jsonl').read_text(encoding='utf-8').splitlines()]
    frame = pd.DataFrame(claims)
    c.require(set(frame.canonical_id) == set(baseline.canonical_id), 'exact claim population')
    # Validate every row against its cached hypothesis-only decomposition before NLI.
    for row in metadata.itertuples():
        group = frame[frame.canonical_id == row.canonical_id]
        value = {'hyp': row.hyp, 'task': row.task}
        digest = cache_key(value)
        cached = c.read_json(c.OUT / f'claims/cache/{digest}.json')
        expected = [row.hyp] if cached['decomposition_fallback'] else validate(cached['raw_output'], row.hyp)
        c.require(group.claim_index.tolist() == list(range(len(expected))) and group.claim_text.tolist() == expected, 'claim order/content')
        c.require((group.task == row.task).all() and (group.cache_hash == digest).all(), 'claim provenance')
        c.require((group.model_snapshot == MODEL).all() and (group.prompt_version == VERSION).all(), 'decomposer identity')
    for name in ['HF_HUB_OFFLINE', 'TRANSFORMERS_OFFLINE', 'HF_DATASETS_OFFLINE']:
        os.environ[name] = '1'
    sys.path.insert(0, str(c.V2 / 'scripts'))
    import v2_common
    import nli_backend
    acquisition = c.read_json(c.V2 / 'provenance/acquisition.json')
    # Verify only pinned NLI model assets; do not invoke broad legacy input traversal.
    c.require(acquisition['model_id'] == v2_common.MODEL_ID and acquisition['revision'] == v2_common.REVISION, 'NLI identity')
    for entry in acquisition['files'].values():
        c.require(c.sha(c.V2 / entry['path']) == entry['sha256'], 'NLI asset hash')
    c.write_json(c.OUT / 'features/nli_started.json', {'model_id': v2_common.MODEL_ID,
                 'revision': v2_common.REVISION, 'claim_count': len(frame)})
    import torch
    torch.set_num_threads(4)
    torch.set_num_interop_threads(4)
    tokenizer, model = nli_backend.load_backend()
    records = []
    for row in metadata.itertuples():
        group = frame[frame.canonical_id == row.canonical_id]
        reference = row.src if row.task == 'PG' else row.tgt
        c.require(isinstance(reference, str) and bool(reference.strip()), 'missing reference')
        pairs = [{'pair_id': f'{row.canonical_id}:{claim.claim_index}', 'canonical_id': row.canonical_id,
                  'group': 'claim', 'premise': reference, 'hypothesis': claim.claim_text} for claim in group.itertuples()]
        scores = []
        for start in range(0, len(pairs), 2):
            batch, audit = nli_backend.infer_batch(tokenizer, model, pairs[start:start+2])
            scores.extend(batch)
            # Row-level score and truncation audits are local-only JSONL.
            with (c.OUT / 'features/nli_claim_audit.jsonl').open('a', encoding='utf-8') as handle:
                handle.write(json.dumps({'scores': batch, 'truncation': audit}) + '\n')
        records.append({'canonical_id': row.canonical_id, **nli([[s[k] for k in ['entailment', 'neutral', 'contradiction']] for s in scores])})
        if len(records) % 20 == 0 or len(records) == 561:
            print(f'NLI feature extraction: {len(records)}/561 samples', flush=True)
    matrix = append_features(baseline, pd.DataFrame(records), c.A)
    verify()
    with (c.OUT / 'features/E9-A.csv').open('x', encoding='utf-8', newline='') as handle:
        matrix.to_csv(handle, index=False)
    frozen_check()
    c.write_json(c.OUT / 'features/E9-A_freeze.json', {'status': 'PASS', 'samples': 561,
        'feature_count': 44, 'claims_scored': len(frame), 'features_sha256': c.sha(c.OUT / 'features/E9-A.csv'),
        'audit_sha256': c.sha(c.OUT / 'features/nli_claim_audit.jsonl'),
        'claims_sha256': stats['full_claims_sha256'], 'model': v2_common.MODEL_ID, 'revision': v2_common.REVISION})


if __name__ == '__main__':
    main()
