"""Build a deterministic E11 scoring manifest from already validated local files."""

from __future__ import annotations

import json
from pathlib import Path

from scoring_common import (HERE, ROOT, FROZEN_PROTOCOL_CONTENT_SHA,
                            FROZEN_PROTOCOL_FILE_SHA, SCORE_FIELDS, atomic_json,
                            protocol, require, sha_file)

REL = "RAG/results/phase3_e11_task_adaptation"
VOLUME = "shroom-e11-raw-detector-scores"


def build() -> dict:
    spec = protocol()
    prep = json.loads((HERE / "E11_INPUT_PREPARATION_REPORT.json").read_text(encoding="utf-8"))
    require(prep["status"] == "PASS", "input preparation report")
    require(all(sha_file(HERE / name) == value for name, value in
                prep["prepared_sha256"].items()), "prepared input hash drift")
    old_modal = json.loads((ROOT / "RAG/results/phase3_e9_claim_verification/modal_gpu/"
                            "MODAL_RUN_MANIFEST.json").read_text(encoding="utf-8"))
    packages = {}
    for name in ("minicheck_gpu", "factcg_gpu"):
        source = ROOT / "RAG/results/phase3_e9_claim_verification" / name
        meta = old_modal["packages"][name]
        archive = source / (name + "_portable.zip")
        original_manifest = source / "GPU_RUN_MANIFEST.json"
        require(sha_file(archive) == meta["archive_sha256"], "frozen ZIP hash")
        require(sha_file(original_manifest) == meta["manifest_sha256"], "frozen manifest hash")
        packages[name] = {"archive": str(archive.relative_to(ROOT)).replace("\\", "/"),
                          "archive_sha256": meta["archive_sha256"],
                          "manifest_sha256": meta["manifest_sha256"],
                          "requirements_lock_sha256": sha_file(source / "requirements_gpu.lock.txt")}
    mirrors = {}
    for name, rel in [
        ("nli", "RAG/results/rag_e6_v2/model/model.safetensors"),
        ("hhem", "RAG/results/rag_e6_v3/model/pytorch_model.bin")]:
        mirrors[name] = {"path": rel, "sha256": sha_file(ROOT / rel),
                         "bytes": (ROOT / rel).stat().st_size}
    scoring_code = ["scoring_common.py", "prepare_scoring_inputs.py",
                    "detector_adapters.py", "run_detector.py", "e11_modal.py",
                    "download_scoring_outputs.py", "validate_scoring_outputs.py"]
    commands = {
        "validate_local": f"python -B {REL}/e11_modal.py --validate-local",
        "benchmark": f"python -m modal run {REL}/e11_modal.py --run-id e11-benchmark-001",
        "download_benchmark": f"python -B {REL}/download_scoring_outputs.py --scope benchmark --run-id e11-benchmark-001 --destination {REL}/downloaded_benchmark/e11-benchmark-001",
        "inspect_benchmark": f"python -B {REL}/validate_scoring_outputs.py --scope benchmark --directory {REL}/downloaded_benchmark/e11-benchmark-001",
        "full": f"python -m modal run {REL}/e11_modal.py --run-id e11-full-001 --full-run",
        "resume_full": f"python -m modal run {REL}/e11_modal.py --run-id e11-full-001 --full-run --resume",
        "download_full": f"python -B {REL}/download_scoring_outputs.py --scope full --run-id e11-full-001 --destination {REL}/downloaded_full/e11-full-001",
        "inspect_full": f"python -B {REL}/validate_scoring_outputs.py --scope full --directory {REL}/downloaded_full/e11-full-001",
    }
    return {
        "schema_version": 1,
        "status": "PREPARED_NOT_EXECUTED",
        "protocol_path": f"{REL}/E11_TEACHER_PROTOCOL.json",
        "protocol_sha256": FROZEN_PROTOCOL_CONTENT_SHA,
        "protocol_file_sha256": FROZEN_PROTOCOL_FILE_SHA,
        "canonical_human": spec["inputs"]["canonical_human"],
        "locked_folds": spec["inputs"]["locked_folds"],
        "unlabeled_source": spec["inputs"]["unlabeled"],
        "human_existing_score_sources": {
            "factcg": {"path": "RAG/results/phase3_e9_claim_verification/factcg_gpu/returned_phase3-003/factcg_scores.jsonl",
                       "sha256": prep["human"]["factcg_human_scores_sha256"], "rows": 561},
            "nli_hhem": {"path": "RAG/results/rag_e6_v3/features/e6_v3_36_features.csv",
                         "sha256": prep["human"]["e6_v3_human_features_sha256"], "rows": 561}},
        "human_reuse": {"factcg": 561, "hhem": 561, "nli": 561,
                        "whole_hyp_minicheck_pending": 561},
        "prepared_sha256": prep["prepared_sha256"],
        "prepared_counts": {"human": 561, "unlabeled_raw": 30000,
                            "unlabeled_unique": 28649, "benchmark": 600,
                            "benchmark_tasks": {"DM": 200, "MT": 200, "PG": 200},
                            "fold_eligible": [28575, 28623, 28627, 28611, 28615]},
        "detectors": {name: {"model_id": spec["detectors"][name]["model_id"],
                              "revision": spec["detectors"][name]["revision"],
                              "score_fields": list(SCORE_FIELDS[name]),
                              "orientation": spec["detectors"][name]["orientation"]}
                      for name in ("factcg", "minicheck", "nli", "hhem")},
        "output_common_fields": ["sample_key", "input_sha256", "detector", "model_id", "revision"],
        "output_score_semantics": "Exactly one record per detector and sample key; all scores finite in [0,1]; NLI probabilities sum to 1.",
        "frozen_gpu_packages": packages,
        "local_model_mirrors": mirrors,
        "scoring_code_sha256": {name: sha_file(HERE / name) for name in scoring_code},
        "modal": {"app": "shroom-e11-raw-scoring", "volume": VOLUME,
                  "gpu": "A100-80GB", "gpu_count": 1, "memory_mib": 65536,
                  "ephemeral_disk_mib": 524288, "timeout_seconds": 43200, "cpu": 8},
        "software": {"modal_cli": "1.5.5", "remote_python": "3.11",
                     "minicheck": "separate frozen E9-B venv/requirements_gpu.lock.txt; torch 2.4.0+cu121, vllm 0.6.3.post1, transformers 4.45.2",
                     "factcg_nli_hhem": "separate frozen FactCG venv/requirements_gpu.lock.txt; torch 2.2.1+cu121, transformers 4.38.1",
                     "nli_hhem_dtype": "float32", "minicheck_dtype": "bfloat16",
                     "factcg_dtype": "float32", "quantization": None,
                     "cpu_fallback": False},
        "persistent_output_root": "e11/",
        "raw_store_layout": "e11/raw_detector_scores/{factcg,minicheck,nli,hhem}/{scores.jsonl,manifest.json,validation_benchmark.json,validation_full.json}; e11/human_minicheck/",
        "full_run_guard": "--full-run",
        "commands": commands,
        "gpu_job_started": False,
        "pseudo_labels_generated": False,
    }


def main() -> None:
    value = build()
    atomic_json(HERE / "E11_SCORING_MANIFEST.json", value)
    print(json.dumps({"status": "PASS", "manifest_path": str(HERE / "E11_SCORING_MANIFEST.json"),
                      "benchmark_sha256": value["prepared_sha256"]["benchmark_600.jsonl"],
                      "gpu_job_started": False}, indent=2))


if __name__ == "__main__":
    main()
