"""Modal orchestration for the two unchanged, frozen Phase 3 GPU ZIP packages.

`python modal_phase3_gpu.py --validate-local` is offline and never starts Modal.
`python -m modal run modal_phase3_gpu.py --run-id <unique-id>` runs the paid GPU.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
import zipfile

import modal

HERE = Path(__file__).resolve().parent
REMOTE_PACKAGE_ROOT = "/opt/SHROOM/SHROOM2024/RAG/results/phase3_e9_claim_verification"
SOURCE = (HERE.parent if (HERE.parent / "minicheck_gpu/minicheck_gpu_portable.zip").is_file()
          else Path(REMOTE_PACKAGE_ROOT))
MANIFEST_PATH = (HERE / "MODAL_RUN_MANIFEST.json" if (HERE / "MODAL_RUN_MANIFEST.json").is_file()
                 else Path(REMOTE_PACKAGE_ROOT) / "MODAL_RUN_MANIFEST.json")
MANIFEST = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
APP_NAME = "shroom-phase3-frozen-gpu"
VOLUME_NAME = "shroom-phase3-frozen-gpu-results"
PACKAGE_ROOT = Path(REMOTE_PACKAGE_ROOT)
RESULT_ROOT = Path("/results")
STAGES = ("minicheck_gpu", "factcg_gpu")
GPU = "A100-80GB"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def validate_local() -> dict:
    """Check only the two portable ZIPs, their allowlisted inputs and this manifest."""
    require(MANIFEST["stages"] == list(STAGES), "Stage order changed")
    require(MANIFEST["gpu"] == GPU and MANIFEST["gpu_count"] == 1, "GPU request changed")
    require(MANIFEST["app_name"] == APP_NAME and MANIFEST["volume_name"] == VOLUME_NAME,
            "App/Volume identity changed")
    require(MANIFEST["memory_mib"] == 65536 and MANIFEST["timeout_seconds"] == 14400,
            "Resource settings changed")
    expected_inputs = {
        "minicheck_gpu": ("minicheck_inputs.jsonl", 575, 561,
            "e41506779d4798c0ad2476e8da38ca197ebda2960a100848890181b852f3080a",
            {"canonical_id", "task", "claim_index", "claim_text", "reference_text"}),
        "factcg_gpu": ("factcg_inputs.jsonl", 561, 561,
            "10ecdbc5f25bd4b9c7c7d4c2d131194647a86c556591c75418dbcb436ba1753d",
            {"canonical_id", "task", "whole_hypothesis", "reference_text"}),
    }
    expected_models = {
        "minicheck_gpu": ("bespokelabs/Bespoke-MiniCheck-7B",
                          "1ed7786bcda3fa1dc35f7c4ed9e3f36b785d33b8"),
        "factcg_gpu": ("yaxili96/FactCG-DeBERTa-v3-Large",
                       "0430e3509dbd28d2dff7a117c0eae25359ff3e80"),
    }
    require(set(MANIFEST["packages"]) == set(STAGES), "Unexpected package")
    checked = {}
    for stage in STAGES:
        entry = MANIFEST["packages"][stage]
        filename, count, samples, input_hash, fields = expected_inputs[stage]
        require((entry["input_file"], entry["rows"], entry["samples"], entry["input_sha256"]) ==
                (filename, count, samples, input_hash), f"Frozen input identity: {stage}")
        require((entry["model_id"], entry["model_revision"]) == expected_models[stage],
                f"Model identity: {stage}")
        require(entry["archive"] == f"{stage}_portable.zip", f"Archive name: {stage}")
        package = SOURCE / stage
        archive = package / entry["archive"]
        require(archive.is_file(), f"Missing archive: {archive}")
        require(sha256(archive) == entry["archive_sha256"], f"Archive SHA-256: {stage}")
        require(sha256(package / "GPU_RUN_MANIFEST.json") == entry["manifest_sha256"],
                f"Frozen manifest SHA-256: {stage}")
        require(sha256(package / filename) == input_hash, f"Local input SHA-256: {stage}")
        with zipfile.ZipFile(archive) as zf:
            names = zf.namelist()
            require(len(names) == len(set(names)), f"Duplicate ZIP member: {stage}")
            prefix = stage + "/"
            inner_manifest_name = prefix + "GPU_RUN_MANIFEST.json"
            require(inner_manifest_name in names, f"Missing ZIP manifest: {stage}")
            embedded_manifest_bytes = zf.read(inner_manifest_name)
            require(hashlib.sha256(embedded_manifest_bytes).hexdigest() == entry["manifest_sha256"],
                    f"Embedded manifest SHA-256: {stage}")
            embedded = json.loads(embedded_manifest_bytes)
            require((embedded["model_id"], embedded["model_revision"]) == expected_models[stage],
                    f"Embedded model/revision: {stage}")
            require(embedded["sample_count"] == samples, f"Embedded sample count: {stage}")
            expected_names = {prefix + name for name in embedded["package_sha256"]}
            expected_names.add(inner_manifest_name)
            require(set(names) == expected_names, f"Unexpected/missing ZIP members: {stage}")
            require(all(not name.startswith("/") and ".." not in Path(name).parts for name in names),
                    f"Unsafe ZIP path: {stage}")
            for name, expected_hash in embedded["package_sha256"].items():
                require(hashlib.sha256(zf.read(prefix + name)).hexdigest() == expected_hash,
                        f"Frozen package member SHA-256: {stage}/{name}")
            rows_bytes = zf.read(prefix + filename)
            require(hashlib.sha256(rows_bytes).hexdigest() == input_hash,
                    f"Embedded input SHA-256: {stage}")
            rows = [json.loads(line) for line in rows_bytes.decode("utf-8").splitlines()]
            require(len(rows) == count and len({r["canonical_id"] for r in rows}) == samples,
                    f"Input population: {stage}")
            require(all(set(row) == fields and row["task"] in {"DM", "MT", "PG"} for row in rows),
                    f"Input allowlist/leakage check: {stage}")
            require(all(name.endswith((".py", ".md", ".txt", ".json", ".jsonl", ".tab", ".gitignore", ".model", "/LICENSE"))
                        for name in names), f"Unexpected archive data file: {stage}")
            require({name for name in names if name.endswith(".jsonl")} == {prefix + filename},
                    f"Unexpected JSONL data: {stage}")
        checked[stage] = {"archive_sha256": entry["archive_sha256"],
                          "input_sha256": input_hash, "rows": count, "samples": samples}
    return checked


def verify_remote_package(stage: str) -> None:
    """Check the baked ZIP and extracted frozen input before running either model."""
    entry = MANIFEST["packages"][stage]
    archive = PACKAGE_ROOT / entry["archive"]
    folder = PACKAGE_ROOT / stage
    require(sha256(archive) == entry["archive_sha256"], f"Remote archive SHA-256: {stage}")
    require(sha256(folder / "GPU_RUN_MANIFEST.json") == entry["manifest_sha256"],
            f"Remote frozen manifest SHA-256: {stage}")
    require(sha256(folder / entry["input_file"]) == entry["input_sha256"],
            f"Remote input SHA-256: {stage}")
    subprocess.run([str(folder / ".venv/bin/python"), "-B", str(folder / entry["input_validator"])],
                   cwd=folder, check=True)


def write_status(run_dir: Path, filename: str, payload: dict) -> None:
    with (run_dir / filename).open("x", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, ensure_ascii=False)
        handle.write("\n")


def execute_stage(stage: str, run_dir: Path, volume: modal.Volume) -> Path:
    entry = MANIFEST["packages"][stage]
    folder = PACKAGE_ROOT / stage
    output_dir = run_dir / f"{stage}_run"
    command = [str(folder / ".venv/bin/python"), "-B", str(folder / entry["runner"]),
               "--run", "--output-dir", str(output_dir),
               "--cache-dir", f"/tmp/phase3_model_cache/{stage}"]
    print(f"Starting frozen {stage} runner", flush=True)
    completed = subprocess.run(command, cwd=folder, check=False)
    volume.commit()  # Keep the runner report even when preflight or inference fails.
    report_path = output_dir / entry["report_file"]
    reason = "runner produced no report"
    if report_path.is_file():
        report = json.loads(report_path.read_text(encoding="utf-8"))
        reason = report.get("reason", reason)
    require(completed.returncode == 0, f"{stage} stopped (exit {completed.returncode}): {reason}")
    score_path = output_dir / entry["output_file"]
    subprocess.run([str(folder / ".venv/bin/python"), "-B",
                    str(folder / entry["output_validator"]), str(score_path)],
                   cwd=folder, check=True)
    write_status(run_dir, f"{stage}_PASS.json",
                 {"stage": stage, "status": "PASS", "output": str(score_path),
                  "output_sha256": sha256(score_path), "report": str(report_path)})
    volume.commit()
    return score_path


image = (
    modal.Image.debian_slim(python_version="3.11")
    .apt_install("git", "unzip")
    .add_local_file(str(SOURCE / "minicheck_gpu/minicheck_gpu_portable.zip"),
                    f"{REMOTE_PACKAGE_ROOT}/minicheck_gpu_portable.zip", copy=True)
    .add_local_file(str(SOURCE / "factcg_gpu/factcg_gpu_portable.zip"),
                    f"{REMOTE_PACKAGE_ROOT}/factcg_gpu_portable.zip", copy=True)
    .add_local_file(str(MANIFEST_PATH), f"{REMOTE_PACKAGE_ROOT}/MODAL_RUN_MANIFEST.json", copy=True)
    .run_commands(
        f"cd {REMOTE_PACKAGE_ROOT} && unzip -q minicheck_gpu_portable.zip && unzip -q factcg_gpu_portable.zip",
        f"python3.11 -m venv {REMOTE_PACKAGE_ROOT}/minicheck_gpu/.venv",
        f"{REMOTE_PACKAGE_ROOT}/minicheck_gpu/.venv/bin/python -m pip install pip==24.3.1",
        f"{REMOTE_PACKAGE_ROOT}/minicheck_gpu/.venv/bin/python -m pip install -r {REMOTE_PACKAGE_ROOT}/minicheck_gpu/requirements_gpu.lock.txt",
        f"{REMOTE_PACKAGE_ROOT}/minicheck_gpu/.venv/bin/python -m pip check",
        f"python3.11 -m venv {REMOTE_PACKAGE_ROOT}/factcg_gpu/.venv",
        f"{REMOTE_PACKAGE_ROOT}/factcg_gpu/.venv/bin/python -m pip install pip==24.3.1",
        f"{REMOTE_PACKAGE_ROOT}/factcg_gpu/.venv/bin/python -m pip install -r {REMOTE_PACKAGE_ROOT}/factcg_gpu/requirements_gpu.lock.txt",
        f"{REMOTE_PACKAGE_ROOT}/factcg_gpu/.venv/bin/python -m pip check",
    )
)
app = modal.App(APP_NAME)
volume = modal.Volume.from_name(VOLUME_NAME, create_if_missing=True)


@app.function(
    image=image,
    gpu=GPU,
    cpu=8,
    memory=65536,  # MiB; frozen MiniCheck gate requires >=24 GiB *available*.
    ephemeral_disk=524288,  # MiB for checkpoints and both Python environments.
    timeout=14400,
    volumes={"/results": volume},
    max_containers=1,
    retries=0,
)
def run_phase3(run_id: str) -> dict:
    """One Linux container, one A100-80GB, two sequential subprocesses."""
    require(re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]{0,63}", run_id) is not None,
            "run_id must be 1-64 ASCII letters/digits/underscore/hyphen")
    # Re-check the unchanged baked inputs remotely before any inference.
    for stage in STAGES:
        verify_remote_package(stage)
    gpu_result = subprocess.run(
        ["nvidia-smi", "--query-gpu=name,memory.total", "--format=csv,noheader,nounits"],
        capture_output=True, text=True, check=True,
    )
    gpu_rows = [line.strip() for line in gpu_result.stdout.splitlines() if line.strip()]
    require(len(gpu_rows) == 1, f"Expected exactly one GPU; nvidia-smi returned {gpu_rows}")
    gpu_name, memory_mib = [part.strip() for part in gpu_rows[0].rsplit(",", 1)]
    require("A100" in gpu_name and "80GB" in gpu_name and int(memory_mib) >= 79000,
            f"Required A100-80GB; got {gpu_name} with {memory_mib} MiB")
    run_dir = RESULT_ROOT / "runs" / run_id
    run_dir.mkdir(parents=True, exist_ok=False)
    write_status(run_dir, "STARTED.json",
                 {"run_id": run_id, "gpu": gpu_name, "gpu_memory_mib": int(memory_mib),
                  "stages": list(STAGES), "manifest_sha256": sha256(PACKAGE_ROOT / "minicheck_gpu/GPU_RUN_MANIFEST.json")})
    volume.commit()
    try:
        mini_output = execute_stage("minicheck_gpu", run_dir, volume)
        fact_output = execute_stage("factcg_gpu", run_dir, volume)
        result = {"status": "PASS", "run_id": run_id, "volume": VOLUME_NAME,
                  "minicheck_output": str(mini_output), "factcg_output": str(fact_output)}
        write_status(run_dir, "COMPLETE.json", result)
        volume.commit()
        return result
    except Exception as exc:
        write_status(run_dir, "FAILED.json", {"status": "FAIL", "reason": str(exc)})
        volume.commit()
        raise


@app.local_entrypoint()
def main(run_id: str) -> None:
    require(re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]{0,63}", run_id) is not None,
            "Invalid run_id")
    checked = validate_local()
    print("Local frozen ZIP/input validation PASS:", json.dumps(checked), flush=True)
    print(json.dumps(run_phase3.remote(run_id), indent=2), flush=True)


if __name__ == "__main__":
    if sys.argv[1:] == ["--validate-local"]:
        print(json.dumps({"status": "PASS", "packages": validate_local()}, indent=2))
    else:
        raise SystemExit("Local validation only: python modal_phase3_gpu.py --validate-local")
