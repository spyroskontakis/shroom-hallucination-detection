"""Reconstruct the frozen ranking, then encode definition-to-hyp features offline."""
import json
import time
import unicodedata
from collections import defaultdict
import numpy as np
import pandas as pd
from e6_common import *


def reconstruct(rows, records, embed):
    """Only query metadata, term and src are accepted; no target/answer/labels."""
    frozen.validate_snapshot(records)
    by_term = defaultdict(list)
    for r in records:
        by_term[r['term_key']].append(r)
    result = []
    allowed = {'example_id', 'task', 'term', 'src', 'rag_applicable'}
    for row in rows:
        if set(row) != allowed:
            raise ValueError('Ranking accepts exactly the label-free query projection')
        candidates = []
        if row['task'] == 'DM' and str(row['rag_applicable']) in ('1', 'True', 'true'):
            key = unicodedata.normalize('NFKC', row['term']).strip().casefold()
            candidates = by_term.get(key, [])
        query = f"{row['term']}\n{row['src']}"
        selected = frozen.select_top5(query, candidates, embed) if candidates else []
        result.append({
            'canonical_id': row['example_id'], 'candidate_count': len(candidates),
            'query_sha256': hashlib.sha256(query.encode('utf-8')).hexdigest(),
            'selected': [{'rank': rank, 'score': score, **candidate}
                         for rank, (candidate, score) in enumerate(selected, 1)],
        })
    return result


def compare_hyp(definition, hyp, embed, nli):
    if definition is None:
        return dict.fromkeys(NEW, 0.0)
    # Same normalization/precision and semantic text policy as Module 4.
    matrix = np.asarray(embed([hyp, definition]), dtype=float)
    matrix = matrix / np.maximum(np.linalg.norm(matrix, axis=1, keepdims=True), 1e-12)
    cosine = float((matrix[1:] @ matrix[0])[0])
    scores = nli([(definition, hyp)])[0]
    return dict(zip(NEW, [cosine, scores['entailment'], scores['neutral'], scores['contradiction']]))


def main():
    offline()
    lock = verify_lock()
    if (OUT / 'config/feature_freeze.json').exists():
        raise FileExistsError('Features already frozen; do not rerun')
    started = now()
    t0 = time.perf_counter()
    # No tgt, hyp or evaluation data is projected into ranking inputs.
    rows = pd.read_csv(INPUTS, dtype=str, keep_default_na=False,
                       usecols=['example_id', 'task', 'term', 'src', 'rag_applicable']).to_dict('records')
    assert len(rows) == len({r['example_id'] for r in rows}) == 561
    records = [json.loads(line) for line in SNAPSHOT.read_text(encoding='utf-8').splitlines() if line]
    embed, nli = frozen.real_backends('cpu')
    print('Pinned local MPNet/NLI loaded; reconstructing ranking.', flush=True)
    ranking = reconstruct(rows, records, embed)
    derived = pd.DataFrame([{'example_id': r['canonical_id'],
                             'rag_evidence_available': int(bool(r['selected'])),
                             'rag_sense_count': len(r['selected']),
                             'rag_retrieval_top1_cosine': r['selected'][0]['score'] if r['selected'] else 0.0}
                            for r in ranking])
    accepted = pd.read_csv(RAG)
    assert derived.example_id.tolist() == accepted.example_id.tolist()
    for col in ['rag_evidence_available', 'rag_sense_count']:
        assert np.array_equal(derived[col], accepted[col]), col
    diff = np.abs(derived.rag_retrieval_top1_cosine - accepted.rag_retrieval_top1_cosine)
    assert np.allclose(derived.rag_retrieval_top1_cosine, accepted.rag_retrieval_top1_cosine,
                       rtol=0, atol=lock['ranking']['consistency_atol']), float(diff.max())
    ranking_path = OUT / 'ranking/reconstructed_top5.jsonl'
    ranking_path.parent.mkdir(parents=True, exist_ok=True)
    with ranking_path.open('x', encoding='utf-8', newline='\n') as f:
        for row in ranking:
            f.write(json.dumps(row, sort_keys=True, ensure_ascii=False) + '\n')
    csv_write(OUT / 'ranking/reconstructed_aggregates.csv', derived)
    ranking_check = {
        'frozen_utc': now(), 'status': 'PASS', 'rows': 561,
        'evidence_rows': int(derived.rag_evidence_available.sum()),
        'availability_equal': True, 'sense_count_equal': True,
        'top1_cosine_max_absolute_difference': float(diff.max()),
        'top1_cosine_bitwise_numeric_equal': bool(np.array_equal(derived.rag_retrieval_top1_cosine, accepted.rag_retrieval_top1_cosine)),
        'atol': 1e-12, 'rtol': 0, 'ranking_sha256': sha(ranking_path),
        'historical_ranking_available': False,
        'limitation': 'Aggregate agreement checks consistency but does not prove the complete historical ordering.',
        'seconds': time.perf_counter() - t0,
    }
    write_json(OUT / 'config/ranking_consistency.json', ranking_check)
    print(json.dumps(ranking_check), flush=True)
    # Ranking is saved and frozen before hyp access. No labels are read here.
    canonical = pd.read_csv(CANONICAL, usecols=['canonical_id', 'task', 'src', 'hyp'], keep_default_na=False)
    assert canonical.canonical_id.nunique() == len(canonical) == 561
    assert set(canonical.canonical_id) == {r['canonical_id'] for r in ranking}
    by_id = canonical.set_index('canonical_id')
    for row in rows:
        c = by_id.loc[row['example_id']]
        assert c.task == row['task'] and c.src == row['src']
    out = []
    for i, row in enumerate(ranking):
        definition = row['selected'][0]['candidate_definition'] if row['selected'] else None
        hyp = by_id.loc[row['canonical_id'], 'hyp']
        out.append({'canonical_id': row['canonical_id'], **compare_hyp(definition, hyp, embed, nli)})
        if (i + 1) % 50 == 0:
            print(f'New features: {i + 1}/561 rows', flush=True)
    extra = pd.DataFrame(out)
    assert np.isfinite(extra[NEW].to_numpy()).all()
    assert (extra.loc[derived.rag_evidence_available.to_numpy() == 0, NEW] == 0).all().all()
    probabilities = extra.loc[derived.rag_evidence_available.to_numpy() == 1, NEW[1:]].to_numpy()
    assert (probabilities >= 0).all() and (probabilities <= 1).all()
    assert np.allclose(probabilities.sum(axis=1), 1, atol=2e-7, rtol=0)
    base14 = pd.read_csv(MIXED, usecols=['canonical_id'] + evaluator.E3)
    base = base14.merge(accepted.rename(columns={'example_id': 'canonical_id'}),
                        on='canonical_id', validate='one_to_one', sort=False)
    old_fused = pd.read_csv(FUSED)
    assert base.canonical_id.tolist() == old_fused.canonical_id.tolist()
    base_diff = np.abs(base[evaluator.E3 + evaluator.RAG].to_numpy() - old_fused[evaluator.E3 + evaluator.RAG].to_numpy())
    assert base_diff.max() <= 1e-15, float(base_diff.max())
    features = base.merge(extra, on='canonical_id', validate='one_to_one', sort=False)[['canonical_id'] + FEATURES]
    assert len(features) == 561 and len(FEATURES) == 25
    csv_write(OUT / 'features/e6_added_4_features.csv', extra)
    csv_write(OUT / 'features/e6_25_features.csv', features)
    inputs_hyp = canonical[['canonical_id', 'hyp']]
    csv_write(OUT / 'features/hyp_inputs_label_free.csv', inputs_hyp)
    verify_lock()
    assert (OUT / 'config/network_attempts.jsonl').stat().st_size == 0
    write_json(OUT / 'config/feature_freeze.json', {
        'started_utc': started, 'frozen_utc': now(), 'status': 'FEATURE_MATRIX_FROZEN_BEFORE_EVALUATION_LABEL_JOIN',
        'duration_seconds': time.perf_counter() - t0, 'rows': 561, 'predictors': FEATURES,
        'e5_fused_serialization_max_absolute_difference': float(base_diff.max()),
        'ranking_sha256': sha(ranking_path), 'network_attempts': 0,
        'files': {str(p.relative_to(OUT)).replace('\\', '/'): sha(p) for p in
                  [OUT / 'features/e6_added_4_features.csv', OUT / 'features/e6_25_features.csv',
                   OUT / 'features/hyp_inputs_label_free.csv', OUT / 'config/ranking_consistency.json']},
    })
    print('E6 561 x 25 feature matrix frozen; no labels joined.', flush=True)


if __name__ == '__main__':
    main()
