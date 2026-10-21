"""Read-only verification of the completed E11-B teacher and pseudo-label files."""

from __future__ import annotations

import json
import math
from collections import Counter, defaultdict
from pathlib import Path

from scoring_common import HERE, FROZEN_PROTOCOL_CONTENT_SHA, read_jsonl, require, sha_file
from scoring_common import protocol as load_protocol

TASKS = ("DM", "MT", "PG")


def verify() -> dict:
    spec = load_protocol()
    require(spec["protocol_sha256"] == FROZEN_PROTOCOL_CONTENT_SHA, "protocol SHA")
    manifest_path = HERE / "E11_PSEUDOLABEL_MANIFEST.json"
    audit_path = HERE / "E11_PSEUDOLABEL_AUDIT.md"
    report = json.loads(manifest_path.read_text(encoding="utf-8"))
    require(report["status"] == "PASS" and report["teacher_fit_count"] == 5 and
            report["protocol_sha256"] == FROZEN_PROTOCOL_CONTENT_SHA and
            report["feature_order"] == spec["teacher"]["feature_order"] and
            report["thresholds"] == spec["leakage_and_selection"]["thresholds"],
            "teacher manifest/protocol contract")
    require(report["human_feature_coverage"] == 561 and
            report["unlabeled_feature_coverage"] == 28649 and
            report["student_trained"] is False and
            report["official_test_accessed"] is False and
            report["gpu_inference_run"] is False, "stage scope")
    require(audit_path.is_file(), "audit missing")
    cross = defaultdict(Counter)
    fold_validation = {}
    for fold_id in range(1, 6):
        key = str(fold_id)
        stats = report["folds"][key]
        paths = report["fold_artifacts"][key]
        for name, info in paths.items():
            path = Path(info["path"])
            require(path.is_file() and sha_file(path) == info["sha256"] and
                    path.stat().st_size == info["bytes"],
                    "fold artifact changed: " + key + "/" + name)
        parameters = json.loads(Path(paths["teacher_parameters.json"]["path"])
                                .read_text(encoding="utf-8"))
        metadata = json.loads(Path(paths["teacher_metadata.json"]["path"])
                              .read_text(encoding="utf-8"))
        require(parameters["fold_id"] == metadata["fold_id"] == fold_id and
                parameters["feature_order"] == report["feature_order"] and
                parameters["classes_"] == [0, 1] and
                parameters["hallucination_predict_proba_column"] == 1 and
                parameters["converged"] == stats["teacher_converged"] and
                len(parameters["coef_"]) == 1 and
                len(parameters["coef_"][0]) == 9 and
                all(math.isfinite(v) for v in parameters["coef_"][0] +
                    parameters["intercept_"]) and
                parameters["configuration"] == spec["teacher"]["configuration"],
                "teacher parameter contract")
        eligible = read_jsonl(Path(paths["eligible_unlabeled_manifest.jsonl"]["path"]))
        scored = read_jsonl(Path(paths["eligible_teacher_scores.jsonl"]["path"]))
        retained = read_jsonl(Path(paths["retained_pseudo_labels.jsonl"]["path"]))
        eligible_keys = [row["sample_key"] for row in eligible]
        scored_keys = [row["sample_key"] for row in scored]
        require(len(eligible) == len(scored) == stats["eligible_unlabeled"] and
                len(set(eligible_keys)) == len(eligible) and
                eligible_keys == scored_keys and
                len(retained) == stats["retained_after_balancing"] <= 24000,
                "fold key/count coverage")
        assignments = {task: Counter() for task in TASKS}
        for eligible_row, score_row in zip(eligible, scored):
            p = score_row["teacher_p_H"]
            expected = "H" if p >= 0.95 else "NH" if p <= 0.05 else "uncertain"
            require(score_row["fold_id"] == eligible_row["fold_id"] == fold_id and
                    score_row["task"] == eligible_row["task"] and
                    type(p) in (float, int) and math.isfinite(p) and 0 <= p <= 1 and
                    score_row["assignment"] == expected,
                    "fold score/threshold contract")
            assignments[score_row["task"]][expected] += 1
            cross[score_row["sample_key"]][expected] += 1
        for task in TASKS:
            t = stats["per_task"][task]
            require(assignments[task]["H"] == t["accepted_H"] and
                    assignments[task]["NH"] == t["accepted_NH"] and
                    sum(assignments[task].values()) == t["eligible"] and
                    t["retained_H"] == t["retained_NH"] ==
                    min(t["accepted_H"], t["accepted_NH"], 4000),
                    "per-task acceptance/balance: " + key + "/" + task)
        require(sum(assignments[t]["uncertain"] for t in TASKS) ==
                stats["uncertain_discarded"] and
                sum(assignments[t]["H"] + assignments[t]["NH"] for t in TASKS) ==
                stats["accepted_before_balancing"] and
                stats["retained_after_balancing"] == sum(
                    t["retained_H"] + t["retained_NH"]
                    for t in stats["per_task"].values()), "fold aggregate counts")
        for row in retained:
            require(row["source"] == "pseudo" and row["fold_id"] == fold_id and
                    row["teacher_protocol_sha256"] == FROZEN_PROTOCOL_CONTENT_SHA and
                    row["reference_field_used"] == spec["reference_policy"][row["task"]],
                    "retained provenance")
        fold_validation[key] = {"eligible": len(eligible), "accepted":
                                stats["accepted_before_balancing"],
                                "retained": len(retained), "status": "PASS"}
    conflicts = sum(c["H"] > 0 and c["NH"] > 0 for c in cross.values())
    require(len(cross) == 28649 and conflicts ==
            report["cross_fold_diagnostics"]["high_confidence_conflict_keys"],
            "cross-fold diagnostics")
    return {"status": "PASS", "folds": fold_validation,
            "high_confidence_conflicts": conflicts,
            "manifest_sha256": sha_file(manifest_path),
            "audit_sha256": sha_file(audit_path),
            "teacher_stage_code_sha256": sha_file(HERE / "run_teacher_stage.py")}


if __name__ == "__main__":
    print(json.dumps(verify(), indent=2))
