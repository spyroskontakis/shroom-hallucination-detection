"""E11-A pre-training and portable bundle validation; no model training."""

from __future__ import annotations

import csv
import json
import math
from collections import Counter
from pathlib import Path

from scoring_common import HERE, ROOT, require, sha_file
from e11a_prepare_data import load_protocol, text_row

EXPECTED_SHA = "518c2df610a1483472b94e8baf3c0c4b277275f351e7448822e35d9dc871772d"
MODEL_ID = "MoritzLaurer/DeBERTa-v3-large-mnli-fever-anli-ling-wanli"
REVISION = "b3546ea6b0346eb6f8d5d68b13c7dc6d0376b3d7"
ALLOWED_ROW_FIELDS = {"sample_id", "fold_id", "task", "reference_field",
                      "text", "text_pair", "label"}


def read_jsonl(path: Path) -> list[dict]:
    with path.open(encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def csv_rows(path: Path) -> list[dict]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def validate_bundle(bundle: Path, model_dir: Path | None = None) -> dict:
    bundle = Path(bundle)
    # The E11-A protocol must be adjacent to the imported helper modules.
    require(bundle.resolve() == HERE.resolve(), "E11-A helper/bundle path mismatch")
    spec = load_protocol()
    require(spec["protocol_sha256"] == EXPECTED_SHA and
            spec["experiment_id"] == "E11-A" and
            spec["data"]["rows"] == 561 and
            spec["data"]["task_counts"] == {"DM": 211, "MT": 216, "PG": 134} and
            spec["data"]["label_mapping"] ==
            {"0": "Not Hallucination", "1": "Hallucination"},
            "frozen protocol/data/label mapping")
    require(spec["reference_policy"] == {"DM": "tgt", "MT": "tgt", "PG": "src"} and
            spec["input"]["sequence_a_template"] ==
            "TASK: {task}\nREFERENCE:\n{reference}" and
            spec["input"]["sequence_b_template"] == "HYPOTHESIS:\n{hyp}" and
            spec["input"]["tokenization"] ==
            {"add_special_tokens": True, "truncation": "longest_first",
             "max_length": 512, "batch_padding": "longest_in_batch"},
            "frozen text input")
    require(spec["model"]["id"] == MODEL_ID and
            spec["model"]["revision"] == REVISION and
            spec["model"]["num_labels"] == 2 and
            spec["model"]["id2label"] ==
            {"0": "not_hallucination", "1": "hallucination"} and
            spec["model"]["label2id"] ==
            {"not_hallucination": 0, "hallucination": 1},
            "pinned model/class mapping")
    train = spec["training"]
    require({name: train[name] for name in (
                "optimizer", "learning_rate", "weight_decay", "epochs",
                "train_batch_size", "evaluation_batch_size",
                "gradient_accumulation_steps", "effective_train_batch_size",
                "warmup_ratio", "gradient_clip_max_norm", "random_seed",
                "precision", "loss", "oversampling", "early_stopping",
                "checkpoint_selection")} == {
            "optimizer": "torch.optim.AdamW", "learning_rate": 1e-5,
            "weight_decay": 0.01, "epochs": 5, "train_batch_size": 8,
            "evaluation_batch_size": 16, "gradient_accumulation_steps": 2,
            "effective_train_batch_size": 16, "warmup_ratio": 0.1,
            "gradient_clip_max_norm": 1.0, "random_seed": 42,
            "precision": "BF16 autocast on one A100-80GB",
            "loss": "weighted torch.nn.CrossEntropyLoss",
            "oversampling": False, "early_stopping": False,
            "checkpoint_selection": "final model after exactly five epochs; no held-out-based selection"},
            "frozen training settings")
    require(spec["output"]["classification_threshold"] == 0.5 and
            spec["output"]["hallucination_class_id"] == 1 and
            spec["output"]["oof_fields"] ==
            ["sample_id", "fold_id", "task", "gold_label", "predicted_class", "p_H"],
            "frozen probability/threshold")
    require(spec["data"]["canonical_path"] ==
            "codex/canonical_human_development_manifest.csv" and
            spec["data"]["folds_path"] == "codex/canonical_fold_assignments.csv" and
            spec["data"]["fold_ids"] == [1, 2, 3, 4, 5] and
            "pseudo" not in spec["data"]["training_rule"].lower(),
            "only canonical/fold data allowed")
    model_dir = model_dir or bundle / "model"
    require(all(sha_file(model_dir / name) == digest for name, digest in
                spec["model"]["local_assets_sha256"].items()),
            "pinned model mirror assets")
    require(sha_file(bundle / "E11A_REQUIREMENTS.lock.txt") ==
            spec["software"]["requirements_sha256"], "requirements lock")
    prepared = json.loads((bundle / "E11A_PREPARATION_MANIFEST.json")
                          .read_text(encoding="utf-8"))
    require(prepared["status"] == "PASS" and
            prepared["protocol_sha256"] == EXPECTED_SHA and
            prepared["canonical_sha256"] == spec["data"]["canonical_sha256"] and
            prepared["folds_sha256"] == spec["data"]["folds_sha256"],
            "prepared manifest provenance")
    fold_results = {}
    for frozen in spec["data"]["folds"]:
        fold_id = frozen["fold_id"]
        meta = prepared["folds"][str(fold_id)]
        train_path, heldout_path = bundle / meta["train_path"], bundle / meta["heldout_path"]
        require(sha_file(train_path) == meta["train_sha256"] and
                sha_file(heldout_path) == meta["heldout_sha256"],
                "prepared split hash: " + str(fold_id))
        training, heldout = read_jsonl(train_path), read_jsonl(heldout_path)
        train_ids = [r["sample_id"] for r in training]
        heldout_ids = [r["sample_id"] for r in heldout]
        counts = Counter(r["label"] for r in training)
        require(len(training) == frozen["train_rows"] and
                len(heldout) == frozen["heldout_rows"] and
                len(set(train_ids)) == len(train_ids) and
                len(set(heldout_ids)) == len(heldout_ids) and
                not (set(train_ids) & set(heldout_ids)) and
                len(set(train_ids) | set(heldout_ids)) == 561 and
                counts == {int(k): v for k, v in frozen["train_class_counts"].items()},
                "fold split/heldout leakage: " + str(fold_id))
        for row in training + heldout:
            require(set(row) == ALLOWED_ROW_FIELDS and row["task"] in
                    spec["reference_policy"] and
                    row["reference_field"] == spec["reference_policy"][row["task"]] and
                    row["label"] in (0, 1) and
                    row["text"].startswith(f"TASK: {row['task']}\nREFERENCE:\n") and
                    row["text_pair"].startswith("HYPOTHESIS:\n") and
                    bool(row["text"].split("REFERENCE:\n", 1)[1].strip()) and
                    bool(row["text_pair"].split("HYPOTHESIS:\n", 1)[1].strip()),
                    "prepared row representation")
        require(all(r["fold_id"] != fold_id for r in training) and
                all(r["fold_id"] == fold_id for r in heldout),
                "train/heldout fold membership")
        for class_id in (0, 1):
            calculated = len(training) / (2 * counts[class_id])
            require(math.isclose(calculated, frozen["class_weights"][str(class_id)],
                                 rel_tol=0, abs_tol=1e-12),
                    "class weight uses train labels only")
        fold_results[str(fold_id)] = {"train": len(training),
                                      "class_counts": dict(counts),
                                      "heldout": len(heldout), "overlap": 0}
    return {"status": "PASS", "protocol_sha256": EXPECTED_SHA,
            "folds": fold_results, "full_training_started": False}


def validate_local() -> dict:
    require(ROOT is not None, "local SHROOM checkout required")
    spec = load_protocol()
    canonical_path = ROOT / spec["data"]["canonical_path"]
    fold_path = ROOT / spec["data"]["folds_path"]
    require(sha_file(canonical_path) == spec["data"]["canonical_sha256"] and
            sha_file(fold_path) == spec["data"]["folds_sha256"],
            "canonical/fold source SHA")
    model_dir = ROOT / spec["model"]["local_mirror_dir"]
    result = validate_bundle(HERE, model_dir)
    canonical = csv_rows(canonical_path)
    fold_of = {r["canonical_id"]: int(r["fold_id"]) for r in csv_rows(fold_path)}
    by_id = {r["canonical_id"]: r for r in canonical}
    require(len(by_id) == len(fold_of) == 561 and set(by_id) == set(fold_of) and
            Counter(r["task"] for r in canonical) == spec["data"]["task_counts"] and
            {(r["label"], r["label_bin"]) for r in canonical} ==
            {("Not Hallucination", "0"), ("Hallucination", "1")},
            "canonical identity/labels")
    prepared = json.loads((HERE / "E11A_PREPARATION_MANIFEST.json").read_text())
    for fold_id in range(1, 6):
        meta = prepared["folds"][str(fold_id)]
        training_text_keys = {r["exact_text_key"] for r in canonical
                              if fold_of[r["canonical_id"]] != fold_id}
        heldout_text_keys = {r["exact_text_key"] for r in canonical
                             if fold_of[r["canonical_id"]] == fold_id}
        require(not (training_text_keys & heldout_text_keys),
                "exact canonical text duplicated across held-out fold")
        actual = (read_jsonl(HERE / meta["train_path"]) +
                  read_jsonl(HERE / meta["heldout_path"]))
        require({r["sample_id"]: r for r in actual} == {
            cid: text_row(row, fold_of[cid], spec) for cid, row in by_id.items()},
            "text pair or label differs from canonical source")
    return result


if __name__ == "__main__":
    print(json.dumps(validate_local(), indent=2))
