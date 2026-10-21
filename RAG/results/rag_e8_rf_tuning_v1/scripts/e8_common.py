"""E8 paths, exclusive outputs, integrity checks and process-local access guard."""
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
        self.diagnostic_path = OUT / f'config/write_guard_diagnostics_{phase}.jsonl'
        with self.diagnostic_path.open('x', encoding='utf-8'):
            pass
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
            raise PermissionError('E8 network forbidden')
        if event in ('subprocess.Popen', 'os.system', 'os.exec', 'os.posix_spawn'):
            raise PermissionError('E8 child process forbidden')
        if event == 'open':
            name, mode, flags = args
            if isinstance(name, int):
                return
            p = Path(os.fsdecode(name)).resolve()
            writing = bool((isinstance(mode, str) and any(c in mode for c in 'wax+')) or
                           (isinstance(flags, int) and flags & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC | os.O_APPEND)))
            if writing:
                if not self.within(p, OUT):
                    raise PermissionError('E8 write outside output directory forbidden')
            elif self.within(p, ROOT):
                if not self.within(p, OUT) and str(p).casefold() not in self.allowed:
                    raise PermissionError('Repository read not allowlisted')
            elif str(p).casefold() != str(Path(os.devnull).resolve()).casefold() and not any(self.within(p, r) for r in self.runtime_roots):
                raise PermissionError('External read not allowlisted')
        if event in ('os.remove', 'os.rmdir', 'os.mkdir', 'os.rename'):
            paths = args[:2] if event == 'os.rename' else args[:1]
            for name in paths:
                if not Path(os.fsdecode(name)).resolve().is_relative_to(OUT):
                    raise PermissionError('Filesystem mutation outside E8 forbidden')

    def hook(self, event, args):
        try:
            self.policy(event, args)
        except PermissionError as exc:
            # Inspect frames directly: traceback formatting can read source files
            # and recursively trigger this access guard while handling a denial.
            stack = []
            frame = sys._getframe(1)
            while frame is not None:
                stack.append({'file': frame.f_code.co_filename,
                              'line': frame.f_lineno, 'function': frame.f_code.co_name})
                frame = frame.f_back
            detail = {'utc': now(), 'event': event, 'reason': str(exc),
                      'pid': os.getpid(), 'cwd': os.getcwd(), 'stack': stack,
                      'environment': {k: os.environ.get(k) for k in
                                      ('TMP','TEMP','TMPDIR','PYTHONDONTWRITEBYTECODE',
                                       'JOBLIB_TEMP_FOLDER','HF_HOME','TRANSFORMERS_CACHE',
                                       'SENTENCE_TRANSFORMERS_HOME')}}
            if event == 'open' and not isinstance(args[0], int):
                detail.update(attempted_absolute_path=str(Path(os.fsdecode(args[0])).resolve()),
                              operation='open', mode=args[1], flags=args[2])
            elif event in ('os.remove','os.rmdir','os.mkdir','os.rename'):
                detail.update(attempted_absolute_path=str(Path(os.fsdecode(args[0])).resolve()),
                              operation=event)
            self.events.append(detail)
            with self.diagnostic_path.open('a', encoding='utf-8', newline='\n') as log:
                log.write(json.dumps(detail, ensure_ascii=False) + '\n')
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
    suppress_optional_windows_shell_probe()
    return GUARD


def suppress_optional_windows_shell_probe():
    """Use platform.win32_ver's native fallback, without its optional ver shell.

    Python 3.11.9 platform._syscmd_ver tries three subprocess commands and
    opens os.devnull O_RDWR for their stdio. The existing guard correctly
    blocks those operations. Returning the helper's documented defaults
    directly selects win32_ver's existing sys.getwindowsversion fallback.
    No platform/library source file, filesystem permission or model is changed.
    """
    if sys.platform != 'win32':
        return
    import platform
    if sys.version_info[:3] != (3, 11, 9):
        raise RuntimeError('Windows shell-probe adapter requires reviewed Python 3.11.9')

    def no_shell_ver(system='', release='', version='',
                     supported_platforms=('win32', 'win16', 'dos')):
        return system, release, version

    platform._syscmd_ver = no_shell_ver


def verify_integrity():
    freeze = read_json(OUT / 'config/protocol_freeze.json')
    assert sha(OUT / 'E8_PROTOCOL.md') == freeze['protocol_sha256'], 'Protocol changed'
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


