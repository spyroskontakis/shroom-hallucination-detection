"""Phase24 source inventory binding; all validation is reused from pinned v2.

H1 and H2 remain separate. No experiment launcher or evaluator is implemented.
"""
from __future__ import annotations
import hashlib
import importlib.util
from pathlib import Path

VERSION = "shroom-repository-source-context-v3"
CATALOG = "project_records/current_layout/repository_sources_v3.json"
CATALOG_SHA256 = "899d046f3132a0302a4fbb7d3493885109efd0103975bc05bb9a007fbc6cb349"
BASE_ADAPTER = "research/shared_tools/repository_source_context_v2.py"
BASE_ADAPTER_SHA256 = "9ca4043b96ec71380b84d8328ad5fe715c359a83eb5f5cfe96c932a70cbf6351"


def context(root, *, version=VERSION, catalog_sha256=CATALOG_SHA256):
    if version != VERSION or catalog_sha256 != CATALOG_SHA256:
        raise ValueError("Unknown source context version/pin")
    root = Path(root)
    if not root.is_absolute() or ".." in root.parts:
        raise ValueError("Explicit absolute source root required")
    path = root / BASE_ADAPTER
    for p in (path, *path.parents):
        if p.is_symlink() or (p.exists() and getattr(p.lstat(), "st_file_attributes", 0) & 1024):
            raise ValueError("Reparse source rejected")
    raw = path.read_bytes()
    if hashlib.sha256(raw).hexdigest() != BASE_ADAPTER_SHA256:
        raise ValueError("Reused implementation identity mismatch")
    spec = importlib.util.spec_from_file_location("_shroom_source_context_v3_binding", path)
    delegate = importlib.util.module_from_spec(spec)
    exec(compile(raw, str(path), "exec"), delegate.__dict__)
    # Bind a fresh namespace to this explicitly versioned, independently pinned
    # catalog. The v2 source, catalog and existing callers are not modified.
    delegate.VERSION = VERSION
    delegate.CATALOG = CATALOG
    delegate.CATALOG_SHA256 = CATALOG_SHA256
    return delegate.context(root, version=VERSION, catalog_sha256=CATALOG_SHA256)


def main(argv=None):
    import argparse
    import json
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", required=True, type=Path)
    parser.add_argument("--original", action="append", required=True)
    parser.add_argument("--mode", choices=("H1_SNAPSHOT", "H2_CURRENT"), required=True)
    args = parser.parse_args(argv)
    try:
        current = context(args.root)
        checks = [current.check(p, mode=args.mode) for p in args.original]
        passed = all(x["status"] == "PASS" for x in checks)
        print(json.dumps({"version": VERSION, "checks": checks, "status": "PASS" if passed else "FAIL",
                          "execution_permitted": False, "runtime_status": "NOT VERIFIED"}))
        return 0 if passed else 1
    except (ValueError, OSError):
        print(json.dumps({"status": "FAIL", "reason": "CONTEXT_VALIDATION_FAILED", "execution_permitted": False}))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
