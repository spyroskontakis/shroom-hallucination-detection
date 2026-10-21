"""Regenerate canonical SHROOM fold assignments with scikit-learn.

Prompt 7C-A scope:
- read only canonical_human_development_manifest.csv as input;
- use sklearn.model_selection.StratifiedKFold exactly;
- write canonical_fold_assignments.csv plus metadata/audit files;
- no model inference, feature extraction, training, scoring, API calls, or DOCX edits.
"""

from __future__ import annotations

import csv
import hashlib
import json
import platform
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path

import pandas as pd
import sklearn
from sklearn.model_selection import StratifiedKFold


ROOT = Path(__file__).resolve().parent
INPUT_MANIFEST = ROOT / "canonical_human_development_manifest.csv"
OUTPUT_FOLDS = ROOT / "canonical_fold_assignments.csv"
METADATA_JSON = ROOT / "canonical_fold_generation_metadata.json"
BALANCE_AUDIT_CSV = ROOT / "canonical_fold_balance_audit.csv"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_csv(path: Path, rows: list[dict[str, object]], fieldnames: list[str]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def validate_input(frame: pd.DataFrame) -> None:
    required = ["canonical_id", "task", "label_bin", "exact_text_key"]
    missing_columns = [column for column in required if column not in frame.columns]
    if missing_columns:
        raise ValueError(f"Missing required columns: {missing_columns}")
    if len(frame) != 561:
        raise ValueError(f"Expected 561 rows, found {len(frame)}")
    if frame["canonical_id"].nunique() != 561:
        raise ValueError("canonical_id is not unique for all 561 samples")
    if frame["exact_text_key"].nunique() != 561:
        raise ValueError("exact_text_key is not unique for all 561 samples")
    observed_labels = set(frame["label_bin"].astype(str))
    if observed_labels != {"0", "1"}:
        raise ValueError(f"Unexpected label_bin values: {sorted(observed_labels)}")
    observed_tasks = set(frame["task"].astype(str))
    if observed_tasks != {"DM", "MT", "PG"}:
        raise ValueError(f"Unexpected task values: {sorted(observed_tasks)}")
    missing_required = int(frame[required].isna().sum().sum())
    if missing_required:
        raise ValueError(f"Missing values in required columns: {missing_required}")


def main() -> None:
    input_hash = sha256_file(INPUT_MANIFEST)
    frame = pd.read_csv(INPUT_MANIFEST, dtype={"label_bin": "int64"})
    validate_input(frame)

    frame = frame.sort_values("canonical_id", kind="mergesort").reset_index(drop=True)
    frame["stratum"] = frame["task"].astype(str) + "__" + frame["label_bin"].astype(str)

    stratum_counts = frame["stratum"].value_counts().sort_index()
    below_minimum = stratum_counts[stratum_counts < 5]
    if not below_minimum.empty:
        raise ValueError(
            "At least one stratum has fewer than 5 samples: "
            + below_minimum.to_dict().__repr__()
        )

    splitter = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    fold_ids = [None] * len(frame)
    for fold_index, (_train_idx, validation_idx) in enumerate(
        splitter.split(frame, frame["stratum"]), start=1
    ):
        for row_index in validation_idx:
            fold_ids[row_index] = fold_index

    if any(fold_id is None for fold_id in fold_ids):
        raise RuntimeError("Some samples were not assigned a fold")

    output = frame.loc[
        :, ["canonical_id", "stratum", "task", "label_bin", "exact_text_key"]
    ].copy()
    output.insert(1, "fold_id", fold_ids)
    output = output.loc[
        :, ["canonical_id", "fold_id", "stratum", "task", "label_bin", "exact_text_key"]
    ]

    if len(output) != 561:
        raise RuntimeError(f"Expected 561 assignments, found {len(output)}")
    if output["canonical_id"].nunique() != 561:
        raise RuntimeError("canonical_id does not appear exactly once")
    if output["exact_text_key"].nunique() != 561:
        raise RuntimeError("exact_text_key does not appear exactly once")
    if set(output["fold_id"]) != {1, 2, 3, 4, 5}:
        raise RuntimeError(f"Unexpected folds: {sorted(set(output['fold_id']))}")

    fold_sizes = output["fold_id"].value_counts().sort_index()
    if int(fold_sizes.max() - fold_sizes.min()) > 1:
        raise RuntimeError("Fold-size difference is greater than 1")

    balance = (
        output.groupby(["fold_id", "stratum"], observed=False)
        .size()
        .rename("samples")
        .reset_index()
        .sort_values(["fold_id", "stratum"], kind="mergesort")
    )
    expected_strata = {"DM__0", "DM__1", "MT__0", "MT__1", "PG__0", "PG__1"}
    for fold_id in range(1, 6):
        fold_strata = set(balance.loc[balance["fold_id"] == fold_id, "stratum"])
        if fold_strata != expected_strata:
            raise RuntimeError(f"Fold {fold_id} does not contain all six strata")
    per_stratum_spread = (
        balance.groupby("stratum", observed=False)["samples"]
        .agg(lambda values: int(values.max() - values.min()))
        .to_dict()
    )
    if any(spread > 1 for spread in per_stratum_spread.values()):
        raise RuntimeError(f"Per-stratum fold spread greater than 1: {per_stratum_spread}")

    merged = output.merge(
        frame[["canonical_id"]], on="canonical_id", how="outer", indicator=True
    )
    if set(merged["_merge"]) != {"both"} or len(merged) != 561:
        raise RuntimeError("Fold file does not merge 1:1 with canonical manifest")

    output.to_csv(OUTPUT_FOLDS, index=False)
    balance.to_csv(BALANCE_AUDIT_CSV, index=False)
    output_hash = sha256_file(OUTPUT_FOLDS)

    repeated_task_refs = frame["task_reference_key"].value_counts()
    repeated_task_refs = repeated_task_refs[repeated_task_refs > 1]
    repeated_task_refs_multi_fold = 0
    if not repeated_task_refs.empty:
        temp = frame[["canonical_id", "task_reference_key"]].merge(
            output[["canonical_id", "fold_id"]], on="canonical_id", how="left"
        )
        repeated_keys = set(repeated_task_refs.index)
        repeated_task_refs_multi_fold = int(
            sum(
                temp.loc[temp["task_reference_key"] == key, "fold_id"].nunique() > 1
                for key in repeated_keys
            )
        )

    metadata = {
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "interpreter_path": sys.executable,
        "python_version": platform.python_version(),
        "sklearn_version": sklearn.__version__,
        "pandas_version": pd.__version__,
        "input_filename": str(INPUT_MANIFEST),
        "input_sha256": input_hash,
        "output_filename": str(OUTPUT_FOLDS),
        "output_sha256": output_hash,
        "splitter": "sklearn.model_selection.StratifiedKFold",
        "n_splits": 5,
        "shuffle": True,
        "random_state": 42,
        "sorting_key": "canonical_id",
        "total_samples": int(len(output)),
        "fold_sizes": {str(k): int(v) for k, v in fold_sizes.to_dict().items()},
        "stratum_counts": {str(k): int(v) for k, v in stratum_counts.to_dict().items()},
        "stratum_counts_by_fold": [
            {
                "fold_id": int(row.fold_id),
                "stratum": str(row.stratum),
                "samples": int(row.samples),
            }
            for row in balance.itertuples(index=False)
        ],
        "task_reference_audit": {
            "task_reference_keys_with_multiple_samples": int(len(repeated_task_refs)),
            "repeated_task_reference_keys_spanning_multiple_folds": repeated_task_refs_multi_fold,
        },
    }
    METADATA_JSON.write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    print("Canonical folds regenerated with sklearn.model_selection.StratifiedKFold")
    print(f"python_executable={sys.executable}")
    print(f"python_version={platform.python_version()}")
    print(f"sklearn_version={sklearn.__version__}")
    print(f"pandas_version={pd.__version__}")
    print(f"input_sha256={input_hash}")
    print(f"output_sha256={output_hash}")
    print("fold_sizes=" + json.dumps(metadata["fold_sizes"], ensure_ascii=False))
    print("stratum_counts=" + json.dumps(metadata["stratum_counts"], ensure_ascii=False))
    print(
        "task_reference_audit="
        + json.dumps(metadata["task_reference_audit"], ensure_ascii=False)
    )


if __name__ == "__main__":
    main()
