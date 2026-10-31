"""Canonical NLI and semantic similarity feature extraction for Prompt 7D.

This script:
- reads only canonical manifests and fold assignments;
- uses local Hugging Face cache only;
- extracts NLI and semantic similarity features;
- writes resumable checkpoints plus final canonical feature matrices;
- does not read the official test set;
- does not train or evaluate any Random Forest;
- does not compute CV metrics.
"""

from __future__ import annotations

import csv
import hashlib
import json
import logging
import math
import os
import platform
import sys
import time
from collections import OrderedDict
from datetime import datetime
from pathlib import Path
from typing import Any

os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")
os.environ.setdefault("HF_HUB_OFFLINE", "1")

import numpy as np
import pandas as pd
import torch
import transformers
from scipy.stats import pearsonr, spearmanr
from sentence_transformers import SentenceTransformer
from transformers import AutoConfig, AutoModelForSequenceClassification, AutoTokenizer
from transformers.utils import cached_file


ROOT = Path(__file__).resolve().parent
OUTPUT_DIR = ROOT / "canonical_feature_outputs"
CHECKPOINT_DIR = OUTPUT_DIR / "checkpoints"
LOG_PATH = OUTPUT_DIR / "canonical_feature_extraction.log"

HUMAN_MANIFEST = ROOT / "canonical_human_development_manifest.csv"
SYNTHETIC_MANIFEST = ROOT / "canonical_synthetic_diagnostic_manifest.csv"
FOLD_ASSIGNMENTS = ROOT / "canonical_fold_assignments.csv"
OLD_TRIAL_FEATURES = (
    ROOT
    / "data"
    / "6. Feature Extraction on Augmented Training Data"
    / "nli_similarity_features_dataset.csv"
)

NLI_MODEL = "microsoft/deberta-large-mnli"
SIM_MODEL = "sentence-transformers/all-mpnet-base-v2"

NLI_BATCH_SIZE_CPU = 2
NLI_BATCH_SIZE_GPU = 8
SIM_BATCH_SIZE = 64
MAX_LENGTH = 512
TOLERANCE = 1e-5
PROCESS_START = time.time()
MAX_SECONDS_PER_RUN = float(os.environ.get("CANONICAL_FEATURE_MAX_SECONDS", "0") or "0")

FEATURE_COLUMNS = [
    "src_ent",
    "src_neu",
    "src_con",
    "tgt_ent",
    "tgt_neu",
    "tgt_con",
    "sim_src_hyp",
    "sim_tgt_hyp",
    "sim_src_tgt",
    "sim_max",
    "sim_min",
    "sim_mean",
    "sim_gap_tgt_src",
    "sim_hyp_distance_from_truth",
]

NLI_COLUMNS = ["src_ent", "src_neu", "src_con", "tgt_ent", "tgt_neu", "tgt_con"]
SIM_COLUMNS = [
    "sim_src_hyp",
    "sim_tgt_hyp",
    "sim_src_tgt",
    "sim_max",
    "sim_min",
    "sim_mean",
    "sim_gap_tgt_src",
    "sim_hyp_distance_from_truth",
]


def ensure_dirs() -> None:
    OUTPUT_DIR.mkdir(exist_ok=True)
    CHECKPOINT_DIR.mkdir(exist_ok=True)


def setup_logging() -> None:
    ensure_dirs()
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
        handlers=[
            logging.FileHandler(LOG_PATH, encoding="utf-8"),
            logging.StreamHandler(sys.stdout),
        ],
    )


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def resolve_cached_artifacts(model_name: str, files: list[str]) -> dict[str, str]:
    resolved: dict[str, str] = {}
    for filename in files:
        try:
            resolved[filename] = cached_file(model_name, filename, local_files_only=True)
        except Exception as exc:
            raise RuntimeError(f"Missing local cached artifact for {model_name}: {filename}") from exc
    return resolved


def validate_inputs() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    human = pd.read_csv(HUMAN_MANIFEST, keep_default_na=False)
    synthetic = pd.read_csv(SYNTHETIC_MANIFEST, keep_default_na=False)
    folds = pd.read_csv(FOLD_ASSIGNMENTS)

    if len(human) != 561:
        raise ValueError(f"Expected 561 human rows, found {len(human)}")
    if human["canonical_id"].nunique() != 561:
        raise ValueError("Expected 561 unique human canonical_id values")
    if human["exact_text_key"].nunique() != 561:
        raise ValueError("Expected 561 unique human exact_text_key values")
    if len(synthetic) != 505:
        raise ValueError(f"Expected 505 synthetic rows, found {len(synthetic)}")
    if synthetic["synthetic_id"].nunique() != 505:
        raise ValueError("Expected 505 unique synthetic_id values")
    if len(folds) != 561 or folds["canonical_id"].nunique() != 561:
        raise ValueError("Fold assignments must contain 561 unique canonical_id values")

    for frame, name in [(human, "human"), (synthetic, "synthetic")]:
        for column in ["src", "tgt", "hyp"]:
            missing = frame[column].isna().sum()
            if missing:
                raise ValueError(f"{name} has missing {column}: {missing}")
        tasks = set(frame["task"].astype(str))
        if not tasks <= {"DM", "MT", "PG"}:
            raise ValueError(f"{name} has unexpected tasks: {sorted(tasks)}")
        labels = set(frame["label_bin"].astype(int))
        if labels != {0, 1}:
            raise ValueError(f"{name} has unexpected label_bin values: {sorted(labels)}")
        p_values = pd.to_numeric(frame["p_hallucination"], errors="coerce")
        if p_values.isna().any():
            raise ValueError(f"{name} p_hallucination contains non-numeric values")

    merged = human[["canonical_id"]].merge(
        folds[["canonical_id", "fold_id"]], on="canonical_id", how="outer", indicator=True
    )
    if len(merged) != 561 or set(merged["_merge"]) != {"both"}:
        raise ValueError("Human manifest and fold assignments do not merge 1:1")

    human = human.merge(folds[["canonical_id", "fold_id"]], on="canonical_id", how="left")
    return human, synthetic, folds


def read_checkpoint(path: Path, id_column: str) -> pd.DataFrame:
    if path.exists():
        return pd.read_csv(path)
    return pd.DataFrame(columns=[id_column])


def write_checkpoint(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    tmp = path.with_suffix(path.suffix + ".tmp")
    with tmp.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    tmp.replace(path)


def maybe_graceful_stop(context: str) -> None:
    if MAX_SECONDS_PER_RUN and (time.time() - PROCESS_START) >= MAX_SECONDS_PER_RUN:
        logging.info("Graceful stop after checkpoint at %s; rerun to resume.", context)
        raise SystemExit(0)


def softmax(logits: torch.Tensor) -> np.ndarray:
    return torch.nn.functional.softmax(logits, dim=-1).detach().cpu().numpy()


def nli_scores_for_pairs(
    pairs: list[tuple[str, str]],
    tokenizer: Any,
    model: Any,
    device: torch.device,
    batch_size: int,
    label_mapping: dict[int, str],
) -> list[dict[str, float]]:
    outputs: list[dict[str, float]] = []
    model.eval()
    with torch.no_grad():
        for start in range(0, len(pairs), batch_size):
            batch = pairs[start : start + batch_size]
            premises = [premise for premise, _hypothesis in batch]
            hypotheses = [hypothesis for _premise, hypothesis in batch]
            encoded = tokenizer(
                premises,
                hypotheses,
                truncation=True,
                max_length=MAX_LENGTH,
                padding=True,
                return_tensors="pt",
            )
            encoded = {key: value.to(device) for key, value in encoded.items()}
            probabilities = softmax(model(**encoded).logits)
            for row in probabilities:
                scores = {label_mapping[index].lower(): float(score) for index, score in enumerate(row)}
                outputs.append(
                    {
                        "entailment": scores["entailment"],
                        "neutral": scores["neutral"],
                        "contradiction": scores["contradiction"],
                    }
                )
    return outputs


def extract_nli(
    frame: pd.DataFrame,
    id_column: str,
    tokenizer: Any,
    model: Any,
    device: torch.device,
    batch_size: int,
    output_checkpoint: Path,
) -> pd.DataFrame:
    existing = read_checkpoint(output_checkpoint, id_column)
    existing_ids = set(existing[id_column].astype(str)) if id_column in existing.columns else set()
    rows: list[dict[str, Any]] = existing.to_dict("records") if not existing.empty else []
    row_by_id = {str(row[id_column]): row for row in rows if id_column in row}
    pending = frame[~frame[id_column].astype(str).isin(existing_ids)].copy()
    logging.info("NLI %s: %s existing, %s pending", id_column, len(existing_ids), len(pending))

    label_mapping = {index: label for index, label in model.config.id2label.items()}
    processed = 0
    for start in range(0, len(pending), batch_size):
        batch = pending.iloc[start : start + batch_size]
        src_pairs = list(zip(batch["src"].astype(str), batch["hyp"].astype(str)))
        tgt_pairs = list(zip(batch["tgt"].astype(str), batch["hyp"].astype(str)))
        src_scores = nli_scores_for_pairs(src_pairs, tokenizer, model, device, batch_size, label_mapping)
        tgt_scores = nli_scores_for_pairs(tgt_pairs, tokenizer, model, device, batch_size, label_mapping)
        for (_, row), src_score, tgt_score in zip(batch.iterrows(), src_scores, tgt_scores):
            result = {
                id_column: row[id_column],
                "src_ent": src_score["entailment"],
                "src_neu": src_score["neutral"],
                "src_con": src_score["contradiction"],
                "tgt_ent": tgt_score["entailment"],
                "tgt_neu": tgt_score["neutral"],
                "tgt_con": tgt_score["contradiction"],
            }
            row_by_id[str(row[id_column])] = result
        processed += len(batch)
        if processed % max(batch_size * 10, 20) == 0 or processed == len(pending):
            ordered = [row_by_id[str(row[id_column])] for _, row in frame.iterrows() if str(row[id_column]) in row_by_id]
            write_checkpoint(output_checkpoint, ordered, [id_column] + NLI_COLUMNS)
            logging.info("NLI %s checkpoint: %s/%s pending processed", id_column, processed, len(pending))
            maybe_graceful_stop(f"NLI {id_column} {len(ordered)}/{len(frame)}")

    final_rows = [row_by_id[str(row[id_column])] for _, row in frame.iterrows()]
    result = pd.DataFrame(final_rows)
    return result


def extract_similarity(
    frame: pd.DataFrame,
    id_column: str,
    model: SentenceTransformer,
    device_name: str,
    batch_size: int,
    output_checkpoint: Path,
) -> pd.DataFrame:
    existing = read_checkpoint(output_checkpoint, id_column)
    existing_ids = set(existing[id_column].astype(str)) if id_column in existing.columns else set()
    if len(existing_ids) == len(frame):
        logging.info("Similarity %s: reusing complete checkpoint", id_column)
        return existing

    logging.info("Similarity %s: computing all rows (%s)", id_column, len(frame))
    src_emb = model.encode(
        frame["src"].astype(str).tolist(),
        batch_size=batch_size,
        normalize_embeddings=True,
        convert_to_numpy=True,
        show_progress_bar=True,
        device=device_name,
    )
    tgt_emb = model.encode(
        frame["tgt"].astype(str).tolist(),
        batch_size=batch_size,
        normalize_embeddings=True,
        convert_to_numpy=True,
        show_progress_bar=True,
        device=device_name,
    )
    hyp_emb = model.encode(
        frame["hyp"].astype(str).tolist(),
        batch_size=batch_size,
        normalize_embeddings=True,
        convert_to_numpy=True,
        show_progress_bar=True,
        device=device_name,
    )
    sim_src_hyp = np.sum(src_emb * hyp_emb, axis=1)
    sim_tgt_hyp = np.sum(tgt_emb * hyp_emb, axis=1)
    sim_src_tgt = np.sum(src_emb * tgt_emb, axis=1)
    result = pd.DataFrame(
        {
            id_column: frame[id_column].values,
            "sim_src_hyp": sim_src_hyp,
            "sim_tgt_hyp": sim_tgt_hyp,
            "sim_src_tgt": sim_src_tgt,
        }
    )
    result["sim_max"] = result[["sim_src_hyp", "sim_tgt_hyp"]].max(axis=1)
    result["sim_min"] = result[["sim_src_hyp", "sim_tgt_hyp"]].min(axis=1)
    result["sim_mean"] = (result["sim_src_hyp"] + result["sim_tgt_hyp"]) / 2.0
    result["sim_gap_tgt_src"] = result["sim_tgt_hyp"] - result["sim_src_hyp"]
    result["sim_hyp_distance_from_truth"] = 1.0 - result["sim_tgt_hyp"]
    result.to_csv(output_checkpoint, index=False)
    return result


def validate_nli(nli: pd.DataFrame, id_column: str) -> list[dict[str, Any]]:
    rows = []
    for prefix in ["src", "tgt"]:
        total = nli[[f"{prefix}_ent", f"{prefix}_neu", f"{prefix}_con"]].sum(axis=1)
        rows.append(
            {
                "check": f"{prefix}_nli_sum_close_to_1",
                "passed": bool(np.allclose(total, 1.0, atol=TOLERANCE)),
                "max_abs_error": float(np.max(np.abs(total - 1.0))),
            }
        )
    values = nli[NLI_COLUMNS].to_numpy(dtype=float)
    rows.append(
        {
            "check": "nli_scores_in_0_1",
            "passed": bool(np.all((values >= -TOLERANCE) & (values <= 1.0 + TOLERANCE))),
            "max_abs_error": 0.0,
        }
    )
    rows.append(
        {
            "check": f"{id_column}_unique",
            "passed": bool(nli[id_column].nunique() == len(nli)),
            "max_abs_error": 0.0,
        }
    )
    return rows


def validate_similarity(sim: pd.DataFrame, id_column: str) -> list[dict[str, Any]]:
    rows = []
    base = sim[["sim_src_hyp", "sim_tgt_hyp", "sim_src_tgt"]].to_numpy(dtype=float)
    rows.append(
        {
            "check": "base_similarity_in_minus1_1",
            "passed": bool(np.all((base >= -1.0 - TOLERANCE) & (base <= 1.0 + TOLERANCE))),
            "max_abs_error": 0.0,
        }
    )
    rows.append(
        {
            "check": "sim_max_ge_sim_min",
            "passed": bool((sim["sim_max"] + TOLERANCE >= sim["sim_min"]).all()),
            "max_abs_error": 0.0,
        }
    )
    formulas = {
        "sim_mean": (sim["sim_src_hyp"] + sim["sim_tgt_hyp"]) / 2.0,
        "sim_gap_tgt_src": sim["sim_tgt_hyp"] - sim["sim_src_hyp"],
        "sim_hyp_distance_from_truth": 1.0 - sim["sim_tgt_hyp"],
    }
    for column, expected in formulas.items():
        error = np.abs(sim[column].to_numpy(dtype=float) - expected.to_numpy(dtype=float))
        rows.append(
            {
                "check": f"{column}_formula",
                "passed": bool(np.max(error) <= TOLERANCE),
                "max_abs_error": float(np.max(error)),
            }
        )
    rows.append(
        {
            "check": f"{id_column}_unique",
            "passed": bool(sim[id_column].nunique() == len(sim)),
            "max_abs_error": 0.0,
        }
    )
    return rows


def write_quality_audit(
    human: pd.DataFrame,
    synthetic: pd.DataFrame,
    human_nli: pd.DataFrame,
    synthetic_nli: pd.DataFrame,
    human_sim: pd.DataFrame,
    synthetic_sim: pd.DataFrame,
    human_combined: pd.DataFrame,
    synthetic_combined: pd.DataFrame,
) -> None:
    rows: list[dict[str, Any]] = []
    for dataset, frame, id_column, expected_rows in [
        ("human_combined", human_combined, "canonical_id", 561),
        ("synthetic_combined", synthetic_combined, "synthetic_id", 505),
    ]:
        rows.extend(
            [
                {"dataset": dataset, "check": "row_count", "passed": len(frame) == expected_rows, "value": len(frame)},
                {
                    "dataset": dataset,
                    "check": f"{id_column}_unique",
                    "passed": frame[id_column].nunique() == expected_rows,
                    "value": frame[id_column].nunique(),
                },
                {
                    "dataset": dataset,
                    "check": "exact_text_key_unique",
                    "passed": frame["exact_text_key"].nunique() == expected_rows,
                    "value": frame["exact_text_key"].nunique(),
                },
                {
                    "dataset": dataset,
                    "check": "no_missing_features",
                    "passed": int(frame[FEATURE_COLUMNS].isna().sum().sum()) == 0,
                    "value": int(frame[FEATURE_COLUMNS].isna().sum().sum()),
                },
                {
                    "dataset": dataset,
                    "check": "no_nan_inf_features",
                    "passed": bool(np.isfinite(frame[FEATURE_COLUMNS].to_numpy(dtype=float)).all()),
                    "value": "finite",
                },
            ]
        )
    for dataset, nli, id_column in [
        ("human_nli", human_nli, "canonical_id"),
        ("synthetic_nli", synthetic_nli, "synthetic_id"),
    ]:
        for row in validate_nli(nli, id_column):
            rows.append({"dataset": dataset, **row})
    for dataset, sim, id_column in [
        ("human_similarity", human_sim, "canonical_id"),
        ("synthetic_similarity", synthetic_sim, "synthetic_id"),
    ]:
        for row in validate_similarity(sim, id_column):
            rows.append({"dataset": dataset, **row})

    pd.DataFrame(rows).to_csv(OUTPUT_DIR / "canonical_feature_quality_audit.csv", index=False)


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


def safe_corr(x: pd.Series, y: pd.Series, kind: str) -> float | None:
    if len(x) < 2 or x.nunique() < 2 or y.nunique() < 2:
        return None
    if kind == "pearson":
        return float(pearsonr(x, y).statistic)
    return float(spearmanr(x, y).statistic)


def compatibility_audit(human_combined: pd.DataFrame, human_manifest_with_text: pd.DataFrame) -> None:
    old = pd.read_csv(OLD_TRIAL_FEATURES, keep_default_na=False)
    old_human = old[old.get("source_type", "") == "human_labeled"].copy()
    if old_human.empty:
        old_human = old.iloc[:0].copy()
    old_human["match_key"] = normalized_key(old_human)
    text_cols = ["canonical_id", "src", "tgt", "hyp"]
    trial_rows = human_combined[human_combined["source_split"] == "trial"].merge(
        human_manifest_with_text[text_cols], on="canonical_id", how="left"
    )
    trial_rows["match_key"] = normalized_key(trial_rows)
    matched = trial_rows.merge(old_human, on="match_key", suffixes=("_new", "_old"))

    rows: list[dict[str, Any]] = []
    for feature in FEATURE_COLUMNS:
        new_col = f"{feature}_new"
        old_col = f"{feature}_old"
        if new_col not in matched.columns or old_col not in matched.columns:
            rows.append(
                {
                    "feature": feature,
                    "matched_rows": len(matched),
                    "mean_abs_diff": None,
                    "median_abs_diff": None,
                    "max_abs_diff": None,
                    "pearson": None,
                    "spearman": None,
                    "note": "feature_missing_in_old_or_new",
                }
            )
            continue
        x = pd.to_numeric(matched[new_col], errors="coerce")
        y = pd.to_numeric(matched[old_col], errors="coerce")
        diff = (x - y).abs()
        rows.append(
            {
                "feature": feature,
                "matched_rows": int(len(matched)),
                "mean_abs_diff": float(diff.mean()) if len(diff) else None,
                "median_abs_diff": float(diff.median()) if len(diff) else None,
                "max_abs_diff": float(diff.max()) if len(diff) else None,
                "pearson": safe_corr(x, y, "pearson"),
                "spearman": safe_corr(x, y, "spearman"),
                "note": "",
            }
        )

    # Simple permutation indicator for NLI label columns: compare aggregate max correlations.
    if len(matched):
        for prefix in ["src", "tgt"]:
            new_cols = [f"{prefix}_ent_new", f"{prefix}_neu_new", f"{prefix}_con_new"]
            old_cols = [f"{prefix}_ent_old", f"{prefix}_neu_old", f"{prefix}_con_old"]
            if all(col in matched.columns for col in new_cols + old_cols):
                corr_matrix = {}
                for ncol in new_cols:
                    for ocol in old_cols:
                        corr_matrix[f"{ncol}->{ocol}"] = safe_corr(
                            pd.to_numeric(matched[ncol], errors="coerce"),
                            pd.to_numeric(matched[ocol], errors="coerce"),
                            "pearson",
                        )
                rows.append(
                    {
                        "feature": f"{prefix}_nli_permutation_indicator",
                        "matched_rows": int(len(matched)),
                        "mean_abs_diff": None,
                        "median_abs_diff": None,
                        "max_abs_diff": None,
                        "pearson": None,
                        "spearman": None,
                        "note": json.dumps(corr_matrix, sort_keys=True),
                    }
                )
    pd.DataFrame(rows).to_csv(OUTPUT_DIR / "canonical_feature_compatibility_audit.csv", index=False)


def run_smoke_test(human: pd.DataFrame, tokenizer: Any, nli_model: Any, sim_model: SentenceTransformer, device: torch.device, device_name: str, batch_size: int) -> dict[str, Any]:
    sample = (
        human.sort_values("canonical_id")
        .groupby("task", observed=False)
        .head(1)
        .sort_values("task")
        .reset_index(drop=True)
    )
    nli = extract_nli(
        sample,
        "canonical_id",
        tokenizer,
        nli_model,
        device,
        batch_size,
        CHECKPOINT_DIR / "smoke_human_nli_checkpoint.csv",
    )
    sim = extract_similarity(
        sample,
        "canonical_id",
        sim_model,
        device_name,
        SIM_BATCH_SIZE,
        CHECKPOINT_DIR / "smoke_human_similarity_checkpoint.csv",
    )
    checks = validate_nli(nli, "canonical_id") + validate_similarity(sim, "canonical_id")
    passed = all(bool(row["passed"]) for row in checks)
    return {
        "sample_ids": sample["canonical_id"].tolist(),
        "tasks": sample["task"].tolist(),
        "passed": passed,
        "checks": checks,
    }


def main() -> None:
    start_time = time.time()
    ensure_dirs()
    setup_logging()
    metadata: OrderedDict[str, Any] = OrderedDict()
    metadata["timestamp_start"] = datetime.now().isoformat(timespec="seconds")
    metadata["interpreter"] = sys.executable
    metadata["python_version"] = platform.python_version()
    metadata["torch_version"] = torch.__version__
    metadata["transformers_version"] = transformers.__version__
    import sentence_transformers

    metadata["sentence_transformers_version"] = sentence_transformers.__version__
    metadata["numpy_version"] = np.__version__
    metadata["pandas_version"] = pd.__version__
    metadata["cuda_available"] = torch.cuda.is_available()
    metadata["cuda_version"] = torch.version.cuda
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    device_name = "cuda" if torch.cuda.is_available() else "cpu"
    metadata["device"] = str(device)
    if torch.cuda.is_available():
        metadata["cuda_device_name"] = torch.cuda.get_device_name(0)
        free, total = torch.cuda.mem_get_info(0)
        metadata["cuda_memory_free_bytes_start"] = int(free)
        metadata["cuda_memory_total_bytes"] = int(total)
    else:
        metadata["cuda_device_name"] = None
        metadata["cuda_memory_free_bytes_start"] = None
        metadata["cuda_memory_total_bytes"] = None

    metadata["human_manifest_sha256"] = sha256_file(HUMAN_MANIFEST)
    metadata["synthetic_manifest_sha256"] = sha256_file(SYNTHETIC_MANIFEST)
    metadata["fold_file_sha256"] = sha256_file(FOLD_ASSIGNMENTS)

    human, synthetic, folds = validate_inputs()
    logging.info("Inputs validated: human=%s synthetic=%s folds=%s", len(human), len(synthetic), len(folds))

    nli_files = resolve_cached_artifacts(NLI_MODEL, ["config.json", "tokenizer_config.json"])
    sim_files = resolve_cached_artifacts(SIM_MODEL, ["config.json", "modules.json"])
    metadata["model_names"] = {"nli": NLI_MODEL, "similarity": SIM_MODEL}
    metadata["model_cached_artifacts"] = {"nli": nli_files, "similarity": sim_files}
    metadata["model_config_hashes"] = {
        "nli_config": sha256_file(Path(nli_files["config.json"])),
        "similarity_config": sha256_file(Path(sim_files["config.json"])),
    }

    logging.info("Loading NLI model locally: %s", NLI_MODEL)
    nli_config = AutoConfig.from_pretrained(NLI_MODEL, local_files_only=True)
    nli_mapping = {int(key): value for key, value in nli_config.id2label.items()}
    if nli_mapping != {0: "CONTRADICTION", 1: "NEUTRAL", 2: "ENTAILMENT"}:
        raise RuntimeError(f"Unexpected NLI id2label mapping: {nli_mapping}")
    tokenizer = AutoTokenizer.from_pretrained(NLI_MODEL, local_files_only=True)
    nli_model = AutoModelForSequenceClassification.from_pretrained(NLI_MODEL, local_files_only=True)
    nli_model.to(device)
    nli_model.eval()

    logging.info("Loading similarity model locally: %s", SIM_MODEL)
    sim_model = SentenceTransformer(SIM_MODEL, local_files_only=True, device=device_name)

    nli_batch_size = NLI_BATCH_SIZE_GPU if torch.cuda.is_available() else NLI_BATCH_SIZE_CPU
    metadata["nli_label_mapping"] = nli_mapping
    metadata["nli_truncation"] = True
    metadata["nli_max_length"] = MAX_LENGTH
    metadata["nli_batch_size"] = nli_batch_size
    metadata["similarity_batch_size"] = SIM_BATCH_SIZE
    metadata["similarity_normalize_embeddings"] = True
    metadata["quality_tolerance"] = TOLERANCE
    metadata["similarity_formulas"] = {
        "sim_src_hyp": "dot(normalized_src_embedding, normalized_hyp_embedding)",
        "sim_tgt_hyp": "dot(normalized_tgt_embedding, normalized_hyp_embedding)",
        "sim_src_tgt": "dot(normalized_src_embedding, normalized_tgt_embedding)",
        "sim_max": "max(sim_src_hyp, sim_tgt_hyp)",
        "sim_min": "min(sim_src_hyp, sim_tgt_hyp)",
        "sim_mean": "(sim_src_hyp + sim_tgt_hyp) / 2",
        "sim_gap_tgt_src": "sim_tgt_hyp - sim_src_hyp",
        "sim_hyp_distance_from_truth": "1.0 - sim_tgt_hyp",
    }

    stage_times: OrderedDict[str, float] = OrderedDict()
    smoke_start = time.time()
    smoke = run_smoke_test(human, tokenizer, nli_model, sim_model, device, device_name, nli_batch_size)
    stage_times["smoke_test_seconds"] = round(time.time() - smoke_start, 3)
    metadata["smoke_test"] = smoke
    if not smoke["passed"]:
        raise RuntimeError(f"Smoke test failed: {smoke}")
    logging.info("Smoke test passed")

    stage_start = time.time()
    human_nli = extract_nli(
        human,
        "canonical_id",
        tokenizer,
        nli_model,
        device,
        nli_batch_size,
        CHECKPOINT_DIR / "human_nli_checkpoint.csv",
    )
    stage_times["human_nli_seconds"] = round(time.time() - stage_start, 3)

    stage_start = time.time()
    synthetic_nli = extract_nli(
        synthetic,
        "synthetic_id",
        tokenizer,
        nli_model,
        device,
        nli_batch_size,
        CHECKPOINT_DIR / "synthetic_nli_checkpoint.csv",
    )
    stage_times["synthetic_nli_seconds"] = round(time.time() - stage_start, 3)

    stage_start = time.time()
    human_sim = extract_similarity(
        human,
        "canonical_id",
        sim_model,
        device_name,
        SIM_BATCH_SIZE,
        CHECKPOINT_DIR / "human_similarity_checkpoint.csv",
    )
    stage_times["human_similarity_seconds"] = round(time.time() - stage_start, 3)

    stage_start = time.time()
    synthetic_sim = extract_similarity(
        synthetic,
        "synthetic_id",
        sim_model,
        device_name,
        SIM_BATCH_SIZE,
        CHECKPOINT_DIR / "synthetic_similarity_checkpoint.csv",
    )
    stage_times["synthetic_similarity_seconds"] = round(time.time() - stage_start, 3)

    human_nli_out = OUTPUT_DIR / "canonical_human_nli_features.csv"
    human_sim_out = OUTPUT_DIR / "canonical_human_similarity_features.csv"
    synthetic_nli_out = OUTPUT_DIR / "canonical_synthetic_nli_features.csv"
    synthetic_sim_out = OUTPUT_DIR / "canonical_synthetic_similarity_features.csv"
    human_nli.to_csv(human_nli_out, index=False)
    human_sim.to_csv(human_sim_out, index=False)
    synthetic_nli.to_csv(synthetic_nli_out, index=False)
    synthetic_sim.to_csv(synthetic_sim_out, index=False)

    human_meta = human[
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
    human_combined = human_meta.merge(human_nli, on="canonical_id", how="inner").merge(
        human_sim, on="canonical_id", how="inner"
    )
    human_combined = human_combined[
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
        + FEATURE_COLUMNS
    ]

    synthetic_meta = synthetic[
        [
            "synthetic_id",
            "source_csv_row_index",
            "sample_id",
            "exact_text_key",
            "task",
            "label",
            "label_bin",
            "p_hallucination",
            "source_type",
        ]
    ].copy()
    synthetic_combined = synthetic_meta.merge(synthetic_nli, on="synthetic_id", how="inner").merge(
        synthetic_sim, on="synthetic_id", how="inner"
    )
    synthetic_combined = synthetic_combined[
        [
            "synthetic_id",
            "source_csv_row_index",
            "sample_id",
            "exact_text_key",
            "task",
            "label",
            "label_bin",
            "p_hallucination",
            "source_type",
        ]
        + FEATURE_COLUMNS
    ]

    human_combined_out = OUTPUT_DIR / "canonical_human_14_features.csv"
    synthetic_combined_out = OUTPUT_DIR / "canonical_synthetic_14_features.csv"
    human_combined.to_csv(human_combined_out, index=False)
    synthetic_combined.to_csv(synthetic_combined_out, index=False)

    write_quality_audit(
        human,
        synthetic,
        human_nli,
        synthetic_nli,
        human_sim,
        synthetic_sim,
        human_combined,
        synthetic_combined,
    )
    compatibility_audit(human_combined, human)

    output_hashes = OrderedDict()
    for path in [
        human_nli_out,
        human_sim_out,
        human_combined_out,
        synthetic_nli_out,
        synthetic_sim_out,
        synthetic_combined_out,
        OUTPUT_DIR / "canonical_feature_quality_audit.csv",
        OUTPUT_DIR / "canonical_feature_compatibility_audit.csv",
    ]:
        output_hashes[path.name] = sha256_file(path)
    metadata["output_sha256"] = output_hashes
    metadata["runtime_seconds_by_stage"] = stage_times
    metadata["rows_completed"] = {
        "human": int(len(human_combined)),
        "synthetic": int(len(synthetic_combined)),
        "human_nli": int(len(human_nli)),
        "synthetic_nli": int(len(synthetic_nli)),
        "human_similarity": int(len(human_sim)),
        "synthetic_similarity": int(len(synthetic_sim)),
    }
    metadata["resumptions_or_retries"] = 0
    metadata["timestamp_end"] = datetime.now().isoformat(timespec="seconds")
    metadata["total_runtime_seconds"] = round(time.time() - start_time, 3)
    (OUTPUT_DIR / "canonical_feature_extraction_metadata.json").write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    logging.info("Prompt 7D feature extraction complete")
    logging.info("Output hashes: %s", json.dumps(output_hashes, ensure_ascii=False))


if __name__ == "__main__":
    main()
