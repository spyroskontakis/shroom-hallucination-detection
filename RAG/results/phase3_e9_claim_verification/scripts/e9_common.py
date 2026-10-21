"""Fixed development-only inputs and immutable E9 outputs; no dataset discovery."""
from pathlib import Path
import hashlib
import json
import numpy as np
from scipy.stats import spearmanr, binomtest

OUT = Path(__file__).resolve().parents[1]
ROOT = OUT.parents[2]
V3 = ROOT / 'RAG/results/rag_e6_v3'
V2 = ROOT / 'RAG/results/rag_e6_v2'
CANONICAL = ROOT / 'codex/canonical_human_development_manifest.csv'
FOLDS = ROOT / 'codex/canonical_fold_assignments.csv'
A = ['claim_count', 'claim_entailment_mean', 'claim_entailment_min',
     'claim_contradiction_mean', 'claim_contradiction_max', 'claim_neutral_mean',
     'claim_unsupported_ratio', 'claim_min_entailment_contradiction_margin']
B = ['minicheck_support_mean', 'minicheck_support_min', 'minicheck_support_max',
     'minicheck_support_std', 'minicheck_unsupported_ratio']


def require(condition, message):
    if not condition:
        raise ValueError(message)


def read_json(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write_json(path, value):
    path = Path(path).resolve()
    path.relative_to(OUT)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x', encoding='utf-8') as handle:
        json.dump(value, handle, indent=2, ensure_ascii=False, allow_nan=False)
        handle.write('\n')


def metric(y, target, predictions):
    y, target, p = np.asarray(y), np.asarray(target), np.asarray(predictions, float)
    require(len(y) == len(target) == len(p) and len(p) > 0, 'metric population')
    require(np.isfinite(p).all() and ((p >= 0) & (p <= 1)).all(), 'prediction range')
    correct = int(((p >= .5).astype(int) == y).sum())
    ranked = np.round(p, 12)
    rho = float(spearmanr(target, ranked).statistic) if len(set(target)) > 1 and len(set(ranked)) > 1 else None
    return dict(n=len(p), correct=correct, accuracy=correct / len(p), spearman=rho)


def diagnostics(metadata, predictions):
    def one(indices):
        rows = metadata.iloc[indices]
        return metric(rows.label_bin, rows.p_hallucination, np.asarray(predictions)[indices])
    return {'overall': one(np.arange(len(metadata))),
            'per_fold': {str(k): one(v) for k, v in metadata.groupby('fold_id').indices.items()},
            'per_task': {str(k): one(v) for k, v in metadata.groupby('task').indices.items()}}


def paired(y, old, new):
    old = (np.asarray(old) >= .5).astype(int) == np.asarray(y)
    new = (np.asarray(new) >= .5).astype(int) == np.asarray(y)
    corrections, regressions = int((~old & new).sum()), int((old & ~new).sum())
    delta = new.astype(int) - old.astype(int)
    rng = np.random.default_rng(42)
    draws = [delta[rng.integers(0, len(delta), len(delta))].mean() for _ in range(10000)]
    return {'corrections': corrections, 'regressions': regressions,
            'net_correct': corrections - regressions,
            'mcnemar_exact_p': float(binomtest(corrections, corrections + regressions, .5).pvalue) if corrections + regressions else 1.,
            'accuracy_difference': float(delta.mean()),
            'bootstrap_95_ci': np.quantile(draws, [.025, .975]).tolist(),
            'bootstrap_seed': 42, 'bootstrap_samples': 10000}
