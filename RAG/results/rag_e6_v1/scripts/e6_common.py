"""Fixed paths, schemas and read-only imports for the single E6 experiment."""
from pathlib import Path
import hashlib
import importlib.util
import json
import os
import socket
from datetime import datetime, timezone

OUT = Path(__file__).resolve().parents[1]
ROOT = OUT.parents[2]
CONT = ROOT / 'RAG/results/rag_module4/continuation_v1'
RUN = CONT / 'schannel_run_v1'
PIN = CONT / 'mpnet_provenance_v2'
REPLAY = PIN / 'replay_20260830T181436Z'
INPUTS = ROOT / 'RAG/results/rag_module4/static_protocol/module4_dev_inputs_locked.csv'
SNAPSHOT = RUN / 'module4_external_lexical_snapshot.jsonl'
CANONICAL = ROOT / 'codex/canonical_human_development_manifest.csv'
MIXED = ROOT / 'codex/canonical_feature_outputs/canonical_human_14_features.csv'
FOLDS = ROOT / 'codex/canonical_fold_assignments.csv'
RAG = RUN / 'features/module4_rag_features.csv'
FUSED = RUN / 'features/module4_fused_21_features.csv'
NEW = ['rag_definition_hyp_cosine', 'rag_definition_hyp_entailment',
       'rag_definition_hyp_neutral', 'rag_definition_hyp_contradiction']


def now():
    return datetime.now(timezone.utc).isoformat()


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for chunk in iter(lambda: f.read(1 << 20), b''):
            h.update(chunk)
    return h.hexdigest()


def read_json(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def write_json(path, data):
    path = Path(path)
    path.resolve().relative_to(OUT.resolve())
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x', encoding='utf-8', newline='\n') as f:
        json.dump(data, f, indent=2, sort_keys=True)
        f.write('\n')


def csv_write(path, frame):
    path = Path(path)
    path.resolve().relative_to(OUT.resolve())
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x', encoding='utf-8-sig', newline='') as f:
        frame.to_csv(f, index=False, lineterminator='\n')


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


frozen = module('module4_pinned', PIN / 'scripts/module4_build_rag_features_pinned.py')
evaluator = module('module4_evaluator', RUN / 'scripts/module4_evaluate_fusion.py')
FEATURES = evaluator.E3 + evaluator.RAG + NEW


def offline():
    for key in ('HF_HUB_OFFLINE', 'TRANSFORMERS_OFFLINE', 'HF_DATASETS_OFFLINE',
                'HF_HUB_DISABLE_TELEMETRY', 'PYTHONDONTWRITEBYTECODE'):
        os.environ[key] = '1'
    log = OUT / 'config/network_attempts.jsonl'
    log.parent.mkdir(parents=True, exist_ok=True)
    log.touch(exist_ok=True)
    if log.stat().st_size:
        raise RuntimeError('Existing network attempt requires investigation')

    def blocked(*args, **kwargs):
        with log.open('a', encoding='utf-8') as f:
            f.write(json.dumps({'time': now(), 'status': 'BLOCKED_NETWORK_ATTEMPT'}) + '\n')
        raise RuntimeError('Network disabled for E6')

    socket.socket.connect = blocked
    socket.socket.connect_ex = blocked
    socket.create_connection = blocked
    socket.getaddrinfo = blocked


def verify_lock():
    lock = read_json(OUT / 'config/run_config.json')
    for p, expected in lock['protected_sha256'].items():
        assert sha(ROOT / p) == expected, f'Protected input changed: {p}'
    for p, expected in lock['implementation_sha256'].items():
        assert sha(OUT / p) == expected, f'Locked implementation changed: {p}'
    return lock
