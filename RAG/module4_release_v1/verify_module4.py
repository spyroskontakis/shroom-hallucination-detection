#!/usr/bin/env python3
"""Read-only, standard-library verifier for the SHROOM Module 4 release."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
from pathlib import Path, PurePosixPath, PureWindowsPath
from typing import Any


SCHEMA_VERSION = "module4-release-manifest-v1"
DEFAULT_MANIFEST = "RAG/module4_release_v1/RELEASE_MANIFEST.json"
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
EXIT_PASS = 0
EXIT_VERIFICATION_FAILED = 1
EXIT_USAGE_OR_MANIFEST_ERROR = 2


class ManifestError(ValueError):
    """Raised when the release manifest is invalid or ambiguous."""


def _unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ManifestError(f"Duplicate JSON key: {key}")
        result[key] = value
    return result


def load_manifest(path: Path) -> dict[str, Any]:
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        raise ManifestError(f"Cannot read manifest: {exc}") from exc
    try:
        data = json.loads(text, object_pairs_hook=_unique_object)
    except (json.JSONDecodeError, ManifestError) as exc:
        raise ManifestError(f"Invalid manifest JSON: {exc}") from exc
    if not isinstance(data, dict):
        raise ManifestError("Manifest root must be an object")
    return data


def _relative_parts(raw: Any) -> tuple[str, ...]:
    if not isinstance(raw, str) or not raw:
        raise ManifestError("Every path must be a non-empty string")
    if "\x00" in raw:
        raise ManifestError(f"NUL byte rejected in path: {raw!r}")
    windows = PureWindowsPath(raw)
    if windows.is_absolute() or windows.drive or raw.startswith(("/", "\\")):
        raise ManifestError(f"Absolute path rejected: {raw}")
    normalized = raw.replace("\\", "/")
    split = normalized.split("/")
    if any(part in ("", ".", "..") for part in split):
        raise ManifestError(f"Ambiguous or traversing path rejected: {raw}")
    parts = PurePosixPath(normalized).parts
    if not parts:
        raise ManifestError(f"Empty normalized path rejected: {raw}")
    return parts


def _normalize_key(raw: str) -> str:
    return "/".join(_relative_parts(raw)).casefold()


def validate_manifest(data: dict[str, Any]) -> None:
    if data.get("schema_version") != SCHEMA_VERSION:
        raise ManifestError(
            f"Unsupported schema_version: {data.get('schema_version')!r}"
        )
    release_root = data.get("release_root")
    root_parts = _relative_parts(release_root)
    inventories = data.get("inventories")
    if not isinstance(inventories, dict):
        raise ManifestError("inventories must be an object")
    if set(inventories) != {"source", "local_artifacts"}:
        raise ManifestError("inventories must contain only source and local_artifacts")

    seen: set[str] = set()
    for name in ("source", "local_artifacts"):
        entries = inventories[name]
        if not isinstance(entries, list) or not entries:
            raise ManifestError(f"Required inventory {name!r} must be non-empty")
        for index, entry in enumerate(entries):
            if not isinstance(entry, dict) or set(entry) != {"path", "size", "sha256"}:
                raise ManifestError(f"Invalid {name} entry at index {index}")
            path = entry["path"]
            parts = _relative_parts(path)
            key = _normalize_key(path)
            if key in seen:
                raise ManifestError(f"Duplicate or ambiguous manifest path: {path}")
            seen.add(key)
            if name == "source" and parts[: len(root_parts)] != root_parts:
                raise ManifestError(f"Source entry escapes release_root: {path}")
            size = entry["size"]
            if isinstance(size, bool) or not isinstance(size, int) or size < 0:
                raise ManifestError(f"Invalid size for {path}: {size!r}")
            digest = entry["sha256"]
            if not isinstance(digest, str) or not SHA256_RE.fullmatch(digest):
                raise ManifestError(f"Invalid SHA-256 for {path}")


def sha256_stream(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _inside(root: Path, candidate: Path) -> bool:
    try:
        candidate.relative_to(root)
    except ValueError:
        return False
    return True


def _resolve_allowed(repo_root: Path, raw: str) -> Path:
    parts = _relative_parts(raw)
    candidate = repo_root.joinpath(*parts)
    try:
        resolved = candidate.resolve(strict=True)
    except FileNotFoundError:
        return candidate
    if not _inside(repo_root, resolved):
        raise ManifestError(f"Resolved path escapes repository root: {raw}")
    return resolved


def verify(repo_root: Path, manifest_path: Path, mode: str) -> dict[str, Any]:
    if mode not in {"source", "local-artifacts"}:
        raise ManifestError(f"Unsupported mode: {mode}")
    try:
        root = repo_root.resolve(strict=True)
    except FileNotFoundError as exc:
        raise ManifestError(f"Repository root does not exist: {repo_root}") from exc
    if not root.is_dir():
        raise ManifestError(f"Repository root is not a directory: {root}")

    try:
        manifest_resolved = manifest_path.resolve(strict=True)
    except FileNotFoundError as exc:
        raise ManifestError(f"Manifest does not exist: {manifest_path}") from exc
    if not _inside(root, manifest_resolved):
        raise ManifestError("Manifest path escapes repository root")

    data = load_manifest(manifest_resolved)
    validate_manifest(data)
    selected = list(data["inventories"]["source"])
    if mode == "local-artifacts":
        selected.extend(data["inventories"]["local_artifacts"])

    checks: list[dict[str, Any]] = []
    errors: list[str] = []
    for entry in selected:
        raw = entry["path"]
        try:
            path = _resolve_allowed(root, raw)
        except ManifestError as exc:
            errors.append(str(exc))
            checks.append({"path": raw, "status": "FAIL", "reason": str(exc)})
            continue
        if not path.exists():
            reason = "missing required file"
            errors.append(f"{raw}: {reason}")
            checks.append({"path": raw, "status": "FAIL", "reason": reason})
            continue
        if not path.is_file():
            reason = "required path is not a regular file"
            errors.append(f"{raw}: {reason}")
            checks.append({"path": raw, "status": "FAIL", "reason": reason})
            continue
        actual_size = path.stat().st_size
        actual_hash = sha256_stream(path)
        reasons: list[str] = []
        if actual_size != entry["size"]:
            reasons.append(f"size {actual_size} != {entry['size']}")
        if actual_hash != entry["sha256"]:
            reasons.append(f"sha256 {actual_hash} != {entry['sha256']}")
        status = "FAIL" if reasons else "PASS"
        if reasons:
            errors.append(f"{raw}: {'; '.join(reasons)}")
        checks.append(
            {
                "path": raw,
                "status": status,
                "size": actual_size,
                "sha256": actual_hash,
                **({"reason": "; ".join(reasons)} if reasons else {}),
            }
        )

    local_count = len(data["inventories"]["local_artifacts"])
    return {
        "schema_version": SCHEMA_VERSION,
        "mode": mode,
        "status": "PASS" if not errors else "FAIL",
        "scope": (
            "Source package verified; external experimental artifacts were not checked."
            if mode == "source"
            else "Source package and allowlisted local experimental artifacts verified."
        ),
        "checked_count": len(checks),
        "passed_count": sum(item["status"] == "PASS" for item in checks),
        "failed_count": sum(item["status"] == "FAIL" for item in checks),
        "external_artifacts_not_checked": mode == "source",
        "skipped_local_artifact_count": local_count if mode == "source" else 0,
        "checks": checks,
        "errors": errors,
    }


def _print_human(result: dict[str, Any]) -> None:
    print(f"Module 4 verification: {result['status']}")
    print(f"Mode: {result['mode']}")
    print(f"Scope: {result['scope']}")
    print(
        f"Checks: {result['passed_count']}/{result['checked_count']} PASS; "
        f"{result['failed_count']} FAIL"
    )
    if result["external_artifacts_not_checked"]:
        print(
            "Local experimental artifacts: NOT CHECKED "
            f"({result['skipped_local_artifact_count']} allowlisted entries skipped)"
        )
    for item in result["checks"]:
        suffix = f" — {item['reason']}" if "reason" in item else ""
        print(f"[{item['status']}] {item['path']}{suffix}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, required=True)
    parser.add_argument(
        "--manifest",
        default=DEFAULT_MANIFEST,
        help="Repository-relative manifest path",
    )
    parser.add_argument(
        "--mode", choices=("source", "local-artifacts"), required=True
    )
    parser.add_argument(
        "--json", action="store_true", dest="json_output", help="Emit JSON only"
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    repo_root = args.repo_root
    try:
        root = repo_root.resolve(strict=True)
        manifest_parts = _relative_parts(args.manifest)
        manifest_path = root.joinpath(*manifest_parts)
        result = verify(root, manifest_path, args.mode)
    except (ManifestError, OSError) as exc:
        result = {
            "schema_version": SCHEMA_VERSION,
            "mode": args.mode,
            "status": "ERROR",
            "scope": "Verification did not start because configuration was invalid.",
            "checked_count": 0,
            "passed_count": 0,
            "failed_count": 0,
            "external_artifacts_not_checked": args.mode == "source",
            "skipped_local_artifact_count": 0,
            "checks": [],
            "errors": [str(exc)],
        }
        if args.json_output:
            print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
        else:
            _print_human(result)
            print(f"Manifest/configuration error: {exc}", file=sys.stderr)
        return EXIT_USAGE_OR_MANIFEST_ERROR

    if args.json_output:
        print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        _print_human(result)
    return EXIT_PASS if result["status"] == "PASS" else EXIT_VERIFICATION_FAILED


if __name__ == "__main__":
    raise SystemExit(main())
