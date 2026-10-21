"""Explicit opt-in GPU raw scoring. No teacher/pseudo-label code is imported."""

from __future__ import annotations

import argparse
import importlib.metadata as metadata
import json
import os
import platform
import sys
import time
from pathlib import Path

from scoring_common import (HERE, SCORE_FIELDS, ScoreStore, protocol, read_jsonl,
                            require, scoring_row, scoring_digest, sha_file, validate_record,
                            atomic_json)

DETECTOR_ORDER = ("minicheck", "factcg", "nli", "hhem")


def load_scope(detector: str, scope: str, prepared_dir: Path, manifest: dict) -> tuple[list[dict], list[dict], str]:
    require(detector in SCORE_FIELDS, "unknown detector")
    require(scope in {"benchmark", "human", "full"}, "unknown scope")
    require(scope != "human" or detector == "minicheck", "human scoring is MiniCheck only")
    require(scope != "full" or manifest["full_run_guard"] == "--full-run", "full-run guard")
    sources = manifest["prepared_sha256"]
    def checked(name: str) -> list[dict]:
        path = prepared_dir / name
        require(sha_file(path) == sources[name], "prepared input SHA mismatch: " + name)
        return read_jsonl(path)
    if scope == "human":
        universe = checked("human_whole_hyp_minicheck_inputs.jsonl")
        return universe, universe, sources["human_whole_hyp_minicheck_inputs.jsonl"]
    universe = checked("unlabeled_master.jsonl")
    requested = checked("benchmark_600.jsonl") if scope == "benchmark" else universe
    require(len(universe) == 28649, "master count")
    require(len(requested) == (600 if scope == "benchmark" else 28649), "scope count")
    return universe, requested, sources["unlabeled_master.jsonl"]


def make_records(detector: str, inputs: list[dict], outputs: list[dict],
                 model_id: str, revision: str) -> list[dict]:
    require(len(inputs) == len(outputs), "detector output length")
    records = []
    for input_row, scores in zip(inputs, outputs):
        source = scoring_row(input_row)
        require(set(scores) == set(SCORE_FIELDS[detector]), "detector score field set")
        record = {"sample_key": source["sample_key"],
                  "input_sha256": scoring_digest(source), "detector": detector,
                  "model_id": model_id, "revision": revision, **scores}
        validate_record(record, detector, source, model_id, revision)
        records.append(record)
    return records


def run(detector: str, scope: str, prepared_dir: Path, output_root: Path,
        package_root: Path, cache_root: Path, models_root: Path,
        batch_size: int, full_run: bool) -> dict:
    started = time.perf_counter()
    require(full_run == (scope == "full"),
            "full scoring requires --scope full --full-run; flag forbidden otherwise")
    require(1 <= batch_size <= 256, "batch size range")
    spec = protocol()
    manifest_path = prepared_dir / "E11_SCORING_MANIFEST.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    require(manifest["protocol_sha256"] == spec["protocol_sha256"], "manifest/protocol mismatch")
    require(manifest["detectors"][detector]["model_id"] ==
            spec["detectors"][detector]["model_id"], "model ID mismatch")
    require(manifest["detectors"][detector]["revision"] ==
            spec["detectors"][detector]["revision"], "model revision mismatch")
    universe, requested, universe_sha = load_scope(detector, scope, prepared_dir, manifest)
    model_id = spec["detectors"][detector]["model_id"]
    revision = spec["detectors"][detector]["revision"]
    folder = output_root / ("human_minicheck" if scope == "human" else
                            "raw_detector_scores/" + detector)
    store = ScoreStore(folder, detector, universe, model_id, revision, universe_sha)
    missing = store.missing(requested)
    model_load_seconds = 0.0
    inference_seconds = 0.0
    if missing:
        import fcntl  # Linux-only; Modal parent uses the same lock for Volume commits.
        from detector_adapters import load_adapter
        cache_root.mkdir(parents=True, exist_ok=True)
        load_started = time.perf_counter()
        adapter = load_adapter(detector, package_root, cache_root,
                               models_root / "nli", models_root / "hhem")
        model_load_seconds = time.perf_counter() - load_started
        with (folder / "scores.lock").open("a+b") as lock:
            for offset in range(0, len(missing), batch_size):
                batch = missing[offset:offset + batch_size]
                infer_started = time.perf_counter()
                outputs = adapter.score(batch)
                inference_seconds += time.perf_counter() - infer_started
                records = make_records(detector, batch, outputs, model_id, revision)
                fcntl.flock(lock, fcntl.LOCK_EX)
                try:
                    store.append(records)
                finally:
                    fcntl.flock(lock, fcntl.LOCK_UN)
                print(json.dumps({"detector": detector, "scope": scope,
                                  "completed_in_store": len(store.rows),
                                  "requested": len(requested)}), flush=True)
    result = store.validate_scope(requested)
    result.update({"scope": scope, "requested_input_sha256":
                   manifest["prepared_sha256"]["benchmark_600.jsonl"]
                   if scope == "benchmark" else universe_sha,
                   "newly_scored": len(missing), "protocol_sha256": spec["protocol_sha256"],
                   "model_load_seconds": model_load_seconds,
                   "inference_seconds": inference_seconds,
                   "total_stage_seconds": time.perf_counter() - started,
                   "runtime": {"python": sys.version.split()[0],
                               "platform": platform.platform(),
                               "torch": metadata.version("torch"),
                               "transformers": metadata.version("transformers"),
                               "vllm": metadata.version("vllm") if detector == "minicheck" else None}})
    atomic_json(folder / f"validation_{scope}.json", result)
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", action="store_true", help="required explicit inference opt-in")
    parser.add_argument("--detector", choices=DETECTOR_ORDER, required=True)
    parser.add_argument("--scope", choices=("benchmark", "human", "full"), required=True)
    parser.add_argument("--full-run", action="store_true", help="required for 28,649-row scope")
    parser.add_argument("--prepared-dir", type=Path, default=HERE)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--package-root", type=Path, required=True)
    parser.add_argument("--cache-root", type=Path, required=True)
    parser.add_argument("--models-root", type=Path, required=True)
    parser.add_argument("--batch-size", type=int, default=64)
    args = parser.parse_args()
    require(args.run, "inference requires --run")
    print(json.dumps(run(args.detector, args.scope, args.prepared_dir, args.output_root,
                         args.package_root, args.cache_root, args.models_root,
                         args.batch_size, args.full_run), indent=2), flush=True)


if __name__ == "__main__":
    main()
