"""Read-only, offline repository checks; no experiment code is imported.

Run with -B. Exit codes: 0 checks pass, 1 actual failure (including known
historical FAILs), 2 incomplete optional verification, 3 invalid invocation.
Use --tests only with a new external --scratch directory.
"""
from __future__ import annotations
import argparse
import ast
import collections
import hashlib
import importlib.util
import json
import os
from pathlib import Path, PurePosixPath
import re
import subprocess
import sys
import urllib.parse

INDEX = "project_records/current_layout/repository_verification_index.json"
INDEX_SHA256 = "d42349301df782f3b67fc82d2d6eb7008a387a16737296cdf2f3dd9407089c12"
BASE = "11822d92070cd29360445cb4dacd8d110c655248"
E11 = "RAG/results/phase3_e11_task_adaptation/E11_DATA_AUDIT.md"
sys.dont_write_bytecode = True


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def git(root, *args, data=None):
    env = dict(os.environ)
    env.update(GIT_NO_LAZY_FETCH="1", GIT_TERMINAL_PROMPT="0", GIT_NO_REPLACE_OBJECTS="1")
    result = subprocess.run(["git", "--no-optional-locks", *args], cwd=root,
                            input=data, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if result.returncode:
        raise ValueError("Read-only Git query failed: " + args[0])
    return result.stdout


def logical(value):
    if not isinstance(value, str) or not value or "\\" in value or "\0" in value:
        raise ValueError("Invalid repository path")
    path = PurePosixPath(value)
    if path.is_absolute() or str(path) != value or any(p in ("..", ".git") for p in path.parts) or ":" in value:
        raise ValueError("Unsafe repository path")
    return value


def reject_links(path):
    path = Path(path).absolute()
    for item in (path, *path.parents):
        if item.is_symlink() or item.is_junction():
            raise ValueError("Links/reparse points are not allowed")
    return path


def root_of(path):
    for parent in (Path(path).absolute(), *Path(path).absolute().parents):
        if (parent / INDEX).is_file() and (parent / ".git").exists():
            return reject_links(parent)
    raise ValueError("Repository markers not found")


def load_index(root):
    raw = (root / INDEX).read_bytes()
    if digest(raw) != INDEX_SHA256:
        raise ValueError("Verification index identity mismatch")
    value = json.loads(raw)
    entries = value["migration_destinations"]
    if len(entries) != 790 or len({x["original"] for x in entries}) != 790:
        raise ValueError("Incomplete migration map")
    for row in entries:
        logical(row["original"]); logical(row["destination"])
    return value


def load_compatibility(root, index):
    item = index["compatibility"]
    path = reject_links(root / logical(item["path"]))
    if digest(path.read_bytes()) != item["sha256"]:
        raise ValueError("Compatibility validator identity mismatch")
    spec = importlib.util.spec_from_file_location("_shroom_repository_verification", path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module, module.Catalog(root)


def git_inventory(root, revision="HEAD"):
    result = {}
    for row in git(root, "ls-tree", "-rz", revision).split(b"\0"):
        if not row:
            continue
        info, name = row.split(b"\t", 1)
        mode, kind, oid = info.decode().split()
        name = logical(name.decode("utf-8"))
        if kind != "blob" or mode not in ("100644", "100755"):
            raise ValueError("Unsupported public Git entry")
        result[name] = {"git_blob": oid, "mode": mode}
    return result


def git_blobs(root, objects):
    # Object IDs, rather than interpolated shell commands or filenames.
    payload = ("\n".join(objects) + "\n").encode()
    raw = git(root, "cat-file", "--batch", data=payload)
    at = 0
    values = []
    for expected in objects:
        end = raw.index(b"\n", at)
        oid, kind, size = raw[at:end].decode().split()
        if oid != expected or kind != "blob":
            raise ValueError("Git blob response mismatch")
        at = end + 1; count = int(size)
        values.append(raw[at:at+count]); at += count + 1
    if at != len(raw):
        raise ValueError("Unexpected Git blob bytes")
    return values


def publication_inventory(root, projected=None, pin=None):
    if projected is None:
        return git_inventory(root), "COMMITTED_HEAD"
    raw = reject_links(projected).read_bytes()
    if not pin or digest(raw) != pin:
        raise ValueError("Projected publication manifest needs exact SHA-256")
    rows = json.loads(raw)["files"]
    values = {}
    for row in rows:
        name = logical(row["path"])
        if name in values:
            raise ValueError("Duplicate public file")
        if not re.fullmatch("[0-9a-f]{64}", row["sha256"]):
            raise ValueError("Invalid projected identity")
        values[name] = row
    return values, "PROJECTED_LOCAL_SNAPSHOT"


def local_links(name, text, inventory):
    """GitHub relative file links. Historical failures remain actual failures."""
    rows = []
    clean = re.sub(r"(?ms)^ *\x60{3}.*?^ *\x60{3}[^\n]*", "", text)
    patterns = [
        r"(?<!!)\[[^\]\n]*\]\((<[^>]+>|[^)\s]+)(?:\s+[^)]*)?\)",
        r"(?m)^\s*\[[^\]]+\]:\s*(<[^>]+>|\S+)"
    ]
    for pattern in patterns:
        for match in re.finditer(pattern, clean):
            target = match.group(1).strip("<>")
            parsed = urllib.parse.urlsplit(target)
            if parsed.scheme or parsed.netloc or not parsed.path:
                continue
            import posixpath
            path = urllib.parse.unquote(parsed.path)
            dest = posixpath.normpath(
                path.lstrip("/") if path.startswith("/") else
                posixpath.join(posixpath.dirname(name), path))
            line = clean[:match.start()].count("\n") + 1
            rows.append({"source": name, "line": line, "target": target,
                         "resolved": dest, "status": "PASS" if dest in inventory or
                         any(x.startswith(dest.rstrip("/")+"/") for x in inventory) else "FAIL"})
    return rows


def syntax_status(name, raw, exceptions):
    if name.endswith(".py"):
        try:
            ast.parse(raw, filename=name)
        except SyntaxError as error:
            if exceptions.get(name) == digest(raw):
                return {"status": "KNOWN_HISTORICAL_EXCEPTION", "historical_status": "FAIL",
                        "line": error.lineno, "kind": "preserved_original_syntax_error"}
            return {"status": "FAIL", "line": error.lineno, "kind": "python_syntax"}
    elif name.endswith(".ipynb"):
        try:
            value = json.loads(raw)
            if value.get("nbformat") != 4 or not isinstance(value["cells"], list):
                raise ValueError("Invalid notebook shape")
            for cell in value["cells"]:
                if cell["cell_type"] not in ("code", "markdown", "raw"):
                    raise ValueError("Invalid notebook cell")
                if not isinstance(cell["source"], (str, list)):
                    raise ValueError("Invalid cell source")
            # Historical cells include notebook magics; JSON validity is not runtime PASS.
        except (ValueError, KeyError, TypeError):
            return {"status": "FAIL", "kind": "notebook_json"}
    elif name.endswith(".json"):
        try:
            json.loads(raw)
        except (ValueError, UnicodeError):
            return {"status": "FAIL", "kind": "json"}
    return {"status": "PASS"}


def privacy_findings(name, raw):
    """High-confidence signals only. Never return secret values."""
    rows = []
    forbidden = (".env", "credentials.json", "id_rsa", "id_ed25519")
    path = PurePosixPath(name)
    if path.name in forbidden or path.suffix.lower() in (".safetensors", ".ckpt", ".pt", ".pth", ".pkl", ".parquet"):
        rows.append({"file": name, "kind": "private_or_runtime_artifact", "status": "FAIL"})
    try:
        text = raw.decode("utf-8")
    except UnicodeError:
        return rows
    if name.endswith((".json", ".ipynb")):
        # JSON escape sequences must not hide personal filesystem paths.
        try:
            text += "\n" + str(json.loads(text))
        except ValueError:
            pass
    rules = {
        "private_key": r"-----BEGIN (?:RSA |OPENSSH |EC )?PRIVATE KEY-----",
        "provider_token": r"\b(?:gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{40,}|hf_[A-Za-z0-9]{30,}|sk-[A-Za-z0-9]{30,}|AIza[A-Za-z0-9_-]{30,})\b",
        "personal_machine_path": r"(?i)(?:[A-Z]:[\\/]+Users[\\/]+(?!PUBLIC\b|USER\b|USERNAME\b|<|YOUR_)[A-Za-z0-9._-]+|/home/(?!user\b|ubuntu\b|runner\b|<)[A-Za-z0-9._-]+|/Users/[A-Za-z0-9._-]+)",
    }
    for kind, pattern in rules.items():
        if re.search(pattern, text):
            rows.append({"file": name, "kind": kind, "status": "FAIL"})
    return rows


def verify(root, index, inventory, scope):
    rows = []
    def add(check, status, **data):
        rows.append({"check": check, "status": status, **data})
    module, catalog = load_compatibility(root, index)
    public = set(inventory)
    for name, item in inventory.items():
        path = reject_links(root / logical(name))
        if not path.is_file():
            add("public_file", "FAIL", file=name, reason="missing")
            continue
        raw = path.read_bytes()
        oid = hashlib.sha1(b"blob "+str(len(raw)).encode()+b"\0"+raw).hexdigest()
        good = (digest(raw) == item["sha256"]) if "sha256" in item else oid == item["git_blob"]
        if not good:
            add("public_file", "FAIL", file=name, reason="changed")
    originals = git_inventory(root, BASE)
    paths = [x["original"] for x in index["migration_destinations"]]
    data = git_blobs(root, [originals[p]["git_blob"] for p in paths])
    counts = collections.Counter()
    for projection, original in zip(index["migration_destinations"], data):
        old = projection["original"]; item = catalog.entries[old]
        if item["h1_sha256"] != digest(original) or item["h1_blob"] != originals[old]["git_blob"]:
            add("original_identity", "FAIL", file=old)
        current = item["current"]
        same = item["sha256"] == item["h1_sha256"]
        status = "MIGRATED_BYTE_IDENTICAL" if same else "MIGRATED_ADAPTED"
        if current != projection["destination"]:
            if current != old:
                add("destination", "FAIL", file=old)
            status = "BLOCKED_HISTORICAL_METADATA" if old.endswith(".ipynb") else "BLOCKED_IMMUTABLE_CONTRACT"
        counts[status] += 1
        if current not in public:
            add("current_public_source", "FAIL", file=current)
        if old != current and (root/old).exists():
            add("duplicate_original", "FAIL", file=old)
    add("migration_identity", "PASS", entries=len(paths), counts=dict(counts))
    for name, pin in index["protected_files"].items():
        if digest((root/name).read_bytes()) != pin:
            add("protected_file", "FAIL", file=name)
    syntax = []
    links = []
    privacy = []
    for name in sorted(inventory):
        path = root/name
        if not path.is_file():
            continue
        raw = path.read_bytes()
        result = syntax_status(name, raw, index["syntax_exceptions"])
        if result["status"] != "PASS":
            syntax.append({"file": name, **result})
        if name.endswith(".md"):
            links.extend(local_links(name, raw.decode("utf-8-sig"), public))
        privacy.extend(privacy_findings(name, raw))
    add("syntax_and_json", "FAIL" if any(x["status"]=="FAIL" for x in syntax) else "PASS",
        files=len(inventory), exceptions=syntax)
    broken = [x for x in links if x["status"]=="FAIL"]
    add("local_markdown_links", "FAIL" if broken else "PASS", links=len(links), broken=broken,
        note="Frozen historical links are reported as real FAIL, never suppressed.")
    add("public_safety_signals", "FAIL" if privacy else "PASS", findings=privacy,
        scope="High-confidence scanner; complements reviewed release inventory, not a guarantee.")
    architecture = []
    for group in index["experiments"]:
        missing = [p for p in group["sources"]+group.get("configurations", []) if p not in public]
        architecture.append({"experiment": group["id"], "status": "FAIL" if missing else "PASS",
                             "missing": missing, "execution_scope": group["execution_scope"]})
    add("architecture_inventory", "FAIL" if any(x["status"]=="FAIL" for x in architecture) else "PASS",
        experiments=architecture)
    # Read raw H0 checksum lists against authentic Git blobs, without generating a snapshot.
    h0 = []
    for logical_list in index["historical_checksums"]:
        raw = catalog.current(logical_list).read_bytes()
        source = git_blobs(root, [originals[logical_list]["git_blob"]])[0]
        if raw != source:
            raise ValueError("Historical checksum list changed")
        for line in raw.decode().splitlines():
            expected, filename = line.split(None, 1)
            target = logical_list.rsplit("/", 1)[0] + "/" + filename.strip()
            historical = git_blobs(root, [originals[target]["git_blob"]])[0]
            actual = digest(historical)
            if actual != expected:
                h0.append({"target": target, "status": "FAIL", "expected_h0_sha256": expected,
                           "observed_public_h1_sha256": actual})
    add("historical_h0_checksums", "KNOWN_HISTORICAL_EXCEPTION" if h0 else "PASS",
        historical_status="FAIL" if h0 else "PASS", failures=h0,
        runtime="HISTORICAL_RUNTIME_NOT_VERIFIED")
    repairs = []
    for repair in index["historical_permalinks"]:
        document = root/repair["source"]
        url = repair["url"]
        match = re.search(r"/blob/([0-9a-f]{40})/(.+)", url)
        present = url in document.read_text(encoding="utf-8")
        if match:
            git(root, "cat-file", "-e", match.group(1)+":"+urllib.parse.unquote(match.group(2)))
        repairs.append({"source": repair["source"], "status":"PASS" if present and match else "FAIL"})
    add("historical_permalink_repairs", "FAIL" if any(x["status"]=="FAIL" for x in repairs) else "PASS",
        repairs=repairs)
    add("historical_runtime", "NOT_VERIFIED",
        reason="Missing original datasets, model assets, run markers and private preservation evidence.")
    add("native_workbook", "NOT_VERIFIED", reason="Native addon unavailable: ERR_DLOPEN_DISABLED; unit fixtures do not validate the native workbook.")
    return {"scope":scope, "files":len(inventory), "checks":rows}


def status_code(result):
    rows = result["checks"]
    if any(x["status"]=="FAIL" or x.get("historical_status")=="FAIL" for x in rows):
        return 1
    if any(x["status"] in ("NOT_VERIFIED", "BLOCKED_MISSING_ARTIFACT") for x in rows):
        return 2
    return 0


def safe_environment(work):
    # Do not pass provider credentials or Python startup overrides to test workers.
    keep = ("SYSTEMROOT", "WINDIR", "PATH", "PATHEXT", "COMSPEC", "SYSTEMDRIVE")
    env = {key: os.environ[key] for key in keep if key in os.environ}
    for name in ("TEMP", "TMP", "TMPDIR", "USERPROFILE", "XDG_CACHE_HOME",
                 "HF_HOME", "HF_HUB_CACHE", "TRANSFORMERS_CACHE", "TORCH_HOME",
                 "MPLCONFIGDIR", "NUMBA_CACHE_DIR", "NLTK_DATA", "JUPYTER_CONFIG_DIR",
                 "IPYTHONDIR", "HF_DATASETS_CACHE", "PIP_CACHE_DIR", "TRITON_CACHE_DIR"):
        path = work/name.lower()
        path.mkdir()
        env[name] = str(path)
    env.update(PYTHONDONTWRITEBYTECODE="1", PYTHONNOUSERSITE="1",
               HF_HUB_OFFLINE="1", TRANSFORMERS_OFFLINE="1", HF_DATASETS_OFFLINE="1",
               HF_HUB_DISABLE_TELEMETRY="1", WANDB_DISABLED="true",
               TOKENIZERS_PARALLELISM="false", CUDA_VISIBLE_DEVICES="")
    return env


def make_junction(work):
    target = work/"junction_target"; target.mkdir()
    link = work/"junction"
    if os.name == "nt":
        # Fixed native PowerShell command with JSON data; no path interpolation,
        # script-policy changes, shell-built deletion or external process windows.
        env = dict(os.environ)
        env["SHROOM_JUNCTION_SPEC"] = json.dumps({"link": str(link), "target": str(target)})
        command = ("$ErrorActionPreference='Stop'; "
                   "$p=ConvertFrom-Json $env:SHROOM_JUNCTION_SPEC; "
                   "New-Item -ItemType Junction -Path $p.link -Target $p.target | Out-Null")
        subprocess.run(["powershell.exe","-NoProfile","-NonInteractive","-Command",command],env=env,check=True,
                       stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    else:
        link.symlink_to(target, target_is_directory=True)
    if link.resolve()!=target.resolve():
        raise ValueError("Reparse fixture could not be established")
    return link


def materialize(root, work, commit, expected_tree):
    if git(root, "rev-parse", commit+"^{tree}").decode().strip()!=expected_tree:
        raise ValueError("Historical test tree mismatch")
    inventory = git_inventory(root, commit)
    values = git_blobs(root, [x["git_blob"] for x in inventory.values()])
    dest = work
    dest.mkdir()
    for (name, spec), raw in zip(inventory.items(), values):
        path = dest/name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(raw)
        path.chmod(0o444)
    return dest


def run_tests(root, index, scratch, *, third_party_python=None, node=None):
    """Only reviewed source-IO/unit tests, never experiment entry points."""
    if str(scratch).startswith(("\\\\", "//")):
        raise ValueError("Network scratch paths are not allowed in offline verification")
    if not Path(scratch).is_absolute():
        raise ValueError("Scratch must be an explicit absolute path")
    scratch = reject_links(scratch)
    if not scratch.is_absolute() or scratch.exists() or scratch.is_relative_to(root):
        raise ValueError("Tests need a NEW absolute scratch directory outside the repository")
    for parent in scratch.parents:
        if (parent/".git").exists():
            raise ValueError("Scratch must be outside all Git repositories")
    scratch.mkdir(parents=True)
    module, catalog = load_compatibility(root, index)
    snapshots = {}
    for name, spec in index["test_snapshots"].items():
        snapshots[name] = materialize(root, scratch/("snapshot_"+name), spec["commit"], spec["tree"])
    for name in ("H1","P26"):
        catalog.snapshot(name, snapshots[name])
    worker = scratch/"worker.py"
    worker.write_text(WORKER,encoding="utf-8")
    results = []
    for suite in index["test_suites"]:
        print("Testing "+suite["name"]+" ["+suite["context"]+"]",file=sys.stderr,flush=True)
        source_root = root if suite["context"]=="CURRENT" else snapshots[suite["context"]]
        test = source_root/suite["path"]
        row = {"suite":suite["name"], "expected":suite["cases"],
               "context":suite["context"], "execution":"FRESHLY_EXECUTED"}
        if digest(test.read_bytes()) != suite["sha256"]:
            raise ValueError("Test source identity mismatch: "+suite["name"])
        work = scratch/suite["name"]; work.mkdir()
        env = safe_environment(work)
        env.update(SHROOM_TEST_SCRATCH=str(work), SHROOM_SNAPSHOT_H1=str(snapshots["H1"]),
                   SHROOM_SNAPSHOT_P26=str(snapshots["P26"]), SHROOM_H2_TEST_SCRATCH=str(work))
        pinpaths = {"SUPPORT":"research/shared_tools/canonical_execution_context.py",
                    "CATALOG":"project_records/current_layout/canonical_relocation_v1.json",
                    "VERIFIER":"research/data_and_evaluation/canonical/verification/verify_e10_e11_lineage.py"}
        for key, relative in pinpaths.items():
            path = root/relative
            env["SHROOM_H2_"+key]=str(path)
            env["SHROOM_H2_"+key+"_SHA256"]=digest(path.read_bytes())
        env["SHROOM_H2_REPARSE_FIXTURE"]=str(make_junction(work))
        if suite.get("cli"):
            cli = source_root / suite["cli"]
            if digest(cli.read_bytes()) != suite["cli_sha256"]:
                raise ValueError("Module4 fixture CLI identity mismatch")
            env["SHROOM_TEST_CLI"] = str(cli)
            env["SHROOM_TEST_CLI_PIN"] = suite["cli_sha256"]
        python = sys.executable
        if suite.get("dependencies"):
            if third_party_python is None:
                row.update(execution="NOT_EXECUTED", status="BLOCKED_MISSING_ARTIFACT",
                           reason="Supply an already installed Python with beautifulsoup4 using --third-party-python.")
                results.append(row); continue
            python = str(reject_links(third_party_python))
            env["SHROOM_EXTRA_SITE"]=str(Path(python).parent/"Lib/site-packages")
        if suite["kind"]=="module1":
            sources = {str(root/p):digest((root/p).read_bytes()) for p in suite["sources"]}
            env.update(M1_TEST_SCRATCH=str(work), M1_NOTEBOOK_PINS=json.dumps(sources),
                       M1_REPARSE=env["SHROOM_H2_REPARSE_FIXTURE"])
            cmd = [python,"-I","-S","-B",str(test)]
        elif suite["kind"]=="module2":
            helper=root/suite["helper"]
            env.update(MODULE2_TEST_ROOT=str(work), MODULE2_HELPER=str(helper),
                       MODULE2_HELPER_PIN=digest(helper.read_bytes()),
                       MODULE2_REPARSE=env["SHROOM_H2_REPARSE_FIXTURE"])
            cmd = [python,"-I","-S","-B",str(test)]
        else:
            cmd = [python,"-I","-S","-B",str(worker),str(source_root),str(work),
                   str(test),str(suite["cases"])]
        p = subprocess.run(cmd,cwd=work,env=env,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        output = p.stdout.decode("utf-8","replace")
        try:
            detail = json.loads(output.strip().splitlines()[-1])
        except (ValueError, IndexError):
            detail = {"output":output[-6000:],"stderr":p.stderr.decode("utf-8","replace")[-6000:]}
        counted = detail.get("tests") == suite["cases"]
        skipped = detail.get("skipped", 0)
        row.update(exit=p.returncode,status="PASS" if p.returncode==0 and counted and not skipped else
                   "NOT_VERIFIED" if p.returncode==0 and counted else "FAIL",result=detail)
        results.append(row)
        print(row["status"]+": "+suite["name"],file=sys.stderr,flush=True)
    if node is not None:
        suite=index["node_test"]; work=scratch/"node_authoring";work.mkdir()
        env=safe_environment(work)
        test=root/suite["path"]; author=root/suite["author"]
        if digest(test.read_bytes())!=suite["sha256"]:
            raise ValueError("Node test source identity mismatch")
        preload=work/"deny_network.cjs";preload.write_text(NODE_GUARD)
        p=subprocess.run([str(node),"--permission","--allow-fs-read=*",
            "--allow-fs-write="+str(work),"--require",str(preload),str(test),
            str(author),str(work),str(snapshots["H1"]/suite["historical_author"]),str(root)],
            cwd=work,env=env,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        try: detail=json.loads(p.stdout.decode().strip().splitlines()[-1])
        except (ValueError,IndexError):detail={"output":p.stdout.decode("utf-8","replace")[-6000:],
                                              "stderr":p.stderr.decode("utf-8","replace")[-6000:]}
        results.append({"suite":"node_authoring", "expected":suite["cases"],"execution":"FRESHLY_EXECUTED",
                        "status":"PASS" if p.returncode==0 and detail.get("tests")==suite["cases"] else "FAIL","exit":p.returncode,"result":detail})
    else:
        results.append({"suite":"node_authoring","expected":index["node_test"]["cases"],
                        "execution":"NOT_EXECUTED","status":"BLOCKED_MISSING_ARTIFACT"})
    return results


WORKER = 'import os,sys,json,unittest,importlib.util,io\nfrom pathlib import Path\nROOT=Path(sys.argv[1]).resolve()\nWORK=Path(sys.argv[2]).resolve()\nTEST=Path(sys.argv[3]).resolve()\nEXPECTED=int(sys.argv[4])\nsys.dont_write_bytecode=True\n_permitted_cli=[None]\nevents={"writes":0,"network_attempts":0,"subprocess_attempts":0,"outside_writes":0,"ml_import_attempts":0}\ndef local(p):\n if isinstance(p,int):return\n p=Path(os.fsdecode(p)).resolve()\n if not p.is_relative_to(WORK):\n  events["outside_writes"]+=1\n  raise PermissionError("Write outside isolated scratch rejected")\ndef audit(event,args):\n if event=="open":\n  p,mode,flags=args\n  if (isinstance(mode,str) and any(c in mode for c in "wax+")) or (isinstance(flags,int) and flags&(os.O_WRONLY|os.O_RDWR|os.O_CREAT|os.O_TRUNC|os.O_APPEND)):\n   local(p);events["writes"]+=1\n elif event in ("os.mkdir","os.remove","os.rmdir","os.chmod","os.utime","os.truncate","os.chown"):\n  local(args[0]);events["writes"]+=1\n elif event in ("os.rename","os.replace","os.link","os.symlink"):\n  local(args[0]);local(args[1]);events["writes"]+=1\n elif event.startswith("socket."):\n  events["network_attempts"]+=1;raise PermissionError("Offline tests")\n elif event in ("subprocess.Popen","os.system","os.exec","os.posix_spawn"):\n  events["subprocess_attempts"]+=1\n  argv=args[1] if event=="subprocess.Popen" else []\n  cwd=args[2] if event=="subprocess.Popen" else None\n  base="11822d92070cd29360445cb4dacd8d110c655248"\n  approved=(isinstance(argv,(list,tuple)) and list(argv[:2])==["git","--no-optional-locks"] and\n            ((len(argv)==4 and argv[2]=="rev-parse" and argv[3]==base+"^{tree}") or\n             (len(argv)==5 and list(argv[2:4])==["cat-file","blob"] and str(argv[4]).startswith(base+":"))) and\n            cwd is not None and Path(cwd).resolve()==ROOT)\n  approved_cli=(_permitted_cli[0] is not None and\n       (argv==_permitted_cli[0][0] or argv==_permitted_cli[0][1]) and\n       cwd is not None and Path(cwd).resolve().is_relative_to(WORK))\n  if not (approved or approved_cli):raise PermissionError("Only pinned read-only Git or audited Module4 fixture CLI allowed")\n elif event=="import" and args[0].split(".")[0] in {"torch","transformers","sentence_transformers","modal","vertexai","google","tensorflow","bert_score"}:\n  events["ml_import_attempts"]+=1;raise ImportError("Model/cloud imports disabled")\nsys.addaudithook(audit)\nif os.environ.get("SHROOM_EXTRA_SITE"):\n sys.path.append(os.environ["SHROOM_EXTRA_SITE"])\n\nif "--cli" in sys.argv[5:]:\n import runpy,hashlib\n if TEST != Path(os.environ["SHROOM_TEST_CLI"]) or hashlib.sha256(TEST.read_bytes()).hexdigest()!=os.environ["SHROOM_TEST_CLI_PIN"]:\n  raise ValueError("Module4 CLI identity mismatch")\n sys.argv=[str(TEST),*sys.argv[6:]]\n runpy.run_path(str(TEST),run_name="__main__")\n raise SystemExit(0)\nif os.environ.get("SHROOM_TEST_CLI"):\n import subprocess,hashlib\n original_run=subprocess.run\n cli=Path(os.environ["SHROOM_TEST_CLI"])\n if hashlib.sha256(cli.read_bytes()).hexdigest()!=os.environ["SHROOM_TEST_CLI_PIN"]:\n  raise ValueError("Module4 CLI source changed")\n def guarded_run(argv, *args, **kwargs):\n  if (not isinstance(argv,(list,tuple)) or len(argv)!=9 or\n      list(argv[:3])!=[sys.executable,str(cli),"--repo-root"] or\n      list(argv[4:])!=["--manifest","RAG/module4_release_v1/RELEASE_MANIFEST.json","--mode","source","--json"] or\n      not Path(argv[3]).resolve().is_relative_to(WORK) or\n      not Path(kwargs.get("cwd","")).resolve().is_relative_to(WORK)):\n   raise PermissionError("Unreviewed test subprocess")\n  command=[sys.executable,"-I","-S","-B",str(Path(__file__).resolve()),str(ROOT),str(WORK),str(cli),"0","--cli",*argv[2:]]\n  _permitted_cli[0]=(subprocess.list2cmdline(command),command)\n  try:return original_run(command,*args,**kwargs)\n  finally:_permitted_cli[0]=None\n subprocess.run=guarded_run\nspec=importlib.util.spec_from_file_location("phase25_resume_test",TEST)\nmod=importlib.util.module_from_spec(spec)\nsys.modules[spec.name]=mod\nspec.loader.exec_module(mod)\nsuite=unittest.defaultTestLoader.loadTestsFromModule(mod)\nstream=io.StringIO()\nresult=unittest.TextTestRunner(stream=stream,verbosity=1).run(suite)\nok=result.wasSuccessful() and result.testsRun==EXPECTED\nprint(json.dumps({"tests":result.testsRun,"expected":EXPECTED,"pass":ok,"failures":len(result.failures),"errors":len(result.errors),"skipped":len(result.skipped),"events":events,"output":stream.getvalue()}))\nraise SystemExit(0 if ok else 1)\n'

NODE_GUARD = "const mod = require('node:module');\r\nconst denied = () => { throw new Error('OFFLINE_NETWORK_REJECTED'); };\r\nfor (const name of ['node:net','node:tls','node:http','node:https','node:http2','node:dgram','node:dns']) {\r\n const m=require(name);\r\n for(const k of ['connect','createConnection','createServer','request','get','createSocket','resolve','resolve4','resolve6','lookup','lookupService']) if(typeof m[k]==='function')m[k]=denied;\r\n if(m.Socket) m.Socket.prototype.connect=denied;\r\n if(m.Server) m.Server.prototype.listen=denied;\r\n}\r\nglobalThis.fetch=denied; globalThis.WebSocket=class {constructor(){denied();}};\r\nmod.syncBuiltinESMExports();"


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root",type=Path,default=Path(__file__))
    parser.add_argument("--projected-manifest",type=Path)
    parser.add_argument("--manifest-sha256")
    parser.add_argument("--tests",action="store_true")
    parser.add_argument("--scratch",type=Path)
    parser.add_argument("--third-party-python",type=Path)
    parser.add_argument("--node",type=Path)
    parser.add_argument("--json",action="store_true")
    args=parser.parse_args(argv)
    try:
        root=root_of(args.root)
        index=load_index(root)
        inventory,scope=publication_inventory(root,args.projected_manifest,args.manifest_sha256)
        result=verify(root,index,inventory,scope)
        if args.tests:
            if args.scratch is None:
                raise ValueError("--tests requires explicit --scratch")
            unsafe = [x for x in result["checks"] if x["status"]=="FAIL"
                      and x["check"]!="local_markdown_links"]
            if unsafe:
                result["checks"].append({"check":"isolated_tests","status":"NOT_VERIFIED",
                    "reason":"Source/static/public-safety checks failed; no test worker was started."})
            else:
                tests=run_tests(root,index,args.scratch,third_party_python=args.third_party_python,node=args.node)
                result["tests"]=tests
                result["checks"].append({"check":"isolated_tests","status":
                    "FAIL" if any(x["status"]=="FAIL" for x in tests) else
                    "BLOCKED_MISSING_ARTIFACT" if any(x["status"]!="PASS" for x in tests) else "PASS"})
        code=status_code(result)
        result["exit"]=code
        if args.json:
            print(json.dumps(result,indent=2))
        else:
            print("Scope:",result["scope"],"| Public files:",result["files"])
            for row in result["checks"]:
                print(row["status"]+": "+row["check"])
            if result.get("tests"):
                for row in result["tests"]:
                    print(row["status"]+": "+row["suite"]+" ("+str(row["expected"])+")")
            print("Exit",code,"| Source/unit verification is not historical runtime reproduction.")
        return code
    except (ValueError,OSError,KeyError) as error:
        print("Verification blocked: "+str(error),file=sys.stderr)
        return 3


if __name__=="__main__":
    raise SystemExit(main())
