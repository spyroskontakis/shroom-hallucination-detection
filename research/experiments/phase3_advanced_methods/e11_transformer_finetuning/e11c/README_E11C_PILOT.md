# E11-C operational pilot

The user authorized exactly 300 unique candidates (100/task) and the frozen
operational retry policy, not the remaining 11,700. Selection takes the first
100/task in the existing candidate hash order, independently of any labels.

`e11c_pilot.py` binds the existing request, guarded Batch and result-parser helpers
to `private/pilot_300/` in an isolated process context. It restores all bindings
on exit. It never modifies protocol, prompt, schema, model, reasoning, output
budget, retries or original 12,000-row artifacts. All row-level files are ignored
by Git. The pilot hard-checks protocol content SHA256:

`792bbe4ef1d0752e606c81dc511684f7bb0a051b2a5c24a937c49d7cb928f818`

Commands from this directory:

```powershell
python e11c_pilot.py prepare
python e11c_pilot.py submit --attempt 1 --execute-api
python e11c_pilot.py download --attempt 1 --execute-api
python e11c_pilot.py parse --attempt 1
```

Submission journals prevent duplicate submission. Download while nonterminal
only reports status; parse only after the terminal receipt exists. If parsed
results have retryable failures, use `prepare-retry --attempt 2`, then the same
submit/download/parse actions for round 2, respecting the frozen delay. Round 3
is the final possible round. Never retry definitive or uncertain answers.

When the final used round has no pending retries:

```powershell
python e11c_pilot.py audit --attempt 1
```

Replace 1 only with the actual final round. This records overall/task label
counts, actual returned usage across all attempts, Batch lifecycle timing,
frozen-price cost estimate, 40x full-pool extrapolation and provenance hashes.
Usage-based estimates are not provider invoices; no cache discount is assumed.
Per-request latency is not supplied by Batch. Never manually inspect/correct
semantic labels or alter the protocol based on these results.

## Reuse boundary

Pilot requests retain the original full-pool custom IDs. Raw response files,
attempt ledger and parsed semantic labels (including final uncertain answers)
must be retained. Before a later authorized full run, its execution plan MUST
import these validated pilot outcomes and exclude all terminal semantic answers
from further submissions. The original prepared 12,000-row shards are historical
preparation artifacts, not a safe continuation command after this pilot.
Do not run the original full-pool submit command. No full-run integration or
remaining-pool submission is authorized in this step.

All additions are pilot-only files. Existing E11-C preparation artifacts are
verified against their frozen preparation manifest; E11-A/B are not modified.
