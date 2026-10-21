"""Prompt 7E: development-only CV for E1-E3 and diagnostic E4.

This script uses only canonical development artifacts:
- canonical human 14-feature matrix;
- canonical synthetic diagnostic 14-feature matrix;
- locked fold assignments.

It does not read or use the official test set, does not run pretrained models,
does not perform feature extraction, and does not modify notebooks or DOCX files.
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
import platform
import sys
import time
from collections import OrderedDict
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import scipy
from scipy.stats import pearsonr, spearmanr
import sklearn
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
)


ROOT = Path(__file__).resolve().parent
FEATURE_DIR = ROOT / "canonical_feature_outputs"
OUTPUT_DIR = Path(os.environ.get("CANONICAL_CV_OUTPUT_DIR", ROOT / "canonical_cv_outputs"))
OUTPUT_DIR.mkdir(exist_ok=True)
LOG_PATH = OUTPUT_DIR / "canonical_cv_execution.log"

HUMAN_FEATURES = FEATURE_DIR / "canonical_human_14_features.csv"
SYNTHETIC_FEATURES = FEATURE_DIR / "canonical_synthetic_14_features.csv"
FOLD_ASSIGNMENTS = ROOT / "canonical_fold_assignments.csv"
HUMAN_MANIFEST = ROOT / "canonical_human_development_manifest.csv"
OLD_TRIAL_FEATURES = (
    ROOT
    / "data"
    / "6. Feature Extraction on Augmented Training Data"
    / "nli_similarity_features_dataset.csv"
)
FEATURE_METADATA = FEATURE_DIR / "canonical_feature_extraction_metadata.json"
UNMATCHED_COMPATIBILITY_ROWS = FEATURE_DIR / "canonical_feature_compatibility_unmatched_rows.csv"

NLI_FEATURES = ["src_ent", "src_neu", "src_con", "tgt_ent", "tgt_neu", "tgt_con"]
SIM_FEATURES = [
    "sim_src_hyp",
    "sim_tgt_hyp",
    "sim_src_tgt",
    "sim_max",
    "sim_min",
    "sim_mean",
    "sim_gap_tgt_src",
    "sim_hyp_distance_from_truth",
]
ALL_FEATURES = NLI_FEATURES + SIM_FEATURES

EXPERIMENTS = OrderedDict(
    [
        ("E1_NLI_only", {"features": NLI_FEATURES, "synthetic": False, "selection_eligible": True}),
        ("E2_similarity_only", {"features": SIM_FEATURES, "synthetic": False, "selection_eligible": True}),
        ("E3_NLI_similarity", {"features": ALL_FEATURES, "synthetic": False, "selection_eligible": True}),
        ("E4_synthetic_diagnostic", {"features": ALL_FEATURES, "synthetic": True, "selection_eligible": False}),
    ]
)

SELECTION_RULE = OrderedDict(
    [
        ("eligible_experiments", ["E1_NLI_only", "E2_similarity_only", "E3_NLI_similarity"]),
        ("excluded_diagnostic_experiments", ["E4_synthetic_diagnostic"]),
        ("primary", "higher overall_oof_accuracy"),
        ("secondary_tie_break", "higher overall_oof_spearman"),
        ("tertiary_tie_break", "fewer predictor features: E1=6, E2=8, E3=14"),
        ("e4_policy", "diagnostic-only; not selection eligible"),
    ]
)


def setup_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
        handlers=[
            logging.FileHandler(LOG_PATH, encoding="utf-8"),
            logging.StreamHandler(sys.stdout),
        ],
        force=True,
    )


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def safe_spearman(y_true: np.ndarray, y_pred: np.ndarray) -> float | None:
    y_pred = np.round(y_pred.astype(float), 12)
    if len(y_true) < 2 or len(np.unique(y_true)) < 2 or len(np.unique(y_pred)) < 2:
        return None
    value = spearmanr(y_true, y_pred).statistic
    if np.isnan(value):
        return None
    return float(value)


def validate_inputs() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    logging.info("Validating canonical CV inputs")
    human = pd.read_csv(HUMAN_FEATURES)
    synthetic = pd.read_csv(SYNTHETIC_FEATURES)
    folds = pd.read_csv(FOLD_ASSIGNMENTS)

    if len(human) != 561 or human["canonical_id"].nunique() != 561:
        raise ValueError("Human features must contain 561 unique canonical_id rows.")
    if human["exact_text_key"].nunique() != 561:
        raise ValueError("Human features must contain 561 unique exact_text_key values.")
    if len(synthetic) != 505 or synthetic["synthetic_id"].nunique() != 505:
        raise ValueError("Synthetic features must contain 505 unique synthetic_id rows.")
    if synthetic["exact_text_key"].nunique() != 505:
        raise ValueError("Synthetic features must contain 505 unique exact_text_key values.")
    if len(folds) != 561 or folds["canonical_id"].nunique() != 561:
        raise ValueError("Fold assignments must contain 561 unique canonical_id rows.")

    for frame, name in [(human, "human"), (synthetic, "synthetic")]:
        if not set(frame["task"].astype(str)) <= {"DM", "MT", "PG"}:
            raise ValueError(f"{name} contains unexpected tasks")
        if set(frame["label_bin"].astype(int)) != {0, 1}:
            raise ValueError(f"{name} contains unexpected label_bin values")
        values = frame[ALL_FEATURES].to_numpy(dtype=float)
        if not np.isfinite(values).all():
            raise ValueError(f"{name} contains NaN/Inf feature values")

    fold_counts = folds["fold_id"].value_counts().sort_index().to_dict()
    if fold_counts != {1: 113, 2: 112, 3: 112, 4: 112, 5: 112}:
        raise ValueError(f"Unexpected fold sizes: {fold_counts}")
    merged = human[["canonical_id", "fold_id"]].merge(
        folds[["canonical_id", "fold_id"]], on="canonical_id", suffixes=("_features", "_fold")
    )
    if len(merged) != 561 or not (merged["fold_id_features"] == merged["fold_id_fold"]).all():
        raise ValueError("Human feature fold_id does not match locked fold file 1:1.")

    return human, synthetic, folds


def normalized_key(frame: pd.DataFrame) -> pd.Series:
    return (
        frame["task"].astype(str).str.strip()
        + "\u241f"
        + frame["src"].astype(str).str.strip()
        + "\u241f"
        + frame["tgt"].astype(str).str.strip()
        + "\u241f"
        + frame["hyp"].astype(str).str.strip()
    )


def create_unmatched_compatibility_rows() -> int:
    logging.info("Creating unmatched compatibility rows audit")
    human_manifest = pd.read_csv(HUMAN_MANIFEST, keep_default_na=False)
    old = pd.read_csv(OLD_TRIAL_FEATURES, keep_default_na=False)
    old_human = old[old.get("source_type", "") == "human_labeled"].copy()
    old_keys = set(normalized_key(old_human)) if not old_human.empty else set()
    trial_rows = human_manifest[human_manifest["source_split"] == "trial"].copy()
    trial_rows["match_key"] = normalized_key(trial_rows)
    unmatched = trial_rows[~trial_rows["match_key"].isin(old_keys)].copy()
    out = unmatched[
        ["canonical_id", "original_row_index", "task", "exact_text_key", "src", "tgt", "hyp"]
    ].copy()
    out["reason"] = "no_exact_normalized_match_in_old_artifact"
    out.to_csv(UNMATCHED_COMPATIBILITY_ROWS, index=False)
    return len(out)


def fit_predict_fold(
    experiment: str,
    features: list[str],
    human: pd.DataFrame,
    synthetic: pd.DataFrame,
    fold_id: int,
    use_synthetic: bool,
) -> tuple[dict[str, Any], pd.DataFrame, list[dict[str, Any]]]:
    train_human = human[human["fold_id"] != fold_id].copy()
    validation = human[human["fold_id"] == fold_id].copy()
    train = train_human.copy()
    synthetic_train_rows = 0
    if use_synthetic:
        synthetic_train = synthetic.copy()
        synthetic_train["fold_id"] = -1
        synthetic_train["canonical_id"] = synthetic_train["synthetic_id"]
        synthetic_train["source_split"] = synthetic_train["source_type"]
        train = pd.concat(
            [
                train_human,
                synthetic_train[
                    [
                        "canonical_id",
                        "fold_id",
                        "source_split",
                        "exact_text_key",
                        "task",
                        "label",
                        "label_bin",
                        "p_hallucination",
                    ]
                    + features
                ],
            ],
            ignore_index=True,
        )
        synthetic_train_rows = len(synthetic_train)

    logging.info(
        "Training %s fold=%s n_train_human=%s n_train_synthetic=%s n_validation=%s",
        experiment,
        fold_id,
        len(train_human),
        synthetic_train_rows,
        len(validation),
    )
    model = RandomForestRegressor(n_estimators=500, random_state=42, n_jobs=-1)
    model.fit(train[features].to_numpy(dtype=float), train["p_hallucination"].to_numpy(dtype=float))
    pred_raw = model.predict(validation[features].to_numpy(dtype=float))
    pred_clipped = np.clip(pred_raw, 0.0, 1.0)
    pred_label = (pred_clipped >= 0.5).astype(int)
    y = validation["p_hallucination"].to_numpy(dtype=float)
    y_bin = validation["label_bin"].to_numpy(dtype=int)

    tn, fp, fn, tp = confusion_matrix(y_bin, pred_label, labels=[0, 1]).ravel()
    fold_metrics = {
        "experiment": experiment,
        "fold_id": fold_id,
        "n_train_human": len(train_human),
        "n_train_synthetic": synthetic_train_rows,
        "n_train_total": len(train),
        "n_validation": len(validation),
        "accuracy": accuracy_score(y_bin, pred_label),
        "spearman": safe_spearman(y, pred_clipped),
        "precision": precision_score(y_bin, pred_label, zero_division=0),
        "recall": recall_score(y_bin, pred_label, zero_division=0),
        "f1": f1_score(y_bin, pred_label, zero_division=0),
        "tn": int(tn),
        "fp": int(fp),
        "fn": int(fn),
        "tp": int(tp),
    }
    predictions = validation[
        [
            "canonical_id",
            "fold_id",
            "source_split",
            "original_row_index",
            "exact_text_key",
            "task",
            "label",
            "label_bin",
            "p_hallucination",
        ]
    ].copy()
    predictions["experiment"] = experiment
    predictions["y_pred_reg_raw"] = pred_raw
    predictions["y_pred_reg_clipped"] = pred_clipped
    predictions["y_pred_bin"] = pred_label
    predictions["pred_p_hallucination"] = pred_clipped
    predictions["pred_label_bin"] = pred_label
    predictions["correct"] = predictions["y_pred_bin"].astype(int) == predictions["label_bin"].astype(int)

    importance_rows = [
        {"experiment": experiment, "fold_id": fold_id, "feature": feature, "importance": float(value)}
        for feature, value in zip(features, model.feature_importances_)
    ]
    return fold_metrics, predictions, importance_rows


def aggregate_results(
    experiment: str, fold_metrics: list[dict[str, Any]], predictions: pd.DataFrame, selection_eligible: bool
) -> dict[str, Any]:
    y_bin = predictions["label_bin"].to_numpy(dtype=int)
    pred_label = predictions["pred_label_bin"].to_numpy(dtype=int)
    y = predictions["p_hallucination"].to_numpy(dtype=float)
    pred = predictions["pred_p_hallucination"].to_numpy(dtype=float)
    tn, fp, fn, tp = confusion_matrix(y_bin, pred_label, labels=[0, 1]).ravel()
    fold_df = pd.DataFrame(fold_metrics)
    return {
        "experiment": experiment,
        "selection_eligible": selection_eligible,
        "n_oof": len(predictions),
        "mean_cv_accuracy": float(fold_df["accuracy"].mean()),
        "std_cv_accuracy": float(fold_df["accuracy"].std(ddof=1)),
        "overall_oof_accuracy": float(accuracy_score(y_bin, pred_label)),
        "mean_cv_spearman": float(fold_df["spearman"].dropna().mean()),
        "std_cv_spearman": float(fold_df["spearman"].dropna().std(ddof=1)),
        "overall_oof_spearman": safe_spearman(y, pred),
        "mean_cv_precision": float(fold_df["precision"].mean()),
        "std_cv_precision": float(fold_df["precision"].std(ddof=1)),
        "mean_cv_recall": float(fold_df["recall"].mean()),
        "std_cv_recall": float(fold_df["recall"].std(ddof=1)),
        "mean_cv_f1": float(fold_df["f1"].mean()),
        "std_cv_f1": float(fold_df["f1"].std(ddof=1)),
        "overall_precision": float(precision_score(y_bin, pred_label, zero_division=0)),
        "overall_recall": float(recall_score(y_bin, pred_label, zero_division=0)),
        "overall_f1": float(f1_score(y_bin, pred_label, zero_division=0)),
        "tn": int(tn),
        "fp": int(fp),
        "fn": int(fn),
        "tp": int(tp),
    }


def per_task_results(experiment: str, predictions: pd.DataFrame) -> list[dict[str, Any]]:
    rows = []
    for task, group in predictions.groupby("task", observed=False):
        y_bin = group["label_bin"].to_numpy(dtype=int)
        pred_label = group["pred_label_bin"].to_numpy(dtype=int)
        y = group["p_hallucination"].to_numpy(dtype=float)
        pred = group["pred_p_hallucination"].to_numpy(dtype=float)
        tn, fp, fn, tp = confusion_matrix(y_bin, pred_label, labels=[0, 1]).ravel()
        rows.append(
            {
                "experiment": experiment,
                "task": task,
                "n": len(group),
                "accuracy": accuracy_score(y_bin, pred_label),
                "spearman": safe_spearman(y, pred),
                "precision": precision_score(y_bin, pred_label, zero_division=0),
                "recall": recall_score(y_bin, pred_label, zero_division=0),
                "f1": f1_score(y_bin, pred_label, zero_division=0),
                "tn": int(tn),
                "fp": int(fp),
                "fn": int(fn),
                "tp": int(tp),
            }
        )
    return rows


def select_experiment(summary: pd.DataFrame) -> dict[str, Any]:
    feature_counts = {"E1_NLI_only": 6, "E2_similarity_only": 8, "E3_NLI_similarity": 14}
    eligible = summary[summary["selection_eligible"]].copy()
    eligible["feature_count"] = eligible["experiment"].map(feature_counts)
    eligible = eligible.sort_values(
        ["overall_oof_accuracy", "overall_oof_spearman", "feature_count"],
        ascending=[False, False, True],
        kind="mergesort",
    )
    return eligible.iloc[0].to_dict()


def confusion_rows(fold_results: pd.DataFrame, summary: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for row in summary.itertuples(index=False):
        rows.append(
            {
                "experiment": row.experiment,
                "scope": "overall",
                "fold_id": "",
                "tn": int(row.tn),
                "fp": int(row.fp),
                "fn": int(row.fn),
                "tp": int(row.tp),
            }
        )
    for row in fold_results.itertuples(index=False):
        rows.append(
            {
                "experiment": row.experiment,
                "scope": "fold",
                "fold_id": int(row.fold_id),
                "tn": int(row.tn),
                "fp": int(row.fp),
                "fn": int(row.fn),
                "tp": int(row.tp),
            }
        )
    return pd.DataFrame(rows)


def feature_importance_summary(feature_importance: pd.DataFrame) -> pd.DataFrame:
    return (
        feature_importance.groupby(["experiment", "feature"], observed=False)["importance"]
        .agg(mean_importance="mean", std_importance=lambda s: s.std(ddof=1), min_importance="min", max_importance="max", folds="count")
        .reset_index()
    )


def e4_vs_e3(predictions: pd.DataFrame, summary: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    e3 = predictions[predictions["experiment"] == "E3_NLI_similarity"].copy()
    e4 = predictions[predictions["experiment"] == "E4_synthetic_diagnostic"].copy()
    merged = e3.merge(e4, on="canonical_id", suffixes=("_E3", "_E4"))
    fixed = merged[(merged["correct_E3"] == False) & (merged["correct_E4"] == True)].copy()
    introduced = merged[(merged["correct_E3"] == True) & (merged["correct_E4"] == False)].copy()
    unchanged_correct = int(((merged["correct_E3"] == True) & (merged["correct_E4"] == True)).sum())
    unchanged_incorrect = int(((merged["correct_E3"] == False) & (merged["correct_E4"] == False)).sum())
    e3s = summary[summary["experiment"] == "E3_NLI_similarity"].iloc[0]
    e4s = summary[summary["experiment"] == "E4_synthetic_diagnostic"].iloc[0]
    diagnostic = pd.DataFrame(
        [
            {
                "e3_overall_oof_accuracy": e3s["overall_oof_accuracy"],
                "e4_overall_oof_accuracy": e4s["overall_oof_accuracy"],
                "delta_accuracy_e4_minus_e3": e4s["overall_oof_accuracy"] - e3s["overall_oof_accuracy"],
                "e3_overall_oof_spearman": e3s["overall_oof_spearman"],
                "e4_overall_oof_spearman": e4s["overall_oof_spearman"],
                "delta_spearman_e4_minus_e3": e4s["overall_oof_spearman"] - e3s["overall_oof_spearman"],
                "delta_precision_e4_minus_e3": e4s["overall_precision"] - e3s["overall_precision"],
                "delta_recall_e4_minus_e3": e4s["overall_recall"] - e3s["overall_recall"],
                "delta_f1_e4_minus_e3": e4s["overall_f1"] - e3s["overall_f1"],
                "fixed_errors": len(fixed),
                "introduced_errors": len(introduced),
                "unchanged_correct": unchanged_correct,
                "unchanged_incorrect": unchanged_incorrect,
            }
        ]
    )

    def error_frame(frame: pd.DataFrame) -> pd.DataFrame:
        if frame.empty:
            return pd.DataFrame(
                columns=[
                    "canonical_id",
                    "fold_id",
                    "source_split",
                    "task",
                    "exact_text_key",
                    "y_true_reg",
                    "y_true_bin",
                    "E3 raw score",
                    "E3 clipped score",
                    "E3 binary label",
                    "E4 raw score",
                    "E4 clipped score",
                    "E4 binary label",
                ]
            )
        return pd.DataFrame(
            {
                "canonical_id": frame["canonical_id"],
                "fold_id": frame["fold_id_E3"],
                "source_split": frame["source_split_E3"],
                "task": frame["task_E3"],
                "exact_text_key": frame["exact_text_key_E3"],
                "y_true_reg": frame["p_hallucination_E3"],
                "y_true_bin": frame["label_bin_E3"],
                "E3 raw score": frame["y_pred_reg_raw_E3"],
                "E3 clipped score": frame["y_pred_reg_clipped_E3"],
                "E3 binary label": frame["y_pred_bin_E3"],
                "E4 raw score": frame["y_pred_reg_raw_E4"],
                "E4 clipped score": frame["y_pred_reg_clipped_E4"],
                "E4 binary label": frame["y_pred_bin_E4"],
            }
        )

    return diagnostic, error_frame(fixed), error_frame(introduced)


def integrity_audit(
    human: pd.DataFrame,
    folds: pd.DataFrame,
    fold_results: pd.DataFrame,
    predictions: pd.DataFrame,
    metadata: dict[str, Any],
) -> pd.DataFrame:
    rows = []

    def add(check: str, expected: Any, observed: Any, passed: bool, note: str = "") -> None:
        rows.append({"check": check, "expected": expected, "observed": observed, "passed": bool(passed), "note": note})

    add("OOF prediction rows", 2244, len(predictions), len(predictions) == 2244)
    counts = predictions["experiment"].value_counts().sort_index().to_dict()
    add("561 predictions per experiment", "all experiments=561", json.dumps(counts, sort_keys=True), all(v == 561 for v in counts.values()) and len(counts) == 4)
    add("unique experiment/canonical_id", 2244, predictions[["experiment", "canonical_id"]].drop_duplicates().shape[0], predictions[["experiment", "canonical_id"]].drop_duplicates().shape[0] == 2244)
    merged = predictions.merge(folds[["canonical_id", "fold_id"]], on="canonical_id", suffixes=("_pred", "_fold"))
    add("fold_id matches fold file", True, bool((merged["fold_id_pred"] == merged["fold_id_fold"]).all()), bool((merged["fold_id_pred"] == merged["fold_id_fold"]).all()))
    add("no synthetic validation predictions", 0, int(predictions["canonical_id"].astype(str).str.startswith("SYN_").sum()), not predictions["canonical_id"].astype(str).str.startswith("SYN_").any())
    add("E1 uses 6 features", 6, len(EXPERIMENTS["E1_NLI_only"]["features"]), len(EXPERIMENTS["E1_NLI_only"]["features"]) == 6)
    add("E2 uses 8 features", 8, len(EXPERIMENTS["E2_similarity_only"]["features"]), len(EXPERIMENTS["E2_similarity_only"]["features"]) == 8)
    add("E3 and E4 use 14 features", "14,14", f"{len(EXPERIMENTS['E3_NLI_similarity']['features'])},{len(EXPERIMENTS['E4_synthetic_diagnostic']['features'])}", len(EXPERIMENTS["E3_NLI_similarity"]["features"]) == 14 and len(EXPERIMENTS["E4_synthetic_diagnostic"]["features"]) == 14)
    add("metadata fields not predictor features", "no metadata columns in feature groups", ",".join(ALL_FEATURES), set(ALL_FEATURES).isdisjoint({"canonical_id", "fold_id", "source_split", "original_row_index", "exact_text_key", "task", "label", "label_bin", "p_hallucination"}))
    synth_by_exp = fold_results.groupby("experiment")["n_train_synthetic"].apply(lambda s: sorted(set(s))).to_dict()
    add("E1-E3 use 0 synthetic training rows", "[0]", json.dumps({k: v for k, v in synth_by_exp.items() if k != "E4_synthetic_diagnostic"}, sort_keys=True), all(synth_by_exp[k] == [0] for k in ["E1_NLI_only", "E2_similarity_only", "E3_NLI_similarity"]))
    add("E4 uses 505 synthetic rows per fold", "[505]", synth_by_exp.get("E4_synthetic_diagnostic"), synth_by_exp.get("E4_synthetic_diagnostic") == [505])
    pred_values = predictions[["y_pred_reg_raw", "y_pred_reg_clipped", "y_pred_bin", "pred_p_hallucination", "pred_label_bin"]].to_numpy(dtype=float)
    add("no NaN or Inf in predictions", True, bool(np.isfinite(pred_values).all()), bool(np.isfinite(pred_values).all()))
    add("all clipped scores in [0,1]", True, bool(((predictions["y_pred_reg_clipped"] >= 0) & (predictions["y_pred_reg_clipped"] <= 1)).all()), bool(((predictions["y_pred_reg_clipped"] >= 0) & (predictions["y_pred_reg_clipped"] <= 1)).all()))
    threshold_ok = (predictions["y_pred_bin"].astype(int) == (predictions["y_pred_reg_clipped"] >= 0.5).astype(int)).all()
    add("binary labels match threshold 0.5", True, bool(threshold_ok), bool(threshold_ok))
    per_exp_unique = predictions.groupby("experiment")["canonical_id"].nunique().to_dict()
    add("one OOF prediction per human sample per experiment", "561 each", json.dumps(per_exp_unique, sort_keys=True), all(v == 561 for v in per_exp_unique.values()))
    declared_input_paths = [
        HUMAN_FEATURES,
        SYNTHETIC_FEATURES,
        FOLD_ASSIGNMENTS,
        HUMAN_MANIFEST,
        OLD_TRIAL_FEATURES,
        FEATURE_METADATA,
    ]
    official_markers = ["test.model-agnostic", "shroom_test-labeled", "labeled test"]
    official_found = [
        str(path)
        for path in declared_input_paths
        if any(marker in str(path).lower() for marker in official_markers)
    ]
    add(
        "official test path/artifact not read",
        "no declared input path points to official test artifacts",
        json.dumps(official_found),
        not official_found,
        "declared input path audit",
    )
    expected_inputs = {
        "canonical_human_14_features.csv": "3038bd8752a94064e05389e03b063484a1191f9e9a6164f06d11b40688a6828b",
        "canonical_synthetic_14_features.csv": "3ba57e611df885a0afe9fd6a12f962d49590938c740afef48665a1d0a72fd462",
        "canonical_fold_assignments.csv": "f5a5964923806a23dd34a8bcc137f3cf489437e033d645e9d0845bf40792eb5d",
    }
    add("input SHA-256 match Prompt 7E", json.dumps(expected_inputs, sort_keys=True), json.dumps(metadata["input_sha256"], sort_keys=True), metadata["input_sha256"] == expected_inputs)
    add("fold assignments unchanged", expected_inputs["canonical_fold_assignments.csv"], sha256_file(FOLD_ASSIGNMENTS), sha256_file(FOLD_ASSIGNMENTS) == expected_inputs["canonical_fold_assignments.csv"])
    return pd.DataFrame(rows)


def write_results_summary(summary: pd.DataFrame, per_task: pd.DataFrame, diagnostic: pd.DataFrame, fixed: pd.DataFrame, introduced: pd.DataFrame, selection: pd.DataFrame) -> None:
    def markdown_table(frame: pd.DataFrame) -> str:
        if frame.empty:
            return "_No rows._"
        text = frame.copy()
        for column in text.columns:
            if pd.api.types.is_float_dtype(text[column]):
                text[column] = text[column].map(lambda value: "" if pd.isna(value) else f"{value:.6f}")
            else:
                text[column] = text[column].map(lambda value: "" if pd.isna(value) else str(value))
        headers = list(text.columns)
        lines = [
            "| " + " | ".join(headers) + " |",
            "| " + " | ".join(["---"] * len(headers)) + " |",
        ]
        for row in text.itertuples(index=False, name=None):
            escaped = [str(value).replace("|", "\\|") for value in row]
            lines.append("| " + " | ".join(escaped) + " |")
        return "\n".join(lines)

    lines = [
        "# Canonical CV results summary — Prompt 7E-A",
        "",
        "Protocol: development-only CV using the locked 561-sample canonical human development pool and locked five folds.",
        "",
        "Official test set used: **false**.",
        "",
        "## Experiments",
        "",
        "- E1_NLI_only: six NLI features.",
        "- E2_similarity_only: eight semantic similarity features.",
        "- E3_NLI_similarity: all 14 features.",
        "- E4_synthetic_diagnostic: same 14 features as E3, plus 505 synthetic samples in training folds only; diagnostic-only.",
        "",
        "## Overall metrics",
        "",
        markdown_table(summary),
        "",
        "## Per-task metrics",
        "",
        markdown_table(per_task),
        "",
        "## Selection",
        "",
        f"Selected experiment: `{selection.iloc[0]['selected_experiment']}`.",
        "",
        "Selection was restricted to E1-E3. E4 did not participate in selection.",
        "",
        "## Diagnostic E4 versus E3",
        "",
        markdown_table(diagnostic),
        "",
        f"Fixed errors: {len(fixed)}.",
        f"Introduced errors: {len(introduced)}.",
        "",
        "## Limitations",
        "",
        "- Development-only results are not official test benchmark results.",
        "- E4 is diagnostic-only.",
        "- Feature importances are descriptive and were not used for feature removal or model selection.",
    ]
    (OUTPUT_DIR / "canonical_cv_results_summary.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    start = time.time()
    setup_logging()
    started_at = datetime.now().isoformat(timespec="seconds")
    logging.info("Prompt 7E/7E-A CV run started")
    human, synthetic, folds = validate_inputs()
    unmatched_count = create_unmatched_compatibility_rows()

    all_fold_metrics = []
    all_predictions = []
    all_importances = []
    summary_rows = []
    per_task_rows = []

    for experiment, spec in EXPERIMENTS.items():
        fold_metrics = []
        prediction_frames = []
        importance_rows = []
        for fold_id in [1, 2, 3, 4, 5]:
            metrics, predictions, importances = fit_predict_fold(
                experiment,
                spec["features"],
                human,
                synthetic,
                fold_id,
                use_synthetic=bool(spec["synthetic"]),
            )
            fold_metrics.append(metrics)
            prediction_frames.append(predictions)
            importance_rows.extend(importances)
        exp_predictions = pd.concat(prediction_frames, ignore_index=True)
        all_fold_metrics.extend(fold_metrics)
        all_predictions.append(exp_predictions)
        all_importances.extend(importance_rows)
        summary_rows.append(
            aggregate_results(
                experiment,
                fold_metrics,
                exp_predictions,
                selection_eligible=bool(spec["selection_eligible"]),
            )
        )
        per_task_rows.extend(per_task_results(experiment, exp_predictions))

    fold_results = pd.DataFrame(all_fold_metrics)
    predictions = pd.concat(all_predictions, ignore_index=True)
    feature_importance = pd.DataFrame(all_importances)
    summary = pd.DataFrame(summary_rows)
    per_task = pd.DataFrame(per_task_rows)

    selected = select_experiment(summary)
    selection = pd.DataFrame(
        [
            {
                "selected_experiment": selected["experiment"],
                "selection_rule": "E1-E3 only; primary overall_oof_accuracy; secondary overall_oof_spearman",
                "selected_overall_oof_accuracy": selected["overall_oof_accuracy"],
                "selected_overall_oof_spearman": selected["overall_oof_spearman"],
                "e4_diagnostic_only": True,
                "official_test_used": False,
            }
        ]
    )

    fold_results.to_csv(OUTPUT_DIR / "canonical_cv_fold_results.csv", index=False)
    predictions.to_csv(OUTPUT_DIR / "canonical_cv_oof_predictions.csv", index=False)
    summary.to_csv(OUTPUT_DIR / "canonical_cv_summary.csv", index=False)
    per_task.to_csv(OUTPUT_DIR / "canonical_cv_per_task_results.csv", index=False)
    feature_importance.to_csv(OUTPUT_DIR / "canonical_cv_feature_importance_by_fold.csv", index=False)
    selection.to_csv(OUTPUT_DIR / "canonical_cv_model_selection.csv", index=False)
    fold_results.to_csv(OUTPUT_DIR / "canonical_cv_fold_metrics.csv", index=False)
    summary.to_csv(OUTPUT_DIR / "canonical_cv_overall_metrics.csv", index=False)
    per_task.to_csv(OUTPUT_DIR / "canonical_cv_per_task_metrics.csv", index=False)
    confusions = confusion_rows(fold_results, summary)
    confusions.to_csv(OUTPUT_DIR / "canonical_cv_confusion_matrices.csv", index=False)
    importance_summary = feature_importance_summary(feature_importance)
    importance_summary.to_csv(OUTPUT_DIR / "canonical_cv_feature_importance_summary.csv", index=False)
    diagnostic, fixed, introduced = e4_vs_e3(predictions, summary)
    diagnostic.to_csv(OUTPUT_DIR / "canonical_cv_e4_vs_e3_diagnostic.csv", index=False)
    fixed.to_csv(OUTPUT_DIR / "e4_fixed_errors.csv", index=False)
    introduced.to_csv(OUTPUT_DIR / "e4_introduced_errors.csv", index=False)
    selection_decision = OrderedDict(
        [
            ("eligible_experiments", SELECTION_RULE["eligible_experiments"]),
            ("excluded_diagnostic_experiments", SELECTION_RULE["excluded_diagnostic_experiments"]),
            ("predeclared_selection_rule", SELECTION_RULE),
            ("metrics_e1_e3", summary[summary["selection_eligible"]].to_dict(orient="records")),
            ("selected_experiment", selected["experiment"]),
            ("selected_feature_count", int(selected["feature_count"])),
            ("e4_participated_in_selection", False),
            ("official_test_used", False),
        ]
    )
    (OUTPUT_DIR / "canonical_cv_selection_decision.json").write_text(
        json.dumps(selection_decision, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    output_files = [
        OUTPUT_DIR / "canonical_cv_fold_results.csv",
        OUTPUT_DIR / "canonical_cv_oof_predictions.csv",
        OUTPUT_DIR / "canonical_cv_summary.csv",
        OUTPUT_DIR / "canonical_cv_per_task_results.csv",
        OUTPUT_DIR / "canonical_cv_feature_importance_by_fold.csv",
        OUTPUT_DIR / "canonical_cv_model_selection.csv",
        OUTPUT_DIR / "canonical_cv_fold_metrics.csv",
        OUTPUT_DIR / "canonical_cv_overall_metrics.csv",
        OUTPUT_DIR / "canonical_cv_per_task_metrics.csv",
        OUTPUT_DIR / "canonical_cv_confusion_matrices.csv",
        OUTPUT_DIR / "canonical_cv_feature_importance_summary.csv",
        OUTPUT_DIR / "canonical_cv_e4_vs_e3_diagnostic.csv",
        OUTPUT_DIR / "e4_fixed_errors.csv",
        OUTPUT_DIR / "e4_introduced_errors.csv",
        OUTPUT_DIR / "canonical_cv_selection_decision.json",
        UNMATCHED_COMPATIBILITY_ROWS,
    ]
    metadata = OrderedDict(
        [
            ("timestamp_start", started_at),
            ("timestamp_end", datetime.now().isoformat(timespec="seconds")),
            ("runtime_seconds", round(time.time() - start, 3)),
            ("interpreter", sys.executable),
            ("python_version", platform.python_version()),
            ("sklearn_version", sklearn.__version__),
            ("numpy_version", np.__version__),
            ("pandas_version", pd.__version__),
            ("scipy_version", scipy.__version__),
            ("cpu_cores", os.cpu_count()),
            ("inputs", {
                "human_features": str(HUMAN_FEATURES),
                "synthetic_features": str(SYNTHETIC_FEATURES),
                "fold_assignments": str(FOLD_ASSIGNMENTS),
            }),
            ("input_sha256", {
                "canonical_human_14_features.csv": sha256_file(HUMAN_FEATURES),
                "canonical_synthetic_14_features.csv": sha256_file(SYNTHETIC_FEATURES),
                "canonical_fold_assignments.csv": sha256_file(FOLD_ASSIGNMENTS),
            }),
            ("random_forest", {
                "class": "sklearn.ensemble.RandomForestRegressor",
                "n_estimators": 500,
                "random_state": 42,
                "n_jobs": -1,
                "get_params": RandomForestRegressor(n_estimators=500, random_state=42, n_jobs=-1).get_params(),
            }),
            ("target", "p_hallucination"),
            ("prediction_clipping", "[0, 1]"),
            ("binary_threshold", 0.5),
            ("calibration", "none"),
            ("feature_groups", {name: spec["features"] for name, spec in EXPERIMENTS.items()}),
            ("e4_policy", "fixed diagnostic only; synthetic rows added only to training folds; uniform weight 1.0"),
            ("selection_rule", SELECTION_RULE),
            ("selected_experiment", selected["experiment"]),
            ("unmatched_old_trial_compatibility_rows", unmatched_count),
            ("official_test_used", False),
            ("pretrained_model_or_feature_extraction_executed", False),
            ("output_sha256", {path.name: sha256_file(path) for path in output_files}),
        ]
    )
    integrity = integrity_audit(human, folds, fold_results, predictions, metadata)
    integrity.to_csv(OUTPUT_DIR / "canonical_cv_integrity_audit.csv", index=False)
    output_files.extend(
        [
            OUTPUT_DIR / "canonical_cv_integrity_audit.csv",
            OUTPUT_DIR / "canonical_cv_results_summary.md",
            OUTPUT_DIR / "canonical_cv_execution.log",
            OUTPUT_DIR / "canonical_cv_experiment_metadata.json",
        ]
    )
    write_results_summary(summary, per_task, diagnostic, fixed, introduced, selection)
    metadata["integrity_audit_passed"] = bool(integrity["passed"].all())
    metadata["row_counts_by_experiment_fold"] = fold_results[
        ["experiment", "fold_id", "n_train_human", "n_train_synthetic", "n_train_total", "n_validation"]
    ].to_dict(orient="records")
    metadata["runtime_by_experiment_fold_seconds"] = "not separately timed; see total runtime"
    metadata["reproducibility_audit_result"] = "pending"
    metadata["output_sha256"] = {path.name: sha256_file(path) for path in output_files if path.exists()}
    (OUTPUT_DIR / "canonical_cv_metadata.json").write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (OUTPUT_DIR / "canonical_cv_experiment_metadata.json").write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    # Recompute hashes after metadata writes.
    metadata["output_sha256"] = {path.name: sha256_file(path) for path in output_files if path.exists()}
    (OUTPUT_DIR / "canonical_cv_metadata.json").write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (OUTPUT_DIR / "canonical_cv_experiment_metadata.json").write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    logging.info("Prompt 7E/7E-A CV run complete. Selected=%s", selected["experiment"])
    print(json.dumps({
        "selected_experiment": selected["experiment"],
        "summary": summary.to_dict(orient="records"),
        "runtime_seconds": metadata["runtime_seconds"],
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
