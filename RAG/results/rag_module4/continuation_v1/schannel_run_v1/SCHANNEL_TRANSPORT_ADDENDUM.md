# Module 4 — Frozen Schannel Transport Addendum

This transport-only revision was frozen before any new source request, lexical snapshot, model inference, feature generation, or score evaluation.

- Client: `external-artifacts/local-0dd4264ef6a3/curl.exe`, SHA-256 `73d24149ff289afc49ec41f08918ef9faa727d39ad993e929757dc2ddafab805`.
- Version/backend: curl 8.21.0, libcurl 8.21.0, Windows Schannel.
- Logical source and endpoint: English Wiktionary only, `https://en.wiktionary.org/w/api.php`.
- Change scope: response-byte transport only. Frozen URL parameters, exact-term ordering, revision acquisition, parsing, normalization, language/POS filtering, extraction, deduplication, evidence IDs, ordering, snapshot semantics, and feature semantics are unchanged.
- Python/OpenSSL root cause: unresolved. This addendum does not claim it was repaired.
- Invocation: `subprocess.run()` with an argument list and `shell=False`; `-q` is the first curl option to exclude user curl-config files. Managed environment route variables are not modified.
- Prohibited options: `-k`, `--insecure`, `--proxy-insecure`, `--ssl-no-revoke`, and `--ssl-revoke-best-effort`; custom CA files and proxy/DNS bypasses are not used.
- Protocol: HTTPS-only via `--proto =https` and `--proto-redir =https`; GET; redirects not followed (`--max-redirs 0`); timeout 30 seconds.
- Retry policy: at most three total attempts per logical request, backoff 1 then 2 seconds only for bounded transport/HTTP transient failures; `Retry-After` is honored when parseable. Certificate-validation failure (curl exit 60) has zero retries and globally stops acquisition.
- Acceptance: curl exit 0, HTTP 200, complete body, valid JSON, no MediaWiki `error`, and purpose-specific response structure. Diagnostics and headers are kept separate from response bytes.
- Storage: response bytes are written to `.part`, hashed and validated, then atomically promoted. Partial or invalid content is never accepted.
- Audit linkage: historical Python Wiktionary failures remain unchanged at SHA-256 `7839ecd3b3e1ce62c35a8379e580a163e67f5ee77b86917875cdf600139fb09c`; the TLS diagnostic report remains unchanged at SHA-256 `79dbb16594543367d4c06036655e42fa6b0a7b6b34b3ea60559afeaf0c8f1a13`.
- Historical label exposure remains disclosed; no counter is reset.

The mandatory host preflight is one metadata request with no retries or redirects. Term acquisition is permitted only after exit code 0, TLS validation, HTTP 200, and valid `query.general` API JSON.
