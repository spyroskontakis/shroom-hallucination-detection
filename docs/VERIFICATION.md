# Offline repository verification

Run this from the repository root with Python 3.12:

~~~console
python -I -S -B research/shared_tools/verify_repository.py
~~~

This command reads files and local Git objects. It does not import experiment
entry points, run notebook cells, download packages or models, contact APIs, or
write experiment outputs. Add --json for detailed findings.

It checks the 790 original migration entries against the original Git blobs and
SHA-256 values, current source identities, approved destinations, protected files,
Python syntax, notebook/JSON structure, local Markdown file targets and selected
historical permalinks. The existing compatibility and H2 validators remain the
source of truth. The verification index adds the approved destinations and test
inventory; it is not a replacement historical source contract.

The default publication scope is the complete committed HEAD. Untracked local
audits are excluded. A tracked file that differs from HEAD is a failure. Local
release reviewers can supply a complete projected inventory with
--projected-manifest and its independently checked --manifest-sha256; that result
is explicitly labelled PROJECTED_LOCAL_SNAPSHOT.

## What the statuses mean

| Status | Meaning |
|---|---|
| PASS | The named source, static or isolated test check succeeded within its stated scope |
| FAIL | An actual failed check, including an unresolved historical link |
| KNOWN_HISTORICAL_EXCEPTION | Preserved historical evidence; an underlying FAIL is still reported as FAIL |
| NOT_VERIFIED | The stated capability has not been established |
| BLOCKED_MISSING_ARTIFACT | A required local dependency or historical artifact is unavailable |

Exit 0 means all selected checks passed. Exit 1 means an actual failure,
including the historical H0 checksum failures. Exit 2 means selected checks are
incomplete without an actual failure. Exit 3 means the invocation, source
identity or required Git evidence could not be validated.

The frozen E11 audit still contains a broken protocol link. Three H0 checksum
comparisons also fail against the published H1 sources. These are reported
openly, so a nonzero result is expected until the underlying issues receive an
approved resolution. The preserved E8 report syntax error is identified by its
exact source hash. These exceptions do not certify publication readiness.

## Optional isolated tests

Add --tests and a **new absolute scratch directory outside every Git
repository**. The directory must not already exist. The verifier creates only
synthetic fixtures, caches and temporary files there. It authenticates historical
test snapshots from local Git objects; it does not fetch missing history.

~~~console
python -I -S -B research/shared_tools/verify_repository.py --tests --scratch C:/SHROOM_REORG_TESTS/new_run --json
~~~

Standard-library workers use isolated Python subprocesses with bytecode disabled,
offline settings, model/cloud import restrictions and write guards. The Module 1
tests execute only the reviewed IO/cache definitions extracted from notebook
source. They do not execute scientific or API cells. Module 2 tests use its
actual IO helper. Historical tests run in their explicitly identified original
source contexts; current tests use the current layout.

Some parser and synthetic feature tests need an **already installed** environment
with Beautiful Soup, NumPy and pandas. Pass its Python executable with
--third-party-python. It is used without site startup hooks; no installation is
performed. Optional Node authoring tests use an already available Node executable
passed with --node and filesystem permissions that allow writes only in scratch.
The Node tests use a workbook interface fixture. Native Workbook execution remains
NOT_VERIFIED following ERR_DLOPEN_DISABLED.

Unavailable dependencies, platform capabilities and skipped tests are reported
separately. In particular, a platform without symlink creation cannot pass the
original Module 4 symlink test. A skipped case is not counted as a passed case.
Test results distinguish fresh execution from unexecuted checks.

## Interpretation and limits

[Research navigation](../research/README.md) and the
[current verification index](../project_records/current_layout/repository_verification_index.json)
identify sources, configurations, inputs and execution scopes for E1-E11.
Historical originals remain identifiable at the
[immutable research baseline](https://github.com/spyroskontakis/shroom-hallucination-detection/tree/11822d92070cd29360445cb4dacd8d110c655248).

Source identity, syntax checks and synthetic tests do not reproduce historical
metrics. Complete datasets, model weights, original generated artifacts, private
preservation records and original run environments are not all included.
Historical relative paths and output writers must not be treated as instructions
for direct execution in the reorganized checkout. Use the
[safe execution contract](SAFE_EXECUTION.md) before proposing a separately
approved run. Training, inference, live retrieval, downloads and cloud/API work
are outside this verification workflow.
