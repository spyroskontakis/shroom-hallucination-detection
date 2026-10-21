"""Deterministic, resumable CPU dense-cache builder for Module 2 Phase A.

The module is imported by the notebook and can also be launched as a CLI.  It
never uses network services, development labels, or the official test split.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import random
import re
import sys
import time
import unicodedata
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from importlib.metadata import version
from pathlib import Path
from typing import Any, Callable

# These settings are applied before importing Hugging Face libraries.
os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"
os.environ["HF_DATASETS_OFFLINE"] = "1"
os.environ["CUDA_VISIBLE_DEVICES"] = ""

import numpy as np
import pandas as pd
import torch
from sentence_transformers import SentenceTransformer
from transformers import AutoTokenizer


RANDOM_STATE = 42
EMBEDDING_MODEL_ID = "sentence-transformers/all-mpnet-base-v2"
EMBEDDING_DEVICE = "cpu"
EMBEDDING_DIMENSION = 768
NORMALIZE_EMBEDDINGS = True
DENSE_TEXT_VERSION = "term_definition_context_window_v1"
DENSE_MAX_SEQ_LENGTH = 256
DENSE_CHUNK_SIZE = 256
BENCHMARK_BATCH_SIZES = (8, 16, 32)
BENCHMARK_SAMPLE_SIZE = 128
BENCHMARK_MAX_SECONDS = 600.0
CACHE_SCHEMA_VERSION = 1

EXPECTED_MODULE1_TRIAL_SHA256 = (
    "A7E0455A11EFFB7C195EFFB1CACB542DD82992FCCE027FB0D297BE598557D20B"
)
EXPECTED_MODULE1_CACHE_SHA256 = (
    "A942A0CC228DEF64B61389BCF7B7A5CB0A93BBCC7B0AA1D726826A9993B14CA5"
)

CLOSED_DEFINE_PATTERN = re.compile(
    r"<define>\s*(.*?)\s*</define>", flags=re.IGNORECASE | re.DOTALL
)
OPEN_DEFINE_MARKER = re.compile(r"<define>", flags=re.IGNORECASE)
ANY_DEFINE_MARKER = re.compile(r"</?define>", flags=re.IGNORECASE)


@dataclass(frozen=True)
class DenseTextRecord:
    text: str
    unbounded_token_length: int
    bounded_token_length: int
    context_tokens_unbounded: int
    context_tokens_bounded: int
    context_truncated: bool
    definition_truncated: bool
    reference_truncated: bool
    context_fallback: str


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def clean_text(value: Any) -> str:
    if pd.isna(value):
        return ""
    return str(value).strip()


def extract_define_term(source_text: Any) -> str | None:
    text = clean_text(source_text)
    if not text:
        return None
    closed_match = CLOSED_DEFINE_PATTERN.search(text)
    if closed_match:
        candidate = closed_match.group(1).strip()
        return candidate or None
    parts = OPEN_DEFINE_MARKER.split(text)
    if len(parts) >= 3:
        candidate = parts[1].strip()
        return candidate or None
    return None


def normalize_term(term: Any) -> str | None:
    text = clean_text(term)
    if not text:
        return None
    text = unicodedata.normalize("NFKC", text).lower()
    text = text.replace("–", "-").replace("—", "-")
    text = re.sub(r"\s*-\s*", "-", text)
    text = re.sub(r"[^\w\s\-']+", " ", text, flags=re.UNICODE)
    text = re.sub(r"[_\-]+", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text or None


def valid_definition(value: Any) -> bool:
    text = clean_text(value)
    return bool(text and re.search(r"[A-Za-z0-9]", text))


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest().upper()


def sha256_json(value: Any) -> str:
    payload = json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest().upper()


def canonical_records_hash(frame: pd.DataFrame, columns: list[str]) -> str:
    return sha256_json(frame[columns].to_dict(orient="records"))


def build_dm_knowledge_base(train_df: pd.DataFrame) -> pd.DataFrame:
    dm = train_df.loc[train_df["task"].astype(str).eq("DM")].copy()
    dm = dm.reset_index().rename(columns={"index": "evidence_id"})
    dm["term_raw"] = dm["src"].map(extract_define_term)
    dm["term_key"] = dm["term_raw"].map(normalize_term)
    dm["definition"] = dm["tgt"].map(clean_text)
    dm["source_context"] = dm["src"].map(clean_text)
    knowledge_base = dm.loc[
        dm["term_key"].notna() & dm["definition"].map(valid_definition),
        ["evidence_id", "term_raw", "term_key", "definition", "source_context"],
    ].copy()
    return knowledge_base.drop_duplicates(
        subset=["term_key", "definition"]
    ).reset_index(drop=True)


def load_module2_kb(project_root: Path) -> tuple[pd.DataFrame, dict[str, str]]:
    train_path = (
        project_root
        / "data"
        / "Unlabeled train"
        / "SHROOM_unlabeled-training-data-v2"
        / "train.model-agnostic.json"
    )
    with train_path.open("r", encoding="utf-8") as stream:
        train_df = pd.DataFrame(json.load(stream))
    assert len(train_df) == 30000
    assert int(train_df["task"].eq("DM").sum()) == 10000
    forbidden = {"label", "labels", "label_bin", "p(Hallucination)", "p_hallucination"}
    assert not forbidden & set(train_df.columns)
    kb = build_dm_knowledge_base(train_df)
    assert len(kb) == 9577
    assert kb["evidence_id"].is_unique
    assert kb["evidence_id"].tolist() == sorted(kb["evidence_id"].tolist())
    hashes = {
        "train_file_sha256": sha256_file(train_path),
        "ordered_kb_sha256": canonical_records_hash(
            kb,
            ["evidence_id", "term_raw", "term_key", "definition", "source_context"],
        ),
        "ordered_candidate_ids_sha256": sha256_json(
            kb["evidence_id"].astype(int).tolist()
        ),
    }
    return kb, hashes


def load_local_tokenizer():
    return AutoTokenizer.from_pretrained(
        EMBEDDING_MODEL_ID,
        local_files_only=True,
        use_fast=True,
    )


def load_local_model() -> SentenceTransformer:
    model = SentenceTransformer(
        EMBEDDING_MODEL_ID,
        device=EMBEDDING_DEVICE,
        local_files_only=True,
    )
    model.max_seq_length = DENSE_MAX_SEQ_LENGTH
    assert str(model.device) == "cpu"
    return model


def token_offsets(tokenizer, text: str) -> tuple[list[int], list[tuple[int, int]]]:
    encoded = tokenizer(
        clean_text(text),
        add_special_tokens=False,
        truncation=False,
        return_attention_mask=False,
        return_offsets_mapping=True,
    )
    return list(encoded["input_ids"]), [tuple(pair) for pair in encoded["offset_mapping"]]


def token_length(tokenizer, text: str) -> int:
    return len(
        tokenizer(
            text,
            add_special_tokens=True,
            truncation=False,
            return_attention_mask=False,
        )["input_ids"]
    )


def _prefix_by_token_count(
    text: str,
    offsets: list[tuple[int, int]],
    count: int,
) -> str:
    if count <= 0 or not offsets:
        return ""
    end = offsets[min(count, len(offsets)) - 1][1]
    return text[:end].strip()


def _anchor_span(source_context: str, term: str) -> tuple[int, int, str]:
    markers = list(ANY_DEFINE_MARKER.finditer(source_context))
    if markers:
        start = markers[0].start()
        end_marker = next(
            (match for match in markers[1:] if match.group(0).startswith("</")),
            markers[1] if len(markers) > 1 else markers[0],
        )
        return start, end_marker.end(), "marker"
    if term:
        position = source_context.casefold().find(term.casefold())
        if position >= 0:
            return position, position + len(term), "term"
    return 0, 0, "initial"


def _window_from_offsets(
    text: str,
    offsets: list[tuple[int, int]],
    anchor_start: int,
    anchor_end: int,
    token_budget: int,
) -> str:
    if token_budget <= 0 or not offsets:
        return ""
    total = len(offsets)
    width = min(token_budget, total)
    if anchor_end > anchor_start:
        overlapping = [
            index
            for index, (start, end) in enumerate(offsets)
            if end > anchor_start and start < anchor_end
        ]
    else:
        overlapping = []
    center = (
        (overlapping[0] + overlapping[-1]) // 2
        if overlapping
        else 0
    )
    start_index = max(0, min(center - width // 2, total - width))
    end_index = start_index + width
    char_start = offsets[start_index][0]
    char_end = offsets[end_index - 1][1]
    return text[char_start:char_end].strip()


def _fit_prefix_field(
    tokenizer,
    payload: str,
    formatter: Callable[[str], str],
    max_tokens: int,
) -> tuple[str, bool]:
    ids, offsets = token_offsets(tokenizer, payload)
    if token_length(tokenizer, formatter(payload)) <= max_tokens:
        return payload, False
    low, high = 0, len(ids)
    while low < high:
        middle = (low + high + 1) // 2
        candidate = _prefix_by_token_count(payload, offsets, middle)
        if token_length(tokenizer, formatter(candidate)) <= max_tokens:
            low = middle
        else:
            high = middle - 1
    fitted = _prefix_by_token_count(payload, offsets, low)
    assert token_length(tokenizer, formatter(fitted)) <= max_tokens
    return fitted, True


def _fit_context_window(
    tokenizer,
    source_context: str,
    term: str,
    formatter: Callable[[str], str],
    max_tokens: int,
) -> tuple[str, int, int, bool, str]:
    context_ids, offsets = token_offsets(tokenizer, source_context)
    anchor_start, anchor_end, fallback = _anchor_span(source_context, term)
    full_count = len(context_ids)
    if token_length(tokenizer, formatter(source_context)) <= max_tokens:
        return source_context, full_count, full_count, False, fallback
    low, high = 0, full_count
    while low < high:
        middle = (low + high + 1) // 2
        candidate = _window_from_offsets(
            source_context, offsets, anchor_start, anchor_end, middle
        )
        if token_length(tokenizer, formatter(candidate)) <= max_tokens:
            low = middle
        else:
            high = middle - 1
    fitted = _window_from_offsets(
        source_context, offsets, anchor_start, anchor_end, low
    )
    assert token_length(tokenizer, formatter(fitted)) <= max_tokens
    return fitted, full_count, low, low < full_count, fallback


def format_candidate(term: str, definition: str, context: str) -> str:
    return (
        f"TERM: {term}\n"
        f"DEFINITION: {definition}\n"
        f"SOURCE CONTEXT: {context}"
    )


def format_query(term: str, context: str, reference: str | None) -> str:
    text = f"TERM: {term}\nSOURCE CONTEXT: {context}"
    if reference is not None:
        text += f"\nPRIMARY REFERENCE: {reference}"
    return text


def build_bounded_candidate_text(
    tokenizer,
    term: str,
    definition: str,
    source_context: str,
) -> DenseTextRecord:
    term = clean_text(term)
    definition = clean_text(definition)
    source_context = clean_text(source_context)
    unbounded = format_candidate(term, definition, source_context)
    unbounded_length = token_length(tokenizer, unbounded)

    definition_fitted, definition_truncated = _fit_prefix_field(
        tokenizer,
        definition,
        lambda value: format_candidate(term, value, ""),
        DENSE_MAX_SEQ_LENGTH,
    )
    if not definition_fitted and definition:
        raise RuntimeError("The normalized term and field tags leave no definition budget.")
    context_fitted, full_context_tokens, fitted_context_tokens, context_truncated, fallback = (
        _fit_context_window(
            tokenizer,
            source_context,
            term,
            lambda value: format_candidate(term, definition_fitted, value),
            DENSE_MAX_SEQ_LENGTH,
        )
    )
    bounded = format_candidate(term, definition_fitted, context_fitted)
    bounded_length = token_length(tokenizer, bounded)
    assert bounded_length <= DENSE_MAX_SEQ_LENGTH
    assert term in bounded
    return DenseTextRecord(
        text=bounded,
        unbounded_token_length=unbounded_length,
        bounded_token_length=bounded_length,
        context_tokens_unbounded=full_context_tokens,
        context_tokens_bounded=fitted_context_tokens,
        context_truncated=context_truncated,
        definition_truncated=definition_truncated,
        reference_truncated=False,
        context_fallback=fallback,
    )


def build_bounded_query_text(
    tokenizer,
    term: str,
    source_context: str,
    reference: str | None,
) -> DenseTextRecord:
    term = clean_text(term)
    source_context = clean_text(source_context)
    reference_value = None if reference is None else clean_text(reference)
    unbounded = format_query(term, source_context, reference_value)
    unbounded_length = token_length(tokenizer, unbounded)

    reference_truncated = False
    fitted_reference = reference_value
    if reference_value is not None:
        fitted_reference, reference_truncated = _fit_prefix_field(
            tokenizer,
            reference_value,
            lambda value: format_query(term, "", value),
            DENSE_MAX_SEQ_LENGTH,
        )
        if not fitted_reference and reference_value:
            raise RuntimeError("The normalized term and field tags leave no reference budget.")

    context_fitted, full_context_tokens, fitted_context_tokens, context_truncated, fallback = (
        _fit_context_window(
            tokenizer,
            source_context,
            term,
            lambda value: format_query(term, value, fitted_reference),
            DENSE_MAX_SEQ_LENGTH,
        )
    )
    bounded = format_query(term, context_fitted, fitted_reference)
    bounded_length = token_length(tokenizer, bounded)
    assert bounded_length <= DENSE_MAX_SEQ_LENGTH
    assert term in bounded
    return DenseTextRecord(
        text=bounded,
        unbounded_token_length=unbounded_length,
        bounded_token_length=bounded_length,
        context_tokens_unbounded=full_context_tokens,
        context_tokens_bounded=fitted_context_tokens,
        context_truncated=context_truncated,
        definition_truncated=False,
        reference_truncated=reference_truncated,
        context_fallback=fallback,
    )


def build_candidate_dense_records(tokenizer, kb: pd.DataFrame) -> list[DenseTextRecord]:
    records = [
        build_bounded_candidate_text(
            tokenizer,
            clean_text(row.term_key),
            clean_text(row.definition),
            clean_text(row.source_context),
        )
        for row in kb.itertuples(index=False)
    ]
    assert len(records) == len(kb)
    assert max(record.bounded_token_length for record in records) <= DENSE_MAX_SEQ_LENGTH
    return records


def percentile_summary(values: list[int]) -> dict[str, float | int]:
    array = np.asarray(values, dtype=float)
    return {
        "p50": float(np.percentile(array, 50)),
        "p90": float(np.percentile(array, 90)),
        "p95": float(np.percentile(array, 95)),
        "p99": float(np.percentile(array, 99)),
        "max": int(array.max()),
    }


def dense_text_diagnostics(records: list[DenseTextRecord]) -> dict[str, Any]:
    total = len(records)
    context_only = sum(
        record.context_truncated
        and not record.definition_truncated
        and not record.reference_truncated
        for record in records
    )
    fallbacks = {
        key: sum(record.context_fallback == key for record in records)
        for key in ("marker", "term", "initial")
    }
    return {
        "rows": total,
        "unbounded_token_lengths": percentile_summary(
            [record.unbounded_token_length for record in records]
        ),
        "bounded_token_lengths": percentile_summary(
            [record.bounded_token_length for record in records]
        ),
        "context_only_truncated_count": int(context_only),
        "context_only_truncated_percent": float(100.0 * context_only / total),
        "definition_truncated_count": int(
            sum(record.definition_truncated for record in records)
        ),
        "reference_truncated_count": int(
            sum(record.reference_truncated for record in records)
        ),
        "context_fallback_counts": fallbacks,
        "all_bounded_at_most_256": bool(
            max(record.bounded_token_length for record in records)
            <= DENSE_MAX_SEQ_LENGTH
        ),
    }


def dense_texts_hash(texts: list[str]) -> str:
    return sha256_json(texts)


def model_config_hash(model: SentenceTransformer) -> str:
    first_module = model._first_module()
    config = first_module.auto_model.config.to_dict()
    return sha256_json(config)


def _assert_embeddings(matrix: np.ndarray, rows: int) -> np.ndarray:
    array = np.asarray(matrix, dtype=np.float32)
    assert array.shape == (rows, EMBEDDING_DIMENSION), array.shape
    assert array.dtype == np.float32
    assert np.isfinite(array).all()
    norms = np.linalg.norm(array, axis=1)
    assert np.allclose(norms, 1.0, atol=1e-5), (float(norms.min()), float(norms.max()))
    return array


def encode_texts(
    model: SentenceTransformer,
    texts: list[str],
    batch_size: int,
) -> np.ndarray:
    with torch.inference_mode():
        matrix = model.encode(
            texts,
            batch_size=batch_size,
            convert_to_numpy=True,
            normalize_embeddings=NORMALIZE_EMBEDDINGS,
            show_progress_bar=False,
        )
    return _assert_embeddings(matrix, len(texts))


def benchmark_batch_sizes(
    model: SentenceTransformer,
    candidate_texts: list[str],
) -> tuple[int, list[dict[str, Any]]]:
    rng = np.random.default_rng(RANDOM_STATE)
    positions = np.sort(
        rng.choice(len(candidate_texts), size=BENCHMARK_SAMPLE_SIZE, replace=False)
    )
    sample = [candidate_texts[int(position)] for position in positions]
    benchmark_started = time.perf_counter()
    reference = None
    results: list[dict[str, Any]] = []
    for batch_size in BENCHMARK_BATCH_SIZES:
        started = time.perf_counter()
        try:
            embeddings = encode_texts(model, sample, batch_size)
            elapsed = time.perf_counter() - started
            if reference is None:
                reference = embeddings
            else:
                assert np.allclose(reference, embeddings, atol=1e-6)
            results.append(
                {
                    "batch_size": batch_size,
                    "seconds": float(elapsed),
                    "completed": True,
                    "error_type": None,
                }
            )
        except Exception as exc:
            results.append(
                {
                    "batch_size": batch_size,
                    "seconds": float(time.perf_counter() - started),
                    "completed": False,
                    "error_type": type(exc).__name__,
                }
            )
        total_elapsed = time.perf_counter() - benchmark_started
        print(
            f"BENCHMARK batch={batch_size} completed={results[-1]['completed']} "
            f"seconds={results[-1]['seconds']:.3f}",
            flush=True,
        )
        if total_elapsed > BENCHMARK_MAX_SECONDS:
            raise TimeoutError(
                "The fixed 128-candidate benchmark exceeded 600 seconds."
            )
    completed = [record for record in results if record["completed"]]
    if not completed:
        raise RuntimeError("No approved benchmark batch size completed.")
    selected = min(completed, key=lambda record: (record["seconds"], record["batch_size"]))
    return int(selected["batch_size"]), results


def atomic_write_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f"{path.name}.{os.getpid()}.tmp")
    with temporary.open("w", encoding="utf-8") as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(temporary, path)


def chunk_path(cache_dir: Path, start: int, end: int) -> Path:
    return cache_dir / f"chunk_{start:05d}_{end:05d}.npz"


def atomic_write_chunk(
    path: Path,
    embeddings: np.ndarray,
    evidence_ids: np.ndarray,
    start: int,
    end: int,
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f"{path.name}.{os.getpid()}.tmp")
    with temporary.open("wb") as stream:
        np.savez(
            stream,
            embeddings=embeddings,
            evidence_ids=evidence_ids,
            start=np.asarray(start, dtype=np.int64),
            end=np.asarray(end, dtype=np.int64),
        )
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(temporary, path)


def validate_chunk(
    path: Path,
    expected_ids: np.ndarray,
    start: int,
    end: int,
) -> np.ndarray:
    with np.load(path, allow_pickle=False) as payload:
        stored_start = int(payload["start"])
        stored_end = int(payload["end"])
        stored_ids = np.asarray(payload["evidence_ids"], dtype=np.int64)
        embeddings = np.asarray(payload["embeddings"])
    assert stored_start == start and stored_end == end
    assert np.array_equal(stored_ids, expected_ids[start:end])
    return _assert_embeddings(embeddings, end - start)


def expected_ranges(total_rows: int) -> list[tuple[int, int]]:
    return [
        (start, min(start + DENSE_CHUNK_SIZE, total_rows))
        for start in range(0, total_rows, DENSE_CHUNK_SIZE)
    ]


def compatibility_fields(
    kb: pd.DataFrame,
    kb_hashes: dict[str, str],
    candidate_texts: list[str],
    model: SentenceTransformer,
    selected_batch_size: int,
) -> dict[str, Any]:
    return {
        "cache_schema_version": CACHE_SCHEMA_VERSION,
        "ordered_kb_sha256": kb_hashes["ordered_kb_sha256"],
        "ordered_candidate_ids_sha256": kb_hashes["ordered_candidate_ids_sha256"],
        "dense_texts_sha256": dense_texts_hash(candidate_texts),
        "model_id": EMBEDDING_MODEL_ID,
        "model_config_sha256": model_config_hash(model),
        "embedding_dimension": EMBEDDING_DIMENSION,
        "dense_text_version": DENSE_TEXT_VERSION,
        "dense_max_seq_length": DENSE_MAX_SEQ_LENGTH,
        "selected_batch_size": selected_batch_size,
        "chunk_size": DENSE_CHUNK_SIZE,
        "normalization": NORMALIZE_EMBEDDINGS,
        "dtype": "float32",
        "sentence_transformers_version": version("sentence-transformers"),
        "transformers_version": version("transformers"),
        "torch_version": version("torch"),
        "total_rows": int(len(kb)),
    }


def assert_manifest_compatible(
    manifest: dict[str, Any], expected: dict[str, Any]
) -> None:
    mismatches = {
        key: {"stored": manifest.get(key), "expected": value}
        for key, value in expected.items()
        if manifest.get(key) != value
    }
    if mismatches:
        raise RuntimeError(
            "Dense cache compatibility mismatch: "
            + json.dumps(mismatches, ensure_ascii=False, sort_keys=True)
        )


def _range_records(ranges: list[tuple[int, int]]) -> list[dict[str, int]]:
    return [{"start": start, "end": end} for start, end in ranges]


def load_manifest(cache_dir: Path) -> dict[str, Any]:
    manifest_path = cache_dir / "dense_cache_manifest.json"
    with manifest_path.open("r", encoding="utf-8") as stream:
        return json.load(stream)


def validate_and_load_complete_cache(
    cache_dir: Path,
    expected: dict[str, Any],
    evidence_ids: np.ndarray,
) -> tuple[np.ndarray, dict[str, Any]]:
    manifest = load_manifest(cache_dir)
    assert_manifest_compatible(manifest, expected)
    ranges = expected_ranges(len(evidence_ids))
    assert manifest.get("cache_complete") is True
    assert manifest.get("completed_chunk_ranges") == _range_records(ranges)
    chunks = [
        validate_chunk(chunk_path(cache_dir, start, end), evidence_ids, start, end)
        for start, end in ranges
    ]
    matrix = np.concatenate(chunks, axis=0)
    return _assert_embeddings(matrix, len(evidence_ids)), manifest


def verify_locked_module1(project_root: Path) -> None:
    rag_dir = project_root / "RAG"
    trial = rag_dir / "shroom_rag_e5_module1_gemini_trial.ipynb"
    cache = rag_dir / "results" / "rag_module1" / "module1_gemini_cache.jsonl"
    assert sha256_file(trial) == EXPECTED_MODULE1_TRIAL_SHA256
    assert sha256_file(cache) == EXPECTED_MODULE1_CACHE_SHA256


def build_or_resume_cache(project_root: Path) -> dict[str, Any]:
    if sys.version.split()[0] != "3.11.9":
        raise RuntimeError("Module 2 cache builder requires Python 3.11.9.")
    if torch.cuda.is_available():
        raise RuntimeError("CUDA must be unavailable for this approved CPU run.")
    random.seed(RANDOM_STATE)
    np.random.seed(RANDOM_STATE)
    torch.manual_seed(RANDOM_STATE)
    torch.use_deterministic_algorithms(True, warn_only=True)
    verify_locked_module1(project_root)

    cache_dir = project_root / "RAG" / "results" / "rag_module2" / "dense_cache"
    cache_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = cache_dir / "dense_cache_manifest.json"

    print("CACHE_BUILDER_PRECHECKS=PASS", flush=True)
    kb, kb_hashes = load_module2_kb(project_root)
    tokenizer = load_local_tokenizer()
    candidate_records = build_candidate_dense_records(tokenizer, kb)
    candidate_texts = [record.text for record in candidate_records]
    diagnostics = dense_text_diagnostics(candidate_records)
    assert diagnostics["all_bounded_at_most_256"]
    print(
        f"TOKEN_DIAGNOSTICS rows={len(candidate_texts)} "
        f"bounded_max={diagnostics['bounded_token_lengths']['max']}",
        flush=True,
    )

    model = load_local_model()
    evidence_ids = kb["evidence_id"].astype(np.int64).to_numpy()
    ranges = expected_ranges(len(kb))

    if manifest_path.exists():
        manifest = load_manifest(cache_dir)
        selected_batch_size = int(manifest.get("selected_batch_size", -1))
        if selected_batch_size not in BENCHMARK_BATCH_SIZES:
            raise RuntimeError("Stored selected batch size is not approved.")
        expected = compatibility_fields(
            kb, kb_hashes, candidate_texts, model, selected_batch_size
        )
        assert_manifest_compatible(manifest, expected)
        previous_launches = int(manifest.get("builder_launches", 0))
        if previous_launches >= 4:
            raise RuntimeError("The four approved dense-cache launches are exhausted.")
        manifest["builder_launches"] = previous_launches + 1
        manifest["cache_resumptions"] = int(manifest.get("cache_resumptions", 0)) + 1
        manifest["last_launch_started_utc"] = utc_now()
        atomic_write_json(manifest_path, manifest)
    else:
        selected_batch_size, benchmark = benchmark_batch_sizes(model, candidate_texts)
        expected = compatibility_fields(
            kb, kb_hashes, candidate_texts, model, selected_batch_size
        )
        manifest = {
            **expected,
            "created_utc": utc_now(),
            "last_launch_started_utc": utc_now(),
            "builder_launches": 1,
            "cache_resumptions": 0,
            "benchmark_sample_size": BENCHMARK_SAMPLE_SIZE,
            "benchmark_seed": RANDOM_STATE,
            "benchmark_results": benchmark,
            "candidate_token_diagnostics": diagnostics,
            "completed_chunk_ranges": [],
            "cache_complete": False,
            "total_chunk_encoding_seconds": 0.0,
            "launch_history": [],
        }
        atomic_write_json(manifest_path, manifest)

    completed: list[tuple[int, int]] = []
    cache_hits = 0
    new_chunks = 0
    launch_chunk_seconds = 0.0
    launch_started = time.perf_counter()

    # Adopt any valid atomically-written chunk that was not yet listed after a crash.
    for start, end in ranges:
        path = chunk_path(cache_dir, start, end)
        if path.exists():
            validate_chunk(path, evidence_ids, start, end)
            completed.append((start, end))
            cache_hits += 1
    manifest["completed_chunk_ranges"] = _range_records(completed)
    atomic_write_json(manifest_path, manifest)

    for start, end in ranges:
        path = chunk_path(cache_dir, start, end)
        if path.exists():
            continue
        started = time.perf_counter()
        embeddings = encode_texts(
            model,
            candidate_texts[start:end],
            int(manifest["selected_batch_size"]),
        )
        chunk_seconds = time.perf_counter() - started
        atomic_write_chunk(
            path,
            embeddings,
            evidence_ids[start:end],
            start,
            end,
        )
        validate_chunk(path, evidence_ids, start, end)
        completed.append((start, end))
        completed.sort()
        new_chunks += 1
        launch_chunk_seconds += chunk_seconds
        manifest["completed_chunk_ranges"] = _range_records(completed)
        manifest["total_chunk_encoding_seconds"] = float(
            manifest.get("total_chunk_encoding_seconds", 0.0) + chunk_seconds
        )
        atomic_write_json(manifest_path, manifest)
        print(
            f"CHUNK_COMPLETE range={start}:{end} seconds={chunk_seconds:.3f} "
            f"completed={len(completed)}/{len(ranges)}",
            flush=True,
        )

    expected = compatibility_fields(
        kb, kb_hashes, candidate_texts, model, int(manifest["selected_batch_size"])
    )
    matrix, _ = validate_and_load_complete_cache_if_ready(
        cache_dir, expected, evidence_ids, ranges, manifest
    )
    assert matrix.shape == (len(kb), EMBEDDING_DIMENSION)
    manifest["cache_complete"] = True
    manifest["completed_chunk_ranges"] = _range_records(ranges)
    manifest["last_launch_finished_utc"] = utc_now()
    manifest["last_launch_cache_hits"] = cache_hits
    manifest["last_launch_new_chunks"] = new_chunks
    manifest["launch_history"].append(
        {
            "launch_number": int(manifest["builder_launches"]),
            "cache_hits": cache_hits,
            "new_chunks": new_chunks,
            "chunk_encoding_seconds": float(launch_chunk_seconds),
            "wall_seconds": float(time.perf_counter() - launch_started),
        }
    )
    atomic_write_json(manifest_path, manifest)
    print(
        f"CACHE_COMPLETE rows={matrix.shape[0]} chunks={len(ranges)} "
        f"launches={manifest['builder_launches']} resumptions={manifest['cache_resumptions']}",
        flush=True,
    )
    return manifest


def validate_and_load_complete_cache_if_ready(
    cache_dir: Path,
    expected: dict[str, Any],
    evidence_ids: np.ndarray,
    ranges: list[tuple[int, int]],
    manifest: dict[str, Any],
) -> tuple[np.ndarray, dict[str, Any]]:
    assert_manifest_compatible(manifest, expected)
    assert manifest.get("completed_chunk_ranges") == _range_records(ranges)
    chunks = [
        validate_chunk(chunk_path(cache_dir, start, end), evidence_ids, start, end)
        for start, end in ranges
    ]
    return _assert_embeddings(np.concatenate(chunks, axis=0), len(evidence_ids)), manifest


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--project-root",
        type=Path,
        default=Path((__import__('os').environ.get('SHROOM_PROJECT_ROOT', '.') + '')),
    )
    args = parser.parse_args()
    build_or_resume_cache(args.project_root.resolve())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
