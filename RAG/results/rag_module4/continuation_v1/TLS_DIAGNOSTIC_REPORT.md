# SHROOM Module 4 — TLS Root-Cause Diagnostic Report

## Verdict

```text
MODULE4_TLS_DIAGNOSIS_COMPLETE_CLIENT_TRUST_PATH_DIVERGENCE
```

**Confidence:** high that the failure is client/trust-path specific; insufficient evidence to identify the exact failing certificate or assign the root cause uniquely to clock, local trust-store state, interception infrastructure, or an upstream chain.

This was diagnosis only. No acquisition, lexical evidence, model execution, feature generation, training, prediction, or metric computation was performed. No existing script, specification, test, manifest, network log, checkpoint, incident report, dataset, or experiment artifact was modified.

## 1. Integrity and existing error evidence

| Artifact | Expected SHA-256 | Result |
|---|---|---:|
| `continuation_v1/scripts/module4_build_wiktionary_lexicon.py` | `91c2c950e066ce613cca3dcdbda14fd83a7bf633fecbbeeb90d065c14e68d4e6` | PASS |
| `continuation_v1/raw_sources/network_requests.jsonl` | `7839ecd3b3e1ce62c35a8379e580a163e67f5ee77b86917875cdf600139fb09c` | PASS |

All 55 existing records contain the same serialized failure:

```text
URLError(
  SSLCertVerificationError(
    [SSL: CERTIFICATE_VERIFY_FAILED]
    certificate verify failed: certificate has expired
  )
)
```

- Existing log failures with that exact cause: 55/55.
- HTTP responses recorded: 0/55.
- TLS verification recorded as enabled: 55/55.
- Accepted response bytes: 0.
- `verify_code` and `verify_message` in the historical log: not recorded.
- Certificate subject, issuer, SAN, validity dates, fingerprint, or failing chain position in the historical log: not recorded.

Therefore the historical log establishes a repeated Python certificate-validation exception but does not contain certificate-level evidence that the upstream Wiktionary certificate itself was expired.

The retry loop continued across terms because `AuditFetcher.get()` performs an initial attempt plus three retries and raises after the fourth failure, while `acquire()` catches that exception for the current term, appends a failure record, and continues its outer term loop. A certificate-validation error is effectively endpoint/host-level in this run, but the implementation currently treats it like a per-term recoverable failure.

## 2. Execution environment

- Operating system: Microsoft Windows 11 Pro, 64-bit, version `10.0.26200`, build `26200`.
- Python executable: `external-artifacts/local-27d73a276c7f/python.exe`.
- Python: `3.12.10`, 64-bit.
- OpenSSL used by Python: `OpenSSL 3.0.16 11 Feb 2025`.
- Requests: `2.32.5`.
- urllib3: `2.6.3`.
- certifi: `2026.01.04`.
- curl comparison client: `curl 8.21.0`, Windows Schannel backend.
- Diagnostic UTC observation: `2026-08-30T07:06:19.7667863Z`.
- Windows Time status query: unavailable because the Windows Time service was not started (`0x80070426`). Consequently, host clock synchronization could not be confirmed.

### Certificate configuration

The acquisition script creates an explicit `ssl.create_default_context()` and passes it to `urllib.request.urlopen`. Verification mode is `CERT_REQUIRED` (`2`) and hostname checking is enabled. It does not use Requests, prepared Requests objects, an explicit `verify` argument, `CERT_NONE`, or an unverified context.

`ssl.get_default_verify_paths()` reported:

- OpenSSL default CA file path: `external-artifacts/local-836fafb1e6d8/Program Files\Common Files\SSL\cert.pem` — file absent.
- OpenSSL default CA directory path: `external-artifacts/local-836fafb1e6d8/Program Files\Common Files\SSL\certs` — directory absent.
- Environment override names: `SSL_CERT_FILE` and `SSL_CERT_DIR`.
- Effective Python default-context store: 89 CA certificates and 2 additional X.509 certificates; 0 CRLs.

The Requests default CA bundle, although not used by the acquisition script, is the installed certifi `cacert.pem` for certifi `2026.01.04`.

Eleven certificates returned by Python's default CA-context enumeration had `notAfter` earlier than the observed host time. This includes several legacy roots/intermediates and an Azure TLS issuing CA expiring on 2026-08-25. Their presence is a diagnostic risk signal, not proof that any of them appeared in the failing Wiktionary chain.

### Redacted transport environment

The following were all unset: `HTTP_PROXY`, `HTTPS_PROXY`, `ALL_PROXY`, `NO_PROXY`, `REQUESTS_CA_BUNDLE`, `CURL_CA_BUNDLE`, `SSL_CERT_FILE`, and `SSL_CERT_DIR`. No credential, token, cookie, proxy password, private key, full environment dump, or sensitive header was accessed or displayed.

## 3. Diagnostic probes

Exactly two metadata-only requests were made to:

```text
https://en.wiktionary.org/w/api.php?action=query&meta=siteinfo&siprop=general&format=json
```

Both used normal certificate/hostname verification, a 30-second timeout, zero retries, redirects disabled, and no authentication. Response bodies and response headers were not displayed or retained as lexical evidence.

### Probe 1 — Python urllib/OpenSSL, same acquisition transport

- TLS verification: FAIL.
- Top-level exception: `urllib.error.URLError`.
- Nested cause: `ssl.SSLCertVerificationError`.
- `verify_code`: `10`.
- `verify_message`: `certificate has expired`.
- HTTP status: unavailable; TLS failed before an HTTP response.
- JSON validity: not applicable.
- Certificate details from the failed handshake: unavailable.

### Probe 2 — installed curl/System Schannel

- TLS verification: PASS (`ssl_verify_result=0`).
- HTTP status: `200`.
- Downloaded metadata response size: 3,102 bytes.
- Remote IP reported by curl: `185.15.59.224`.
- Response body displayed: no.
- JSON validity: not inspected because the body was intentionally discarded; a valid JSON claim is therefore not made.

The curl success confirms that one validating system-client path could establish TLS and receive HTTP 200 at the observation time. It does not by itself prove which Python trust, chain-building, clock, or route component is wrong.

## 4. Certificate evidence

| Field | Evidence |
|---|---|
| Failing certificate subject | UNAVAILABLE |
| Failing certificate issuer | UNAVAILABLE |
| SAN/hostname data | UNAVAILABLE |
| `notBefore` | UNAVAILABLE |
| `notAfter` | UNAVAILABLE |
| SHA-256 fingerprint | UNAVAILABLE |
| Failing chain position | UNAVAILABLE |

No verification bypass was used to obtain certificate details. The generic `verify_code=10` does not identify which chain certificate was considered expired.

## 5. Evidence-based diagnosis

### Confirmed

1. Python 3.12/OpenSSL with the same default context as acquisition fails consistently with verify code 10.
2. curl using Windows Schannel succeeds against the same metadata URL with verification enabled.
3. No proxy or CA-bundle environment override was active.
4. The Python context and Schannel client therefore do not produce the same validation outcome.
5. The historical logs do not contain the peer chain or failing-certificate identity.
6. Host clock synchronization status is unavailable because the Windows Time service is stopped.

### Plausible but not proven

- Python/OpenSSL and Schannel may build or select different certificate chains from the Windows trust material.
- Python may select an expired cached/intermediate certificate that Schannel avoids or refreshes dynamically.
- Security/interception infrastructure could expose different chains by client characteristics, although no configured proxy was detected.
- An unsynchronized or incorrect host clock could contribute; however, both clients observed the same host time and only Python failed, so clock alone does not explain the client divergence.
- A genuine upstream chain issue affecting only some chain-building clients remains possible, but the available evidence does not establish it.

### Not supported

- A definitive claim that Wiktionary's own leaf certificate is expired.
- A definitive claim that an enterprise proxy is responsible.
- A definitive claim that certifi is responsible; the failing script does not use Requests/certifi.
- A conclusion that changing lexical source or disabling verification is justified.

## 6. Minimum proposed correction — not applied

The minimum safe corrective sequence is host-level and requires user/administrator action:

1. Restore/verify Windows Time service operation and synchronize the host clock with the approved organizational time source.
2. Refresh and validate the Windows root/intermediate certificate stores through normal Windows Update or the organization's managed PKI process.
3. Capture the exact validating Python peer chain using approved administrator/network diagnostic tooling that preserves verification; identify the certificate producing verify code 10 before removing or adding trust material.
4. Re-run one host-level metadata preflight with the exact Python acquisition context. Proceed to term iteration only if TLS verification and HTTP metadata response both succeed.

Do not switch to curl, Requests/certifi, a custom CA file, or another route inside the experiment without a separately reviewed transport-only protocol revision. Such changes may be reasonable remediation options, but this diagnosis did not validate their scientific equivalence or apply them.

The acquisition implementation should later receive a reviewed host-level preflight and immediate fail-fast behavior for `SSLCertVerificationError`, before entering the 206-term loop. The current retry logic must not be changed as part of this diagnostic-only task.

## 7. Accounting and integrity

- Diagnostic network requests: 2.
- Python probe: 1 failed TLS validation.
- curl/Schannel probe: 1 successful TLS validation and HTTP 200.
- Redirects followed: 0.
- Retries: 0.
- HTTP downgrade requests: 0.
- TLS bypasses: 0.
- Authentication data sent: 0.
- Response bodies displayed: 0.
- Acquisition requests: 0.
- Existing network-log records added or changed: 0.
- Embedding/NLI/RF/prediction/metric executions: 0.
- Mixed E3, development-label, holdout, official-test, annotation, protected, and quarantine accesses: 0.
- Existing experiment artifacts modified: 0.
- Project artifacts created: 1, this report only.

Because embedding a file's own final SHA-256 inside itself is self-referential, the final byte size and SHA-256 are computed after writing and reported in the handoff. No detached checksum artifact is created, in accordance with the one-output restriction.
