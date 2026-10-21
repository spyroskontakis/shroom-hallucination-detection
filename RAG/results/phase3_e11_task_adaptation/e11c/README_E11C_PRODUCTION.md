# E11-C production continuation

The user authorized the exact frozen complement: 11,700 candidates, 3,900 per
task. The 300 pilot candidates, including its two terminal uncertain answers,
are excluded from every production request. Original preparation and pilot
files remain unchanged. New row-level files live in ignored
`private/production_11700/`.

`e11c_production.py` scopes the existing frozen request, Batch, and parser
helpers to the complement, preserving original candidate order, request bodies,
custom IDs, 500-request shards, and three-attempt technical retry limit.
Submission requires a passing saved preflight and `--execute-api`; existing
submission receipts are skipped, while ambiguous submission intents stop the
run for reconciliation. Never run the original full-pool submission command.

Commands from this directory:

```powershell
python e11c_production.py preflight
python e11c_production.py submit --attempt 1 --execute-api
python e11c_production.py download --attempt 1 --execute-api
python e11c_production.py parse --attempt 1
```

Repeat download only while batches remain nonterminal; saved downloads are
skipped. Parsing requires all shards to be terminal. Only when the parse report
has retryable failures, prepare the next round with `prepare-retry --attempt 2`
(or 3), then submit/download/parse that round. The existing helper enforces the
frozen delay. Definitive answers and uncertain answers are never retried.

After the final round has no pending retries:

```powershell
python audit_e11c_production.py --attempt 1
```

Use the actual last round number. The audit consolidates all 12,000 candidate
IDs exactly once and exports definitive supervision separately from the full
ledger. It does not select folds, purge leakage, balance labels, train, or
evaluate. Costs use returned usage and the frozen pricing assumptions, and are
estimates rather than invoice amounts. Preflight and final logs cover all
E11-C tests and the broader E11 offline tests.
