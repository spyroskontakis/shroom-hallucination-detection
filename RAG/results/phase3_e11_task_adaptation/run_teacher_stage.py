"""Local-only frozen E11-B teacher fits and fold-specific pseudo-label audit.

This script never invokes a detector, Modal function, student trainer, or test data.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import platform
import warnings
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np
import sklearn
from sklearn.exceptions import ConvergenceWarning
from sklearn.linear_model import LogisticRegression

from scoring_common import (HERE, ROOT, FROZEN_PROTOCOL_CONTENT_SHA, POLICY,
                            read_jsonl, reference, require, sha_file, text_keys)
from scoring_common import protocol as load_protocol
from validate_scoring_outputs import validate_download

DETECTORS = ("factcg", "minicheck", "hhem", "nli")
TASKS = ("DM", "MT", "PG")
FEATURES = (
    "factcg_support_probability", "minicheck_support_probability",
    "hhem_ref_hyp_consistency", "nli_ref_hyp_entailment",
    "nli_ref_hyp_neutral", "nli_ref_hyp_contradiction",
    "task_DM", "task_MT", "task_PG",
)
EXPECTED_ELIGIBLE = (28575, 28623, 28627, 28611, 28615)
CONFIG = {"penalty": "l2", "C": 1.0, "solver": "lbfgs",
          "class_weight": "balanced", "max_iter": 2000, "random_state": 42}
RAW_DEFAULT = HERE / "downloaded_full" / "e11-full-001-verified"
STAGE = HERE / "teacher_stage"


def checked(path: Path, expected: str) -> Path:
    require(path.is_file() and sha_file(path) == expected,
            "SHA256 mismatch or missing: " + str(path))
    return path


def csv_rows(path: Path) -> list[dict]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def strict_number(value: object, name: str) -> float:
    number = float(value)
    require(math.isfinite(number) and 0 <= number <= 1,
            "invalid probability: " + name)
    return number


def json_bytes(value: object) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n").encode("utf-8")


def jsonl_bytes(rows: list[dict]) -> bytes:
    return b"".join(json.dumps(row, ensure_ascii=False, separators=(",", ":"),
                               allow_nan=False).encode("utf-8") + b"\n" for row in rows)


def write_once(path: Path, data: bytes) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        require(path.read_bytes() == data, "existing output differs: " + str(path))
    else:
        with path.open("xb") as handle:
            handle.write(data)
    return hashlib.sha256(data).hexdigest()


def hard_protocol(spec: dict) -> None:
    require(spec["protocol_sha256"] == FROZEN_PROTOCOL_CONTENT_SHA,
            "frozen protocol digest")
    require(spec["reference_policy"] == POLICY == {"DM": "tgt", "MT": "tgt", "PG": "src"},
            "reference policy")
    require(tuple(spec["teacher"]["feature_order"]) == FEATURES and len(FEATURES) == 9,
            "teacher feature order")
    require(spec["teacher"]["configuration"] == CONFIG and
            spec["teacher"]["fit_intercept"] is True and
            spec["teacher"]["fit_count"] == 5,
            "teacher configuration")
    require(spec["inputs"]["canonical_human"]["hallucination_label"] == 1,
            "hallucination label orientation")
    selection = spec["leakage_and_selection"]
    require(selection["thresholds"] == {"hallucination_min_inclusive": 0.95,
                                       "not_hallucination_max_inclusive": 0.05} and
            selection["per_task_per_class_cap"] == 4000 and
            selection["maximum_pseudo_rows_per_fold"] == 24000,
            "frozen thresholds or cap")
    require("task+source+target pair" in selection["unlabeled_fold_purge"],
            "four-key frozen unlabeled purge")


def validate_raw(raw_dir: Path, spec: dict, scoring: dict, master: list[dict],
                 human_inputs: list[dict]) -> tuple[dict, dict, dict]:
    report = validate_download(raw_dir, "full")
    require(report["status"] == "PASS", "raw score validation")
    complete_path = raw_dir / "runs/e11-full-001/COMPLETE.json"
    complete = json.loads(complete_path.read_text(encoding="utf-8"))
    require((complete["status"], complete["mode"], complete["run_id"], complete["volume"]) ==
            ("PASS", "full", "e11-full-001", "shroom-e11-raw-detector-scores"),
            "completed Modal run provenance")
    require(complete["stages"] == [["minicheck", "human"],
                                    *[[name, "full"] for name in
                                      ("minicheck", "factcg", "nli", "hhem")]],
            "completed stage order")
    master_keys = {row["sample_key"] for row in master}
    human_keys = {row["sample_key"] for row in human_inputs}
    score_by_detector, source_hashes = {}, {"complete": sha_file(complete_path)}
    for detector in (*DETECTORS, "human_minicheck"):
        human = detector == "human_minicheck"
        kind = "minicheck" if human else detector
        folder = (raw_dir / "human_minicheck" if human else
                  raw_dir / "raw_detector_scores" / detector)
        score_path = folder / "scores.jsonl"
        rows = read_jsonl(score_path)
        expected_keys = human_keys if human else master_keys
        require(len(rows) == len(expected_keys) == (561 if human else 28649),
                "raw score row count: " + detector)
        by_key = {row["sample_key"]: row for row in rows}
        require(len(by_key) == len(rows) and set(by_key) == expected_keys,
                "raw score key universe: " + detector)
        score_by_detector[detector] = by_key
        source_hashes[detector] = sha_file(score_path)
        meta = json.loads((folder / "manifest.json").read_text(encoding="utf-8"))
        validation = json.loads((folder / f"validation_{'human' if human else 'full'}.json")
                                .read_text(encoding="utf-8"))
        require(meta["protocol_sha256"] == validation["protocol_sha256"] ==
                FROZEN_PROTOCOL_CONTENT_SHA and
                meta["model_id"] == spec["detectors"][kind]["model_id"] and
                meta["revision"] == spec["detectors"][kind]["revision"] and
                meta["detector"] == kind,
                "raw model/protocol provenance: " + detector)
        universe_hash = scoring["prepared_sha256"][
            "human_whole_hyp_minicheck_inputs.jsonl" if human else "unlabeled_master.jsonl"]
        require(meta["universe_sha256"] == validation["requested_input_sha256"] ==
                universe_hash and meta["universe_rows"] == meta["completed_rows"] ==
                len(expected_keys) and meta["scores_sha256"] == validation["scores_sha256"] ==
                source_hashes[detector] and validation["status"] == "PASS" and
                validation["requested_rows"] == validation["store_rows"] ==
                len(expected_keys), "raw checkpoint/report mismatch: " + detector)
    return score_by_detector, source_hashes, report


def vector(scores: dict, task: str) -> list[float]:
    require(task in TASKS, "unknown task")
    values = [strict_number(scores[name], name) for name in FEATURES[:6]]
    require(abs(sum(values[3:6]) - 1) <= 2e-6, "NLI probability sum")
    return [*values, *(int(task == name) for name in TASKS)]


def summaries(values: list[float]) -> dict:
    if not values:
        return {"min": None, "median": None, "max": None}
    return {"min": float(min(values)), "median": float(np.median(values)),
            "max": float(max(values))}


def main(raw_dir: Path, preflight_only: bool = False) -> dict:
    # No source data is loaded before the immutable protocol check.
    spec = load_protocol()
    hard_protocol(spec)
    require(ROOT is not None, "local checkout required")
    scoring = json.loads((HERE / "E11_SCORING_MANIFEST.json").read_text(encoding="utf-8"))
    require(scoring["protocol_sha256"] == spec["protocol_sha256"],
            "scoring manifest protocol mismatch")
    for name, digest in scoring["prepared_sha256"].items():
        checked(HERE / name, digest)
    master = read_jsonl(HERE / "unlabeled_master.jsonl")
    human_inputs = read_jsonl(HERE / "human_whole_hyp_minicheck_inputs.jsonl")
    require(len(master) == len({r["sample_key"] for r in master}) == 28649 and
            len(human_inputs) == len({r["sample_key"] for r in human_inputs}) == 561,
            "prepared input keys")
    require(all(row["reference_text"] == reference(row) for row in master),
            "unlabeled task reference policy")
    scores, raw_hashes, raw_report = validate_raw(raw_dir, spec, scoring, master,
                                                  human_inputs)

    human = csv_rows(checked(HERE / "HUMAN_TEACHER_INPUTS.csv",
                             scoring["prepared_sha256"]["HUMAN_TEACHER_INPUTS.csv"]))
    canonical = csv_rows(checked(ROOT / spec["inputs"]["canonical_human"]["path"],
                                 spec["inputs"]["canonical_human"]["sha256"]))
    fold_rows = csv_rows(checked(ROOT / spec["inputs"]["locked_folds"]["path"],
                                 spec["inputs"]["locked_folds"]["sha256"]))
    require(len(human) == len(canonical) == len(fold_rows) == 561 and
            Counter(r["task"] for r in canonical) == {"DM": 211, "MT": 216, "PG": 134},
            "human population")
    canonical_by_id = {r["canonical_id"]: r for r in canonical}
    fold_of = {r["canonical_id"]: int(r["fold_id"]) for r in fold_rows}
    human_by_id = {r["canonical_id"]: r for r in human}
    require(len(canonical_by_id) == len(fold_of) == len(human_by_id) == 561 and
            set(canonical_by_id) == set(fold_of) == set(human_by_id) ==
            {r["sample_key"] for r in human_inputs} == set(scores["human_minicheck"]),
            "human ID coverage")
    require([Counter(fold_of.values())[i] for i in range(1, 6)] ==
            [113, 112, 112, 112, 112], "locked fold sizes")
    fact_source = scoring["human_existing_score_sources"]["factcg"]
    e6_source = scoring["human_existing_score_sources"]["nli_hhem"]
    fact_rows = read_jsonl(checked(ROOT / fact_source["path"], fact_source["sha256"]))
    e6_rows = csv_rows(checked(ROOT / e6_source["path"], e6_source["sha256"]))
    fact_by_id = {r["canonical_id"]: r for r in fact_rows}
    e6_by_id = {r["canonical_id"]: r for r in e6_rows}
    require(len(fact_rows) == len(fact_by_id) == len(e6_rows) == len(e6_by_id) == 561 and
            set(fact_by_id) == set(e6_by_id) == set(canonical_by_id),
            "frozen human score source coverage")
    input_by_id = {r["sample_key"]: r for r in human_inputs}
    human_features = {}
    for cid, item in human_by_id.items():
        source = canonical_by_id[cid]
        require(item["task"] == source["task"] and int(item["fold_id"]) == fold_of[cid] and
                item["sample_key"] == cid and item["minicheck_support_probability"] == "" and
                input_by_id[cid]["reference_text"] == reference(source) and
                input_by_id[cid]["whole_hypothesis"] == source["hyp"],
                "human reference/fold/score-source contract")
        require(float(item["factcg_support_probability"]) ==
                float(fact_by_id[cid]["support_probability"]) and
                float(item["hhem_ref_hyp_consistency"]) ==
                float(e6_by_id[cid]["hhem_ref_hyp_consistency"]) and
                all(float(item["nli_ref_hyp_" + name]) ==
                    float(e6_by_id[cid]["nli2_ref_hyp_" + name])
                    for name in ("entailment", "neutral", "contradiction")),
                "human frozen signal reuse changed")
        row_scores = {name: item[name] for name in FEATURES[:6] if name !=
                      "minicheck_support_probability"}
        row_scores["minicheck_support_probability"] = scores["human_minicheck"][cid][
            "minicheck_support_probability"]
        human_features[cid] = vector(row_scores, item["task"])

    master_by_key = {r["sample_key"]: r for r in master}
    master_keys = [r["sample_key"] for r in master]
    unlabeled_features = np.asarray([
        vector({field: scores[detector][key][field] for detector in DETECTORS
                for field in spec["detectors"][detector].get("outputs", [
                    spec["detectors"][detector].get("output")])}, row["task"])
        for key, row in zip(master_keys, master)], dtype=np.float64)
    require(unlabeled_features.shape == (28649, 9) and
            np.isfinite(unlabeled_features).all(), "unlabeled 9-feature matrix")

    # Validate every frozen fold map against independent text-only recomputation
    # before the first teacher fit. The protocol's fourth key is task/src/tgt.
    fold_data = {}
    master_text_keys = [text_keys(r) for r in master]
    for fold_id in range(1, 6):
        heldout_text = [{name: r[name] for name in ("task", "src", "tgt", "hyp")}
                        for r in canonical if fold_of[r["canonical_id"]] == fold_id]
        blocked = {name: {text_keys(r)[name] for r in heldout_text}
                   for name in ("full", "hyp", "task_ref", "pair")}
        map_name = f"fold_{fold_id}_eligibility.jsonl"
        map_rows = read_jsonl(checked(HERE / map_name,
                                      scoring["prepared_sha256"][map_name]))
        require(len(map_rows) == 28649 and
                [r["sample_key"] for r in map_rows] == master_keys,
                "eligibility map universe/order")
        eligible_indices = []
        for index, (row, keys) in enumerate(zip(map_rows, master_text_keys)):
            first_match = next((name for name in ("full", "hyp", "task_ref", "pair")
                                if keys[name] in blocked[name]), None)
            require(row["eligible"] is (first_match is None) and
                    row["purge_reason"] == first_match,
                    f"frozen text purge drift: fold {fold_id}, row {index}")
            if first_match is None:
                eligible_indices.append(index)
        require(len(eligible_indices) == EXPECTED_ELIGIBLE[fold_id - 1],
                "frozen eligible count drift: fold " + str(fold_id))
        training_ids = [r["canonical_id"] for r in canonical
                        if fold_of[r["canonical_id"]] != fold_id and
                        text_keys(r)["hyp"] not in blocked["hyp"] and
                        text_keys(r)["task_ref"] not in blocked["task_ref"]]
        require(not any(fold_of[cid] == fold_id for cid in training_ids),
                "heldout human training leak")
        fold_data[fold_id] = (eligible_indices, training_ids)

    if preflight_only:
        return {"status": "PASS", "raw_score_integrity": raw_report,
                "human_feature_coverage": len(human_features),
                "unlabeled_feature_coverage": len(unlabeled_features),
                "folds": {str(fold_id): {"eligible": len(indices),
                                          "training_human": len(training_ids)}
                          for fold_id, (indices, training_ids) in fold_data.items()},
                "teacher_fits": 0}

    artifacts = {}
    fold_stats = {}
    cross = defaultdict(Counter)
    fit_count = 0
    for fold_id in range(1, 6):
        eligible_indices, training_ids = fold_data[fold_id]
        X = np.asarray([human_features[cid] for cid in training_ids], dtype=np.float64)
        # Gold labels are accessed only for the already filtered training IDs.
        y = np.asarray([int(canonical_by_id[cid]["label_bin"]) for cid in training_ids],
                       dtype=np.int64)
        require(X.shape == (len(training_ids), 9) and set(y.tolist()) == {0, 1},
                "human training matrix/classes")
        model = LogisticRegression(**CONFIG, fit_intercept=True)
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always", ConvergenceWarning)
            model.fit(X, y)
        fit_count += 1
        classes = model.classes_.tolist()
        require(classes.count(1) == 1 and set(classes) == {0, 1},
                "cannot prove hallucination predict_proba class")
        hallucination_column = classes.index(1)
        probabilities = model.predict_proba(unlabeled_features[eligible_indices])[:,
                                                              hallucination_column]
        require(len(probabilities) == len(eligible_indices) and
                np.isfinite(probabilities).all() and
                ((probabilities >= 0) & (probabilities <= 1)).all(),
                "teacher probability range")
        per_task = {task: {"eligible": 0, "accepted_H": 0, "accepted_NH": 0,
                           "retained_H": 0, "retained_NH": 0} for task in TASKS}
        accepted = {task: {"H": [], "NH": []} for task in TASKS}
        score_rows = []
        uncertain = 0
        for index, probability in zip(eligible_indices, probabilities):
            row = master[index]
            key, task, p_h = row["sample_key"], row["task"], float(probability)
            label = "H" if p_h >= 0.95 else "NH" if p_h <= 0.05 else "uncertain"
            cross[key][label] += 1
            per_task[task]["eligible"] += 1
            score_rows.append({"sample_key": key, "task": task, "fold_id": fold_id,
                               "teacher_p_H": p_h, "assignment": label})
            if label == "uncertain":
                uncertain += 1
            else:
                accepted[task][label].append((key, p_h))
        retained = []
        retained_prob = {"H": [], "NH": []}
        for task in TASKS:
            h = sorted(accepted[task]["H"], key=lambda pair: (-pair[1], pair[0]))
            nh = sorted(accepted[task]["NH"], key=lambda pair: (pair[1], pair[0]))
            n_keep = min(len(h), len(nh), 4000)
            per_task[task].update({"accepted_H": len(h), "accepted_NH": len(nh),
                                   "retained_H": n_keep, "retained_NH": n_keep})
            for label, chosen in (("H", h[:n_keep]), ("NH", nh[:n_keep])):
                for key, p_h in chosen:
                    row = master_by_key[key]
                    raw = {field: scores[detector][key][field]
                           for detector in DETECTORS
                           for field in spec["detectors"][detector].get("outputs", [
                               spec["detectors"][detector].get("output")])}
                    retained.append({
                        "sample_key": key, "task": task, "fold_id": fold_id,
                        "source": "pseudo", "reference_field_used": POLICY[task],
                        "src": row["src"], "tgt": row["tgt"], "hyp": row["hyp"],
                        "reference_text": row["reference_text"],
                        "whole_hypothesis": row["whole_hypothesis"],
                        "pseudo_label": 1 if label == "H" else 0,
                        "teacher_p_H": p_h, **raw,
                        "teacher_protocol_sha256": FROZEN_PROTOCOL_CONTENT_SHA,
                        "source_row_index": row["source_row_index"],
                        "unlabeled_source_sha256": row["provenance"],
                    })
                    retained_prob[label].append(p_h)
        total_retained = len(retained)
        require(total_retained <= 24000 and
                len({r["sample_key"] for r in retained}) == total_retained and
                all(per_task[t]["retained_H"] == per_task[t]["retained_NH"] for t in TASKS),
                "per-task balance/cap/unique pseudo labels")
        accepted_total = sum(v["accepted_H"] + v["accepted_NH"] for v in per_task.values())
        require(uncertain + accepted_total == len(eligible_indices),
                "threshold partition")
        warning_names = [type(w.message).__name__ for w in caught]
        converged = not any(issubclass(w.category, ConvergenceWarning) for w in caught)
        training_counts = Counter(y.tolist())
        fold_stats[str(fold_id)] = {
            "heldout_rows": [113, 112, 112, 112, 112][fold_id - 1],
            "human_training_rows": len(training_ids),
            "human_class_counts": {"0": training_counts[0], "1": training_counts[1]},
            "eligible_unlabeled": len(eligible_indices),
            "removed_by_leakage_purge": len(master) - len(eligible_indices),
            "per_task": per_task, "accepted_before_balancing": accepted_total,
            "retained_after_balancing": total_retained,
            "uncertain_discarded": uncertain,
            "accepted_removed_by_balancing": accepted_total - total_retained,
            "retained_p_H_H": summaries(retained_prob["H"]),
            "retained_p_H_NH": summaries(retained_prob["NH"]),
            "teacher_converged": converged, "teacher_n_iter": model.n_iter_.tolist(),
            "teacher_warning_types": warning_names,
        }
        folder = STAGE / f"fold_{fold_id}"
        parameters = {
            "fold_id": fold_id, "protocol_sha256": FROZEN_PROTOCOL_CONTENT_SHA,
            "model": "sklearn.linear_model.LogisticRegression", "configuration": CONFIG,
            "fit_intercept": True, "feature_order": list(FEATURES),
            "classes_": classes, "hallucination_class": 1,
            "hallucination_predict_proba_column": hallucination_column,
            "coef_": model.coef_.tolist(), "intercept_": model.intercept_.tolist(),
            "n_iter_": model.n_iter_.tolist(), "converged": converged,
        }
        metadata = {"fold_id": fold_id, "training_ids_sha256": hashlib.sha256(
            "\n".join(training_ids).encode("utf-8")).hexdigest(), **fold_stats[str(fold_id)],
            "eligibility_source": f"fold_{fold_id}_eligibility.jsonl",
            "eligibility_source_sha256": scoring["prepared_sha256"][
                f"fold_{fold_id}_eligibility.jsonl"]}
        fold_files = {
            "teacher_parameters.json": json_bytes(parameters),
            "teacher_metadata.json": json_bytes(metadata),
            "eligible_unlabeled_manifest.jsonl": jsonl_bytes([
                {"sample_key": master[i]["sample_key"], "task": master[i]["task"],
                 "fold_id": fold_id} for i in eligible_indices]),
            "eligible_teacher_scores.jsonl": jsonl_bytes(score_rows),
            "retained_pseudo_labels.jsonl": jsonl_bytes(retained),
        }
        artifacts[str(fold_id)] = {
            name: {"path": str(folder / name), "sha256": write_once(folder / name, data),
                   "bytes": len(data)} for name, data in fold_files.items()}

    require(fit_count == 5 and len(fold_stats) == 5, "exactly five teacher fits")
    conflict = sum(c["H"] > 0 and c["NH"] > 0 for c in cross.values())
    cross_summary = {
        "sample_keys": len(cross), "high_confidence_conflict_keys": conflict,
        "accepted_H_fold_assignments": sum(c["H"] for c in cross.values()),
        "accepted_NH_fold_assignments": sum(c["NH"] for c in cross.values()),
        "uncertain_fold_assignments": sum(c["uncertain"] for c in cross.values()),
        "eligible_fold_count_distribution": dict(sorted(Counter(
            sum(c.values()) for c in cross.values()).items())),
    }
    require(len(cross) == 28649 and
            sum(int(k) * v for k, v in cross_summary["eligible_fold_count_distribution"].items()) ==
            sum(EXPECTED_ELIGIBLE), "cross-fold score coverage")
    source_hashes = {
        "frozen_protocol_file": sha_file(HERE / "E11_TEACHER_PROTOCOL.json"),
        "scoring_manifest": sha_file(HERE / "E11_SCORING_MANIFEST.json"),
        "canonical_human": spec["inputs"]["canonical_human"]["sha256"],
        "locked_folds": spec["inputs"]["locked_folds"]["sha256"],
        "human_teacher_inputs": scoring["prepared_sha256"]["HUMAN_TEACHER_INPUTS.csv"],
        "human_factcg_e10": fact_source["sha256"],
        "human_nli_hhem_e6_v3": e6_source["sha256"],
        "unlabeled_master": scoring["prepared_sha256"]["unlabeled_master.jsonl"],
        **{f"raw_{name}": digest for name, digest in raw_hashes.items()},
    }
    manifest = {
        "status": "PASS", "stage": "E11-B_fold_specific_pseudo_labels",
        "protocol_sha256": FROZEN_PROTOCOL_CONTENT_SHA,
        "raw_run_id": "e11-full-001", "raw_score_integrity": raw_report,
        "human_feature_coverage": 561, "unlabeled_feature_coverage": 28649,
        "feature_order": list(FEATURES), "teacher_fit_count": fit_count,
        "thresholds": spec["leakage_and_selection"]["thresholds"],
        "folds": fold_stats, "cross_fold_diagnostics": cross_summary,
        "source_sha256": source_hashes, "fold_artifacts": artifacts,
        "software": {"python": platform.python_version(), "numpy": np.__version__,
                     "scikit_learn": sklearn.__version__},
        "student_trained": False, "official_test_accessed": False,
        "gpu_inference_run": False,
    }
    manifest_path = HERE / "E11_PSEUDOLABEL_MANIFEST.json"
    write_once(manifest_path, json_bytes(manifest))
    lines = ["# E11-B pseudo-label audit", "",
             f"Status: **PASS**. Protocol SHA256: `{FROZEN_PROTOCOL_CONTENT_SHA}`.",
             "Raw run: `e11-full-001`; all four unlabeled score files cover 28,649/28,649 keys; human whole-hypothesis MiniCheck covers 561/561.",
             "Human FactCG, HHEM, and NLI features reuse their previously frozen local sources. HHEM remains a support score and was not inverted.",
             "The locked fold IDs are **1–5**; the requested fold-0-through-4 counts map in that order to folds 1–5. The frozen purge includes the task/source/target pair check in addition to full sample, hypothesis, and task/reference.",
             "", "| Fold | Training | Class 0 | Class 1 | Eligible | Purged | Accepted | Retained | Uncertain | Balance dropped | Converged |",
             "| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | :---: |"]
    for fold_id in range(1, 6):
        s = fold_stats[str(fold_id)]
        lines.append(f"| {fold_id} | {s['human_training_rows']} | {s['human_class_counts']['0']} | {s['human_class_counts']['1']} | {s['eligible_unlabeled']} | {s['removed_by_leakage_purge']} | {s['accepted_before_balancing']} | {s['retained_after_balancing']} | {s['uncertain_discarded']} | {s['accepted_removed_by_balancing']} | {'yes' if s['teacher_converged'] else 'NO'} |")
    lines += ["", "| Fold | Task | Eligible | Accepted H | Accepted non-H | Retained H | Retained non-H | Retained total | % eligible retained |",
              "| ---: | :--- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |"]
    for fold_id in range(1, 6):
        for task in TASKS:
            t = fold_stats[str(fold_id)]["per_task"][task]
            total = t["retained_H"] + t["retained_NH"]
            lines.append(f"| {fold_id} | {task} | {t['eligible']} | {t['accepted_H']} | {t['accepted_NH']} | {t['retained_H']} | {t['retained_NH']} | {total} | {100 * total / t['eligible']:.2f}% |")
    lines += ["", "Retained p(H) ranges by fold (min / median / max):", ""]
    for fold_id in range(1, 6):
        s = fold_stats[str(fold_id)]
        lines.append(f"- Fold {fold_id}: H {s['retained_p_H_H']}; non-H {s['retained_p_H_NH']}; teacher iterations {s['teacher_n_iter']}.")
    lines += ["", f"Cross-fold high-confidence conflicts: **{conflict}** sample keys. A conflict means at least one eligible fold teacher accepted H and another accepted non-H; no global resolution or consensus file was made.",
              f"Cross-fold acceptance assignments: H {cross_summary['accepted_H_fold_assignments']}, non-H {cross_summary['accepted_NH_fold_assignments']}, uncertain {cross_summary['uncertain_fold_assignments']}.",
              "", "Each fold has its own teacher parameters, metadata, eligible-key manifest, complete eligible teacher scores, and retained pseudo-label JSONL in `teacher_stage/fold_<id>/`. Exact hashes, feature order, score-source provenance and software versions are in `E11_PSEUDOLABEL_MANIFEST.json`.",
              "", "No student training, OOF evaluation, official-test access, GPU inference, Modal function, protocol edit, commit, or push occurred in this stage.", ""]
    write_once(HERE / "E11_PSEUDOLABEL_AUDIT.md", "\n".join(lines).encode("utf-8"))
    return {"status": "PASS", "teacher_fits": fit_count,
            "folds": fold_stats, "cross_fold": cross_summary,
            "manifest": str(manifest_path),
            "audit": str(HERE / "E11_PSEUDOLABEL_AUDIT.md")}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raw-dir", type=Path, default=RAW_DEFAULT)
    parser.add_argument("--preflight-only", action="store_true")
    args = parser.parse_args()
    print(json.dumps(main(args.raw_dir, args.preflight_only), ensure_ascii=False, indent=2))
