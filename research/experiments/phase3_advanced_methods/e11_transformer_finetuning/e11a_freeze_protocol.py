"""One-time, local-only E11-A protocol freeze. Refuses to overwrite either file."""

from __future__ import annotations

import csv
import hashlib
import json
import math
from collections import Counter
from pathlib import Path

from scoring_common import HERE, ROOT, require, sha_file

MODEL_ID = "MoritzLaurer/DeBERTa-v3-large-mnli-fever-anli-ling-wanli"
REVISION = "b3546ea6b0346eb6f8d5d68b13c7dc6d0376b3d7"
CANONICAL_REL = "codex/canonical_human_development_manifest.csv"
FOLDS_REL = "codex/canonical_fold_assignments.csv"
CANONICAL_SHA = "754b66c6c4eca2e92902d0408db4854e922d7dfb396953a0cc043c5477bd6a9b"
FOLDS_SHA = "f5a5964923806a23dd34a8bcc137f3cf489437e033d645e9d0845bf40792eb5d"


def rows(path: Path) -> list[dict]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def build() -> dict:
    require(ROOT is not None, "local checkout required")
    canonical_path, folds_path = ROOT / CANONICAL_REL, ROOT / FOLDS_REL
    require(sha_file(canonical_path) == CANONICAL_SHA and
            sha_file(folds_path) == FOLDS_SHA, "canonical source hash drift")
    human, fold_rows = rows(canonical_path), rows(folds_path)
    by_id = {r["canonical_id"]: r for r in human}
    fold_of = {r["canonical_id"]: int(r["fold_id"]) for r in fold_rows}
    require(len(human) == len(by_id) == len(fold_rows) == len(fold_of) == 561 and
            set(by_id) == set(fold_of), "canonical/fold ID coverage")
    require(Counter(r["task"] for r in human) == {"DM": 211, "MT": 216, "PG": 134} and
            Counter(r["label_bin"] for r in human) == {"0": 307, "1": 254} and
            {(r["label"], r["label_bin"]) for r in human} ==
            {("Not Hallucination", "0"), ("Hallucination", "1")},
            "canonical task/label mapping")
    require([Counter(fold_of.values())[i] for i in range(1, 6)] ==
            [113, 112, 112, 112, 112], "locked fold sizes")
    scoring = json.loads((HERE / "E11_SCORING_MANIFEST.json").read_text(encoding="utf-8"))
    mirror = scoring["local_model_mirrors"]["nli"]
    require(scoring["detectors"]["nli"]["model_id"] == MODEL_ID and
            scoring["detectors"]["nli"]["revision"] == REVISION and
            mirror["path"] == "RAG/results/rag_e6_v2/model/model.safetensors",
            "pre-existing model pin")
    model_dir = ROOT / Path(mirror["path"]).parent
    require(all(sha_file(model_dir / name) == digest
                for name, digest in mirror["assets_sha256"].items()),
            "local model mirror hash drift")
    require(sha_file(HERE / "E11A_REQUIREMENTS.lock.txt") ==
            "28d6e3c646b425f1c8c1795b04337e1bb94f22a5fb9e49ae3aaf64d116fb40a5",
            "training dependency lock drift")
    fold_info = []
    for fold_id in range(1, 6):
        training = [r for r in human if fold_of[r["canonical_id"]] != fold_id]
        heldout = [r for r in human if fold_of[r["canonical_id"]] == fold_id]
        counts = Counter(int(r["label_bin"]) for r in training)
        n = len(training)
        require(set(counts) == {0, 1} and n + len(heldout) == 561,
                "training class coverage")
        fold_info.append({
            "fold_id": fold_id, "train_rows": n, "heldout_rows": len(heldout),
            "train_class_counts": {"0": counts[0], "1": counts[1]},
            "class_weights": {"0": n / (2 * counts[0]),
                              "1": n / (2 * counts[1])},
        })
    return {
        "schema_version": 1,
        "status": "FROZEN_BEFORE_E11A_TRAINING",
        "experiment_id": "E11-A",
        "definition": "Human-only task-specific DeBERTa-v3-large binary SHROOM hallucination classification",
        "separate_from": {"E11-B": "Frozen detector-teacher experiment with zero retained pseudo-labels"},
        "data": {
            "canonical_path": CANONICAL_REL, "canonical_sha256": CANONICAL_SHA,
            "rows": 561, "unique_ids": 561,
            "task_counts": {"DM": 211, "MT": 216, "PG": 134},
            "label_column": "label_bin",
            "label_mapping": {"0": "Not Hallucination", "1": "Hallucination"},
            "folds_path": FOLDS_REL, "folds_sha256": FOLDS_SHA,
            "fold_ids": [1, 2, 3, 4, 5],
            "folds": fold_info,
            "training_rule": "For fold k train on all canonical rows with locked fold_id != k; validate only on fold_id == k. No text purge or extra rows.",
        },
        "reference_policy": {"DM": "tgt", "MT": "tgt", "PG": "src"},
        "input": {
            "type": "tokenizer_text_pair",
            "sequence_a_template": "TASK: {task}\nREFERENCE:\n{reference}",
            "sequence_b_template": "HYPOTHESIS:\n{hyp}",
            "reference_field_by_task": {"DM": "tgt", "MT": "tgt", "PG": "src"},
            "claim": "Unchanged complete original hyp field",
            "tokenization": {"add_special_tokens": True, "truncation": "longest_first",
                             "max_length": 512, "batch_padding": "longest_in_batch"},
            "forbidden_text_fields": ["label", "label_bin", "p_hallucination", "model",
                                      "detector_scores", "RF_predictions", "external_definitions"],
        },
        "model": {
            "id": MODEL_ID, "revision": REVISION,
            "local_mirror_dir": "RAG/results/rag_e6_v2/model",
            "local_assets_sha256": mirror["assets_sha256"],
            "loading": "local_files_only=True; safetensors; reuse pinned pretrained encoder; replace mismatched 3-way NLI classifier head with a seeded 2-way head",
            "num_labels": 2,
            "id2label": {"0": "not_hallucination", "1": "hallucination"},
            "label2id": {"not_hallucination": 0, "hallucination": 1},
            "quantization": None,
        },
        "training": {
            "optimizer": "torch.optim.AdamW", "learning_rate": 1e-5,
            "weight_decay": 0.01, "epochs": 5,
            "train_batch_size": 8, "evaluation_batch_size": 16,
            "gradient_accumulation_steps": 2, "effective_train_batch_size": 16,
            "warmup_ratio": 0.1,
            "warmup_steps_rule": "ceil(0.1 * total_optimizer_steps)",
            "lr_schedule": "linear warmup then linear decay to zero by final optimizer step",
            "gradient_clip_max_norm": 1.0,
            "random_seed": 42, "precision": "BF16 autocast on one A100-80GB",
            "loss": "weighted torch.nn.CrossEntropyLoss",
            "class_weight_formula": "weight_c = N_train / (2 * N_class_c), using only fold training labels",
            "class_weight_values_by_fold": {str(f["fold_id"]): f["class_weights"]
                                            for f in fold_info},
            "oversampling": False, "early_stopping": False,
            "checkpoint_selection": "final model after exactly five epochs; no held-out-based selection",
        },
        "output": {
            "hallucination_class_id": 1,
            "probability": "softmax(logits)[class_id=1] using explicit id2label/label2id assertion",
            "classification_threshold": 0.5,
            "prediction_rule": "predicted_class=1 if p(H)>=0.5 else 0",
            "oof_fields": ["sample_id", "fold_id", "task", "gold_label",
                           "predicted_class", "p_H"],
            "oof_rule": "Five independent final checkpoints, one per locked fold; predict held-out fold only; concatenate to 561 unique IDs after all five runs.",
        },
        "smoke": {
            "fold_id": 1,
            "selection": "First 16 fold-1 training examples of each class in canonical order (32 total)",
            "optimizer_steps": 2, "epochs": 1, "no_heldout_predictions": True,
            "checks": ["exact local model loads", "tokenization", "BF16 support",
                       "finite loss", "backward", "peak CUDA memory",
                       "final checkpoint and status writing"],
            "is_e11a_score": False,
        },
        "modal": {
            "gpu": "A100-80GB", "gpu_count": 1,
            "memory_mib": 65536, "ephemeral_disk_mib": 524288,
            "smoke_timeout_seconds": 1800,
            "volume": "shroom-e11a-training-results", "volume_mount": "/results",
            "runtime_root": "/opt/e11a", "model_root": "/opt/e11a/model",
            "output_root": "/results/e11a",
        },
        "software": {"python": "3.11", "requirements_lock":
                     "RAG/results/phase3_e11_task_adaptation/E11A_REQUIREMENTS.lock.txt",
                     "requirements_sha256": sha_file(HERE / "E11A_REQUIREMENTS.lock.txt")},
        "prohibitions": ["official_test_access", "pseudo_label_training_rows",
                         "unlabeled_training_rows", "detector_score_features",
                         "external_definitions", "heldout_label_training",
                         "OOF_hyperparameter_tuning", "heldout_checkpoint_selection"],
    }


def main() -> None:
    target = HERE / "E11A_TRAINING_PROTOCOL.json"
    markdown = HERE / "E11A_TRAINING_PROTOCOL.md"
    require(not target.exists() and not markdown.exists(), "E11-A protocol already frozen")
    value = build()
    encoded = json.dumps(value, ensure_ascii=False, sort_keys=True,
                         separators=(",", ":"), allow_nan=False).encode("utf-8")
    digest = hashlib.sha256(encoded).hexdigest()
    value["protocol_sha256"] = digest
    target.write_text(json.dumps(value, ensure_ascii=False, indent=2,
                                 allow_nan=False) + "\n", encoding="utf-8")
    lines = ["# E11-A frozen training protocol", "",
             f"Protocol content SHA256: `{digest}`. Frozen before any E11-A training or OOF result.",
             "", "E11-A tests direct, human-only adaptation of the pinned MoritzLaurer DeBERTa-v3-large encoder to the binary SHROOM label. It is separate from the frozen zero-yield E11-B detector-teacher experiment.",
             "", f"Canonical input: `{CANONICAL_REL}` (SHA256 `{CANONICAL_SHA}`), 561 unique samples: DM 211, MT 216, PG 134. Locked folds: `" + FOLDS_REL + f"` (SHA256 `{FOLDS_SHA}`), IDs 1–5, sizes 113/112/112/112/112. Labels: 0=Not Hallucination, 1=Hallucination.",
             "", "Exact tokenizer pair: sequence A is `TASK: {task}\\nREFERENCE:\\n{reference}`; sequence B is `HYPOTHESIS:\\n{hyp}`. The backslash-n markers here denote literal newline characters. Reference is `tgt` for DM/MT and `src` for PG. The complete original hypothesis is used. Tokenization adds standard model special tokens, truncates longest-first to 512, and pads dynamically per batch.",
             "", f"Base: `{MODEL_ID}@{REVISION}` from the hash-verified local safetensors mirror. The 3-way NLI classifier head is replaced by a seeded two-class head; output class 1 is hallucination.",
             "", "Training: AdamW; learning rate 1e-5; weight decay 0.01; five fixed epochs; microbatch 8; gradient accumulation 2 (effective batch 16); evaluation batch 16; warmup ratio 0.1 with ceil rounding; linear decay; max gradient norm 1.0; seed 42; BF16 autocast on A100; no quantization, oversampling, early stopping or sweep. Save the final epoch checkpoint only.",
             "", "Loss is weighted cross-entropy. For each fold, `weight_c = N_train / (2 * N_class_c)` using only its training labels. No held-out label contributes to model fitting, weighting, scheduling or checkpoint selection.",
             "", "| Held-out fold | Train rows | Train class 0 | Train class 1 | Held-out rows | Weight 0 | Weight 1 |",
             "| ---: | ---: | ---: | ---: | ---: | ---: | ---: |"]
    for f in value["data"]["folds"]:
        lines.append(f"| {f['fold_id']} | {f['train_rows']} | {f['train_class_counts']['0']} | {f['train_class_counts']['1']} | {f['heldout_rows']} | {f['class_weights']['0']:.9f} | {f['class_weights']['1']:.9f} |")
    lines += ["", "For each fold, train on all other canonical folds, then predict the held-out fold with the final checkpoint. `p(H)` is softmax class 1 and the fixed classification threshold is 0.50 (`>=` predicts 1). The eventual OOF union must have 561 unique IDs. No held-out-based checkpoint choice or hyperparameter selection is permitted.",
              "", "The separate A100 smoke uses 32 fold-1 training rows, two optimizer steps and one checkpoint write. It produces no held-out predictions or E11-A score. It must pass before any full fold run is allowed. This preparation does not launch that smoke.",
              "", "Official test, unlabeled/pseudo-labeled rows, detector scores, RF outputs, MPNet, BERTScore, claim decomposition and external definitions are prohibited. E11-B remains unchanged.", ""]
    markdown.write_text("\n".join(lines), encoding="utf-8")
    print(json.dumps({"status": "FROZEN", "protocol_sha256": digest,
                      "json": str(target), "markdown": str(markdown)}, indent=2))


if __name__ == "__main__":
    main()
