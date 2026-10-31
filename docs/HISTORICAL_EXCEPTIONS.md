# Documented historical exceptions

Policy ID: **SHROOM-PUBLICATION-EXCEPTIONS-v1**

Version: **1.0 - 2026-10-31**

This policy accepts the bounded exceptions below for a research-source portfolio
release only when the mandatory gates pass independently. It does not authorize
a push, PR, merge, tag or release. It does not certify historical numerical
reproduction. A failed original check remains FAIL; unverified execution remains
NOT_VERIFIED; a skipped test remains SKIPPED.

The physical architecture is frozen at **777/790 original migration entries**.
The remaining13 are intentional retained sources, not additional completed moves.
The [verification index](../project_records/current_layout/repository_verification_index.json)
lists actual current paths and proposed V2 destinations. Proposed destinations
for retained files are not installed entry points. New documentation is not an
original migration entry.

## Mandatory gates

| Gate | Requirement |
|---|---|
| M1 - Source and science | Exact public/source identities, all790 dispositions, protected contracts/AccessGuards/run markers, scientific settings and recorded results are preserved |
| M2 - Security | No unmitigated sensitive exposure in the public tree or history introduced by integration; no LOCAL_ONLY audits, private datasets, weights or caches |
| M3 - Current navigation | Current source/configuration links resolve; no new unreviewed broken references or duplicate active scientific implementations |
| M4 - Honest scope | Original/public-safe/adapted identities and missing inputs are distinct; no claim of full experiment replay or native Workbook validation |
| M5 - Applicable policy | Repository/owner/organization rules and required CI permit the documented exception; no mandatory zero-broken-link or exact-reproduction rule is overridden |

Adding this document cannot waive an applicable external requirement. A required
GitHub check must not be bypassed. The release assessment must recheck mutable
remote rules, the public main baseline and the exact candidate tree before
publication. New findings or changed exception identities invalidate acceptance.

## A - Retained legacy compatibility inventory

Actual outcome: **13 NOT MOVED** -12 preserve immutable historical connections and
one notebook lacks authentic SHA-associated preservation metadata. Release
classification: KNOWN_EXCEPTION. PublicH1 bytes below are unchanged.

| ID | Exact retained source/current location | PublicH1/current SHA-256 | Binding connection or reason |
|---|---|---|---|
| A01 | `RAG/E6_REPRODUCIBILITY.md` | 6aaed1600d38cccfffa3d63e3cf82c0b1032e356f741f2c9003faf7bab710aaa | Immutable document and outgoing relative-link context |
| A02 | `RAG/results/phase3_e11_task_adaptation/E11_DATA_AUDIT.md` | 2767b8f0e286deafd6ca6f5467ac393c9bf3ec55c8400c75b2da10643b2c544c | Immutable document and outgoing relative-link context |
| A03 | `RAG/results/phase3_e9_claim_verification/factcg_gpu/factcg_backend.py` | 1e72485f9458ffd87ff8503f7ccdbe4fdd19e05f2a3bd0283607f94fb0f4a36e | E11_DATA_AUDIT.md:74 |
| A04 | `RAG/results/phase3_e9_claim_verification/minicheck_gpu/run_minicheck_gpu.py` | cb140483019a2c9885a3d858ebbfaf8981f52d354f2c108542251d5847bed0ef | E11_DATA_AUDIT.md:76 |
| A05 | `RAG/results/rag_e6_v1/E6_PROTOCOL.md` | e921dc332d4038edaae3c964d8497c78ce7f1b1bda69ec4444d424de7d889e96 | E6_REPRODUCIBILITY.md:54 |
| A06 | `RAG/results/rag_e6_v1/E6_RESULTS.md` | 0f09eb299ce928ca62bccdeb423b4016728ca5029f56052fcfcbd1a336a4ddd0 | E6_REPRODUCIBILITY.md:55 |
| A07 | `RAG/results/rag_e6_v1/config/completion_manifest.json` | b6dcb439b6a4791391afce55027831d746d4b007e1929043037816becdef566b | E6_REPRODUCIBILITY.md:46 |
| A08 | `RAG/results/rag_e6_v1/config/run_config.json` | d50061c212e1166c13a757aff3840f059352b21b7fa91cab76db5fbc994dd5bc | E6_REPRODUCIBILITY.md:33 |
| A09 | `RAG/results/rag_e6_v2/scripts/nli_backend.py` | b2ab335aa8e856af65db64f6ba141c57090accc96642525cc2467f27e14f0702 | E11_DATA_AUDIT.md:73 |
| A10 | `RAG/results/rag_e6_v3/scripts/evaluate_v3.py` | fd6a041ac07201f702a0927628d01e58060ed4e5ed3d1ab5cc0b9d468a251893 | E11_DATA_AUDIT.md:77 |
| A11 | `RAG/results/rag_e6_v3/scripts/hhem_backend.py` | 84a84df1a75563a57286291276abe91e6b490327a7ca662810c3c410ce0a6cb0 | E11_DATA_AUDIT.md:75 |
| A12 | `codex/canonical_fold_generation_metadata.json` | bca7da770d1748028ffb4cb89c597b6aabedf5a9ff97a07e0f9f6827a0f0d6b1 | E11_DATA_AUDIT.md:16 |
| A13 | `codex/data/shroom_ensemble.ipynb` | 53e60b98c7eba15aa3fde27559885bdae70bf936513dfff60fda5c6a01486d03 | SHA/timestamp evidence and protected execution-matrix reference |

**Evidence and age.** These files existed at public baseline
11822d92070cd29360445cb4dacd8d110c655248. The source identities and original/public
metadata differences predate this release preparation. Retaining their old local
paths is an explicit migration-design decision, not a claim that every historical
scientific process needs those paths in a new implementation. Moving the unchanged
document closure to the proposed V2 targets adds10 broken references.

**Current code and usability.** All actual locations remain available through the
research guide and current index. Authenticated H1 snapshots preserve public byte
identity and the original namespace. They do not supply different privateH0 bytes,
datasets, run markers, model assets or original filesystem chronology. The
historical commands are not verified direct commands for the new checkout.

**Acceptance and prohibition.** Retention is acceptable for this source release;
790/790 relocation is not mandatory under this policy. It would not be acceptable
under a binding rule that forbids legacy locations, missing source identity or
unsupported scientific claims. M1-M5 still apply.

**Future resolution.** Relocate only for a concrete verified dependency need,
with authorization for any protected document/consumer change and preserved
historical originals. For A13, obtain authentic metadata associated with the exact
notebook SHA. Its publicSHA53e60b98c7eba15aa3fde27559885bdae70bf936513dfff60fda5c6a01486d03
must not inherit the timestamp recorded for originalSHA
e2b8e7737771ab7b50ccf9e9acf7d08977c6510179e22ff1ed667725c9dba7c7.
Git commit dates are not original filesystem timestamps. Do not fabricate evidence
or create duplicate active implementations to increase the migration count.

## B - Three historical original-H0 checksum mismatches

Actual outcome: **3 FAIL**. Release classification: KNOWN_EXCEPTION.

| ID | Exact current public record | Expected originalH0 SHA-256 | Observed publicH1/current SHA-256 | Provenance entry |
|---|---|---|---|---|
| B01 | [E11D_RESULTS.json](../research/experiments/phase3_advanced_methods/e11_transformer_finetuning/e11d_training/E11D_RESULTS.json) | 818fdd8fa9810f0932b95ab4dee608baa1de514b2f4d4c8b864b65cd931dd354 | d72c620d1abf44a91fb7b42635fb7a9a056da7cf2d65c92952a13adafbe20dd2 | /278 |
| B02 | [E11E_RESULTS.json](../research/experiments/phase3_advanced_methods/e11_transformer_finetuning/e11e_training/E11E_RESULTS.json) | 95e7857cbf154e08d20d416fd4d86dfe13544e475465a3cf1d7af14e0effe79c | 97b439664b316ed55feea4263278cf067d33768252c376488fe6033ef514c9af | /304 |
| B03 | [E11E_TRAINING_AUDIT.json](../research/experiments/phase3_advanced_methods/e11_transformer_finetuning/e11e_training/E11E_TRAINING_AUDIT.json) | 2444ec4c96fbcee7a19aba274c4a8c098d026e37471128cd8077fdcba427eafc | 2093eb7dd855ff50c45692c9d2c986c1e23bc4498ff312467cf223e6bbf8dd86 | /306 |

**Evidence and age.** The unchanged
[source-provenance record](../manifests/source_provenance.public.json), at entries
278/304/306, identifies PUBLIC_SAFE_DERIVATIVE_SHA256 projections with private
fields/paths removed. The observed bytes already exist at the initial public
root da6568ceb67c277dc4a877549fea32a702251e74. They were not introduced by physical
migration. The original expected values in the D/E SHA256SUMS records remain
unchanged. Original private artifacts were not independently recovered/compared;
the recorded claim that scientific values were retained is not a new numerical
verification performed by release preparation.

**Current code and usability.** PublicH1 source integrity passes independently.
Private-original hash requirements do not pass against the derivatives. Historical
runtime reproduction remains unverified; the public records remain readable.

**Acceptance and prohibition.** Preserving privacy-safe records with these explicit
FAILs is acceptable for the source portfolio. Restoring private fields to obtain
a public checksum PASS is not an acceptable remedy. A mandatory exact-H0 replay
requirement would prohibit treating the exception as satisfied. M1-M5 still apply.

**Future resolution.** Use the authentic exact private originals only in a separately
authorized isolated context when original replay is required. Never refresh a
frozen expected hash or manufacture a replacement historical artifact.

## C01 - Immutable E11 audit reference

Exact document:
[RAG/results/phase3_e11_task_adaptation/E11_DATA_AUDIT.md](../RAG/results/phase3_e11_task_adaptation/E11_DATA_AUDIT.md),
line67.

Original URL: ../../../codex/evaluation_protocol_decision.md.

Actual current result: **FAIL - ORIGINAL_LINK_STILL_BROKEN**.

Release classification: KNOWN_EXCEPTION.

The immutable publicH1 auditSHA is
2767b8f0e286deafd6ca6f5467ac393c9bf3ec55c8400c75b2da10643b2c544c.
Its historical readers in e11c/e11c_production.py and
e11c_training/prepare_training.py retain originalH0 requirement
20760181a13735b10ca3bf867b3132e5526dbd5f7e8a78cc39b9185829ba6cb4.
Source-provenance entry128 separately records this public-safe path/identifier
projection. Public identity and original-H0 identity are not interchangeable.

**Evidence and age.** The URL worked in the original public layout. It became
broken after earlier relocation of the protocol; the audit bytes were not changed.
The issue predates this policy, not the original migration baseline.

**Current code and usability.** The
[current protocol](../research/data_and_evaluation/canonical/protocols/evaluation_protocol_decision.md)
and [exact baseline protocol](https://github.com/spyroskontakis/shroom-hallucination-detection/blob/11822d92070cd29360445cb4dacd8d110c655248/codex/evaluation_protocol_decision.md)
are valid references. Current navigation identifies them. They do not repair the
original link. Historical source integrity remains protected; the broken citation
alone does not invalidate the scientific work.

HISTORICAL_AUDIT_IMMUTABLE: true.

CURRENT_REFERENCE_VALID: true.

ORIGINAL_LINK_STILL_BROKEN: true.

**Acceptance and prohibition.** Publishing the immutable historical audit with
this explicit limitation and valid alternatives is acceptable under this bounded
source-release policy. It is not acceptable if a mandatory publication/CI rule
requires that original link itself to resolve or requires zero historical broken
links. Documentation cannot waive that rule. M1-M5 still apply.

**Future resolution.** Any URL-only current-document remedy is a protected whole-file
change and needs separate explicit authorization, independently current identity
updates and preserved original objects/contracts. No protected URL or historical
expected hash is changed by this policy.

## D01 - Full historical runtime reproduction

Exact scope: canonical evaluation and E1-E11 sources/configurations identified in the
[research guide](../research/README.md) and verification index.

Actual result: **NOT_VERIFIED**. Release classification: KNOWN_EXCEPTION.

**Evidence and age.** Original datasets, model assets, generated features/evidence,
private preservation records, original run context and some authentic metadata
are outside the public package. This limitation predates the reorganized release.
Source checks and isolated synthetic tests do not supply those artifacts.

**Effects.** Source exploration and the supported IO/library tests remain useful.
A clean public clone is not certified to reproduce the recorded metrics or run
all historical producers. The README distinguishes dev-499, canonical-561 OOF and
retrospective official-test results.

**Acceptance and prohibition.** This is acceptable for a qualified research-source
portfolio, not a certified reproducible runtime release. A binding requirement for
exact numerical replay would prohibit acceptance. M1-M5 still apply.

**Future resolution.** Separately approve an isolated run with authentic inputs,
models, original evidence and safe output roots. Do not infer runtime PASS from
file migrations or synthetic fixtures.

## E01 - Native Workbook authoring runtime

Exact source:
[E6-v3 build_csv.mjs](../research/experiments/phase2_rag_features/e6_feature_extensions/v3/error_analysis/build_csv.mjs).
Related tests:
[Node authoring unit tests](../research/shared_tools/tests/test_node_authoring.mjs).

Actual production runtime result: **NOT_VERIFIED**. Release classification: KNOWN_EXCEPTION.

**Evidence and age.** The prior host probe reported ERR_DLOPEN_DISABLED. This was
observed before this policy; it does not establish that the historical original
runtime failed. The fixture tests validate the limited authoring/IO interface and
scientific render fragment, not the production native Workbook implementation.

**Effects and acceptance.** Native authoring is not advertised as verified.
Source publication with this limit is acceptable; a required native-production
validation gate would prohibit acceptance. M1-M5 still apply.

**Future resolution.** Test the exact pinned native runtime in a separately approved
compatible environment. Do not bypass native-addon restrictions or run production
Workbook workflows as part of source-release preparation.

## Additional unchanged capability and historical evidence

The original Module4 case, at research/experiments/phase2_rag_features/e5_rag/modules/module4/historical_release_v1/tests/test_verify_module4.py, VerifierTests.test_symlink_escape_rejected, is **SKIPPED** when the host cannot create the file link. Other negative tests do not convert that case to PASS. A mandatory
all-platform-capability gate would need its own real test, not a documentation waiver.

The E8 source research/experiments/phase2_rag_features/e8_rf_tuning/historical_implementations/report_e8.py, line138, SHA-256 7699f5dbc0d383994028ae7ebbc5ba38bf828ca1befb2341f4049e5eba13675a, retains its original SyntaxError. The E7 initial record at research/experiments/phase2_rag_features/e7_selective_rag/configs/security_preflight.json retains its original operational write violations. Both remain historical evidence. They are not repaired scientific implementations or fresh
runtime successes. The preserved renderer correction is a distinct source.

## Verification and release interpretation

Run the unchanged [offline verifier](VERIFICATION.md). It keeps the original
findings and deterministic strict exit status. With the known E11/H0 findings,
strict exit1 is expected and is not relabelled a historical PASS. KNOWN_EXCEPTION
is a release-acceptance classification, separate from the underlying audit result.

All mandatory gates must pass for the exact candidate. Only then may its local
release assessment be MERGE_READY_WITH_DOCUMENTED_EXCEPTIONS. Any new or unmitigated
source, privacy, active-navigation or mandatory-policy failure requires
NOT_MERGE_READY. A separate explicit authorization is always required for public
push, PR, merge, tag or release.
