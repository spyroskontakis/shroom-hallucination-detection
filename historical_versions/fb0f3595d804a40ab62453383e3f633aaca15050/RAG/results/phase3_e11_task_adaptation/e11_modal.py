"""Prepared Modal A100 scoring orchestration. Import/validation never runs a job.

Default Modal entrypoint is the 600-row benchmark plus 561 HUMAN MiniCheck rows.
The 28,649-row path requires the explicit --full-run flag at both entrypoint
and subprocess levels. Do not invoke a paid run during local preparation.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

import modal

from scoring_common import (HERE, ROOT, FROZEN_PROTOCOL_CONTENT_SHA,
                            FROZEN_PROTOCOL_FILE_SHA, atomic_json, protocol,
                            read_jsonl, require, sha_file)

APP_NAME = "shroom-e11-raw-scoring"
VOLUME_NAME = "shroom-e11-raw-detector-scores"
GPU = "A100-80GB"
MEMORY_MIB = 65536
DISK_MIB = 524288
TIMEOUT_SECONDS = 43200
REMOTE_E11 = "/opt/SHROOM/SHROOM2024/RAG/results/phase3_e11_task_adaptation"
REMOTE_PHASE3 = "/opt/SHROOM/SHROOM2024/RAG/results/phase3_e9_claim_verification"
REMOTE_MODELS = "/opt/e11_models"
REMOTE_OUTPUT = "/results/e11"
MANIFEST_PATH = HERE / "E11_SCORING_MANIFEST.json"


def validate_local() -> dict:
    spec = protocol()
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    require(manifest["protocol_sha256"] == FROZEN_PROTOCOL_CONTENT_SHA,
            "scoring manifest protocol digest")
    require(manifest["protocol_file_sha256"] == FROZEN_PROTOCOL_FILE_SHA,
            "scoring manifest protocol file SHA")
    require(manifest["modal"] == {
        "app": APP_NAME, "volume": VOLUME_NAME, "gpu": GPU, "gpu_count": 1,
        "memory_mib": MEMORY_MIB, "ephemeral_disk_mib": DISK_MIB,
        "timeout_seconds": TIMEOUT_SECONDS, "cpu": 8}, "Modal resource request drift")
    require(manifest["full_run_guard"] == "--full-run", "full-run guard drift")
    for name, expected in manifest["prepared_sha256"].items():
        require(sha_file(HERE / name) == expected, "prepared input SHA: " + name)
    for name, expected in manifest["scoring_code_sha256"].items():
        require(sha_file(HERE / name) == expected, "scoring code SHA: " + name)
    require(len(read_jsonl(HERE / "unlabeled_master.jsonl")) == 28649,
            "master row count")
    require(len(read_jsonl(HERE / "benchmark_600.jsonl")) == 600,
            "benchmark row count")
    require(len(read_jsonl(HERE / "human_whole_hyp_minicheck_inputs.jsonl")) == 561,
            "human MiniCheck input count")
    for detector in ("factcg", "minicheck", "hhem", "nli"):
        require(manifest["detectors"][detector]["model_id"] ==
                spec["detectors"][detector]["model_id"], "model ID drift")
        require(manifest["detectors"][detector]["revision"] ==
                spec["detectors"][detector]["revision"], "revision drift")
    for stage, meta in manifest["frozen_gpu_packages"].items():
        package = ROOT / "RAG/results/phase3_e9_claim_verification" / stage
        require(sha_file(package / (stage + "_portable.zip")) == meta["archive_sha256"],
                "frozen ZIP hash drift: " + stage)
        require(sha_file(package / "GPU_RUN_MANIFEST.json") == meta["manifest_sha256"],
                "frozen package manifest hash drift: " + stage)
    for name, info in manifest["local_model_mirrors"].items():
        require(sha_file(ROOT / info["path"]) == info["sha256"],
                "model mirror hash drift: " + name)
    return {"status": "PASS", "protocol_sha256": spec["protocol_sha256"],
            "benchmark_rows": 600, "human_whole_hyp_minicheck_rows": 561,
            "full_rows": 28649, "modal_job_started": False}


def make_image():
    source = ROOT / "RAG/results/phase3_e9_claim_verification"
    image = modal.Image.debian_slim(python_version="3.11").apt_install("git", "unzip")
    for stage in ("minicheck_gpu", "factcg_gpu"):
        archive = source / stage / (stage + "_portable.zip")
        image = image.add_local_file(str(archive),
                                     f"{REMOTE_PHASE3}/{stage}_portable.zip", copy=True)
    for name in ("scoring_common.py", "detector_adapters.py", "run_detector.py",
                 "E11_TEACHER_PROTOCOL.json", "E11_SCORING_MANIFEST.json",
                 "unlabeled_master.jsonl", "benchmark_600.jsonl",
                 "human_whole_hyp_minicheck_inputs.jsonl"):
        image = image.add_local_file(str(HERE / name), f"{REMOTE_E11}/{name}", copy=True)
    image = image.add_local_dir(
        str(ROOT / "RAG/results/rag_e6_v2/model"), f"{REMOTE_MODELS}/nli", copy=True)
    image = image.add_local_dir(
        str(ROOT / "RAG/results/rag_e6_v3/model"), f"{REMOTE_MODELS}/hhem", copy=True)
    image = image.run_commands(
        f"cd {REMOTE_PHASE3} && unzip -q minicheck_gpu_portable.zip && unzip -q factcg_gpu_portable.zip",
        f"python3.11 -m venv {REMOTE_PHASE3}/minicheck_gpu/.venv",
        f"{REMOTE_PHASE3}/minicheck_gpu/.venv/bin/python -m pip install pip==24.3.1",
        f"{REMOTE_PHASE3}/minicheck_gpu/.venv/bin/python -m pip install -r {REMOTE_PHASE3}/minicheck_gpu/requirements_gpu.lock.txt",
        f"{REMOTE_PHASE3}/minicheck_gpu/.venv/bin/python -m pip check",
        f"python3.11 -m venv {REMOTE_PHASE3}/factcg_gpu/.venv",
        f"{REMOTE_PHASE3}/factcg_gpu/.venv/bin/python -m pip install pip==24.3.1",
        f"{REMOTE_PHASE3}/factcg_gpu/.venv/bin/python -m pip install -r {REMOTE_PHASE3}/factcg_gpu/requirements_gpu.lock.txt",
        f"{REMOTE_PHASE3}/factcg_gpu/.venv/bin/python -m pip check",
    )
    return image


image = make_image()
app = modal.App(APP_NAME)
volume = modal.Volume.from_name(VOLUME_NAME, create_if_missing=True)


def check_gpu() -> dict:
    result = subprocess.run(
        ["nvidia-smi", "--query-gpu=name,memory.total", "--format=csv,noheader,nounits"],
        capture_output=True, text=True, check=True)
    rows = [line.strip() for line in result.stdout.splitlines() if line.strip()]
    require(len(rows) == 1, "exactly one GPU required")
    name, memory = [part.strip() for part in rows[0].rsplit(",", 1)]
    require("A100" in name and "80GB" in name and int(memory) >= 79000,
            "A100-80GB required; no fallback")
    return {"name": name, "memory_mib": int(memory)}


def stage_command(detector: str, scope: str) -> list[str]:
    python = (f"{REMOTE_PHASE3}/minicheck_gpu/.venv/bin/python"
              if detector == "minicheck" else
              f"{REMOTE_PHASE3}/factcg_gpu/.venv/bin/python")
    command = [python, "-B", f"{REMOTE_E11}/run_detector.py", "--run",
               "--detector", detector, "--scope", scope,
               "--prepared-dir", REMOTE_E11, "--output-root", REMOTE_OUTPUT,
               "--package-root", REMOTE_PHASE3,
               "--cache-root", f"{REMOTE_OUTPUT}/model_cache",
               "--models-root", REMOTE_MODELS, "--batch-size", "64"]
    if scope == "full":
        command.append("--full-run")
    return command


def run_stage(detector: str, scope: str, run_dir: Path) -> None:
    import fcntl  # Linux Modal container only.
    started = time.perf_counter()
    folder = Path(REMOTE_OUTPUT) / ("human_minicheck" if scope == "human" else
                                    f"raw_detector_scores/{detector}")
    folder.mkdir(parents=True, exist_ok=True)
    lock_path = folder / "scores.lock"
    env = dict(os.environ)
    env["HF_HOME"] = f"{REMOTE_OUTPUT}/model_cache/huggingface"
    env["TRANSFORMERS_CACHE"] = f"{REMOTE_OUTPUT}/model_cache/huggingface"
    env["HF_HUB_DISABLE_TELEMETRY"] = "1"
    process = subprocess.Popen(stage_command(detector, scope), env=env)
    try:
        while process.poll() is None:
            time.sleep(30)
            with lock_path.open("a+b") as lock:
                fcntl.flock(lock, fcntl.LOCK_EX)
                try:
                    volume.commit()  # Persist checkpointed batches during long stages.
                finally:
                    fcntl.flock(lock, fcntl.LOCK_UN)
        volume.commit()
        require(process.returncode == 0,
                f"{detector}/{scope} failed with exit {process.returncode}")
        report = folder / f"validation_{scope}.json"
        require(report.is_file() and json.loads(report.read_text(encoding="utf-8"))["status"] ==
                "PASS", "stage validation report missing or failed")
        atomic_json(run_dir / f"{detector}_{scope}_PASS.json",
                    {"status": "PASS", "detector": detector, "scope": scope,
                     "report": str(report), "report_sha256": sha_file(report),
                     "wall_seconds_including_volume_commits": time.perf_counter() - started})
        volume.commit()
    finally:
        if process.poll() is None:
            process.terminate()
            process.wait(timeout=30)


@app.function(image=image, gpu=GPU, cpu=8, memory=MEMORY_MIB,
              ephemeral_disk=DISK_MIB, timeout=TIMEOUT_SECONDS,
              volumes={"/results": volume}, max_containers=1, retries=0)
def score_e11(run_id: str, full_run: bool = False, resume: bool = False) -> dict:
    started = time.perf_counter()
    require(re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]{0,63}", run_id) is not None,
            "invalid run ID")
    require(not resume or full_run, "--resume is for explicit full runs only")
    mode = "full" if full_run else "benchmark"
    # Recheck baked scoring inputs, model identities, and hashes before GPU use.
    baked_manifest = json.loads(Path(f"{REMOTE_E11}/E11_SCORING_MANIFEST.json").read_text())
    require(baked_manifest["protocol_sha256"] == FROZEN_PROTOCOL_CONTENT_SHA,
            "baked protocol mismatch")
    require(sha_file(Path(f"{REMOTE_E11}/E11_TEACHER_PROTOCOL.json")) ==
            FROZEN_PROTOCOL_FILE_SHA, "baked protocol changed")
    for name in ("unlabeled_master.jsonl", "benchmark_600.jsonl",
                 "human_whole_hyp_minicheck_inputs.jsonl"):
        require(sha_file(Path(REMOTE_E11) / name) == baked_manifest["prepared_sha256"][name],
                "baked scoring input changed: " + name)
    for name in ("scoring_common.py", "detector_adapters.py", "run_detector.py"):
        require(sha_file(Path(REMOTE_E11) / name) ==
                baked_manifest["scoring_code_sha256"][name],
                "baked scorer code changed: " + name)
    for stage, meta in baked_manifest["frozen_gpu_packages"].items():
        require(sha_file(Path(REMOTE_PHASE3) / (stage + "_portable.zip")) ==
                meta["archive_sha256"], "baked frozen ZIP changed: " + stage)
        require(sha_file(Path(REMOTE_PHASE3) / stage / "GPU_RUN_MANIFEST.json") ==
                meta["manifest_sha256"], "extracted frozen manifest changed: " + stage)
    for name, meta in baked_manifest["local_model_mirrors"].items():
        filename = "model.safetensors" if name == "nli" else "pytorch_model.bin"
        require(sha_file(Path(REMOTE_MODELS) / name / filename) == meta["sha256"],
                "baked model mirror changed: " + name)
    gpu = check_gpu()
    run_dir = Path(REMOTE_OUTPUT) / "runs" / run_id
    run_dir.mkdir(parents=True, exist_ok=resume)
    require(resume or not (run_dir / "STARTED.json").exists(), "run ID already used")
    atomic_json(run_dir / "STARTED.json", {"status": "STARTED", "mode": mode,
                                           "run_id": run_id, "gpu": gpu,
                                           "protocol_sha256": FROZEN_PROTOCOL_CONTENT_SHA})
    volume.commit()
    stages = ([ ("minicheck", "human"),
                *[(name, "full") for name in ("minicheck", "factcg", "nli", "hhem")]]
              if full_run else
              [("minicheck", "benchmark"), ("minicheck", "human"),
               ("factcg", "benchmark"), ("nli", "benchmark"),
               ("hhem", "benchmark")])
    try:
        for detector, scope in stages:
            run_stage(detector, scope, run_dir)
        result = {"status": "PASS", "mode": mode, "run_id": run_id,
                  "volume": VOLUME_NAME, "stages": stages,
                  "total_wall_seconds": time.perf_counter() - started}
        atomic_json(run_dir / "COMPLETE.json", result)
        volume.commit()
        return result
    except Exception as exc:
        atomic_json(run_dir / "FAILED.json", {"status": "FAIL", "mode": mode,
                                               "run_id": run_id, "reason": str(exc)})
        volume.commit()
        raise


@app.local_entrypoint()
def main(run_id: str, full_run: bool = False, resume: bool = False) -> None:
    require(not resume or full_run, "--resume requires --full-run")
    checked = validate_local()
    print("Local E11 static validation PASS:", json.dumps(checked), flush=True)
    print(json.dumps(score_e11.remote(run_id, full_run, resume), indent=2), flush=True)


if __name__ == "__main__":
    if sys.argv[1:] == ["--validate-local"]:
        print(json.dumps(validate_local(), indent=2))
    else:
        raise SystemExit("Local validation only: python e11_modal.py --validate-local")
