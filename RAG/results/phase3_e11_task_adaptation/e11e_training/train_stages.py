"""E11-E two-stage trainer; E11-C training plus the frozen E11-D loss.
Differences: validated stage datasets, initial checkpoint and fixed epoch count.
No model selection, evaluation-driven scheduling, or teacher API calls.
"""
import json
import math
import os
import random
import sys
import time
import importlib.metadata
from collections import Counter
from pathlib import Path
from contrastive import pair_loss, sequence_masks


def require(ok,message):
    if not ok:raise ValueError(message)


def sha_file(path):
    import hashlib
    with Path(path).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()


def read_jsonl(path):
    return [json.loads(line) for line in Path(path).read_text(encoding='utf-8').splitlines() if line]


def linear_lr(base_lr,step,total,warmup):
    require(1<=step<=total and 1<=warmup<total,'learning-rate steps')
    factor=step/warmup if step<=warmup else max(0.,(total-step)/(total-warmup))
    return base_lr*factor


def execute(fold_id,stage,bundle,model_dir,output_root):
    import hashlib
    spec0=json.loads((bundle/'E11E_TRAINING_PROTOCOL.json').read_text())
    content={k:v for k,v in spec0.items() if k!='protocol_sha256'}
    require(hashlib.sha256(json.dumps(content,sort_keys=True,ensure_ascii=False,separators=(',',':'),allow_nan=False).encode()).hexdigest()==spec0['protocol_sha256'],'protocol hash')
    require(fold_id in range(1,6) and stage in (1,2),'fold/stage range')
    design = spec0['contrastive']
    require(design['lambda'] == 0.1 and design['margin'] == 0.0 and design['temperature'] is None, 'frozen E11-D loss')
    foldspec=spec0['folds'][str(fold_id)]
    data=bundle/'private'/f'fold_{fold_id}'
    for name,digest in foldspec['files_sha256'].items():
        require(sha_file(data/name)==digest,'prepared file changed')
    for name,digest in spec0.get('runtime_code_sha256',{}).items():
        require(sha_file(bundle/name)==digest,'runtime code changed')
    if stage==1:
        for name,digest in spec0['model']['local_assets_sha256'].items():
            require(sha_file(model_dir/name)==digest,'base model/tokenizer hash')
    else:
        previous=json.loads((model_dir.parent/'STAGE_PASS.json').read_text())
        require(previous['stage']==1 and previous['fold_id']==fold_id and previous['protocol_sha256']==spec0['protocol_sha256'] and sha_file(model_dir/'model.safetensors')==previous['checkpoint_sha256'],'Stage-1 checkpoint provenance')
    training=read_jsonl(data/('synthetic.jsonl' if stage==1 else 'train.jsonl'))
    require(len(training)==(foldspec['synthetic_rows'] if stage==1 else foldspec['human_train_rows']),'training count')
    require(all(r['fold_id']!=fold_id for r in training),'heldout in training')
    counts=Counter(r['label'] for r in training)
    weights=[len(training)/(2*counts[k]) for k in (0,1)]
    selected=training
    spec={**spec0,'training':spec0[f'stage{stage}']}
    require(all(abs(weights[k]-spec['training']['class_weight_values_by_fold'][str(fold_id)][str(k)])<1e-12 for k in (0,1)),'class weights')
    run_id=f'e11e-fold-{fold_id:03d}-stage-{stage}'
    target=output_root/f'fold_{fold_id}'/f'stage_{stage}'
    require(not target.exists(),'run already exists; do not retrain')
    target.mkdir(parents=True)
    fold={'heldout_path':f'private/fold_{fold_id}/heldout.jsonl','heldout_rows':foldspec['heldout_rows']}
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
        use_safetensors=True, num_labels=2, ignore_mismatched_sizes=(stage == 1),
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

    # Label-free representative tokenizer check covers all three SHROOM tasks.
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
    masks = sequence_masks(encoded)
    for i, example in enumerate(examples):
        example["mask_a"], example["mask_b"] = masks[i]
    for example, row in zip(examples, selected):
        example["labels"] = row["label"]
    def collate(batch: list[dict]) -> dict:
        labels = torch.tensor([r["labels"] for r in batch], dtype=torch.long)
        inputs = [{k: v for k, v in row.items() if k not in ("labels", "mask_a", "mask_b")} for row in batch]
        padded = tokenizer.pad(inputs, padding=True, return_tensors="pt")
        for key in ("mask_a", "mask_b"):
            padded[key] = torch.tensor([r[key] + [False] * (padded["input_ids"].shape[1] - len(r[key])) for r in batch], dtype=torch.bool)
        padded["labels"] = labels
        return padded

    generator = torch.Generator().manual_seed(seed)
    loader = DataLoader(examples, batch_size=spec["training"]["train_batch_size"],
                        shuffle=True, generator=generator, collate_fn=collate,
                        num_workers=0)
    epochs = spec["training"]["epochs"]
    accumulation = spec["training"]["gradient_accumulation_steps"]
    total_updates = epochs * math.ceil(len(loader) / accumulation)
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
    ce_losses = []
    contrastive_losses = []
    loss_by_epoch = []
    backward_passes = 0
    started = time.perf_counter()
    model.train()
    for _epoch in range(epochs):
        epoch_loss_start = len(losses)
        epoch_update_start = update
        num_batches = len(loader)
        for batch_idx, batch in enumerate(loader):
            batch = {k: v.to(device) for k, v in batch.items()}
            group_start = (batch_idx // accumulation) * accumulation
            group_size = min(accumulation, num_batches - group_start)
            with torch.autocast(device_type="cuda", dtype=torch.bfloat16):
                outputs = model(**{k: v for k, v in batch.items() if k not in ("labels", "mask_a", "mask_b")}, output_hidden_states=True)
                ce = criterion(outputs.logits.float(), batch["labels"])
                contrast = pair_loss(outputs.hidden_states[-1], batch["mask_a"], batch["mask_b"], batch["labels"], design["margin"])
                loss = ce + design["lambda"] * contrast
            ce_losses.append(float(ce.detach().cpu()))
            contrastive_losses.append(float(contrast.detach().cpu()))
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
        epoch_losses = losses[epoch_loss_start:]
        require(len(epoch_losses) == num_batches, "epoch loss coverage")
        loss_by_epoch.append({"epoch": _epoch + 1,
                              "mean_loss": sum(epoch_losses) / len(epoch_losses),
                              "mean_classification_loss": sum(ce_losses[epoch_loss_start:]) / num_batches,
                              "mean_contrastive_loss": sum(contrastive_losses[epoch_loss_start:]) / num_batches,
                              "last_loss": epoch_losses[-1],
                              "optimizer_steps": update - epoch_update_start})
    require(update == total_updates and backward_passes >= update and
            all(math.isfinite(x) for x in losses), "fixed training step count")

    checkpoint = target / "final_checkpoint"
    model.save_pretrained(str(checkpoint), safe_serialization=True)
    tokenizer.save_pretrained(str(checkpoint))
    require((checkpoint / "model.safetensors").is_file() and
            (checkpoint / "config.json").is_file(), "checkpoint writing")
    summary = {
        "initial_model_weights_sha256": sha_file(model_dir / "model.safetensors"),
        "status": "PASS", "stage": stage, "run_id": run_id, "fold_id": fold_id,
        "protocol_sha256": spec["protocol_sha256"],
        "trainer_sha256": sha_file(Path(__file__)),
        "contrastive_sha256": sha_file(bundle / "contrastive.py"),
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
        "loss_by_epoch": loss_by_epoch,
        "final_training_loss": losses[-1],
        "losses_all_finite": True, "checkpoint_sha256": sha_file(
            checkpoint / "model.safetensors"),
        "checkpoint_path": str(checkpoint),
        "elapsed_seconds": time.perf_counter() - started,
        "runtime": {"python": sys.version.split()[0], "torch": torch.__version__,
            "cuda": torch.version.cuda, "packages": {n: importlib.metadata.version(n) for n in ("transformers","tokenizers","numpy","safetensors")}},
        "e11e_score_produced": stage == 2,
    }
    if stage == 2:
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
    status_name = "STAGE_PASS.json"
    with (target / status_name).open("x", encoding="utf-8") as handle:
        json.dump(summary, handle, ensure_ascii=False, indent=2, allow_nan=False)
        handle.write("\n")
    return summary

