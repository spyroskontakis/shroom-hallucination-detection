"""Lazy, label-blind adapters around pinned frozen detector implementations.

Importing this module does not load a checkpoint or start inference. Only the
explicit GPU runner calls ``load_adapter``.
"""

from __future__ import annotations

import sys
from pathlib import Path

from scoring_common import POLICY, SCORE_FIELDS, require, scoring_row


class FactCGAdapter:
    def __init__(self, package: Path, cache: Path):
        cache.mkdir(parents=True, exist_ok=True)
        sys.path.insert(0, str(package))
        import nltk
        import factcg_backend
        import factcg_common
        import run_factcg_gpu

        nltk.data.path.insert(0, str(package / "nltk_data"))
        frozen_manifest, _ = factcg_common.validate_inputs()
        run_factcg_gpu.preflight(frozen_manifest, {})
        self.backend = factcg_backend
        self.tokenizer, self.model = factcg_backend.load(cache)

    def score(self, rows: list[dict]) -> list[dict]:
        outputs = []
        for original in rows:
            row = scoring_row(original)
            score, _ = self.backend.score(self.tokenizer, self.model,
                                          row["reference_text"], row["whole_hypothesis"])
            outputs.append({"factcg_support_probability": float(score)})
        return outputs


class MiniCheckAdapter:
    def __init__(self, package: Path, cache: Path):
        cache.mkdir(parents=True, exist_ok=True)
        sys.path.insert(0, str(package))
        import nltk
        import gpu_common
        import run_minicheck_gpu

        nltk.data.path.insert(0, str(package / "nltk_data"))
        frozen_manifest, _ = gpu_common.validate_inputs()
        run_minicheck_gpu.preflight(frozen_manifest, {})
        self.scorer = run_minicheck_gpu.load_scorer(cache)

    def score(self, rows: list[dict]) -> list[dict]:
        outputs = []
        for offset in range(0, len(rows), 16):
            batch = [scoring_row(row) for row in rows[offset:offset + 16]]
            _, values, _, _ = self.scorer.score(
                docs=[row["reference_text"] for row in batch],
                claims=[row["whole_hypothesis"] for row in batch], chunk_size=32468)
            require(len(values) == len(batch), "MiniCheck batch length")
            outputs.extend({"minicheck_support_probability": float(value)}
                           for value in values)
        return outputs


class PairModelAdapter:
    def __init__(self, model_dir: Path, kind: str):
        require(kind in ("nli", "hhem"), "invalid pair model")
        import torch
        from transformers import AutoModelForSequenceClassification, AutoTokenizer

        self.kind, self.torch = kind, torch
        self.tokenizer = AutoTokenizer.from_pretrained(
            str(model_dir), local_files_only=True, trust_remote_code=False, use_fast=True)
        self.model = AutoModelForSequenceClassification.from_pretrained(
            str(model_dir), local_files_only=True, trust_remote_code=False,
            use_safetensors=(kind == "nli"), torch_dtype=torch.float32)
        require(self.tokenizer.is_fast, "pinned fast tokenizer required")
        require(self.model.config.model_type == "deberta-v2", "DeBERTa architecture")
        if kind == "nli":
            require({int(k): v for k, v in self.model.config.id2label.items()} ==
                    {0: "entailment", 1: "neutral", 2: "contradiction"},
                    "NLI class index mapping")
            require(self.model.config.label2id ==
                    {"entailment": 0, "neutral": 1, "contradiction": 2},
                    "NLI inverse class mapping")
        else:
            require(self.model.config.num_labels == 1, "HHEM single logit")
        require(torch.cuda.is_available(), "CUDA required; no CPU fallback")
        self.model = self.model.to("cuda:0").eval().requires_grad_(False)
        require(next(self.model.parameters()).dtype == torch.float32,
                "frozen float32 precision")

    def score(self, rows: list[dict]) -> list[dict]:
        torch = self.torch
        outputs = []
        for offset in range(0, len(rows), 16):
            batch = [scoring_row(row) for row in rows[offset:offset + 16]]
            enc = self.tokenizer(
                [row["reference_text"] for row in batch],
                [row["whole_hypothesis"] for row in batch],
                truncation="longest_first", max_length=512, padding=True,
                return_attention_mask=True, return_tensors="pt")
            require(enc["input_ids"].shape[1] <= 512, "token length")
            with torch.inference_mode():
                logits = self.model(**{key: value.to("cuda:0")
                                       for key, value in enc.items()}).logits
                if self.kind == "nli":
                    require(tuple(logits.shape) == (len(batch), 3), "NLI logit shape")
                    probs = torch.softmax(logits, dim=-1).float().cpu().tolist()
                    outputs.extend(dict(zip(SCORE_FIELDS["nli"], map(float, values)))
                                   for values in probs)
                else:
                    require(tuple(logits.shape) == (len(batch), 1), "HHEM logit shape")
                    values = torch.sigmoid(logits[:, 0]).float().cpu().tolist()
                    outputs.extend({"hhem_ref_hyp_consistency": float(value)}
                                   for value in values)
        return outputs


def load_adapter(kind: str, package_root: Path, cache_root: Path,
                 nli_model: Path, hhem_model: Path):
    require(kind in SCORE_FIELDS, "unknown detector")
    if kind == "factcg":
        return FactCGAdapter(package_root / "factcg_gpu", cache_root / "factcg")
    if kind == "minicheck":
        return MiniCheckAdapter(package_root / "minicheck_gpu", cache_root / "minicheck")
    return PairModelAdapter(nli_model if kind == "nli" else hhem_model, kind)
