# Local Azure alternate-model rescue

Run from a PowerShell session that already has `AZURE_OPENAI_API_KEY`,
`AZURE_OPENAI_BASE_URL`, and `AZURE_OPENAI_DEPLOYMENT` set. Do not paste the key
into commands shared with others. Python 3.11+ and the `openai` Python package
are required for live execution; repository modules are imported beside the script.

```powershell
Set-Location 
python RAG/results/phase3_e11_task_adaptation/e11c/run_azure_alternate_rescue.py --dry-run
python RAG/results/phase3_e11_task_adaptation/e11c/run_azure_alternate_rescue.py --execute-api
```

If needed, install the client into that Python environment with
`python -m pip install openai`. Dry-run does not import or instantiate the client,
write files, or make API calls. It requires the same environment checks as live
execution. Missing variables in Codex do not prevent offline unit testing.

The script loads and validates the four existing frozen PG requests. Only the
model field changes to `gpt-5-mini`. Medium reasoning, prompt, schema, source
reference, input formatting, output budget and decoding defaults stay unchanged.
Calls use Azure's synchronous Responses endpoint, with SDK retries disabled.
There are at most three alternate-model attempts per candidate, using the frozen
60/300-second retry delays. Terminal labels, including uncertain, are cached and
never resent. An interrupted request with an intent but no receipt stops for
manual reconciliation rather than risking duplicate execution. HTTP failures are
stored as status codes only; SDK exception text and credentials are not logged.

Azure outputs and provenance live only in ignored `private/azure_alternate_rescue/`.
Separate `E11C_ALTERNATE_MODEL_RESCUE_AUDIT.json`, `.md`, and `_MANIFEST.json`
summarize the judgments and hashes. A failed/exhausted call is recorded as a failure,
never converted into a label. A returned model outside the gpt-5-mini family stops
the run for review. No unsupported parameter is silently removed.

The 11,887 definitive gpt-5.6-sol labels, 109 uncertain outcomes and four original
pending statuses remain authoritative and unchanged. Rescue judgments are never
merged into that pool. Costs are reported as unavailable because the Responses
API does not expose Azure billed cost; token usage is recorded when supplied.

Microsoft documentation supports medium reasoning, structured output and Responses
for gpt-5-mini: https://learn.microsoft.com/en-us/azure/foundry/openai/how-to/reasoning
and https://learn.microsoft.com/en-us/azure/foundry/openai/how-to/responses .
