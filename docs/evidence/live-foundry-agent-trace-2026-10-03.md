# Live Microsoft Foundry Agent Trace — 3 October 2026

> **Superseded by [4 October](live-foundry-agent-trace-2026-10-04.md).** This record describes the earlier forced-tool-choice version with no side-effecting tool. Keep it as history; do not cite it as evidence for the current code.

This is a sanitized record of the verified live run. Secrets, tokens, connection strings, raw prompts, and raw model content are omitted.

## Configuration

| Field | Value |
|---|---|
| Authentication | Microsoft Entra ID |
| Project endpoint | Microsoft Foundry project endpoint (not repeated here) |
| Deployment | `gpt-5.4-nano` |
| Tool policy | `get_training_plan` only |
| Side effects | None |
| Trace backend | Azure Monitor / Application Insights |

## Evaluator output

```text
LIVE PASS forced tool selection
LIVE PASS validated tool execution
LIVE PASS final model response after tool result
LIVE PASS final-answer consistency
LIVE PASS observability configured: azure-monitor
EXIT_CODE=0
```

## Sanitized event sequence

```json
{"event":"observability_configured","backend":"azure-monitor"}
{"event":"model_response","tool_calls":[{"name":"get_training_plan","arguments":{"days_available":5}}]}
{"event":"tool_executed","tool":"get_training_plan","validated":true}
{"event":"model_response","phase":"final","tool_calls":[]}
{"event":"quality_check","name":"training_plan_consistency","passed":true,"expected_days":5,"observed_schedule_days":[5]}
```

## What this proves

The live model requested a structured tool call; application code validated and executed the allowlisted tool; the tool result was handed back before the final response; a deterministic consistency check passed; and Azure Monitor tracing initialized successfully through Entra-authenticated local execution.

## What this does not prove

This is not a general production-readiness certification. Real side effects still require durable authorization, idempotency, retries, recovery, privacy review, and domain-specific evaluation. The example is evidence for one production-grade aspect: a controlled and observable tool-execution boundary.
