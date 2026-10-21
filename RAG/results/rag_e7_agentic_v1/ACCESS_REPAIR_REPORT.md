# E7 preflight access-control investigation — PASS

Scope: diagnostic investigation and preflight/access contracts only. **E7 evaluations = 0; RF fits = 0; E7 scores observed = 0.** No research-design change, commit, push or tag.

## Reproduced failure

The original failure log did not store destinations, so its exact paths cannot be recovered retroactively. A minimal import-only reproduction recorded the same three-denial pattern: numpy alone caused zero events; importing sklearn.ensemble caused three. No datasets were loaded in that diagnostic process.

| Attempt | Resolved absolute path | Operation | Component/caller | Classification |
|---|---|---|---|---|
| 1 | `\\.\NUL\` | `open`, mode null, flags 130 (O_RDWR plus binary flag) | `subprocess._get_devnull`, via `platform._syscmd_ver`: `ver` | Windows null-device stdio for optional runtime OS probe |
| 2 | `\\.\NUL\` | same | same helper: `command /c ver` | same |
| 3 | `\\.\NUL\` | same | same helper: `cmd /c ver` | same |

The command order is established from the installed Python 3.11.9 platform.py loop and the three matching stacks. Each attempt was blocked before child-process creation. The import stack includes numpy.testing._private.utils calling platform.machine(), then platform.uname(), win32_ver(), _syscmd_ver(), subprocess.check_output/run/Popen, _get_handles(), _get_devnull(). Full stacks, PID, CWD, timestamp and selected temp/cache environment values are in `config/write_guard_diagnostics_import_diagnostic.jsonl`.

The writes are not bytecode, cache files, model artifacts, frozen datasets, or output logs. NUL is a Windows device that discards output. The optional shell-based OS-version lookup is unnecessary for the experiment; Python already has a native sys.getwindowsversion fallback. The earlier suspicion of temporary-file discovery was not confirmed.

## Minimal repair

Only diagnostic/access-control code changed. Blocked operations now persist their resolved path, operation/mode/flags, PID, CWD, Python frames, timestamp and relevant temp/cache environment values inside E7 config. Frames are captured without traceback source-file reads, avoiding recursive guard access during logging.

In E7's guarded Python process, after the audit hook is installed and before scientific imports, a Python-3.11.9-specific adapter makes platform._syscmd_ver return its documented default tuple. The unchanged platform.win32_ver then uses its existing sys.getwindowsversion fallback. No installed Python/library file is edited. The adapter avoids the optional shell operation entirely; it does not allow NUL writes or child processes. A contract confirms native version and machine identification.

No new environment redirects were added. Existing -B/PYTHONDONTWRITEBYTECODE=1, offline flags and JOBLIB_TEMP_FOLDER remain as before. TMP/TEMP, HF_HOME and Transformers/sentence-transformers cache variables were not changed. No local cache/temp output was needed for this repair. No external directory was added to the allowlist.

## Verification

- Seven diagnostic/access-control contracts: **PASS**. They check the adapter defaults, native Windows version/machine, continued denial of network/child processes, frozen and external writes (including NUL), official-test synthetic path denial, E7-local write policy, and integrity/no evaluation outputs.
- Label-free preflight: **PASS**, verifying 561 unique canonical IDs, locked 113/112/112/112/112 folds, exact E3/E6 feature alignment, evidence metadata, model defaults and installed versions. Constructing the RF estimator for get_params does not fit it.
- Operational violations after the fix: **0** in both contract and preflight processes. Operational network attempts: **0**. Synthetic policy-denial probes are recorded separately, not presented as real attempted writes.
- Protocol SHA-256 before/after: `0491505c0f98a2a4d2a0896370adbbc3674c6fdf873b96a8a31833e587923002`.
- All **481 protected files** remain hash-identical. The frozen router rule remains untouched.
- No RF fitting, feature scoring, route generation, E7 metrics, or OOF prediction generation. The evaluation directory remains empty.

This is not the full E7 router contract suite: the controller/evaluation implementation is still pending and was outside the authorized scope of this repair. The historical `E7_RESULTS.md`, failure audit, security log and original output manifest are retained unchanged as records of the failed first attempt. This report and `config/access_repair_audit.json` describe the current repaired preflight state. The old manifest describes its earlier snapshot; the new repair manifest records current files.

## Files and rerun policy

Changed: scripts/e7_common.py and scripts/preflight.py. Added diagnostic runner scripts/diagnose_imports.py, tests/test_access_repair.py, this report and config diagnostic/security/test/preflight/audit/manifests. Diagnostic and security outputs use phase-specific names; previous evidence was not overwritten. Exclusive creation intentionally prevents accidental overwrite on rerun. The import-only diagnostic record was produced before the adapter was installed.

Branch: agentic-rag-e7; HEAD remains 0a1ef3e792867796c412070087095274b0206849. Git status contains only the existing untracked Augmentation Pipeline.txt and the untracked E7 directory. **STOP after preflight; evaluation requires a later instruction.**
