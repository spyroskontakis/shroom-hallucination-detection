# E11-C operational pilot: PASS

Teacher: `gpt-5.6-sol`, medium reasoning. Protocol content SHA256: `792bbe4ef1d0752e606c81dc511684f7bb0a051b2a5c24a937c49d7cb928f818`.

300/300 requests completed with valid structured output; zero failed requests, retries or schema failures. 298 definitive labels are reusable; 2 uncertain answers are preserved as terminal rejections. No semantic tuning or manual label correction.

| Task | Hallucination | Not hallucination | Uncertain |
|---|---:|---:|---:|
| DM | 61 | 39 | 0 |
| MT | 27 | 73 | 0 |
| PG | 35 | 63 | 2 |
| Total | 123 | 175 | 2 |

Uncertain proportion: 0.6667%.

| Returned usage | Input | Output |
|---|---:|---:|
| Total | 96,675 | 21,038 |
| Mean/request | 322.25 | 70.1267 |
| Median/request | 319 | 43.5 |
| Maximum/request | Not requested | 337 |

Reasoning tokens: 9,351, included in output. Cached input tokens: 0.

Pilot Batch cost estimate from returned usage: **$0.40373** at frozen prices ($4/M input, $20/M output, 50% Batch discount). Provider invoice not queried. Extrapolated 12,000-request cost: **$16.1492**, not guaranteed. No cache discount assumed.

Batch `private-service-id-withheld`: completed in 165 seconds from provider creation to completion; 62 seconds before in-progress, 91 seconds in-progress to finalizing, 12 seconds finalizing. Individual request latency is not exposed.

## Artifact hashes

- `private/pilot_300/candidates.jsonl`: `d1d7e18fc9a536b4a7996fde03a1502327bdded9d96d6d8fff61b131021a05db`
- `private\pilot_300\round_1\requests.jsonl`: `54604c07739cb9b724782deac99440e3d0c4f94385237c318d7dd2433ab23702`
- `private\pilot_300\round_1\batch_001\output_file.jsonl`: `de40b8e9aed86ddb50ef70df8b6679ca32142da278dcfca3623607fd985a0e23`
- `private/pilot_300/parsed_labels.jsonl`: `f814498298eefa7c907f5a5858abde810f3afc9449c407076bb486b5f54a0217`
- `E11C_PILOT_AUDIT.json`: `19faf0dcfa5ea89acd28477aab1c956762105a20fb93729fd0bc1a5baced7cbe`
- `E11C_PILOT_MANIFEST.json`: `8d0cd7edd16a2c765f28609cb5f0d9f53f01dbd6c5135a7fc7b770fd080d85ae`

All row-level files are git-ignored. Raw responses and the complete parsed ledger are retained for exact replay. The original 12,000-row request shards must not be blindly submitted after this pilot: later integration must reuse these outcomes and exclude final semantic answers. The remaining 11,700 were not submitted.

No prompt/schema/model changes, student training, development evaluation, GPU/Modal jobs, official-test access, commit or push.
