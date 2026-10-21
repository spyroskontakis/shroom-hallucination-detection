"""Prepare canonical evaluation manifests for the SHROOM thesis protocol.

Prompt 7C scope:
- lightweight deterministic data processing only;
- no notebook execution;
- no model inference;
- no feature extraction;
- no Random Forest training or cross-validation scoring.

The script reads raw JSON/CSV artifacts and writes canonical manifests used by the
next experimental stage.
"""

from __future__ import annotations

import csv
import hashlib
import json
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

import pandas as pd


CODEX_ROOT = Path(__file__).resolve().parent
PROJECT_ROOT = CODEX_ROOT.parent

TRIAL_PATH = CODEX_ROOT / "data" / "Trial" / "SHROOM_trial-v1.1" / "trial-v1.json"
DEV_AGNOSTIC_PATH = PROJECT_ROOT / "Dev" / "SHROOM_dev-v2" / "val.model-agnostic.json"
TEST_AGNOSTIC_PATH = (
    CODEX_ROOT
    / "data"
    / "Labeled test"
    / "SHROOM_test-labeled"
    / "test.model-agnostic.json"
)
TRAIN_AGNOSTIC_PATH = (
    CODEX_ROOT
    / "data"
    / "Unlabeled train"
    / "SHROOM_unlabeled-training-data-v2"
    / "train.model-agnostic.json"
)
SYNTHETIC_BALANCED_PATH = (
    CODEX_ROOT
    / "data"
    / "6. Feature Extraction on Augmented Training Data"
    / "filtered_synthetic_data_balanced.csv"
)

DUPLICATE_AUDIT_PATH = CODEX_ROOT / "duplicate_group_audit.csv"
EXCLUDED_HUMAN_TEST_OVERLAPS_PATH = CODEX_ROOT / "excluded_human_test_overlaps.csv"
CANONICAL_HUMAN_MANIFEST_PATH = CODEX_ROOT / "canonical_human_development_manifest.csv"
CANONICAL_SYNTHETIC_MANIFEST_PATH = CODEX_ROOT / "canonical_synthetic_diagnostic_manifest.csv"
EXCLUDED_SYNTHETIC_PATH = CODEX_ROOT / "excluded_synthetic_overlap_rows.csv"
FOLD_ASSIGNMENTS_PATH = CODEX_ROOT / "canonical_fold_assignments.csv"


def normalize_value(value: Any) -> str:
    """Deterministic text normalization allowed by Prompt 7C."""
    if value is None:
        text = ""
    elif isinstance(value, (list, dict)):
        text = json.dumps(value, ensure_ascii=False, sort_keys=True)
    else:
        text = str(value)
    text = unicodedata.normalize("NFC", text)
    text = " ".join(text.strip().split())
    return text


def hash_parts(*parts: Any) -> str:
    payload = "\u241f".join(normalize_value(part) for part in parts)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def load_json(path: Path) -> list[dict[str, Any]]:
    with path.open("r", encoding="utf-8") as handle:
        rows = json.load(handle)
    if not isinstance(rows, list):
        raise TypeError(f"Expected a list in {path}")
    return rows


def binary_label(label: Any) -> int | str:
    value = normalize_value(label)
    if value == "Hallucination":
        return 1
    if value == "Not Hallucination":
        return 0
    return value


def labels_text(value: Any) -> str:
    if isinstance(value, str):
        try:
            parsed = json.loads(value)
            return json.dumps(parsed, ensure_ascii=False, sort_keys=True)
        except json.JSONDecodeError:
            return normalize_value(value)
    return normalize_value(value)


def decorate_row(row: dict[str, Any], source_split: str, original_row_index: int) -> dict[str, Any]:
    task = normalize_value(row.get("task"))
    src = normalize_value(row.get("src"))
    tgt = normalize_value(row.get("tgt"))
    hyp = normalize_value(row.get("hyp"))
    ref = normalize_value(row.get("ref", row.get("reference_text", "")))
    task_reference_text = src if task == "PG" else tgt
    label = normalize_value(row.get("label"))
    p_hallucination = row.get("p(Hallucination)", row.get("p_hallucination", ""))
    return {
        "source_split": source_split,
        "original_row_index": original_row_index,
        "task": task,
        "src": src,
        "tgt": tgt,
        "hyp": hyp,
        "label": label,
        "label_bin": binary_label(label),
        "p_hallucination": normalize_value(p_hallucination),
        "labels": labels_text(row.get("labels", "")),
        "model": normalize_value(row.get("model", "")),
        "ref": ref,
        "exact_text_key": hash_parts(task, src, tgt, hyp),
        "source_pair_key": hash_parts(task, src, tgt),
        "task_reference_key": hash_parts(task, task_reference_text),
    }


def group_consistency(rows: list[dict[str, Any]]) -> dict[str, bool]:
    labels = {row["label_bin"] for row in rows}
    probabilities = {row["p_hallucination"] for row in rows}
    annotation_lists = {row["labels"] for row in rows}
    return {
        "binary_labels_agree": len(labels) <= 1,
        "p_hallucination_values_agree": len(probabilities) <= 1,
        "individual_annotation_lists_agree": len(annotation_lists) <= 1,
    }


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def deterministic_stratified_folds(
    strata: list[str], n_splits: int = 5, random_state: int = 42
) -> list[int]:
    """Small local fallback for StratifiedKFold-style assignment.

    The bundled runtime used for this project does not provide scikit-learn.
    This function performs the only needed operation for Prompt 7C: create a
    deterministic, shuffled, stratified assignment of each sample to one
    validation fold. It does not train or evaluate any model.
    """
    import random

    grouped: dict[str, list[int]] = defaultdict(list)
    for index, stratum in enumerate(strata):
        grouped[stratum].append(index)

    fold_assignment = [0] * len(strata)
    for stratum in sorted(grouped):
        indices = grouped[stratum][:]
        random.Random(f"{random_state}:{stratum}").shuffle(indices)
        for offset, index in enumerate(indices):
            fold_assignment[index] = (offset % n_splits) + 1
    return fold_assignment


def main() -> None:
    trial_rows = [
        decorate_row(row, "trial", index)
        for index, row in enumerate(load_json(TRIAL_PATH))
    ]
    dev_rows = [
        decorate_row(row, "development_model_agnostic", index)
        for index, row in enumerate(load_json(DEV_AGNOSTIC_PATH))
    ]
    test_rows = [
        decorate_row(row, "official_test_model_agnostic", index)
        | {"test_id": normalize_value(row.get("id"))}
        for index, row in enumerate(load_json(TEST_AGNOSTIC_PATH))
    ]
    train_rows = load_json(TRAIN_AGNOSTIC_PATH)
    synthetic = pd.read_csv(SYNTHETIC_BALANCED_PATH)

    combined_human = trial_rows + dev_rows
    by_exact: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in combined_human:
        by_exact[row["exact_text_key"]].append(row)

    duplicate_audit_rows: list[dict[str, Any]] = []
    duplicate_policy: dict[tuple[str, int], str] = {}
    duplicate_group_summary: list[dict[str, Any]] = []
    for exact_key, group in sorted(by_exact.items()):
        if len(group) == 1:
            continue
        consistency = group_consistency(group)
        sources = {row["source_split"] for row in group}
        if sources == {"trial", "development_model_agnostic"}:
            policy = "keep_development_remove_trial"
            for row in group:
                duplicate_policy[(row["source_split"], row["original_row_index"])] = (
                    "remove_trial_development_duplicate"
                    if row["source_split"] == "trial"
                    else "keep_development_duplicate_precedence"
                )
        elif sources == {"development_model_agnostic"}:
            if all(consistency.values()):
                policy = "keep_first_development_duplicate"
                first_seen = min(row["original_row_index"] for row in group)
                for row in group:
                    duplicate_policy[(row["source_split"], row["original_row_index"])] = (
                        "keep_first_internal_development_duplicate"
                        if row["original_row_index"] == first_seen
                        else "remove_internal_development_duplicate"
                    )
            else:
                policy = "excluded_annotation_conflict"
                for row in group:
                    duplicate_policy[(row["source_split"], row["original_row_index"])] = (
                        "excluded_annotation_conflict"
                    )
        else:
            policy = "manual_review_unexpected_duplicate_group"
        duplicate_group_summary.append(
            {
                "exact_text_key": exact_key,
                "group_size": len(group),
                "sources": ";".join(sorted(sources)),
                "policy": policy,
                **consistency,
            }
        )
        for row in group:
            duplicate_audit_rows.append(
                {
                    **row,
                    **consistency,
                    "duplicate_group_size": len(group),
                    "duplicate_group_sources": ";".join(sorted(sources)),
                    "applied_policy": policy,
                    "row_policy": duplicate_policy.get(
                        (row["source_split"], row["original_row_index"]),
                        "manual_review",
                    ),
                }
            )

    audit_fields = [
        "exact_text_key",
        "source_split",
        "original_row_index",
        "task",
        "src",
        "tgt",
        "hyp",
        "label",
        "p_hallucination",
        "labels",
        "model",
        "ref",
        "binary_labels_agree",
        "p_hallucination_values_agree",
        "individual_annotation_lists_agree",
        "duplicate_group_size",
        "duplicate_group_sources",
        "applied_policy",
        "row_policy",
    ]
    write_csv(DUPLICATE_AUDIT_PATH, duplicate_audit_rows, audit_fields)

    kept_after_duplicates: list[dict[str, Any]] = []
    duplicate_excluded_statuses = {
        "remove_trial_development_duplicate",
        "remove_internal_development_duplicate",
        "excluded_annotation_conflict",
    }
    for row in combined_human:
        status = duplicate_policy.get((row["source_split"], row["original_row_index"]), "keep_unique")
        if status not in duplicate_excluded_statuses:
            kept_after_duplicates.append(row | {"duplicate_policy": status})

    test_by_exact: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in test_rows:
        test_by_exact[row["exact_text_key"]].append(row)

    human_test_overlap_rows: list[dict[str, Any]] = []
    final_human_rows: list[dict[str, Any]] = []
    for row in kept_after_duplicates:
        matches = test_by_exact.get(row["exact_text_key"], [])
        if matches:
            for test_row in matches:
                human_test_overlap_rows.append(
                    {
                        "exact_text_key": row["exact_text_key"],
                        "development_origin": row["source_split"],
                        "development_row_index": row["original_row_index"],
                        "test_id": test_row["test_id"],
                        "test_row_index": test_row["original_row_index"],
                        "task": row["task"],
                        "development_label": row["label"],
                        "development_p_hallucination": row["p_hallucination"],
                        "development_labels": row["labels"],
                        "test_label": test_row["label"],
                        "test_p_hallucination": test_row["p_hallucination"],
                        "test_labels": test_row["labels"],
                        "binary_labels_agree": row["label_bin"] == test_row["label_bin"],
                        "p_hallucination_values_agree": row["p_hallucination"]
                        == test_row["p_hallucination"],
                        "individual_annotation_lists_agree": row["labels"] == test_row["labels"],
                    }
                )
        else:
            final_human_rows.append(row)

    write_csv(
        EXCLUDED_HUMAN_TEST_OVERLAPS_PATH,
        human_test_overlap_rows,
        [
            "exact_text_key",
            "development_origin",
            "development_row_index",
            "test_id",
            "test_row_index",
            "task",
            "development_label",
            "development_p_hallucination",
            "development_labels",
            "test_label",
            "test_p_hallucination",
            "test_labels",
            "binary_labels_agree",
            "p_hallucination_values_agree",
            "individual_annotation_lists_agree",
        ],
    )

    final_human_rows = sorted(
        final_human_rows,
        key=lambda row: (row["source_split"], int(row["original_row_index"]), row["exact_text_key"]),
    )
    canonical_rows: list[dict[str, Any]] = []
    for index, row in enumerate(final_human_rows, start=1):
        canonical_id = f"HDEV_{index:04d}_{row['exact_text_key'][:12]}"
        canonical_rows.append({"canonical_id": canonical_id, **row})

    canonical_fields = [
        "canonical_id",
        "source_split",
        "original_row_index",
        "task",
        "src",
        "tgt",
        "hyp",
        "label",
        "label_bin",
        "p_hallucination",
        "labels",
        "model",
        "ref",
        "exact_text_key",
        "source_pair_key",
        "task_reference_key",
    ]
    write_csv(CANONICAL_HUMAN_MANIFEST_PATH, canonical_rows, canonical_fields)

    human_source_pairs = {row["source_pair_key"] for row in canonical_rows}
    human_task_refs = {row["task_reference_key"] for row in canonical_rows}
    test_source_pairs = {row["source_pair_key"] for row in test_rows}
    test_task_refs = {row["task_reference_key"] for row in test_rows}

    synthetic_rows: list[dict[str, Any]] = []
    excluded_synthetic_rows: list[dict[str, Any]] = []
    for index, syn_row in synthetic.iterrows():
        sample_id = int(syn_row["sample_id"])
        original = train_rows[sample_id]
        task = normalize_value(syn_row.get("task"))
        src = normalize_value(syn_row.get("src"))
        tgt = normalize_value(syn_row.get("tgt"))
        hyp = normalize_value(syn_row.get("hyp"))
        task_reference_text = src if task == "PG" else tgt
        source_pair_key = hash_parts(task, src, tgt)
        task_reference_key = hash_parts(task, task_reference_text)
        synthetic_exact_key = hash_parts(task, src, tgt, hyp)
        original_task = normalize_value(original.get("task"))
        original_src = normalize_value(original.get("src"))
        original_tgt = normalize_value(original.get("tgt"))
        original_hyp = normalize_value(original.get("hyp"))
        original_task_reference_text = original_src if original_task == "PG" else original_tgt
        original_task_reference_key = hash_parts(original_task, original_task_reference_text)
        row = {
            "synthetic_id": f"SYN_{index + 1:04d}_{synthetic_exact_key[:12]}",
            "source_csv_row_index": index,
            "sample_id": sample_id,
            "task": task,
            "src": src,
            "tgt": tgt,
            "hyp": hyp,
            "label": normalize_value(syn_row.get("label")),
            "label_bin": binary_label(syn_row.get("label")),
            "p_hallucination": normalize_value(syn_row.get("p_hallucination")),
            "source_type": normalize_value(syn_row.get("source_type")),
            "generation_mode": normalize_value(syn_row.get("generation_mode")),
            "reference_text": normalize_value(syn_row.get("reference_text")),
            "original_task": original_task,
            "original_src": original_src,
            "original_tgt": original_tgt,
            "original_hyp": original_hyp,
            "exact_text_key": synthetic_exact_key,
            "source_pair_key": source_pair_key,
            "task_reference_key": task_reference_key,
            "original_task_reference_key": original_task_reference_key,
            "sample_id_task_matches_train": task == original_task,
            "sample_id_src_matches_train": src == original_src,
            "sample_id_tgt_matches_train": tgt == original_tgt,
            "sample_id_original_hyp_matches_train": normalize_value(syn_row.get("original_hyp"))
            == original_hyp,
        }
        reasons = []
        if source_pair_key in human_source_pairs:
            reasons.append("source_pair_in_canonical_human_development")
        if task_reference_key in human_task_refs:
            reasons.append("task_reference_in_canonical_human_development")
        if source_pair_key in test_source_pairs:
            reasons.append("source_pair_in_official_test")
        if task_reference_key in test_task_refs:
            reasons.append("task_reference_in_official_test")
        if reasons:
            excluded_synthetic_rows.append(row | {"exclusion_reason": ";".join(reasons)})
        else:
            synthetic_rows.append(row)

    synthetic_fields = [
        "synthetic_id",
        "source_csv_row_index",
        "sample_id",
        "task",
        "src",
        "tgt",
        "hyp",
        "label",
        "label_bin",
        "p_hallucination",
        "source_type",
        "generation_mode",
        "reference_text",
        "original_task",
        "original_src",
        "original_tgt",
        "original_hyp",
        "exact_text_key",
        "source_pair_key",
        "task_reference_key",
        "original_task_reference_key",
        "sample_id_task_matches_train",
        "sample_id_src_matches_train",
        "sample_id_tgt_matches_train",
        "sample_id_original_hyp_matches_train",
    ]
    write_csv(CANONICAL_SYNTHETIC_MANIFEST_PATH, synthetic_rows, synthetic_fields)
    write_csv(EXCLUDED_SYNTHETIC_PATH, excluded_synthetic_rows, synthetic_fields + ["exclusion_reason"])

    stratum = [f"{row['task']}__{row['label_bin']}" for row in canonical_rows]
    stratum_counts = Counter(stratum)
    too_small = {key: count for key, count in stratum_counts.items() if count < 5}
    if too_small:
        raise RuntimeError(
            "Cannot create 5-fold StratifiedKFold. Strata below 5 samples: "
            + json.dumps(too_small, ensure_ascii=False, sort_keys=True)
        )

    fold_assignment = deterministic_stratified_folds(stratum, n_splits=5, random_state=42)
    fold_rows: list[dict[str, Any]] = []
    for idx, fold_id in enumerate(fold_assignment):
        row = canonical_rows[idx]
        fold_rows.append(
            {
                "canonical_id": row["canonical_id"],
                "fold_id": fold_id,
                "stratum": f"{row['task']}__{row['label_bin']}",
                "task": row["task"],
                "label_bin": row["label_bin"],
                "exact_text_key": row["exact_text_key"],
            }
        )

    fold_rows = sorted(fold_rows, key=lambda row: row["canonical_id"])
    fold_ids_by_sample = Counter(row["canonical_id"] for row in fold_rows)
    exact_key_fold_sets: dict[str, set[int]] = defaultdict(set)
    for row in fold_rows:
        exact_key_fold_sets[row["exact_text_key"]].add(int(row["fold_id"]))
    if any(count != 1 for count in fold_ids_by_sample.values()):
        raise RuntimeError("At least one canonical_id is not assigned exactly once.")
    if any(len(folds) > 1 for folds in exact_key_fold_sets.values()):
        raise RuntimeError("At least one exact_text_key appears in more than one fold.")

    write_csv(
        FOLD_ASSIGNMENTS_PATH,
        fold_rows,
        ["canonical_id", "fold_id", "stratum", "task", "label_bin", "exact_text_key"],
    )

    print("Prompt 7C canonical data preparation complete.")
    print(f"duplicate_groups_total={len(duplicate_group_summary)}")
    print(
        "trial_development_duplicate_groups="
        f"{sum(1 for row in duplicate_group_summary if row['sources'] == 'development_model_agnostic;trial')}"
    )
    print(
        "internal_development_duplicate_groups="
        f"{sum(1 for row in duplicate_group_summary if row['sources'] == 'development_model_agnostic')}"
    )
    print(f"excluded_human_test_overlaps={len(human_test_overlap_rows)}")
    print(f"canonical_human_samples={len(canonical_rows)}")
    print(f"canonical_synthetic_diagnostic_samples={len(synthetic_rows)}")
    print(f"excluded_synthetic_rows={len(excluded_synthetic_rows)}")
    print("stratum_counts=" + json.dumps(dict(sorted(stratum_counts.items())), ensure_ascii=False))
    print("fold_counts=" + json.dumps(dict(sorted(Counter(row['fold_id'] for row in fold_rows).items()))))


if __name__ == "__main__":
    main()
