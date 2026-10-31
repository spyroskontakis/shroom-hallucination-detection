"""Regenerate canonical SHROOM fold assignments with scikit-learn.

Explicit input and fresh external run paths are required. Importing this module
only initializes the standard-library bootstrap; analysis dependencies are deferred.
Full generation needs a separately approved isolated runtime and original input.

Prompt 7C-A scope:
- read only canonical_human_development_manifest.csv as input;
- use sklearn.model_selection.StratifiedKFold exactly;
- write canonical_fold_assignments.csv plus metadata/audit files;
- no model inference, feature extraction, training, scoring, API calls, or DOCX edits.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import platform
import stat
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path

# Bound only by explicit command-line execution, never during import.
INPUT_MANIFEST = None
OUTPUT_FOLDS = None
METADATA_JSON = None
BALANCE_AUDIT_CSV = None


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


def _generate_folds() -> None:
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


def _checked_path(value: Path) -> Path:
    """Normalize a path without intentionally following symlink/reparse ancestors."""
    path = Path(os.path.abspath(value.expanduser()))
    for candidate in reversed((path, *path.parents)):
        try:
            info = candidate.lstat()
        except FileNotFoundError:
            continue
        if stat.S_ISLNK(info.st_mode) or getattr(info, "st_file_attributes", 0) & 0x400:
            raise ValueError(f"Symlink/reparse-point path is not accepted: {candidate}")
    return path


def _validated_paths(input_manifest: Path, run_dir: Path) -> tuple[Path, Path]:
    output = _checked_path(run_dir)
    for parent in (output, *output.parents):
        try:
            (parent / ".git").lstat()
        except FileNotFoundError:
            continue
        raise ValueError("The run directory must be outside Git repositories.")
    if output.exists():
        raise ValueError("The run directory already exists; choose a new path.")
    if not output.parent.is_dir():
        raise ValueError("The run parent must already be an existing directory.")

    manifest = _checked_path(input_manifest)
    if not manifest.is_file():
        raise ValueError("The input manifest must already be a regular file.")
    if output.is_relative_to(manifest.parent) or manifest.is_relative_to(output):
        raise ValueError("The run directory must not overlap the input directory.")
    return manifest, output


def _validate_input_header(path: Path) -> None:
    """Check columns used by the unchanged body before allowing output creation."""
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        fields = csv.DictReader(handle).fieldnames or []
    required = ["canonical_id", "task", "label_bin", "exact_text_key",
                "task_reference_key"]
    missing = [column for column in required if column not in fields]
    if missing:
        raise ValueError(f"Missing required input columns: {missing}")


def _load_runtime_dependencies() -> None:
    global pd, sklearn, StratifiedKFold
    import pandas as pd
    import sklearn
    from sklearn.model_selection import StratifiedKFold


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Recorded sklearn canonical fold-generation procedure.",
        epilog=(
            "--check-paths reads no CSV content and creates no directories. "
            "--generate is a scientific execution requiring separate approval, "
            "original input and isolated dependency/cache/temp settings."
        ),
    )
    parser.add_argument(
        "--input-manifest", type=Path, required=True,
        help="Existing full canonical human manifest; no public-projection fallback.",
    )
    parser.add_argument(
        "--run-dir", type=Path, required=True,
        help="Fresh external output directory; its parent must already exist.",
    )
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument(
        "--check-paths", action="store_true",
        help="Read-only existence/location plan; no imports, CSV reads or generation.",
    )
    mode.add_argument(
        "--generate", action="store_true",
        help="Explicit generation into the new run directory; never historical outputs.",
    )
    args = parser.parse_args(argv)
    try:
        manifest, run_dir = _validated_paths(args.input_manifest, args.run_dir)
    except (OSError, ValueError) as exc:
        parser.error(str(exc))

    outputs = {
        "folds": run_dir / "canonical_fold_assignments.csv",
        "balance_audit": run_dir / "canonical_fold_balance_audit.csv",
        "metadata": run_dir / "canonical_fold_generation_metadata.json",
    }
    if args.check_paths:
        print(json.dumps({
            "validation": "path_existence_only",
            "input_manifest": str(manifest),
            "outputs": {key: str(path) for key, path in outputs.items()},
            "input_contents_checked": False,
            "generation_executed": False,
        }, indent=2))
        return 0

    try:
        _validate_input_header(manifest)
    except (OSError, ValueError, csv.Error) as exc:
        parser.error(str(exc))
    _load_runtime_dependencies()

    global INPUT_MANIFEST, OUTPUT_FOLDS, METADATA_JSON, BALANCE_AUDIT_CSV
    INPUT_MANIFEST = manifest
    OUTPUT_FOLDS = outputs["folds"]
    METADATA_JSON = outputs["metadata"]
    BALANCE_AUDIT_CSV = outputs["balance_audit"]
    try:
        run_dir.mkdir(exist_ok=False)
    except OSError as exc:
        parser.error(str(exc))
    _generate_folds()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
