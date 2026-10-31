"""Read-only E11-B protocol/hash/leakage validation; no inference or model fitting."""

from __future__ import annotations

import csv
import hashlib
import json
import unicodedata
from collections import Counter
from pathlib import Path
from scoring_common import find_local_repo_root


HERE = Path(__file__).resolve().parent
ROOT = find_local_repo_root(HERE)
PROTOCOL = HERE / "E11_TEACHER_PROTOCOL.json"
LABEL_FIELDS = {"label", "labels", "label_bin", "p(Hallucination)", "p_hallucination"}


def sha_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def normalize(value: object) -> str:
    if value is None:
        text = ""
    elif isinstance(value, (list, dict)):
        text = json.dumps(value, ensure_ascii=False, sort_keys=True)
    else:
        text = str(value)
    return " ".join(unicodedata.normalize("NFC", text).strip().split())


def key(*parts: object) -> str:
    return hashlib.sha256("\u241f".join(normalize(p) for p in parts).encode("utf-8")).hexdigest()


def ref(row: dict, policy: dict) -> str:
    task = row["task"]
    assert task in policy, task
    value = row[policy[task]]
    assert isinstance(value, str) and value.strip(), task
    return value


def keys(row: dict, policy: dict) -> dict[str, str]:
    return {
        "full": key(row["task"], row["src"], row["tgt"], row["hyp"]),
        "hyp": key(row["hyp"]),
        "task_ref": key(row["task"], ref(row, policy)),
        "pair": key(row["task"], row["src"], row["tgt"]),
    }


def checked_file(info: dict) -> Path:
    path = ROOT / info["path"]
    assert path.is_file() and sha_file(path) == info["sha256"], path
    return path


def main() -> None:
    assert ROOT is not None, "local SHROOM repository root not found"
    p = json.loads(PROTOCOL.read_text(encoding="utf-8"))
    payload = {k: v for k, v in p.items() if k != "protocol_sha256"}
    canonical = json.dumps(payload, sort_keys=True, ensure_ascii=False,
                           separators=(",", ":"), allow_nan=False).encode("utf-8")
    assert hashlib.sha256(canonical).hexdigest() == p["protocol_sha256"]
    assert p["status"] == "FROZEN_BEFORE_PSEUDO_LABEL_GENERATION"
    assert p["reference_policy"] == {"DM": "tgt", "MT": "tgt", "PG": "src"}
    assert p["teacher"]["feature_order"] == [
        "factcg_support_probability", "minicheck_support_probability",
        "hhem_ref_hyp_consistency", "nli_ref_hyp_entailment", "nli_ref_hyp_neutral",
        "nli_ref_hyp_contradiction", "task_DM", "task_MT", "task_PG"]
    assert p["teacher"]["configuration"] == {
        "penalty": "l2", "C": 1.0, "solver": "lbfgs",
        "class_weight": "balanced", "max_iter": 2000, "random_state": 42}
    assert p["teacher"]["fit_count"] == 5
    assert p["leakage_and_selection"]["maximum_pseudo_rows_per_fold"] == 24000
    assert p["normalization"]["source_sha256"] == sha_file(
        ROOT / p["normalization"]["source"].split("::")[0])
    assert p["leakage_and_selection"]["thresholds"] == {
        "hallucination_min_inclusive": 0.95,
        "not_hallucination_max_inclusive": 0.05}
    assert p["leakage_and_selection"]["per_task_per_class_cap"] == 4000

    for detector in p["detectors"].values():
        source = ROOT / detector["implementation"]
        assert source.is_file() and sha_file(source) == detector["implementation_sha256"]

    canonical_path = checked_file(p["inputs"]["canonical_human"])
    folds_path = checked_file(p["inputs"]["locked_folds"])
    unlabeled_path = checked_file(p["inputs"]["unlabeled"])
    with canonical_path.open(encoding="utf-8", newline="") as handle:
        humans = list(csv.DictReader(handle))
    with folds_path.open(encoding="utf-8", newline="") as handle:
        folds = list(csv.DictReader(handle))
    assert len(humans) == len(folds) == 561
    assert len({r["canonical_id"] for r in humans}) == 561
    assert {r["canonical_id"] for r in humans} == {r["canonical_id"] for r in folds}
    fold_of = {r["canonical_id"]: int(r["fold_id"]) for r in folds}
    assert [Counter(fold_of.values())[f] for f in range(1, 6)] == [113, 112, 112, 112, 112]
    for row in humans:
        assert row["task"] in p["reference_policy"]
        assert row["label_bin"] in {"0", "1"}
        assert normalize(row["hyp"]) and normalize(ref(row, p["reference_policy"]))

    unlabeled = json.loads(unlabeled_path.read_text(encoding="utf-8"))
    assert len(unlabeled) == 30000
    assert all(not (LABEL_FIELDS & row.keys()) for row in unlabeled)
    assert Counter(r["task"] for r in unlabeled) == {"DM": 10000, "MT": 10000, "PG": 10000}
    policy = p["reference_policy"]
    unique = {}
    for index, row in enumerate(unlabeled):
        assert set(row) == {"task", "src", "tgt", "hyp", "ref", "model"}
        assert normalize(row["hyp"]) and normalize(ref(row, policy))
        row_keys = keys(row, policy)
        unique.setdefault(row_keys["full"], (index, row_keys))
    assert len(unique) == p["inputs"]["unlabeled"]["unique_normalized_full_samples"]

    # Set comparisons use held-out TEXT only; no held-out label is read here.
    summary = {}
    for fold in range(1, 6):
        heldout = [r for r in humans if fold_of[r["canonical_id"]] == fold]
        heldout_keys = [keys(r, policy) for r in heldout]
        blocked = {kind: {k[kind] for k in heldout_keys} for kind in
                   ("full", "hyp", "task_ref", "pair")}
        kept = [item for item in unique.values() if not any(
            item[1][kind] in blocked[kind] for kind in blocked)]
        training = [r for r in humans if fold_of[r["canonical_id"]] != fold]
        training = [r for r in training if
                    keys(r, policy)["hyp"] not in blocked["hyp"] and
                    keys(r, policy)["task_ref"] not in blocked["task_ref"]]
        assert all(fold_of[r["canonical_id"]] != fold for r in training)
        assert all(not any(item[1][kind] in blocked[kind] for kind in blocked)
                   for item in kept)
        summary[str(fold)] = {"heldout_human": len(heldout),
                              "training_human_after_text_purge": len(training),
                              "unlabeled_after_text_purge": len(kept)}

    # Feasibility is local-artifact presence; remote A100 loads were recorded separately.
    nli_weights = ROOT / "RAG/results/rag_e6_v2/model/model.safetensors"
    hhem_weights = ROOT / "RAG/results/rag_e6_v3/model/pytorch_model.bin"
    assert nli_weights.is_file() and nli_weights.stat().st_size == 870182606
    assert hhem_weights.is_file() and hhem_weights.stat().st_size == 737761269
    for name, common in [
        ("nli", "RAG/results/rag_e6_v2/scripts/v2_common.py"),
        ("hhem", "RAG/results/rag_e6_v3/scripts/v3_common.py"),
    ]:
        constants = (ROOT / common).read_text(encoding="utf-8")
        spec = p["detectors"][name]
        assert "MODEL_ID='" + spec["model_id"] + "'" in constants
        assert "REVISION='" + spec["revision"] + "'" in constants
    nli_config = json.loads((ROOT / "RAG/results/rag_e6_v2/model/config.json").read_text(encoding="utf-8"))
    hhem_config = json.loads((ROOT / "RAG/results/rag_e6_v3/model/config.json").read_text(encoding="utf-8"))
    assert {int(k): v for k, v in nli_config["id2label"].items()} == {
        0: "entailment", 1: "neutral", 2: "contradiction"}
    assert hhem_config["id2label"] == {"0": "LABEL_0"}
    for name, report in [
        ("factcg", "RAG/results/phase3_e9_claim_verification/factcg_gpu/returned_phase3-003/FACTCG_GPU_REPORT.json"),
        ("minicheck", "RAG/results/phase3_e9_claim_verification/minicheck_gpu/returned_phase3-003/MINICHECK_GPU_REPORT.json"),
    ]:
        record = json.loads((ROOT / report).read_text(encoding="utf-8"))
        assert record["status"] == "PASS" and record["model_loaded"]
        assert record["model_id"] == p["detectors"][name]["model_id"]
        assert record["model_revision"] == p["detectors"][name]["revision"]
        manifest_path = (ROOT / "RAG/results/phase3_e9_claim_verification" /
                         (name + "_gpu") / "GPU_RUN_MANIFEST.json")
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        assert manifest["model_id"] == record["model_id"]
        assert manifest["model_revision"] == record["model_revision"]

    print(json.dumps({"status": "PASS", "protocol_sha256": p["protocol_sha256"],
                      "raw_unlabeled": len(unlabeled), "deduplicated_unlabeled": len(unique),
                      "folds": summary, "inference_or_training_run": False}, indent=2))


if __name__ == "__main__":
    main()
