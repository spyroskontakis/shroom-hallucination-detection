"""Additive v2 source inventory; reuse the unchanged v1/H2-P0 verifier.

Adds four relocated final E11 outputs and fifteen E9-B/E10 fold logs. The
original finalization, variant and output-directory gates remain at their
original paths, with unchanged bytes.
This does not run or independently confirm the reported scientific results.
"""
from __future__ import annotations
import importlib.util
from pathlib import Path

VERSION = "shroom-repository-source-context-v2"
CATALOG = "project_records/current_layout/repository_sources_v2.json"
CATALOG_SHA256 = "5af5b7f229b4243011ccf84e0e2af35b1e9f2e21ecac3f40493018bef058dcf0"
BASE_ADAPTER = "research/shared_tools/repository_source_context_v1.py"
BASE_ADAPTER_SHA256 = "b43735374a2eacfed6af53f1fb4ad2ec911ebcd569b1315999b8bc2b6c9dffc1"


def context(root, *, version=VERSION, catalog_sha256=CATALOG_SHA256):
    """Construct v2 by binding the v1 implementation to the independently pinned successor."""
    import hashlib
    root = Path(root)
    if version != VERSION or catalog_sha256 != CATALOG_SHA256:
        raise ValueError("Unknown source context version/pin")
    if not root.is_absolute() or ".." in root.parts:
        raise ValueError("Explicit absolute source root required")
    path = root / BASE_ADAPTER
    for p in (path, *path.parents):
        if p.is_symlink() or (p.exists() and getattr(p.lstat(), "st_file_attributes", 0) & 1024):
            raise ValueError("Reparse source rejected")
    raw = path.read_bytes()
    if hashlib.sha256(raw).hexdigest() != BASE_ADAPTER_SHA256:
        raise ValueError("Base implementation identity mismatch")
    spec = importlib.util.spec_from_file_location("_shroom_source_context_v2_base", path)
    base = importlib.util.module_from_spec(spec)
    exec(compile(raw, str(path), "exec"), base.__dict__)
    # A fresh module namespace; the released v1 module/config/catalog is untouched.
    base.VERSION = VERSION
    base.CATALOG = CATALOG
    base.CATALOG_SHA256 = CATALOG_SHA256
    return base.SourceContext(root, version=VERSION, catalog_sha256=CATALOG_SHA256)


def main(argv=None):
    import argparse
    import json
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--original", action="append", required=True)
    parser.add_argument("--mode", choices=["H1_SNAPSHOT", "H2_CURRENT"], required=True)
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
