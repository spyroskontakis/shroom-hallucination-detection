# E9 frozen full-run authorization

The user authorized the full canonical 561-row decomposition, E9-A evaluation,
then exact Bespoke-MiniCheck-7B hardware/dependency preflight and E9-B only if safe.
This supersedes earlier smoke-only execution limits, without modifying the frozen
decomposition prompt, schema, validator, retry/fallback policy, model, temperature
or Amendment 01. The user accepted observed atomicity/self-containment limitations.

The full-run orchestrator delegates every payload to the unchanged decomposer.
It consolidates matching semantic-v2 smoke caches, groups identical hyp/task payloads
to avoid duplicate concurrent requests, and uses four independent request workers.
Concurrency does not change each payload, its maximum three attempts, validation,
fallback, task-specific reference policy, features, folds or RF settings.
Only hyp/task sample data enter API requests. IDs and split metadata remain local.

Exactly one E9-A configuration and, if executable, one E9-B configuration are
authorized. No tuning, extra variants, official-test access, committing or pushing.
Baseline verification uses saved artifacts without refitting E6-v3.

## Explicit continuation after HTTP 429

The user explicitly requested continuation from the blocked checkpoint. Transport
is now serialized with one second spacing to reduce rate pressure. Completed
responses for interrupted uncached rows are replayed through the unchanged validator,
so previous validation attempts are not discarded or bought again. The frozen
decomposer file remains byte-identical. No automatic retry of an HTTP availability
error was added; another such error still stops the invocation.
