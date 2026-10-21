"""Descriptive EDA for the SHROOM development splits.

This script is intentionally non-destructive. It reads the two labeled development
JSON files, reproduces the inspection logic used by the project notebook, and writes
only descriptive tables and figures to ``prompt6_development_eda_outputs``.
It does not train a model, select features, tune thresholds, or read test labels.
"""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from transformers import AutoTokenizer


HERE = Path(__file__).resolve().parent
PROJECT_ROOT = HERE.parent
DEV_DIR = PROJECT_ROOT / "Dev" / "SHROOM_dev-v2"
OUTPUT_DIR = HERE / "prompt6_development_eda_outputs"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

INPUTS = {
    "model-agnostic": DEV_DIR / "val.model-agnostic.json",
    "model-aware": DEV_DIR / "val.model-aware.v2.json",
}
EXPECTED_ROWS = {"model-agnostic": 499, "model-aware": 501}
TOKENIZER_NAME = "microsoft/deberta-v3-large"
LABEL_ORDER = ["Not Hallucination", "Hallucination"]
TASK_ORDER = ["DM", "MT", "PG"]
TRACK_ORDER = ["model-agnostic", "model-aware"]
COLORS = ["#4C78A8", "#F58518"]


def load_split(track: str, path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(path)
    with path.open("r", encoding="utf-8") as handle:
        rows = json.load(handle)
    frame = pd.DataFrame(rows)
    if len(frame) != EXPECTED_ROWS[track]:
        raise ValueError(
            f"Unexpected row count for {track}: {len(frame)} != {EXPECTED_ROWS[track]}"
        )
    frame.insert(0, "track", track)
    return frame


def save_figure(fig: plt.Figure, filename: str) -> None:
    fig.tight_layout()
    fig.savefig(OUTPUT_DIR / filename, dpi=300, bbox_inches="tight")
    plt.close(fig)


def inspection_table(frames: dict[str, pd.DataFrame]) -> pd.DataFrame:
    records = []
    for track, frame in frames.items():
        comparable = frame.drop(columns="track").copy()
        for column in comparable.columns:
            if comparable[column].map(lambda value: isinstance(value, (list, dict))).any():
                comparable[column] = comparable[column].map(
                    lambda value: json.dumps(value, ensure_ascii=False, sort_keys=True)
                    if isinstance(value, (list, dict))
                    else value
                )
        records.append(
            {
                "split": "development",
                "track": track,
                "rows": len(frame),
                "columns": len(frame.columns) - 1,
                "missing_cells": int(frame.drop(columns="track").isna().sum().sum()),
                "duplicate_rows": int(comparable.duplicated().sum()),
            }
        )
    return pd.DataFrame(records)


def token_count(tokenizer, text: object) -> int:
    value = "" if pd.isna(text) else str(text)
    return len(tokenizer.encode(value, add_special_tokens=True))


def add_token_lengths(frame: pd.DataFrame, tokenizer) -> pd.DataFrame:
    result = frame.copy()
    for column in ("src", "hyp", "tgt"):
        result[f"{column}_tokens"] = result[column].map(
            lambda value: token_count(tokenizer, value)
        )
    result["src_hyp_tokens"] = [
        len(tokenizer.encode(str(src), str(hyp), add_special_tokens=True))
        for src, hyp in zip(result["src"], result["hyp"])
    ]
    result["tgt_hyp_tokens"] = [
        len(tokenizer.encode(str(tgt), str(hyp), add_special_tokens=True))
        for tgt, hyp in zip(result["tgt"], result["hyp"])
    ]
    return result


def write_tables(data: pd.DataFrame, frames: dict[str, pd.DataFrame]) -> None:
    inspection_table(frames).to_csv(
        OUTPUT_DIR / "development_inspection_summary.csv", index=False
    )

    schema_rows = []
    for track, frame in frames.items():
        for column in frame.drop(columns="track").columns:
            schema_rows.append(
                {
                    "split": "development",
                    "track": track,
                    "column": column,
                    "dtype": str(frame[column].dtype),
                    "missing": int(frame[column].isna().sum()),
                }
            )
    pd.DataFrame(schema_rows).to_csv(
        OUTPUT_DIR / "development_schema_and_missing.csv", index=False
    )

    label_counts = (
        data.groupby(["track", "label"], observed=False)
        .size()
        .rename("count")
        .reset_index()
    )
    label_counts["percentage"] = label_counts.groupby("track")["count"].transform(
        lambda values: 100 * values / values.sum()
    )
    label_counts.to_csv(
        OUTPUT_DIR / "development_label_distribution.csv", index=False
    )

    task_counts = (
        data.groupby(["track", "task"], observed=False)
        .size()
        .rename("count")
        .reset_index()
    )
    task_counts["percentage"] = task_counts.groupby("track")["count"].transform(
        lambda values: 100 * values / values.sum()
    )
    task_counts.to_csv(
        OUTPUT_DIR / "development_task_distribution.csv", index=False
    )

    bins = [-1e-9, 0.2, 0.4, 0.6, 0.8, 1.0 + 1e-9]
    labels = ["0.0–0.2", "0.2–0.4", "0.4–0.6", "0.6–0.8", "0.8–1.0"]
    binned = data.assign(
        p_bin=pd.cut(
            data["p(Hallucination)"], bins=bins, labels=labels, include_lowest=True
        )
    )
    p_bins = (
        binned.groupby(["track", "p_bin"], observed=False)
        .size()
        .rename("count")
        .reset_index()
    )
    p_bins["percentage"] = p_bins.groupby("track")["count"].transform(
        lambda values: 100 * values / values.sum()
    )
    p_bins.to_csv(
        OUTPUT_DIR / "development_p_hallucination_bins.csv", index=False
    )

    token_columns = [
        "src_tokens",
        "hyp_tokens",
        "tgt_tokens",
        "src_hyp_tokens",
        "tgt_hyp_tokens",
    ]
    token_summary = (
        data.groupby("track")[token_columns]
        .agg(["count", "mean", "std", "min", "median", "max"])
        .round(3)
    )
    token_summary.columns = ["_".join(column) for column in token_summary.columns]
    token_summary.reset_index().to_csv(
        OUTPUT_DIR / "development_token_length_summary.csv", index=False
    )

    label_task = (
        data.groupby(["track", "task", "label"], observed=False)
        .size()
        .rename("count")
        .reset_index()
    )
    label_task["within_task_percentage"] = label_task.groupby(
        ["track", "task"]
    )["count"].transform(lambda values: 100 * values / values.sum())
    label_task.to_csv(
        OUTPUT_DIR / "development_label_by_task_and_track.csv", index=False
    )

    p_task = (
        data.groupby(["track", "task"], observed=False)["p(Hallucination)"]
        .agg(["count", "mean", "median", "std", "min", "max"])
        .round(4)
        .reset_index()
    )
    p_task.to_csv(
        OUTPUT_DIR / "development_p_hallucination_by_task_and_track.csv",
        index=False,
    )

    pair_summary = (
        data.groupby(["track", "task", "label"], observed=False)[
            ["src_hyp_tokens", "tgt_hyp_tokens"]
        ]
        .agg(["count", "mean", "median", "std", "min", "max"])
        .round(3)
    )
    pair_summary.columns = ["_".join(column) for column in pair_summary.columns]
    pair_summary.reset_index().to_csv(
        OUTPUT_DIR / "development_pair_token_lengths_by_task_and_label.csv",
        index=False,
    )


def plot_distributions(data: pd.DataFrame) -> None:
    fig, axes = plt.subplots(1, 2, figsize=(10, 4), sharey=False)
    for axis, track in zip(axes, TRACK_ORDER):
        counts = data.loc[data.track == track, "label"].value_counts().reindex(LABEL_ORDER)
        bars = axis.bar(LABEL_ORDER, counts.values, color=COLORS)
        axis.bar_label(bars, padding=3)
        axis.set_title(track)
        axis.set_ylabel("Πλήθος δειγμάτων")
        axis.tick_params(axis="x", rotation=12)
    fig.suptitle("Development: κατανομή τελικής ετικέτας ανά track")
    save_figure(fig, "development_label_distribution_by_track.png")

    fig, axes = plt.subplots(1, 2, figsize=(10, 4), sharey=False)
    for axis, track in zip(axes, TRACK_ORDER):
        counts = data.loc[data.track == track, "task"].value_counts().reindex(TASK_ORDER)
        bars = axis.bar(TASK_ORDER, counts.values, color="#4C78A8")
        axis.bar_label(bars, padding=3)
        axis.set_title(track)
        axis.set_xlabel("Task")
        axis.set_ylabel("Πλήθος δειγμάτων")
    fig.suptitle("Development: κατανομή tasks ανά track")
    save_figure(fig, "development_task_distribution_by_track.png")

    fig, axes = plt.subplots(1, 2, figsize=(10, 4), sharey=True)
    for axis, track in zip(axes, TRACK_ORDER):
        values = data.loc[data.track == track, "p(Hallucination)"]
        axis.hist(values, bins=np.linspace(0, 1, 6), color="#4C78A8", edgecolor="black")
        axis.set_title(track)
        axis.set_xlabel("p(Hallucination)")
        axis.set_ylabel("Πλήθος δειγμάτων")
        axis.set_xlim(0, 1)
    fig.suptitle("Development: κατανομή p(Hallucination) ανά track")
    save_figure(fig, "development_p_hallucination_distribution_by_track.png")


def plot_token_lengths(data: pd.DataFrame) -> None:
    columns = [
        "src_tokens",
        "hyp_tokens",
        "tgt_tokens",
        "src_hyp_tokens",
        "tgt_hyp_tokens",
    ]
    labels = ["source", "hypothesis", "target", "source+hyp.", "target+hyp."]
    fig, axes = plt.subplots(2, 1, figsize=(9, 7), sharex=True)
    for axis, track in zip(axes, TRACK_ORDER):
        subset = data.loc[data.track == track, columns]
        axis.boxplot([subset[column].values for column in columns], showfliers=True)
        axis.set_title(track)
        axis.set_ylabel("Tokens")
        axis.set_xticks(range(1, len(labels) + 1), labels=labels, rotation=12)
    fig.suptitle(
        f"Development: μήκη ακολουθιών με tokenizer {TOKENIZER_NAME}"
    )
    save_figure(fig, "development_token_length_boxplots_by_track.png")


def plot_multivariate(data: pd.DataFrame) -> None:
    fig, axes = plt.subplots(1, 2, figsize=(11, 4), sharey=False)
    for axis, track in zip(axes, TRACK_ORDER):
        subset = data[data.track == track]
        pivot = (
            subset.groupby(["task", "label"], observed=False)
            .size()
            .unstack(fill_value=0)
            .reindex(index=TASK_ORDER, columns=LABEL_ORDER, fill_value=0)
        )
        pivot.plot(kind="bar", stacked=True, ax=axis, color=COLORS)
        axis.set_title(track)
        axis.set_xlabel("Task")
        axis.set_ylabel("Πλήθος δειγμάτων")
        axis.tick_params(axis="x", rotation=0)
        axis.legend(title="Label", fontsize=8)
    fig.suptitle("Development: ετικέτα ως προς task και track")
    save_figure(fig, "development_label_by_task_and_track.png")

    fig, axes = plt.subplots(1, 2, figsize=(11, 4), sharey=True)
    for axis, track in zip(axes, TRACK_ORDER):
        subset = data[data.track == track]
        values = [
            subset.loc[subset.task == task, "p(Hallucination)"].values
            for task in TASK_ORDER
        ]
        axis.boxplot(values, tick_labels=TASK_ORDER, showfliers=True)
        axis.set_title(track)
        axis.set_xlabel("Task")
        axis.set_ylabel("p(Hallucination)")
        axis.set_ylim(-0.05, 1.05)
    fig.suptitle("Development: p(Hallucination) ως προς task και track")
    save_figure(fig, "development_p_hallucination_by_task_and_track.png")


def main() -> None:
    frames = {track: load_split(track, path) for track, path in INPUTS.items()}
    tokenizer = AutoTokenizer.from_pretrained(TOKENIZER_NAME, local_files_only=True)
    enriched = [add_token_lengths(frame, tokenizer) for frame in frames.values()]
    data = pd.concat(enriched, ignore_index=True)
    data["track"] = pd.Categorical(data["track"], TRACK_ORDER, ordered=True)
    data["task"] = pd.Categorical(data["task"], TASK_ORDER, ordered=True)
    data["label"] = pd.Categorical(data["label"], LABEL_ORDER, ordered=True)

    write_tables(data, frames)
    plot_distributions(data)
    plot_token_lengths(data)
    plot_multivariate(data)

    metadata = pd.DataFrame(
        [
            {"key": "tokenizer", "value": TOKENIZER_NAME},
            {"key": "model_agnostic_rows", "value": len(frames["model-agnostic"])},
            {"key": "model_aware_rows", "value": len(frames["model-aware"])},
            {"key": "figure_dpi", "value": 300},
            {"key": "scope", "value": "descriptive development EDA only"},
        ]
    )
    metadata.to_csv(OUTPUT_DIR / "development_eda_metadata.csv", index=False)
    print(f"Wrote development EDA outputs to {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
