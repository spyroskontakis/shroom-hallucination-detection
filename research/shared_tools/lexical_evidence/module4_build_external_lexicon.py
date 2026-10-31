"""Deterministic Module 4 external lexical snapshot builder.

No model inference, retrieval ranking, labels, predictions, metrics, official test,
holdout, annotations, or credentials are read by this program.
"""
from __future__ import annotations

import argparse
import copy
import csv
import hashlib
import html
import json
import re
import tarfile
import time
import unicodedata
import urllib.error
import urllib.parse
import urllib.request
from collections import Counter, OrderedDict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from bs4 import BeautifulSoup

VERSION = "module4-external-parser-v1"
WORDNET_URL = "https://wordnetcode.princeton.edu/wn3.1.dict.tar.gz"
WIKTIONARY_API = "https://en.wiktionary.org/w/api.php"
USER_AGENT = "SHROOM-Thesis-Module4/1.0 (academic reproducibility study)"
TIMEOUT_SECONDS = 30
BACKOFF_SECONDS = (1, 2, 4)
POS_FILES = OrderedDict((x, x) for x in ("noun", "verb", "adj", "adv"))
POS_ALLOWLIST = {
    "Noun", "Proper noun", "Verb", "Adjective", "Adverb", "Pronoun",
    "Preposition", "Conjunction", "Determiner", "Interjection", "Numeral",
    "Particle", "Phrase", "Idiom", "Proverb", "Letter", "Symbol",
}
CLOSED_DEFINE = re.compile(r"<define>\s*(.*?)\s*</define>", re.I | re.S)
OPEN_DEFINE = re.compile(r"<define>", re.I)
TOKEN_RE = re.compile(r"[^\W_]+", re.UNICODE)


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def norm_space(value: Any) -> str:
    return re.sub(r"\s+", " ", unicodedata.normalize("NFKC", str(value or ""))).strip()


def term_key(value: Any) -> str:
    return norm_space(value).casefold()


def definition_key(value: Any) -> str:
    return " ".join(TOKEN_RE.findall(unicodedata.normalize("NFKC", str(value or "")).casefold()))


def extract_dm_term(src: Any) -> str | None:
    text = str(src or "").strip()
    m = CLOSED_DEFINE.search(text)
    if m:
        value = m.group(1).strip()
        return value or None
    parts = OPEN_DEFINE.split(text)
    if len(parts) >= 3:
        value = parts[1].strip()
        return value or None
    return None


def write_csv_bom(path: Path, headers: list[str], rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=headers, extrasaction="raise", lineterminator="\n")
        w.writeheader()
        w.writerows(rows)


def load_canonical_inputs(manifest: Path) -> list[dict[str, Any]]:
    # Select only allowlisted positions. Forbidden label/probability fields are never referenced or emitted.
    with manifest.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.reader(f)
        header = next(reader)
        required = ["canonical_id", "task", "src", "tgt", "hyp"]
        idx = {name: header.index(name) for name in required}
        out = []
        for values in reader:
            chosen = {name: values[pos] for name, pos in idx.items()}
            task = chosen["task"].strip()
            term = extract_dm_term(chosen["src"]) if task == "DM" else None
            out.append({
                "example_id": chosen["canonical_id"], "task": task,
                "term": term or "", "src": chosen["src"], "tgt": chosen["tgt"],
                "rag_applicable": 1 if task == "DM" and term else 0,
            })
    if len(out) != 561 or len({r["example_id"] for r in out}) != 561:
        raise RuntimeError("Canonical input must contain 561 ordered unique IDs")
    return out


def build_term_rows(inputs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: OrderedDict[str, dict[str, Any]] = OrderedDict()
    for row in inputs:
        if row["rag_applicable"] != 1:
            continue
        key = term_key(row["term"])
        if not key:
            raise RuntimeError(f"Empty normalized DM term: {row['example_id']}")
        grouped.setdefault(key, {"term_key": key, "surface_term": norm_space(row["term"]), "development_row_count": 0})
        grouped[key]["development_row_count"] += 1
    return list(grouped.values())


def parse_wordnet_archive(archive: Path, terms: list[dict[str, Any]]) -> list[dict[str, Any]]:
    with tarfile.open(archive, "r:gz") as tf:
        members = {Path(m.name).name: m for m in tf.getmembers() if m.isfile()}
        needed = [f"index.{p}" for p in POS_FILES] + [f"data.{p}" for p in POS_FILES]
        if any(name not in members for name in needed):
            raise RuntimeError("WordNet archive missing required index/data files")
        texts = {name: tf.extractfile(members[name]).read().decode("utf-8", "strict") for name in needed}
    outputs = []
    for pos in POS_FILES:
        index: dict[str, list[str]] = {}
        for line in texts[f"index.{pos}"].splitlines():
            if not line or line[0].isspace():
                continue
            fields = line.split()
            if len(fields) < 6:
                continue
            lemma, synset_cnt, ptr_cnt = fields[0], int(fields[2]), int(fields[3])
            start = 4 + ptr_cnt + 2
            index[lemma] = fields[start:start + synset_cnt]
        data = {}
        for line in texts[f"data.{pos}"].splitlines():
            if line and line[0].isdigit():
                data[line.split(" ", 1)[0]] = line
        for term in terms:
            lookup = term["term_key"].replace(" ", "_")
            for offset in index.get(lookup, []):
                line = data.get(offset)
                if not line or " | " not in line:
                    raise RuntimeError(f"Missing WordNet data offset {pos}:{offset}")
                gloss = norm_space(line.split(" | ", 1)[1])
                definition = norm_space(gloss.split('; "', 1)[0])
                if not definition:
                    continue
                outputs.append({
                    "term_key": term["term_key"], "source": "wordnet31",
                    "source_entry_id": f"wn31:{pos}:{offset}",
                    "candidate_term": term["surface_term"],
                    "candidate_definition": definition, "candidate_context": gloss,
                    "provenance": {"archive_sha256": sha256_file(archive), "pos": pos, "synset_offset": offset},
                })
    return outputs


def _heading_name(tag) -> str:
    target = tag.find(id=True) if tag else None
    return norm_space(target.get("id", "") if target else tag.get("id", "") if tag else "")


def parse_wiktionary_html(rendered_html: str, term: dict[str, Any], page_id: int, revision_id: int, provenance: dict[str, Any]) -> list[dict[str, Any]]:
    soup = BeautifulSoup(rendered_html, "html.parser")
    marker = soup.find(id="English")
    english_h2 = marker if marker and marker.name == "h2" else marker.find_parent("h2") if marker else None
    if english_h2 is None:
        return []
    outputs, current_pos, ordinal = [], None, Counter()
    node = english_h2.find_next()
    while node is not None:
        if getattr(node, "name", None) == "h2" and node is not english_h2:
            break
        if getattr(node, "name", None) in {"h3", "h4", "h5", "h6"}:
            name = _heading_name(node).replace("_", " ")
            current_pos = name if name in POS_ALLOWLIST else None
        elif getattr(node, "name", None) == "ol" and current_pos and node.find_parent("ol") is None:
            for li in node.find_all("li", recursive=False):
                clone = BeautifulSoup(str(li), "html.parser").find("li")
                for bad in clone.select("ul, ol, dl, table, style, script, sup.reference, .reference, .citation"):
                    bad.decompose()
                definition = norm_space(html.unescape(clone.get_text(" ", strip=True)))
                if not definition:
                    continue
                ordinal[current_pos] += 1
                outputs.append({
                    "term_key": term["term_key"], "source": "enwiktionary",
                    "source_entry_id": f"wiktionary:{page_id}:{revision_id}:{current_pos}:{ordinal[current_pos]}",
                    "candidate_term": term["surface_term"],
                    "candidate_definition": definition,
                    "candidate_context": f"{current_pos}: {definition}",
                    "provenance": copy.deepcopy(provenance),
                })
        node = node.find_next()
    return outputs


def deduplicate(records: list[dict[str, Any]], term_order: dict[str, int]) -> list[dict[str, Any]]:
    priority = {"wordnet31": 0, "enwiktionary": 1}
    groups: dict[tuple[str, str], list[dict[str, Any]]] = {}
    for row in records:
        key = definition_key(row["candidate_definition"])
        if key:
            groups.setdefault((row["term_key"], key), []).append(row)
    output = []
    for (tkey, dkey), rows in groups.items():
        rows.sort(key=lambda r: (priority[r["source"]], r["source_entry_id"]))
        chosen = rows[0]
        evidence = "M4EV-" + hashlib.sha256((tkey + "\n" + dkey).encode("utf-8")).hexdigest()[:20].upper()
        provenance = [{"source": r["source"], "source_entry_id": r["source_entry_id"], **r["provenance"]} for r in rows]
        provenance.sort(key=lambda p: (priority[p["source"]], p["source_entry_id"], json.dumps(p, sort_keys=True)))
        output.append({
            "evidence_id": evidence, "term_key": tkey, "source": chosen["source"],
            "source_entry_id": chosen["source_entry_id"], "candidate_term": chosen["candidate_term"],
            "candidate_definition": chosen["candidate_definition"], "candidate_context": chosen["candidate_context"],
            "provenance": provenance,
        })
    output.sort(key=lambda r: (term_order[r["term_key"]], priority[r["source"]], r["source_entry_id"], r["evidence_id"]))
    return output


class SequentialFetcher:
    def __init__(self, log_path: Path):
        self.log_path, self.last_wiki = log_path, 0.0
        self.events: list[dict[str, Any]] = []

    def get(self, url: str, is_wiki: bool) -> bytes:
        if is_wiki:
            delay = 1.0 - (time.monotonic() - self.last_wiki)
            if delay > 0:
                time.sleep(delay)
        attempts = len(BACKOFF_SECONDS) + 1
        for attempt in range(attempts):
            try:
                req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
                with urllib.request.urlopen(req, timeout=TIMEOUT_SECONDS) as resp:
                    data, status = resp.read(), int(resp.status)
                self.events.append({"url": url, "attempt": attempt + 1, "status": status, "bytes": len(data), "timestamp_utc": datetime.now(timezone.utc).isoformat()})
                if is_wiki:
                    self.last_wiki = time.monotonic()
                self._flush()
                return data
            except urllib.error.HTTPError as exc:
                self.events.append({"url": url, "attempt": attempt + 1, "status": exc.code, "error": str(exc), "timestamp_utc": datetime.now(timezone.utc).isoformat()})
                self._flush()
                if attempt >= attempts - 1:
                    raise
                wait = BACKOFF_SECONDS[attempt]
                if exc.code == 429:
                    try: wait = max(wait, int(exc.headers.get("Retry-After", "0")))
                    except ValueError: pass
                time.sleep(wait)
            except Exception as exc:
                self.events.append({"url": url, "attempt": attempt + 1, "status": None, "error": repr(exc), "timestamp_utc": datetime.now(timezone.utc).isoformat()})
                self._flush()
                if attempt >= attempts - 1:
                    raise
                time.sleep(BACKOFF_SECONDS[attempt])
        raise AssertionError("unreachable")

    def _flush(self):
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        self.log_path.write_text("\n".join(json.dumps(x, ensure_ascii=False, sort_keys=True) for x in self.events) + "\n", encoding="utf-8")


def acquire_sources(raw_dir: Path, terms: list[dict[str, Any]], fetcher: SequentialFetcher) -> None:
    raw_dir.mkdir(parents=True, exist_ok=True)
    archive = raw_dir / "wn3.1.dict.tar.gz"
    if not archive.exists():
        archive.write_bytes(fetcher.get(WORDNET_URL, False))
    for i, term in enumerate(terms, 1):
        stem = f"{i:04d}_{hashlib.sha256(term['term_key'].encode()).hexdigest()[:12]}"
        rev_path, parse_path = raw_dir / f"{stem}_revision.json", raw_dir / f"{stem}_parse.json"
        if not rev_path.exists():
            params = {"action":"query","format":"json","formatversion":"2","redirects":"1","prop":"revisions","titles":term["surface_term"],"rvslots":"main","rvprop":"ids|timestamp|sha1"}
            rev_path.write_bytes(fetcher.get(WIKTIONARY_API + "?" + urllib.parse.urlencode(params), True))
        payload = json.loads(rev_path.read_text(encoding="utf-8"))
        pages = payload.get("query", {}).get("pages", [])
        if not pages or pages[0].get("missing") is True or not pages[0].get("revisions"):
            continue
        revision_id = pages[0]["revisions"][0]["revid"]
        if not parse_path.exists():
            params = {"action":"parse","format":"json","formatversion":"2","oldid":str(revision_id),"prop":"text|revid"}
            parse_path.write_bytes(fetcher.get(WIKTIONARY_API + "?" + urllib.parse.urlencode(params), True))


def offline_build(raw_dir: Path, terms: list[dict[str, Any]], snapshot_path: Path, term_manifest_path: Path) -> dict[str, Any]:
    archive = raw_dir / "wn3.1.dict.tar.gz"
    wordnet = parse_wordnet_archive(archive, terms)
    wiktionary, failed = [], []
    for i, term in enumerate(terms, 1):
        stem = f"{i:04d}_{hashlib.sha256(term['term_key'].encode()).hexdigest()[:12]}"
        rev_path, parse_path = raw_dir / f"{stem}_revision.json", raw_dir / f"{stem}_parse.json"
        if not rev_path.exists():
            failed.append(term["term_key"]); continue
        rev_raw = rev_path.read_bytes(); rev = json.loads(rev_raw)
        pages = rev.get("query", {}).get("pages", [])
        if not pages or pages[0].get("missing") is True or not pages[0].get("revisions"):
            continue
        page, revision = pages[0], pages[0]["revisions"][0]
        if not parse_path.exists():
            failed.append(term["term_key"]); continue
        parse_raw = parse_path.read_bytes(); parsed = json.loads(parse_raw)
        provenance = {
            "requested_title": term["surface_term"], "canonical_title": page.get("title"),
            "page_id": page.get("pageid"), "revision_id": revision.get("revid"),
            "revision_timestamp": revision.get("timestamp"), "wikimedia_sha1": revision.get("sha1"),
            "revision_raw_sha256": sha256_bytes(rev_raw), "parse_raw_sha256": sha256_bytes(parse_raw),
        }
        wiktionary.extend(parse_wiktionary_html(parsed["parse"]["text"], term, int(page["pageid"]), int(revision["revid"]), provenance))
    order = {t["term_key"]: i for i, t in enumerate(terms)}
    deduped = deduplicate(wordnet + wiktionary, order)
    snapshot_path.parent.mkdir(parents=True, exist_ok=True)
    snapshot_path.write_text("".join(json.dumps(r, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n" for r in deduped), encoding="utf-8")
    wn_counts = Counter(r["term_key"] for r in wordnet)
    wk_counts = Counter(r["term_key"] for r in wiktionary)
    unique_counts = Counter(r["term_key"] for r in deduped)
    failed_set = set(failed)
    manifest_rows = []
    for term in terms:
        key = term["term_key"]
        status = "SOURCE_REQUEST_FAILED" if key in failed_set else "EVIDENCE_FOUND" if unique_counts[key] else "NO_SENSE_FOUND"
        manifest_rows.append({**term, "wordnet_sense_count": wn_counts[key], "wiktionary_sense_count": wk_counts[key], "total_unique_sense_count": unique_counts[key], "coverage_status": status})
    write_csv_bom(term_manifest_path, ["term_key","surface_term","development_row_count","wordnet_sense_count","wiktionary_sense_count","total_unique_sense_count","coverage_status"], manifest_rows)
    return {"wordnet_before_dedup": len(wordnet), "wiktionary_before_dedup": len(wiktionary), "unique_after_dedup": len(deduped), "failed_terms": failed}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--canonical-manifest", type=Path, required=True)
    ap.add_argument("--output-dir", type=Path, required=True)
    ap.add_argument("--mode", choices=["prepare-inputs", "acquire", "offline-build"], required=True)
    args = ap.parse_args()
    inputs = load_canonical_inputs(args.canonical_manifest)
    terms = build_term_rows(inputs)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    if args.mode == "prepare-inputs":
        write_csv_bom(args.output_dir / "module4_dev_inputs_locked.csv", ["example_id","task","term","src","tgt","rag_applicable"], inputs)
        (args.output_dir / "module4_terms_input.json").write_text(json.dumps(terms, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    elif args.mode == "acquire":
        fetcher = SequentialFetcher(args.output_dir / "raw_sources" / "network_requests.jsonl")
        acquire_sources(args.output_dir / "raw_sources", terms, fetcher)
    else:
        result = offline_build(args.output_dir / "raw_sources", terms, args.output_dir / "module4_external_lexical_snapshot.jsonl", args.output_dir / "module4_dev_term_manifest.csv")
        print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
