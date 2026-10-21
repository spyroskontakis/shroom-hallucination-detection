"""Explicit-opt-in E11-A A100 smoke or one frozen human-only fold run.

Importing this module performs no training, model load, or GPU allocation.
"""

from __future__ import annotations

import argparse
import json
import math
import os
import random
import re
import sys
import time
from collections import Counter
from pathlib import Path

from e11a_prepare_data import load_protocol
from validate_e11a_protocol import read_jsonl, validate_bundle
from scoring_common import require, sha_file


def select_smoke_rows(training: list[dict]) -> list[dict]:
    chosen = []
    for class_id in (0, 1):
        selected = [r for r in training if r["label"] == class_id][:16]
        require(len(selected) == 16, "smoke requires 16 training rows per class")
        chosen.extend(selected)
    require(len(chosen) == len({r["sample_id"] for r in chosen}) == 32,
            "smoke selection")
    return chosen


def linear_lr(base_lr: float, step: int, total: int, warmup: int) -> float:
    require(1 <= step <= total and 1 <= warmup < total, "learning-rate steps")
    factor = (step / warmup if step <= warmup else
              max(0.0, (total - step) / (total - warmup)))
    return base_lr * factor


def execute(fold_id: int, mode: str, bundle: Path, model_dir: Path,
            output_root: Path, run_id: str, allow_full_fold: bool) -> dict:
    require(fold_id in range(1, 6), "explicit locked fold ID 1..5 required")
    require(mode in ("smoke", "fold"), "mode must be smoke or fold")
    require(re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]{0,63}", run_id) is not None,
            "invalid run ID")
    require(mode != "fold" or allow_full_fold,
            "full fold requires explicit --allow-full-fold")
    require(mode != "smoke" or fold_id == 1, "frozen smoke uses fold 1 only")
    validate_bundle(bundle, model_dir)
    spec = load_protocol()
    prepared = json.loads((bundle / "E11A_PREPARATION_MANIFEST.json")
                          .read_text(encoding="utf-8"))
    fold = prepared["folds"][str(fold_id)]
    training = read_jsonl(bundle / fold["train_path"])
    require(all(r["fold_id"] != fold_id for r in training) and
            len(training) == fold["train_rows"] and
            len({r["sample_id"] for r in training}) == len(training),
            "held-out fold present in training")
    counts = Counter(r["label"] for r in training)
    frozen_fold = spec["data"]["folds"][fold_id - 1]
    require({str(k): v for k, v in counts.items()} ==
            frozen_fold["train_class_counts"], "training label counts")
    weights = [len(training) / (2 * counts[c]) for c in (0, 1)]
    require(all(math.isclose(weights[c], frozen_fold["class_weights"][str(c)],
                             rel_tol=0, abs_tol=1e-12) for c in (0, 1)),
            "class weights must use fold training labels only")
    selected = select_smoke_rows(training) if mode == "smoke" else training
    target = (output_root / "smoke" / run_id if mode == "smoke" else
              output_root / "folds" / f"fold_{fold_id}" / run_id)
    require(not target.exists(), "output run ID already used")
    target.mkdir(parents=True, exist_ok=False)

    # Import CUDA libraries only after every data, protocol, and split guard.
    os.environ["CUBLAS_WORKSPACE_CONFIG"] = ":4096:8"
    os.environ["HF_HUB_OFFLINE"] = "1"
    os.environ["TRANSFORMERS_OFFLINE"] = "1"
    import numpy as np
    import torch
    from torch.utils.data import DataLoader
    from transformers import AutoModelForSequenceClassification, AutoTokenizer

    require(torch.cuda.is_available() and torch.cuda.device_count() == 1,
            "one CUDA GPU required")
    gpu_name = torch.cuda.get_device_name(0)
    gpu_bytes = torch.cuda.get_device_properties(0).total_memory
    require("A100" in gpu_name and gpu_bytes >= 79_000_000_000 and
            torch.cuda.is_bf16_supported(),
            "A100 BF16 required; no precision fallback")
    seed = spec["training"]["random_seed"]
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)
    torch.backends.cudnn.deterministic = True
    torch.backends.cudnn.benchmark = False
    torch.cuda.reset_peak_memory_stats()
    device = torch.device("cuda:0")
    tokenizer = AutoTokenizer.from_pretrained(str(model_dir), local_files_only=True,
                                               trust_remote_code=False, use_fast=True)
    require(tokenizer.is_fast, "pinned fast tokenizer required")
    label2id = spec["model"]["label2id"]
    id2label = {int(k): v for k, v in spec["model"]["id2label"].items()}
    model = AutoModelForSequenceClassification.from_pretrained(
        str(model_dir), local_files_only=True, trust_remote_code=False,
        use_safetensors=True, num_labels=2, ignore_mismatched_sizes=True,
        torch_dtype=torch.float32, id2label=id2label, label2id=label2id)
    require(model.config.num_labels == 2 and model.config.label2id == label2id and
            model.config.id2label == id2label and
            model.config.label2id["hallucination"] == 1,
            "explicit binary class orientation")
    model.to(device)

    tokenization = spec["input"]["tokenization"]
    def encode(rows: list[dict]) -> list[dict]:
        return tokenizer([r["text"] for r in rows],
                         [r["text_pair"] for r in rows],
                         add_special_tokens=tokenization["add_special_tokens"],
                         truncation=tokenization["truncation"],
                         max_length=tokenization["max_length"], padding=False)

    # The frozen two-step smoke trains on its 32 class-balanced examples; this
    # separate label-free tokenizer check covers all three SHROOM tasks.
    representative = [next(r for r in training if r["task"] == task)
                      for task in ("DM", "MT", "PG")]
    representative_tokens = encode(representative)
    require(len(representative_tokens["input_ids"]) == 3 and
            all(1 <= len(ids) <= 512 for ids in representative_tokens["input_ids"]),
            "DM/MT/PG representative tokenization")
    encoded = encode(selected)
    require(len(encoded["input_ids"]) == len(selected) and
            all(1 <= len(ids) <= 512 for ids in encoded["input_ids"]),
            "smoke/fold tokenization")
    examples = [{name: encoded[name][i] for name in encoded.keys()}
                for i in range(len(selected))]
    for example, row in zip(examples, selected):
        example["labels"] = row["label"]
    def collate(batch: list[dict]) -> dict:
        labels = torch.tensor([r["labels"] for r in batch], dtype=torch.long)
        inputs = [{k: v for k, v in row.items() if k != "labels"} for row in batch]
        padded = tokenizer.pad(inputs, padding=True, return_tensors="pt")
        padded["labels"] = labels
        return padded

    generator = torch.Generator().manual_seed(seed)
    loader = DataLoader(examples, batch_size=spec["training"]["train_batch_size"],
                        shuffle=True, generator=generator, collate_fn=collate,
                        num_workers=0)
    epochs = spec["smoke"]["epochs"] if mode == "smoke" else spec["training"]["epochs"]
    accumulation = spec["training"]["gradient_accumulation_steps"]
    total_updates = epochs * math.ceil(len(loader) / accumulation)
    if mode == "smoke":
        require(total_updates == spec["smoke"]["optimizer_steps"] == 2,
                "smoke must be exactly two optimizer steps")
    warmup_updates = max(1, math.ceil(total_updates * spec["training"]["warmup_ratio"]))
    require(warmup_updates < total_updates, "warmup step range")
    optimizer = torch.optim.AdamW(model.parameters(),
                                  lr=spec["training"]["learning_rate"],
                                  weight_decay=spec["training"]["weight_decay"])
    criterion = torch.nn.CrossEntropyLoss(
        weight=torch.tensor(weights, dtype=torch.float32, device=device))
    optimizer.zero_grad(set_to_none=True)
    update = 0
    losses = []
    backward_passes = 0
    started = time.perf_counter()
    model.train()
    for _epoch in range(epochs):
        num_batches = len(loader)
        for batch_idx, batch in enumerate(loader):
            batch = {k: v.to(device) for k, v in batch.items()}
            group_start = (batch_idx // accumulation) * accumulation
            group_size = min(accumulation, num_batches - group_start)
            with torch.autocast(device_type="cuda", dtype=torch.bfloat16):
                logits = model(**{k: v for k, v in batch.items() if k != "labels"}).logits
                loss = criterion(logits.float(), batch["labels"])
            require(bool(torch.isfinite(loss).item()), "nonfinite training loss")
            (loss / group_size).backward()
            backward_passes += 1
            losses.append(float(loss.detach().cpu()))
            if (batch_idx + 1) % accumulation == 0 or batch_idx + 1 == num_batches:
                norm = torch.nn.utils.clip_grad_norm_(
                    model.parameters(), spec["training"]["gradient_clip_max_norm"])
                require(bool(torch.isfinite(norm).item()), "nonfinite gradient norm")
                update += 1
                lr = linear_lr(spec["training"]["learning_rate"], update,
                               total_updates, warmup_updates)
                for group in optimizer.param_groups:
                    group["lr"] = lr
                optimizer.step()
                optimizer.zero_grad(set_to_none=True)
    require(update == total_updates and backward_passes >= update and
            all(math.isfinite(x) for x in losses), "fixed training step count")

    checkpoint = target / "final_checkpoint"
    model.save_pretrained(str(checkpoint), safe_serialization=True)
    tokenizer.save_pretrained(str(checkpoint))
    require((checkpoint / "model.safetensors").is_file() and
            (checkpoint / "config.json").is_file(), "checkpoint writing")
    summary = {
        "status": "PASS", "mode": mode, "run_id": run_id, "fold_id": fold_id,
        "protocol_sha256": spec["protocol_sha256"],
        "base_model_id": spec["model"]["id"], "base_revision": spec["model"]["revision"],
        "gpu": gpu_name, "bf16_supported": True,
        "gpu_total_memory_bytes": gpu_bytes,
        "peak_gpu_memory_bytes": torch.cuda.max_memory_allocated(),
        "training_rows_used": len(selected), "fold_training_class_counts":
        {"0": counts[0], "1": counts[1]},
        "representative_tokenized_tasks": [r["task"] for r in representative],
        "class_weights": {"0": weights[0], "1": weights[1]},
        "optimizer_steps": update, "backward_passes": backward_passes,
        "first_loss": losses[0], "last_loss": losses[-1],
        "losses_all_finite": True, "checkpoint_sha256": sha_file(
            checkpoint / "model.safetensors"),
        "checkpoint_path": str(checkpoint),
        "elapsed_seconds": time.perf_counter() - started,
        "runtime": {"python": sys.version.split()[0], "torch": torch.__version__},
        "e11a_score_produced": False if mode == "smoke" else True,
    }
    if mode == "fold":
        heldout = read_jsonl(bundle / fold["heldout_path"])
        train_ids = {r["sample_id"] for r in training}
        require(all(r["fold_id"] == fold_id and r["sample_id"] not in train_ids
                    for r in heldout) and len(heldout) == fold["heldout_rows"],
                "held-out evaluation leakage")
        model.eval()
        class_id = model.config.label2id["hallucination"]
        predictions = []
        with torch.inference_mode():
            for start in range(0, len(heldout), spec["training"]["evaluation_batch_size"]):
                rows = heldout[start:start + spec["training"]["evaluation_batch_size"]]
                tokens = tokenizer([r["text"] for r in rows],
                                   [r["text_pair"] for r in rows],
                                   add_special_tokens=True, truncation="longest_first",
                                   max_length=512, padding=True, return_tensors="pt")
                with torch.autocast(device_type="cuda", dtype=torch.bfloat16):
                    logits = model(**{k: v.to(device) for k, v in tokens.items()}).logits
                probabilities = torch.softmax(logits.float(), dim=-1)[:, class_id]
                for row, value in zip(rows, probabilities.tolist()):
                    require(math.isfinite(value) and 0 <= value <= 1,
                            "nonfinite held-out probability")
                    predictions.append({"sample_id": row["sample_id"],
                                        "fold_id": fold_id, "task": row["task"],
                                        "gold_label": row["label"],
                                        "predicted_class": int(value >= 0.5),
                                        "p_H": value})
        require(len(predictions) == len(heldout) and
                len({r["sample_id"] for r in predictions}) == len(heldout),
                "held-out output coverage")
        oof_path = target / "heldout_predictions.jsonl"
        with oof_path.open("x", encoding="utf-8", newline="\n") as handle:
            for row in predictions:
                handle.write(json.dumps(row, ensure_ascii=False,
                                        allow_nan=False) + "\n")
        summary["heldout_predictions"] = len(predictions)
        summary["heldout_predictions_sha256"] = sha_file(oof_path)
    status_name = "SMOKE_PASS.json" if mode == "smoke" else "FOLD_PASS.json"
    with (target / status_name).open("x", encoding="utf-8") as handle:
        json.dump(summary, handle, ensure_ascii=False, indent=2, allow_nan=False)
        handle.write("\n")
    return summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", action="store_true")
    parser.add_argument("--fold-id", type=int, choices=range(1, 6), required=True)
    parser.add_argument("--mode", choices=("smoke", "fold"), required=True)
    parser.add_argument("--allow-full-fold", action="store_true")
    parser.add_argument("--bundle-root", type=Path, required=True)
    parser.add_argument("--model-dir", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--run-id", required=True)
    args = parser.parse_args()
    require(args.run, "GPU execution requires explicit --run")
    print(json.dumps(execute(args.fold_id, args.mode, args.bundle_root,
                             args.model_dir, args.output_root, args.run_id,
                             args.allow_full_fold), indent=2))
