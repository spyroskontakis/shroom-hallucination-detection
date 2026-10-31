"""Pinned, read-only source contexts for the current repository layout.

This is not an experiment launcher. H1 authenticates the public Git snapshot;
H2 authenticates separately reviewed current files. Neither replaces H0 inputs.
The existing canonical H2-P0 validator owns schema, path and evidence checks.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path
import subprocess
import sys

VERSION = "shroom-repository-source-context-v1"
CATALOG = "project_records/current_layout/repository_sources_v1.json"
CATALOG_SHA256 = "1fe827210ec604b85166d6842807b98171ab7f2adf380f9f1eed97f8c45b79e4"
SHARED = "research/shared_tools/canonical_execution_context.py"
SHARED_SHA256 = "c668cce4282d6865373f50525fc78fb5a87b5be14463cc4fef3e93284b326247"
BASELINE = "11822d92070cd29360445cb4dacd8d110c655248"
BASE_TREE = "81690aef257042354b6886f145919ae794e941ee"


def _digest(raw):
    import hashlib
    return hashlib.sha256(raw).hexdigest()


def load_shared_validator(root):
    # Pin before importing even this stdlib-only support module.
    path = Path(root) / SHARED
    for p in (path, *path.parents):
        if p.is_symlink() or (p.exists() and getattr(p.lstat(), "st_file_attributes", 0) & 1024):
            raise ValueError("Reparse source root rejected")
    raw = path.read_bytes()
    if _digest(raw) != SHARED_SHA256:
        raise ValueError("Shared validator identity mismatch")
    name = "_shroom_repository_source_h2p0_v1"
    # Never reuse a mutable or caller-supplied cached module.
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    previous = sys.modules.get(name)
    sys.modules[name] = module
    try:
        exec(compile(raw, str(path), "exec"), module.__dict__)
    finally:
        if previous is None:
            sys.modules.pop(name, None)
        else:
            sys.modules[name] = previous
    return module


class GitSnapshot:
    """Read only the fixed H1 tree; never checkout/materialize or execute it."""
    mode = "H1_SNAPSHOT"
    baseline_commit = BASELINE
    baseline_tree = BASE_TREE

    def __init__(self, root, shared):
        self.root = shared.reject_links(Path(root))
        self.shared = shared
        tree = self._git("rev-parse", BASELINE + "^{tree}").decode("ascii").strip()
        if tree != BASE_TREE:
            raise ValueError("Historical Git tree mismatch")

    def _git(self, *args):
        p = subprocess.run(["git", "--no-optional-locks", *args], cwd=self.root,
                           stdin=subprocess.DEVNULL, capture_output=True, timeout=30,
                           env={**__import__("os").environ, "GIT_NO_REPLACE_OBJECTS": "1"})
        if p.returncode:
            raise ValueError("Required historical Git evidence unavailable")
        return p.stdout

    def read(self, relative):
        relative = self.shared.logical_path(relative)
        # Fixed commit and validated logical path; no caller-provided revisions.
        return self._git("cat-file", "blob", BASELINE + ":" + relative)


class SourceContext:
    def __init__(self, root, *, version=VERSION, catalog_sha256=CATALOG_SHA256):
        root = Path(root)
        if version != VERSION or catalog_sha256 != CATALOG_SHA256:
            raise ValueError("Unrecognized independent context pin/version")
        if not root.is_absolute() or ".." in root.parts:
            raise ValueError("Explicit absolute source root required")
        self.h = load_shared_validator(root)
        self.root = self.h.reject_links(root)
        self.catalog = self.h.load_catalog(self.root / CATALOG, expected_sha256=CATALOG_SHA256)
        if self.catalog["baseline"] != {"commit": BASELINE, "tree": BASE_TREE}:
            raise ValueError("Historical context substitution")
        self.entries = {x["historical_path"]: x for x in self.catalog["artifacts"]}

    def check(self, original_path, *, mode, evidence=None):
        """An explicit mode is mandatory; no H0 -> H1/H2 fallback exists."""
        key = self.h.logical_path(original_path)
        if key not in self.entries:
            raise ValueError("Unknown source identity")
        item = self.entries[key]
        if mode not in {"H1_SNAPSHOT", "H2_CURRENT"}:
            raise ValueError("Use an explicit frozen contract for H0 requirements")
        if evidence is None:
            evidence = (GitSnapshot(self.root, self.h) if mode == "H1_SNAPSHOT" else
                        self.h.FileEvidence(self.root, mode=mode,
                                            baseline_commit=BASELINE, baseline_tree=BASE_TREE))
        return self.h.verify_artifact(self.catalog, item["id"], mode=mode, evidence=evidence).as_dict()

    def frozen_inputs(self, contract, original_root):
        """Validate the original independently pinned H0 claims, without writes."""
        evidence = self.h.FileEvidence(original_root, mode="H0_REPLAY",
                                      baseline_commit=BASELINE, baseline_tree=BASE_TREE)
        return self.h.verify_contract(self.catalog, contract, mode="H0_REPLAY", evidence=evidence)

    def audit_plan(self, originals, *, run_dir, cache_dir, temporary_dir):
        """Pure output ownership planning for metadata audits, never experiments."""
        if not originals or len(set(originals)) != len(originals):
            raise ValueError("Nonempty unique input identities required")
        inputs = []
        for original in originals:
            result = self.check(original, mode="H2_CURRENT")
            if result["status"] != "PASS":
                raise ValueError("Current evidence is missing or unreviewed")
            inputs.append(self.h.confined(self.root, self.entries[original]["target_path"]))
        roots = [self.h.reject_links(Path(p)) for p in (run_dir, cache_dir, temporary_dir)]
        for i, a in enumerate(roots):
            for b in roots[i + 1:]:
                if a == b or a.is_relative_to(b) or b.is_relative_to(a):
                    raise ValueError("Output/cache/temporary roots overlap")
        plans = [self.h.plan_run(p, source_roots=[self.root], input_paths=inputs,
                                 output_names=[name]) for p, name in
                 zip(roots, ("source_audit.json", "audit_cache.json", "audit_tmp.json"))]
        return {"version": VERSION, "plans": plans, "created": False,
                "execution_permitted": False, "runtime_status": "NOT VERIFIED"}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--original", action="append", required=True)
    parser.add_argument("--mode", choices=["H1_SNAPSHOT", "H2_CURRENT"], required=True)
    args = parser.parse_args(argv)
    try:
        context = SourceContext(args.root)
        checks = [context.check(p, mode=args.mode) for p in args.original]
        passed = all(x["status"] == "PASS" for x in checks)
        print(json.dumps({"version": VERSION, "checks": checks,
                          "status": "PASS" if passed else "FAIL",
                          "execution_permitted": False, "runtime_status": "NOT VERIFIED"}))
        return 0 if passed else 1
    except (ValueError, OSError, subprocess.SubprocessError):
        # Do not echo physical paths, private inputs or subprocess diagnostics.
        print(json.dumps({"status": "FAIL", "reason": "CONTEXT_VALIDATION_FAILED",
                          "execution_permitted": False}))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
