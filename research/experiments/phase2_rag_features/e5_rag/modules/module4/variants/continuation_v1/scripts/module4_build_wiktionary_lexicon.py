"""Versioned Wiktionary-only orchestration for Module 4 continuation v1.

Imports the frozen parser's normalization, English/POS extraction, deduplication,
and stable evidence-ID semantics. It never reads E3 features, labels, predictions,
holdout, official test, annotations, or quarantine content.
"""
from __future__ import annotations

import argparse, csv, hashlib, json, os, ssl, sys, time, urllib.error, urllib.parse, urllib.request
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(ROOT / "RAG" / "scripts"))
import module4_build_external_lexicon as frozen  # noqa: E402

VERSION = "module4-wiktionary-only-orchestration-v1"
ENDPOINT = frozen.WIKTIONARY_API
USER_AGENT = frozen.USER_AGENT
TIMEOUT_SECONDS = frozen.TIMEOUT_SECONDS
BACKOFF_SECONDS = frozen.BACKOFF_SECONDS


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def atomic_write(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".part")
    tmp.write_bytes(data)
    os.replace(tmp, path)


def append_event(path: Path, event: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8", newline="") as handle:
        handle.write(json.dumps(event, ensure_ascii=False, sort_keys=True) + "\n")


class AuditFetcher:
    def __init__(self, log_path: Path):
        self.log_path = log_path
        self.last_request = 0.0
        self.context = ssl.create_default_context()

    def get(self, url: str, purpose: str, term_key: str, batch_identity: str) -> bytes:
        delay = 1.0 - (time.monotonic() - self.last_request)
        if delay > 0:
            time.sleep(delay)
        for retry in range(len(BACKOFF_SECONDS) + 1):
            started = datetime.now(timezone.utc).isoformat()
            try:
                request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
                with urllib.request.urlopen(request, timeout=TIMEOUT_SECONDS, context=self.context) as response:
                    data = response.read()
                    status = int(response.status)
                self.last_request = time.monotonic()
                append_event(self.log_path, {
                    "endpoint": ENDPOINT, "url": url, "logical_source": "English Wiktionary",
                    "request_purpose": purpose, "requested_term": term_key,
                    "batch_identity": batch_identity, "retry_number": retry,
                    "timestamp_utc": started, "http_status": status,
                    "tls_verification": "enabled_and_passed", "response_size": len(data),
                    "response_sha256": sha256_bytes(data), "status": "SUCCESS", "failure_reason": None,
                })
                return data
            except urllib.error.HTTPError as exc:
                append_event(self.log_path, {
                    "endpoint": ENDPOINT, "url": url, "logical_source": "English Wiktionary",
                    "request_purpose": purpose, "requested_term": term_key,
                    "batch_identity": batch_identity, "retry_number": retry,
                    "timestamp_utc": started, "http_status": exc.code,
                    "tls_verification": "enabled", "response_size": 0,
                    "response_sha256": None, "status": "FAILED", "failure_reason": str(exc),
                })
                if retry >= len(BACKOFF_SECONDS): raise
                wait = BACKOFF_SECONDS[retry]
                if exc.code == 429:
                    try: wait = max(wait, int(exc.headers.get("Retry-After", "0")))
                    except (TypeError, ValueError): pass
                time.sleep(wait)
            except Exception as exc:
                append_event(self.log_path, {
                    "endpoint": ENDPOINT, "url": url, "logical_source": "English Wiktionary",
                    "request_purpose": purpose, "requested_term": term_key,
                    "batch_identity": batch_identity, "retry_number": retry,
                    "timestamp_utc": started, "http_status": None,
                    "tls_verification": "enabled", "response_size": 0,
                    "response_sha256": None, "status": "FAILED", "failure_reason": repr(exc),
                })
                if retry >= len(BACKOFF_SECONDS): raise
                time.sleep(BACKOFF_SECONDS[retry])
        raise AssertionError("unreachable")


def load_inputs(path: Path) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        expected = ["example_id", "task", "term", "src", "tgt", "rag_applicable"]
        if reader.fieldnames != expected:
            raise ValueError(f"Unexpected label-free input schema: {reader.fieldnames}")
        rows = list(reader)
    if len(rows) != 561 or len({r["example_id"] for r in rows}) != 561:
        raise ValueError("Expected 561 ordered unique label-free rows")
    normalized = [{**r, "rag_applicable": int(r["rag_applicable"])} for r in rows]
    terms = frozen.build_term_rows(normalized)
    if len(terms) != 206:
        raise ValueError(f"Expected 206 terms, found {len(terms)}")
    return normalized, terms


def stem_for(index: int, term_key: str) -> str:
    return f"{index:04d}_{hashlib.sha256(term_key.encode()).hexdigest()[:12]}"


def acquire(raw_dir: Path, terms: list[dict[str, Any]], fetcher: AuditFetcher) -> list[dict[str, str]]:
    raw_dir.mkdir(parents=True, exist_ok=True)
    failures = []
    for index, term in enumerate(terms, 1):
        stem = stem_for(index, term["term_key"])
        revision_path = raw_dir / f"{stem}_revision.json"
        parse_path = raw_dir / f"{stem}_parse.json"
        try:
            if not revision_path.exists():
                params = {"action":"query","format":"json","formatversion":"2","redirects":"1","prop":"revisions","titles":term["surface_term"],"rvslots":"main","rvprop":"ids|timestamp|sha1"}
                atomic_write(revision_path, fetcher.get(ENDPOINT + "?" + urllib.parse.urlencode(params), "revision_identity", term["term_key"], stem))
            payload = json.loads(revision_path.read_text(encoding="utf-8"))
            pages = payload.get("query", {}).get("pages", [])
            if not pages or pages[0].get("missing") is True or not pages[0].get("revisions"):
                continue
            revision_id = pages[0]["revisions"][0]["revid"]
            if not parse_path.exists():
                params = {"action":"parse","format":"json","formatversion":"2","oldid":str(revision_id),"prop":"text|revid"}
                atomic_write(parse_path, fetcher.get(ENDPOINT + "?" + urllib.parse.urlencode(params), "frozen_revision_content", term["term_key"], stem))
        except Exception as exc:
            failures.append({"term_key": term["term_key"], "reason": repr(exc)})
    return failures


def offline_build(raw_dir: Path, terms: list[dict[str, Any]], snapshot_path: Path, manifest_path: Path) -> dict[str, Any]:
    records, manifest_rows, failed = [], [], []
    raw_sense_count = 0
    for index, term in enumerate(terms, 1):
        stem = stem_for(index, term["term_key"])
        revision_path, parse_path = raw_dir / f"{stem}_revision.json", raw_dir / f"{stem}_parse.json"
        base = {"term_order": index, "term_key": term["term_key"], "surface_term": term["surface_term"], "development_row_count": term["development_row_count"]}
        if not revision_path.exists():
            failed.append(term["term_key"]); manifest_rows.append({**base,"requested_page_title":term["surface_term"],"resolved_page_title":"","redirect_status":"unknown","page_id":"","revision_id":"","revision_timestamp":"","acquisition_status":"SOURCE_REQUEST_FAILED","extracted_sense_count":0,"raw_revision_reference":"","raw_revision_sha256":"","raw_parse_reference":"","raw_parse_sha256":""}); continue
        revision_raw = revision_path.read_bytes()
        try: revision_payload = json.loads(revision_raw)
        except Exception:
            failed.append(term["term_key"]); manifest_rows.append({**base,"requested_page_title":term["surface_term"],"resolved_page_title":"","redirect_status":"unknown","page_id":"","revision_id":"","revision_timestamp":"","acquisition_status":"SOURCE_REQUEST_FAILED","extracted_sense_count":0,"raw_revision_reference":revision_path.name,"raw_revision_sha256":sha256_bytes(revision_raw),"raw_parse_reference":"","raw_parse_sha256":""}); continue
        pages = revision_payload.get("query", {}).get("pages", [])
        redirects = revision_payload.get("query", {}).get("redirects", [])
        if not pages or pages[0].get("missing") is True or not pages[0].get("revisions"):
            manifest_rows.append({**base,"requested_page_title":term["surface_term"],"resolved_page_title":pages[0].get("title","") if pages else "","redirect_status":"redirected" if redirects else "not_redirected","page_id":pages[0].get("pageid","") if pages else "","revision_id":"","revision_timestamp":"","acquisition_status":"NO_SENSE_FOUND","extracted_sense_count":0,"raw_revision_reference":revision_path.name,"raw_revision_sha256":sha256_bytes(revision_raw),"raw_parse_reference":"","raw_parse_sha256":""}); continue
        page, revision = pages[0], pages[0]["revisions"][0]
        if not parse_path.exists():
            failed.append(term["term_key"]); manifest_rows.append({**base,"requested_page_title":term["surface_term"],"resolved_page_title":page.get("title",""),"redirect_status":"redirected" if redirects else "not_redirected","page_id":page.get("pageid",""),"revision_id":revision.get("revid",""),"revision_timestamp":revision.get("timestamp",""),"acquisition_status":"SOURCE_REQUEST_FAILED","extracted_sense_count":0,"raw_revision_reference":revision_path.name,"raw_revision_sha256":sha256_bytes(revision_raw),"raw_parse_reference":"","raw_parse_sha256":""}); continue
        parse_raw = parse_path.read_bytes()
        try:
            parsed = json.loads(parse_raw)
            provenance = {"requested_title":term["surface_term"],"canonical_title":page.get("title"),"page_id":page.get("pageid"),"revision_id":revision.get("revid"),"revision_timestamp":revision.get("timestamp"),"wikimedia_sha1":revision.get("sha1"),"revision_raw_sha256":sha256_bytes(revision_raw),"parse_raw_sha256":sha256_bytes(parse_raw)}
            senses = frozen.parse_wiktionary_html(parsed["parse"]["text"], term, int(page["pageid"]), int(revision["revid"]), provenance)
        except Exception:
            failed.append(term["term_key"]); senses = []
        raw_sense_count += len(senses); records.extend(senses)
        status = "SOURCE_REQUEST_FAILED" if term["term_key"] in failed else "SENSES_FOUND" if senses else "NO_SENSE_FOUND"
        manifest_rows.append({**base,"requested_page_title":term["surface_term"],"resolved_page_title":page.get("title",""),"redirect_status":"redirected" if redirects else "not_redirected","page_id":page.get("pageid",""),"revision_id":revision.get("revid",""),"revision_timestamp":revision.get("timestamp",""),"acquisition_status":status,"extracted_sense_count":len(senses),"raw_revision_reference":revision_path.name,"raw_revision_sha256":sha256_bytes(revision_raw),"raw_parse_reference":parse_path.name,"raw_parse_sha256":sha256_bytes(parse_raw)})
    order = {term["term_key"]: index for index, term in enumerate(terms)}
    deduped = frozen.deduplicate(records, order)
    snapshot_path.parent.mkdir(parents=True, exist_ok=True)
    snapshot_path.write_text("".join(json.dumps(row, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n" for row in deduped), encoding="utf-8")
    headers = ["term_order","term_key","surface_term","development_row_count","requested_page_title","resolved_page_title","redirect_status","page_id","revision_id","revision_timestamp","acquisition_status","extracted_sense_count","raw_revision_reference","raw_revision_sha256","raw_parse_reference","raw_parse_sha256"]
    frozen.write_csv_bom(manifest_path, headers, manifest_rows)
    status_counts = Counter(row["acquisition_status"] for row in manifest_rows)
    return {"terms":len(terms),"raw_sense_count":raw_sense_count,"unique_sense_count":len(deduped),"status_counts":dict(status_counts),"failed_terms":failed}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--inputs", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--mode", choices=["acquire", "offline-build"], required=True)
    args = parser.parse_args()
    _rows, terms = load_inputs(args.inputs)
    raw_dir = args.output_dir / "raw_sources"
    if args.mode == "acquire":
        failures = acquire(raw_dir, terms, AuditFetcher(raw_dir / "network_requests.jsonl"))
        print(json.dumps({"failed_terms": failures, "term_count": len(terms)}, sort_keys=True))
    else:
        print(json.dumps(offline_build(raw_dir, terms, args.output_dir / "module4_external_lexical_snapshot.jsonl", args.output_dir / "module4_dev_term_manifest.csv"), sort_keys=True))


if __name__ == "__main__":
    main()
