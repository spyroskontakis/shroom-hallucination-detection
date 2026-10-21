"""Prepared Modal A100 smoke and explicitly gated frozen full-fold execution."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import modal

REMOTE_ROOT = "/opt/e11a"
REMOTE_MODEL = "/opt/e11a/model"
REMOTE_RESULTS = "/results/e11a"
MODULE_ROOT = Path(__file__).resolve().parent if modal.is_local() else Path(REMOTE_ROOT)
if str(MODULE_ROOT) not in sys.path:
    sys.path.insert(0, str(MODULE_ROOT))

from scoring_common import HERE, ROOT, require, sha_file
from e11a_prepare_data import load_protocol
from validate_e11a_protocol import validate_bundle, validate_local

APP = "shroom-e11a-human-only-smoke"
VOLUME = "shroom-e11a-training-results"
GPU = "A100-80GB"
MEMORY_MIB = 65536
DISK_MIB = 524288
TIMEOUT_SECONDS = 1800
E11A_IMAGE_FILES = (
    "scoring_common.py", "e11a_prepare_data.py", "validate_e11a_protocol.py",
    "e11a_train_fold.py", "E11A_TRAINING_PROTOCOL.json",
    "E11A_PREPARATION_MANIFEST.json", "E11A_REQUIREMENTS.lock.txt",
)


def validate_local_config() -> dict:
    result = validate_local()
    spec = load_protocol()
    require(spec["modal"] == {
        "gpu": GPU, "gpu_count": 1, "memory_mib": MEMORY_MIB,
        "ephemeral_disk_mib": DISK_MIB, "smoke_timeout_seconds": TIMEOUT_SECONDS,
        "volume": VOLUME, "volume_mount": "/results",
        "runtime_root": REMOTE_ROOT, "model_root": REMOTE_MODEL,
        "output_root": REMOTE_RESULTS}, "Modal smoke resource/path drift")
    require(all((HERE / name).is_file() for name in E11A_IMAGE_FILES),
            "missing E11-A image file")
    require(ROOT is not None and sha_file(HERE / "E11A_REQUIREMENTS.lock.txt") ==
            spec["software"]["requirements_sha256"], "dependency lock drift")
    return {**result, "modal_gpu": GPU, "modal_disk_mib": DISK_MIB,
            "modal_job_started": False}


def make_image():
    require(ROOT is not None, "local model checkout required for image build")
    image = modal.Image.debian_slim(python_version="3.11")
    for name in E11A_IMAGE_FILES:
        image = image.add_local_file(str(HERE / name),
                                     f"{REMOTE_ROOT}/{name}", copy=True)
    for fold_id in range(1, 6):
        for split in ("train", "heldout"):
            source = HERE / "e11a_prepared" / f"fold_{fold_id}" / f"{split}.jsonl"
            target = f"{REMOTE_ROOT}/e11a_prepared/fold_{fold_id}/{split}.jsonl"
            image = image.add_local_file(str(source), target, copy=True)
    spec = load_protocol()
    image = image.add_local_dir(str(ROOT / spec["model"]["local_mirror_dir"]),
                                str(REMOTE_MODEL), copy=True)
    return image.run_commands(
        f"python -m pip install --no-cache-dir -r {REMOTE_ROOT}/E11A_REQUIREMENTS.lock.txt",
        "python -m pip check",
    )


# Modal reimports the function module inside its shallow container. It must
# never try to discover the Windows checkout or rebuild the local image there.
image = make_image() if modal.is_local() else modal.Image.debian_slim(python_version="3.11")
app = modal.App(APP)
volume = modal.Volume.from_name(VOLUME, create_if_missing=True)


@app.function(image=image, gpu=GPU, cpu=8, memory=MEMORY_MIB,
              ephemeral_disk=DISK_MIB, timeout=TIMEOUT_SECONDS,
              volumes={"/results": volume}, max_containers=1, retries=0)
def smoke(run_id: str) -> dict:
    require(re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]{0,63}", run_id) is not None,
            "invalid smoke run ID")
    validate_bundle(Path(REMOTE_ROOT), Path(REMOTE_MODEL))
    from e11a_train_fold import execute
    result = execute(1, "smoke", Path(REMOTE_ROOT), Path(REMOTE_MODEL),
                     Path(REMOTE_RESULTS),
                     run_id, False)
    require(result["status"] == "PASS" and result["e11a_score_produced"] is False and
            result["optimizer_steps"] == 2, "smoke result contract")
    volume.commit()
    return result


@app.function(image=image, gpu=GPU, cpu=8, memory=MEMORY_MIB,
              ephemeral_disk=DISK_MIB, timeout=14400,
              volumes={"/results": volume}, max_containers=1, retries=0)
def train_locked_fold(fold_id: int, run_id: str) -> dict:
    require(fold_id in range(1, 6), "locked fold ID must be 1..5")
    require(run_id == f"e11a-fold-{fold_id:03d}", "frozen fold run ID")
    validate_bundle(Path(REMOTE_ROOT), Path(REMOTE_MODEL))
    from e11a_train_fold import execute
    result = execute(fold_id, "fold", Path(REMOTE_ROOT), Path(REMOTE_MODEL),
                     Path(REMOTE_RESULTS), run_id, True)
    require(result["status"] == "PASS" and result["mode"] == "fold" and
            result["heldout_predictions"] == (113 if fold_id == 1 else 112) and
            len(result["loss_by_epoch"]) == 5,
            "full-fold result contract")
    volume.commit()
    return result


@app.local_entrypoint()
def main(run_id: str = "e11a-smoke-001", fold_id: int = 1,
         full_fold: bool = False) -> None:
    checked = validate_local_config()
    print("E11-A local validation PASS:", json.dumps(checked), flush=True)
    if full_fold:
        print(json.dumps(train_locked_fold.remote(fold_id, run_id), indent=2), flush=True)
    else:
        require(fold_id == 1 and run_id == "e11a-smoke-001",
                "smoke requires frozen smoke ID and fold 1")
        print(json.dumps(smoke.remote(run_id), indent=2), flush=True)


if __name__ == "__main__":
    if sys.argv[1:] == ["--validate-local"]:
        print(json.dumps(validate_local_config(), indent=2))
    else:
        raise SystemExit("Local validation only: python e11a_modal.py --validate-local")
