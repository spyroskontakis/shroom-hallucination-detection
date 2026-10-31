"""CPU-only E11-A text-pair preparation from the frozen 561 human rows."""

from __future__ import annotations

import csv
import hashlib
import json
from collections import Counter
from pathlib import Path

from scoring_common import HERE, ROOT, require, sha_file

PROTOCOL = HERE / "E11A_TRAINING_PROTOCOL.json"
PREPARED = HERE / "e11a_prepared"
MANIFEST = HERE / "E11A_PREPARATION_MANIFEST.json"


def load_protocol() -> dict:
    value = json.loads(PROTOCOL.read_text(encoding="utf-8"))
    content = {k: v for k, v in value.items() if k != "protocol_sha256"}
    encoded = json.dumps(content, sort_keys=True, ensure_ascii=False,
                         separators=(",", ":"), allow_nan=False).encode("utf-8")
    require(hashlib.sha256(encoded).hexdigest() == value["protocol_sha256"] and
            value["status"] == "FROZEN_BEFORE_E11A_TRAINING", "E11-A protocol changed")
    return value


def csv_rows(path: Path) -> list[dict]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def jsonl_bytes(rows: list[dict]) -> bytes:
    return b"".join(json.dumps(row, ensure_ascii=False, separators=(",", ":"),
                               allow_nan=False).encode("utf-8") + b"\n" for row in rows)


def write_once(path: Path, data: bytes) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        require(path.read_bytes() == data, "prepared E11-A bytes changed: " + str(path))
    else:
        with path.open("xb") as handle:
            handle.write(data)
    return hashlib.sha256(data).hexdigest()


def text_row(row: dict, fold_id: int, spec: dict) -> dict:
    task = row["task"]
    field = spec["reference_policy"][task]
    reference = row[field]
    hypothesis = row["hyp"]
    require(isinstance(reference, str) and reference.strip() and
            isinstance(hypothesis, str) and hypothesis.strip(),
            "empty task reference or hypothesis")
    text = spec["input"]["sequence_a_template"].format(task=task,
                                                         reference=reference)
    text_pair = spec["input"]["sequence_b_template"].format(hyp=hypothesis)
    label = int(row[spec["data"]["label_column"]])
    require(label in (0, 1) and (row["label"], label) in
            {("Not Hallucination", 0), ("Hallucination", 1)},
            "canonical label orientation")
    return {"sample_id": row["canonical_id"], "fold_id": fold_id,
            "task": task, "reference_field": field,
            "text": text, "text_pair": text_pair, "label": label}


def main() -> dict:
    spec = load_protocol()
    require(ROOT is not None, "local SHROOM checkout required")
    source = ROOT / spec["data"]["canonical_path"]
    fold_path = ROOT / spec["data"]["folds_path"]
    require(sha_file(source) == spec["data"]["canonical_sha256"] and
            sha_file(fold_path) == spec["data"]["folds_sha256"],
            "canonical or locked fold hash drift")
    human, folds = csv_rows(source), csv_rows(fold_path)
    fold_of = {r["canonical_id"]: int(r["fold_id"]) for r in folds}
    require(len(human) == len(folds) == len(fold_of) == 561 and
            {r["canonical_id"] for r in human} == set(fold_of) and
            Counter(r["task"] for r in human) == spec["data"]["task_counts"],
            "canonical/fold population")
    all_rows = [text_row(row, fold_of[row["canonical_id"]], spec) for row in human]
    result = {"status": "PASS", "protocol_sha256": spec["protocol_sha256"],
              "canonical_sha256": spec["data"]["canonical_sha256"],
              "folds_sha256": spec["data"]["folds_sha256"], "folds": {}}
    for expected in spec["data"]["folds"]:
        fold_id = expected["fold_id"]
        train = [r for r in all_rows if r["fold_id"] != fold_id]
        heldout = [r for r in all_rows if r["fold_id"] == fold_id]
        train_ids = {r["sample_id"] for r in train}
        heldout_ids = {r["sample_id"] for r in heldout}
        counts = Counter(r["label"] for r in train)
        require(len(train) == expected["train_rows"] and
                len(heldout) == expected["heldout_rows"] and
                not (train_ids & heldout_ids) and
                len(train_ids | heldout_ids) == 561 and
                {str(k): v for k, v in counts.items()} ==
                expected["train_class_counts"], "fold split/class count")
        folder = PREPARED / f"fold_{fold_id}"
        train_path, heldout_path = folder / "train.jsonl", folder / "heldout.jsonl"
        train_sha = write_once(train_path, jsonl_bytes(train))
        heldout_sha = write_once(heldout_path, jsonl_bytes(heldout))
        result["folds"][str(fold_id)] = {
            "train_path": str(train_path.relative_to(HERE)).replace("\\", "/"),
            "train_sha256": train_sha, "train_rows": len(train),
            "train_class_counts": {"0": counts[0], "1": counts[1]},
            "heldout_path": str(heldout_path.relative_to(HERE)).replace("\\", "/"),
            "heldout_sha256": heldout_sha, "heldout_rows": len(heldout),
            "train_heldout_overlap": 0,
        }
    output = json.dumps(result, ensure_ascii=False, indent=2,
                        allow_nan=False).encode("utf-8") + b"\n"
    write_once(MANIFEST, output)
    return result


if __name__ == "__main__":
    print(json.dumps(main(), indent=2))
