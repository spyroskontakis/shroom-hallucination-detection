"""E7 paths, exclusive outputs, integrity checks and process-local access guard."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import os
import sys
import types

OUT = Path(__file__).resolve().parents[1]
ROOT = OUT.parents[2]
E6 = ROOT / 'RAG/results/rag_e6_v1'
RUN = ROOT / 'RAG/results/rag_module4/continuation_v1/schannel_run_v1'
CANONICAL = ROOT / 'codex/canonical_human_development_manifest.csv'
MIXED = ROOT / 'codex/canonical_feature_outputs/canonical_human_14_features.csv'
FOLDS = ROOT / 'codex/canonical_fold_assignments.csv'
FEATURES = E6 / 'features/e6_25_features.csv'
RANKING = E6 / 'ranking/reconstructed_top5.jsonl'
RAG = RUN / 'features/module4_rag_features.csv'
EVALUATOR = RUN / 'scripts/module4_evaluate_fusion.py'
GUARD = None


def now():
    return datetime.now(timezone.utc).isoformat()


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda: f.read(1 << 20), b''):
            h.update(block)
    return h.hexdigest()


def read_json(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def write_json(path, data):
    path = Path(path).resolve()
    path.relative_to(OUT)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x', encoding='utf-8', newline='\n') as f:
        json.dump(data, f, indent=2, sort_keys=True, ensure_ascii=False, allow_nan=False)
        f.write('\n')


def csv_write(path, frame):
    path = Path(path).resolve()
    path.relative_to(OUT)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x', encoding='utf-8', newline='') as f:
        frame.to_csv(f, index=False, lineterminator='\n')


class AccessGuard:
    def __init__(self, phase):
        self.phase = phase
        self.events = []
        self.probes = []
        self.reads = set()
        self.allowed = {str((ROOT / p).resolve()).casefold()
                        for p in read_json(OUT / 'config/protocol_freeze.json')['protected_sha256']}
        self.runtime_roots = [Path(sys.prefix).resolve(), Path(sys.base_prefix).resolve(),
                              Path(os.environ.get('WINDIR', 'C:/Windows')).resolve()]

    @staticmethod
    def within(path, parent):
        return path.is_relative_to(parent)

    def policy(self, event, args):
        if event in ('socket.connect', 'socket.connect_ex', 'socket.getaddrinfo',
                     'socket.bind', 'socket.sendto', 'socket.sendmsg'):
            raise PermissionError('E7 network forbidden')
        if event in ('subprocess.Popen', 'os.system', 'os.exec', 'os.posix_spawn'):
            raise PermissionError('E7 child process forbidden')
        if event == 'open':
            name, mode, flags = args
            if isinstance(name, int):
                return
            p = Path(os.fsdecode(name)).resolve()
            writing = bool((isinstance(mode, str) and any(c in mode for c in 'wax+')) or
                           (isinstance(flags, int) and flags & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC | os.O_APPEND)))
            if writing:
                if not self.within(p, OUT):
                    raise PermissionError('E7 write outside output directory forbidden')
            elif self.within(p, ROOT):
                if not self.within(p, OUT) and str(p).casefold() not in self.allowed:
                    raise PermissionError('Repository read not allowlisted')
            elif str(p).casefold() != str(Path(os.devnull).resolve()).casefold() and not any(self.within(p, r) for r in self.runtime_roots):
                raise PermissionError('External read not allowlisted')
        if event in ('os.remove', 'os.rmdir', 'os.mkdir', 'os.rename'):
            paths = args[:2] if event == 'os.rename' else args[:1]
            for name in paths:
                if not Path(os.fsdecode(name)).resolve().is_relative_to(OUT):
                    raise PermissionError('Filesystem mutation outside E7 forbidden')

    def hook(self, event, args):
        try:
            self.policy(event, args)
        except PermissionError as exc:
            self.events.append({'utc': now(), 'event': event, 'reason': str(exc)})
            raise
        if event == 'open' and not isinstance(args[0], int):
            p = Path(os.fsdecode(args[0])).resolve()
            if p.is_relative_to(ROOT) and not p.is_relative_to(OUT):
                self.reads.add(p.relative_to(ROOT).as_posix())

    def probe(self, event, args):
        try:
            self.policy(event, args)
        except PermissionError:
            self.probes.append({'event': event, 'blocked': True, 'synthetic': True})
            return True
        return False

    def save(self):
        write_json(OUT / f'config/security_{self.phase}.json', {
            'phase': self.phase, 'finished_utc': now(), 'operational_violations': self.events,
            'operational_network_attempts': sum(e['event'].startswith('socket.') for e in self.events),
            'synthetic_probes': self.probes, 'repository_reads': sorted(self.reads),
            'scope': 'Python audit hook; explicitly allowlisted files and libraries; not OS sandbox',
        })


def offline(phase):
    global GUARD
    for key in ('HF_HUB_OFFLINE', 'TRANSFORMERS_OFFLINE', 'HF_DATASETS_OFFLINE',
                'HF_HUB_DISABLE_TELEMETRY', 'PYTHONDONTWRITEBYTECODE'):
        os.environ[key] = '1'
    os.environ['JOBLIB_TEMP_FOLDER'] = str(OUT / 'runtime_tmp')
    GUARD = AccessGuard(phase)
    sys.addaudithook(GUARD.hook)
    return GUARD


def verify_integrity():
    freeze = read_json(OUT / 'config/protocol_freeze.json')
    assert sha(OUT / 'E7_PROTOCOL.md') == freeze['protocol_sha256'], 'Protocol changed'
    for p, expected in freeze['protected_sha256'].items():
        assert sha(ROOT / p) == expected, f'Frozen artifact changed: {p}'
    completion = read_json(E6 / 'config/completion_manifest.json')
    for p, expected in completion['files'].items():
        assert sha(E6 / p) == expected, f'E6 manifest mismatch: {p}'
    return freeze


def accepted_evaluator():
    # Read/compile the frozen source without creating or loading repository pycache.
    mod = types.ModuleType('accepted_module4_evaluator')
    exec(compile(EVALUATOR.read_text(encoding='utf-8'), str(EVALUATOR), 'exec'), mod.__dict__)
    return mod


def aligned_label_free():
    import numpy as np
    import pandas as pd
    ev = accepted_evaluator()
    columns = read_json(E6 / 'config/feature_freeze.json')['predictors']
    assert len(columns) == 25 and columns[:21] == ev.E3 + ev.RAG
    features = pd.read_csv(FEATURES, float_precision='round_trip')
    assert features.columns.tolist() == ['canonical_id'] + columns
    ids = features.canonical_id.tolist()
    assert len(ids) == len(set(ids)) == 561
    mixed = pd.read_csv(MIXED, usecols=['canonical_id', 'fold_id', 'task'] + ev.E3)
    folds = pd.read_csv(FOLDS, usecols=['canonical_id', 'fold_id'])
    canonical = pd.read_csv(CANONICAL, usecols=['canonical_id', 'task'])
    rag = pd.read_csv(RAG).rename(columns={'example_id': 'canonical_id'})
    for frame in (mixed, folds, canonical, rag):
        assert len(frame) == frame.canonical_id.nunique() == 561
        assert set(frame.canonical_id) == set(ids)
    assert mixed.canonical_id.tolist() == ids
    folds = folds.set_index('canonical_id').loc[ids].reset_index()
    canonical = canonical.set_index('canonical_id').loc[ids].reset_index()
    rag = rag.set_index('canonical_id').loc[ids].reset_index()
    assert np.array_equal(mixed.fold_id, folds.fold_id)
    assert np.array_equal(mixed.task, canonical.task)
    assert folds.fold_id.value_counts().sort_index().tolist() == [113,112,112,112,112]
    assert np.array_equal(features[ev.E3].to_numpy(float), mixed[ev.E3].to_numpy(float))
    assert np.array_equal(features[ev.RAG].to_numpy(float), rag[ev.RAG].to_numpy(float))
    assert np.isfinite(features[columns].to_numpy(float)).all()
    no = features.rag_evidence_available == 0
    assert (features.loc[no, columns[21:]] == 0).all().all()
    metadata = mixed[['canonical_id', 'fold_id', 'task']].copy()
    return features, metadata, columns, ev


def retrieval_metadata(ids):
    import math
    import pandas as pd
    rows = [json.loads(line) for line in RANKING.read_text(encoding='utf-8').splitlines() if line]
    assert len(rows) == len({r['canonical_id'] for r in rows}) == 561
    by_id = {r['canonical_id']: r for r in rows}
    assert set(by_id) == set(ids)
    result = []
    for cid in ids:
        r = by_id[cid]
        selected = r['selected']
        count = r['candidate_count']
        assert isinstance(count, int) and count >= 0
        assert len(selected) == min(count, 5)
        assert [s['rank'] for s in selected] == list(range(1,len(selected)+1))
        assert len({s['evidence_id'] for s in selected}) == len(selected)
        scores = [float(s['score']) for s in selected]
        assert all(math.isfinite(s) and -1.000000000001 <= s <= 1.000000000001 for s in scores)
        assert scores == sorted(scores, reverse=True)
        result.append({'canonical_id': cid, 'evidence_available': int(bool(selected)),
                       'candidate_count': count, 'selected_sense_count': len(selected),
                       'top1_cosine': scores[0] if scores else None,
                       'top2_cosine': scores[1] if len(scores)>1 else None,
                       'top1_minus_top2': scores[0]-scores[1] if len(scores)>1 else None})
    return pd.DataFrame(result)


def initial_preflight():
    import numpy as np
    import importlib.metadata
    from sklearn.ensemble import RandomForestRegressor
    freeze = verify_integrity()
    features, meta, columns, ev = aligned_label_free()
    signals = retrieval_metadata(meta.canonical_id.tolist())
    assert np.array_equal(signals.evidence_available, features.rag_evidence_available)
    assert np.array_equal(signals.selected_sense_count, features.rag_sense_count)
    assert np.allclose(signals.top1_cosine.fillna(0), features.rag_retrieval_top1_cosine, rtol=0, atol=1e-12)
    lock = read_json(E6 / 'config/run_config.json')
    assert RandomForestRegressor(n_estimators=500,random_state=42,n_jobs=-1).get_params() == lock['random_forest']
    expected = {'numpy':'2.4.4','pandas':'3.0.2','scipy':'1.17.1','scikit-learn':'1.8.0'}
    versions = {p: importlib.metadata.version(p) for p in expected}
    assert versions == expected, versions
    assert sys.version_info[:3] == (3,11,9)
    return {'status':'PASS','checked_utc':now(),'rows':561,'unique_ids':561,
            'fold_sizes':[113,112,112,112,112],'e3_predictors':ev.E3,'e6_predictors':columns,
            'evidence_rows':int(signals.evidence_available.sum()),'labels_projected':False,
            'protocol_sha256':freeze['protocol_sha256'],'protected_count':len(freeze['protected_sha256']),
            'packages':versions,'python':sys.version,'executable':sys.executable,
            'random_forest':lock['random_forest']}
