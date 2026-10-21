"""Validate the single frozen E11-A five-fold return and report its OOF result.

Local analysis only. This script never loads or trains a model.
"""

from __future__ import annotations

import csv
import hashlib
import json
import math
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
from scipy.stats import binomtest, spearmanr

HERE = Path(__file__).resolve().parent
E11 = HERE.parent
sys.path.insert(0, str(E11))
from e11a_prepare_data import load_protocol  # noqa: E402
from scoring_common import ROOT, require, sha_file  # noqa: E402


def rows_csv(path: Path) -> list[dict]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def rows_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()
            if line.strip()]


def save_json(path: Path, value: dict) -> None:
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False,
                               allow_nan=False) + "\n", encoding="utf-8")


def metric(rows: list[dict], human: dict[str, dict]) -> dict:
    y = np.array([int(human[r["sample_id"]]["label_bin"]) for r in rows])
    predicted = np.array([r["predicted_class"] for r in rows])
    scores = np.array([r["p_H"] for r in rows], dtype=float)
    ratings = np.array([float(human[r["sample_id"]]["p_hallucination"])
                        for r in rows])
    tn = int(np.sum((y == 0) & (predicted == 0)))
    fp = int(np.sum((y == 0) & (predicted == 1)))
    fn = int(np.sum((y == 1) & (predicted == 0)))
    tp = int(np.sum((y == 1) & (predicted == 1)))
    n = len(rows)
    rho = float(spearmanr(scores, ratings).statistic) if n > 2 else None
    return {"n": n, "correct": tn + tp, "accuracy": (tn + tp) / n,
            "spearman": rho, "confusion_matrix": [[tn, fp], [fn, tp]],
            "precision": tp / (tp + fp) if tp + fp else None,
            "recall": tp / (tp + fn) if tp + fn else None,
            "f1": 2 * tp / (2 * tp + fp + fn) if 2 * tp + fp + fn else None}


def baseline(name: str, path: Path, metric_path: Path, expected: dict,
             human: dict[str, dict], folds: dict[str, int]) -> dict:
    saved = json.loads(metric_path.read_text(encoding="utf-8"))
    require(sha_file(path) == saved["oof_sha256"], f"{name} OOF SHA mismatch")
    data = rows_csv(path)
    require(len(data) == len(human) == 561 and
            {r["canonical_id"] for r in data} == set(human),
            f"{name} OOF IDs")
    by_id = {}
    for row in data:
        sid = row["canonical_id"]
        require(sid not in by_id and int(row["fold_id"]) == folds[sid],
                f"{name} duplicate or fold mismatch")
        p = float(row["prediction"])
        require(math.isfinite(p) and 0 <= p <= 1, f"{name} probability")
        by_id[sid] = p
    correct = sum((p >= 0.5) == (int(human[sid]["label_bin"]) == 1)
                  for sid, p in by_id.items())
    rho = float(spearmanr(
        [round(by_id[sid], 12) for sid in human],
        [float(human[sid]["p_hallucination"]) for sid in human]).statistic)
    require(correct == expected["correct"] and
            abs(correct / 561 - expected["accuracy"]) < 1e-12 and
            abs(rho - expected["spearman"]) < 1e-8,
            f"{name} saved metrics mismatch")
    return {"path": str(path), "sha256": sha_file(path),
            "correct": correct, "accuracy": correct / 561,
            "spearman": expected["spearman"], "scores": by_id}


def compare(rows: list[dict], human: dict[str, dict], base: dict) -> dict:
    new_good = np.array([r["predicted_class"] ==
                         int(human[r["sample_id"]]["label_bin"]) for r in rows])
    old_good = np.array([(base["scores"][r["sample_id"]] >= 0.5) ==
                         (int(human[r["sample_id"]]["label_bin"]) == 1)
                         for r in rows])
    corrections = int(np.sum(new_good & ~old_good))
    regressions = int(np.sum(~new_good & old_good))
    discordant = corrections + regressions
    p_value = float(binomtest(corrections, discordant, 0.5).pvalue)
    rng = np.random.default_rng(42)
    delta = new_good.astype(int) - old_good.astype(int)
    draws = rng.integers(0, len(rows), size=(10_000, len(rows)))
    bootstrap = delta[draws].mean(axis=1)
    ci = np.quantile(bootstrap, [0.025, 0.975]).tolist()
    return {"corrections": corrections, "regressions": regressions,
            "net_correct": corrections - regressions,
            "accuracy_difference": float(delta.mean()),
            "spearman_difference": metric(rows, human)["spearman"] - base["spearman"],
            "mcnemar_exact_two_sided_p": p_value,
            "paired_bootstrap": {"resamples": 10_000, "seed": 42,
                                 "accuracy_difference_ci95": ci}}


def main() -> dict:
    spec = load_protocol()
    require(ROOT is not None and spec["protocol_sha256"] ==
            "518c2df610a1483472b94e8baf3c0c4b277275f351e7448822e35d9dc871772d",
            "frozen protocol")
    canonical_path = ROOT / spec["data"]["canonical_path"]
    folds_path = ROOT / spec["data"]["folds_path"]
    require(sha_file(canonical_path) == spec["data"]["canonical_sha256"] and
            sha_file(folds_path) == spec["data"]["folds_sha256"],
            "canonical/fold SHA mismatch")
    human_rows = rows_csv(canonical_path)
    human = {r["canonical_id"]: r for r in human_rows}
    folds = {r["canonical_id"]: int(r["fold_id"]) for r in rows_csv(folds_path)}
    require(len(human_rows) == len(human) == len(folds) == 561 and
            set(human) == set(folds), "canonical population")

    all_rows = []
    fold_reports = {}
    hashes = {"protocol": sha_file(E11 / "E11A_TRAINING_PROTOCOL.json"),
              "canonical": sha_file(canonical_path), "locked_folds": sha_file(folds_path)}
    for fold_id in range(1, 6):
        folder = HERE / f"fold_{fold_id}"
        run_folder = folder / f"e11a-fold-{fold_id:03d}"
        if not run_folder.is_dir():
            run_folder = folder
        status_path = run_folder / "FOLD_PASS.json"
        pred_path = run_folder / "heldout_predictions.jsonl"
        checkpoint_path = run_folder / "final_checkpoint" / "model.safetensors"
        require(all(p.is_file() for p in (status_path, pred_path, checkpoint_path)),
                f"fold {fold_id} missing result artifact")
        status = json.loads(status_path.read_text(encoding="utf-8"))
        predictions = rows_jsonl(pred_path)
        expected_n = 113 if fold_id == 1 else 112
        require(status["status"] == "PASS" and status["mode"] == "fold" and
                status["fold_id"] == fold_id and
                status["run_id"] == f"e11a-fold-{fold_id:03d}" and
                status["protocol_sha256"] == spec["protocol_sha256"] and
                status["base_model_id"] == spec["model"]["id"] and
                status["base_revision"] == spec["model"]["revision"] and
                status["training_rows_used"] == spec["data"]["folds"][fold_id - 1]["train_rows"] and
                status["heldout_predictions"] == expected_n and
                len(status["loss_by_epoch"]) == 5 and
                status["losses_all_finite"] and
                math.isfinite(status["final_training_loss"]),
                f"fold {fold_id} status drift")
        require(sha_file(pred_path) == status["heldout_predictions_sha256"] and
                sha_file(checkpoint_path) == status["checkpoint_sha256"],
                f"fold {fold_id} output hash mismatch")
        prepared = rows_jsonl(E11 / "e11a_prepared" /
                              f"fold_{fold_id}" / "heldout.jsonl")
        heldout = {r["sample_id"]: r for r in prepared}
        require(len(prepared) == len(heldout) == len(predictions) == expected_n,
                f"fold {fold_id} heldout coverage")
        seen = set()
        for row in predictions:
            sid = row["sample_id"]
            require(sid in heldout and sid not in seen and sid in human and
                    row["fold_id"] == fold_id == folds[sid] and
                    row["task"] == heldout[sid]["task"] == human[sid]["task"] and
                    row["gold_label"] == heldout[sid]["label"] ==
                    int(human[sid]["label_bin"]) and
                    isinstance(row["p_H"], (int, float)) and
                    math.isfinite(row["p_H"]) and 0 <= row["p_H"] <= 1 and
                    row["predicted_class"] == int(row["p_H"] >= 0.5),
                    f"fold {fold_id} prediction mismatch")
            seen.add(sid)
        require(seen == set(heldout), f"fold {fold_id} missing ID")
        all_rows.extend(predictions)
        fold_reports[str(fold_id)] = {
            "status": "PASS", "training_rows": status["training_rows_used"],
            "heldout_rows": len(predictions),
            "training_seconds": status["elapsed_seconds"],
            "loss_by_epoch": status["loss_by_epoch"],
            "final_training_loss": status["final_training_loss"],
            "peak_gpu_memory_bytes": status["peak_gpu_memory_bytes"],
            "optimizer_steps": status["optimizer_steps"],
            "class_counts": status["fold_training_class_counts"],
            "class_weights": status["class_weights"],
            "checkpoint_sha256": sha_file(checkpoint_path),
            "heldout_predictions_sha256": sha_file(pred_path),
            "checkpoint_path": str(checkpoint_path),
            "heldout_predictions_path": str(pred_path),
            "metrics": metric(predictions, human)}
        hashes[f"fold_{fold_id}_checkpoint"] = sha_file(checkpoint_path)
        hashes[f"fold_{fold_id}_predictions"] = sha_file(pred_path)
        hashes[f"fold_{fold_id}_status"] = sha_file(status_path)

    ids = [r["sample_id"] for r in all_rows]
    require(len(ids) == len(set(ids)) == len(human) == 561 and
            set(ids) == set(human) and
            Counter(r["task"] for r in all_rows) == spec["data"]["task_counts"],
            "OOF population")
    all_rows.sort(key=lambda r: list(human).index(r["sample_id"]))
    oof_path = HERE / "E11A_OOF_PREDICTIONS.jsonl"
    oof_path.write_text("".join(json.dumps(r, ensure_ascii=False, allow_nan=False) + "\n"
                                for r in all_rows), encoding="utf-8", newline="\n")
    overall = metric(all_rows, human)
    task_metrics = {task: metric([r for r in all_rows if r["task"] == task], human)
                    for task in ("DM", "MT", "PG")}

    baseline_specs = {
        "E6-v3": (ROOT / "RAG/results/rag_e6_v3/evaluation/e6_v3_oof_predictions.csv",
                  ROOT / "RAG/results/rag_e6_v3/evaluation/e6_v3_metrics.json",
                  {"correct": 474, "accuracy": 474 / 561,
                   "spearman": 0.7816945786401444}),
        "E10": (ROOT / "RAG/results/phase3_e9_claim_verification/evaluation/E10/E10_oof.csv",
                ROOT / "RAG/results/phase3_e9_claim_verification/evaluation/E10/E10_metrics.json",
                {"correct": 475, "accuracy": 475 / 561,
                 "spearman": 0.7828092941190203}),
    }
    comparisons = {}
    for name, (path, metric_path, expected) in baseline_specs.items():
        try:
            base = baseline(name, path, metric_path, expected, human, folds)
            per_task_change = {}
            for task in ("DM", "MT", "PG"):
                task_ids = [r["sample_id"] for r in all_rows if r["task"] == task]
                baseline_correct = sum(
                    (base["scores"][sid] >= 0.5) ==
                    (int(human[sid]["label_bin"]) == 1) for sid in task_ids)
                per_task_change[task] = {
                    "baseline_correct": baseline_correct,
                    "e11a_correct": task_metrics[task]["correct"],
                    "net_correct": task_metrics[task]["correct"] - baseline_correct,
                }
            comparisons[name] = {"baseline_correct": base["correct"],
                                 "baseline_accuracy": base["accuracy"],
                                 "baseline_spearman": base["spearman"],
                                 "baseline_oof_path": base["path"],
                                 "baseline_oof_sha256": base["sha256"],
                                 "per_task_correct_change": per_task_change,
                                 **compare(all_rows, human, base)}
        except (AssertionError, KeyError, ValueError, OSError) as exc:
            comparisons[name] = {"paired_analysis": "UNAVAILABLE",
                                 "reason": str(exc)}

    results = {"status": "PASS", "experiment": "E11-A",
               "created_utc": datetime.now(timezone.utc).isoformat(),
               "protocol_sha256": spec["protocol_sha256"],
               "model_id": spec["model"]["id"],
               "base_revision": spec["model"]["revision"],
               "oof_rows": len(all_rows), "oof_unique_ids": len(set(ids)),
               "task_counts": dict(Counter(r["task"] for r in all_rows)),
               "overall": overall, "per_task": task_metrics,
               "folds": fold_reports, "comparisons": comparisons}
    result_path = HERE / "E11A_RESULTS.json"
    save_json(result_path, results)
    md = ["# E11-A frozen development result", "",
          f"Protocol content SHA-256: `{spec['protocol_sha256']}`. Five locked A100 folds, one seed (42), final epoch-5 checkpoints, 561/561 held-out predictions.",
          "", f"**Accuracy:** {overall['correct']}/561 = {overall['accuracy']:.9f}; **Spearman:** {overall['spearman']:.9f}.",
          "", "Confusion matrix (rows gold 0/1, columns predicted 0/1): " +
          f"`{overall['confusion_matrix']}`. " +
          f"Precision {overall['precision']:.9f}, recall {overall['recall']:.9f}, F1 {overall['f1']:.9f}.",
          "", "| Task | Correct / total | Accuracy | Spearman |", "|---|---:|---:|---:|"]
    for task, m in task_metrics.items():
        md.append(f"| {task} | {m['correct']}/{m['n']} | {m['accuracy']:.9f} | {m['spearman']:.9f} |")
    md += ["", "| Fold | Training rows | Held out | Correct | Train seconds | Final loss | Peak GPU GiB |", "|---|---:|---:|---:|---:|---:|---:|"]
    for fold_id, f in fold_reports.items():
        md.append(f"| {fold_id} | {f['training_rows']} | {f['heldout_rows']} | {f['metrics']['correct']} | {f['training_seconds']:.1f} | {f['final_training_loss']:.6f} | {f['peak_gpu_memory_bytes']/2**30:.2f} |")
    md += ["", "| Baseline | Correct | Accuracy | Spearman | E11-A Δ correct | E11-A Δ accuracy | E11-A Δ Spearman | McNemar p | Bootstrap 95% Δ accuracy |",
           "|---|---:|---:|---:|---:|---:|---:|---:|---:|"]
    for name, c in comparisons.items():
        if "net_correct" in c:
            low, high = c["paired_bootstrap"]["accuracy_difference_ci95"]
            md.append(f"| {name} | {c['baseline_correct']}/561 | {c['baseline_accuracy']:.9f} | {c['baseline_spearman']:.9f} | {c['net_correct']:+d} | {c['accuracy_difference']:+.9f} | {c['spearman_difference']:+.9f} | {c['mcnemar_exact_two_sided_p']:.6g} | [{low:+.6f}, {high:+.6f}] |")
        else:
            md.append(f"| {name} | — | — | — | — | — | — | — | Paired analysis unavailable: {c['reason']} |")
    if "per_task_correct_change" in comparisons["E10"]:
        changes = comparisons["E10"]["per_task_correct_change"]
        md += ["", "E11-A correct-count change versus E10 by task: " +
               ", ".join(f"{task} {changes[task]['net_correct']:+d}"
                         for task in ("DM", "MT", "PG")) + ".",
               "E11-A is below E10 on frozen development accuracy and Spearman; "
               "it should not replace E10 as the current final-model candidate."]
    md += ["", "Paired McNemar tests are exact two-sided; bootstrap resamples the same 561 OOF rows 10,000 times with seed 42. These are descriptive development comparisons and do not include retraining uncertainty.",
           "", "No hyperparameter or threshold tuning, second seed, pseudo-labels, official-test access, commit, or push was performed by this result assembly.", ""]
    report_path = HERE / "E11A_RESULTS.md"
    report_path.write_text("\n".join(md), encoding="utf-8")
    hashes.update({"oof_predictions": sha_file(oof_path),
                   "results_json": sha_file(result_path),
                   "results_md": sha_file(report_path)})
    manifest = {"status": "PASS", "experiment": "E11-A",
                "protocol_content_sha256": spec["protocol_sha256"],
                "files_sha256": hashes,
                "baseline_oof_sha256": {k: v.get("baseline_oof_sha256")
                                         for k, v in comparisons.items()},
                "fold_count": 5, "oof_rows": 561}
    save_json(HERE / "E11A_RESULTS_MANIFEST.json", manifest)
    return results


if __name__ == "__main__":
    result = main()
    print(json.dumps({"status": result["status"], "overall": result["overall"],
                      "comparisons": result["comparisons"]}, indent=2))
