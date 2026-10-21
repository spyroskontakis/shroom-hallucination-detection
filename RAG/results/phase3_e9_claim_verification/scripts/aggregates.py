"""Label-free fixed aggregations and strict append-only feature contracts."""
import numpy as np
import e9_common as c


def nli(values):
    p = np.asarray(values, float)
    c.require(p.ndim == 2 and p.shape[1] == 3 and len(p) > 0, 'nonempty NLI claims')
    c.require(np.isfinite(p).all() and ((p >= 0) & (p <= 1)).all(), 'NLI probability range')
    c.require(np.allclose(p.sum(axis=1), 1, atol=2e-7, rtol=0), 'NLI normalization')
    e, n, x = p.T
    return dict(zip(c.A, [len(p), e.mean(), e.min(), x.mean(), x.max(), n.mean(),
                         (p.argmax(axis=1) != 0).mean(), (e-x).min()]))


def minicheck(values):
    p = np.asarray(values, float)
    c.require(p.ndim == 1 and len(p) > 0, 'nonempty MiniCheck claims')
    c.require(np.isfinite(p).all() and ((p >= 0) & (p <= 1)).all(), 'MiniCheck probability range')
    return dict(zip(c.B, [p.mean(), p.min(), p.max(), p.std(ddof=0), (p < .5).mean()]))


def append_features(base, extra, names):
    c.require(extra.columns.tolist() == ['canonical_id'] + names, 'new feature order')
    c.require(len(extra) == extra.canonical_id.nunique() == 561, 'claim rows cannot disappear')
    c.require(base.canonical_id.tolist() == extra.canonical_id.tolist(), 'append ID order')
    c.require(not set(names).intersection(base.columns), 'duplicate features')
    result = base.copy()
    for name in names:
        result[name] = extra[name].to_numpy()
    c.require(np.array_equal(result[base.columns].to_numpy(), base.to_numpy()), 'baseline values changed')
    c.require(np.isfinite(result.iloc[:, 1:].to_numpy(float)).all(), 'nonfinite feature')
    return result
