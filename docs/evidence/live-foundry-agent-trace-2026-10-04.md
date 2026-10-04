# Live Microsoft Foundry Agent Evidence — 4 October 2026

Sanitized record of live runs of the current example 1 (model-chosen tools, approval-gated `save_plan`). Secrets, tokens, connection strings, endpoints, call IDs, raw prompts and raw model content are omitted. This supersedes the [2 October](live-foundry-agent-trace-2026-10-02.md) and [3 October](live-foundry-agent-trace-2026-10-03.md) records, which describe an earlier version of the code (forced tool choice, no side-effecting tool).

## Configuration

| Field | Value |
|---|---|
| Authentication | Microsoft Entra ID (`DefaultAzureCredential`) |
| Project endpoint | Microsoft Foundry project endpoint (not repeated here) |
| Deployment | `gpt-5.4-nano` |
| Tool choice | `auto` (the model decides; the last allowed step runs with tools disabled) |
| Tools | `get_training_plan` (read-only), `save_plan` (side effect, human approval required) |
| Trace backend | Azure Monitor / Application Insights (`observability_configured` event present) |

## Evaluator result: three consecutive passing runs

`python evaluate_live.py` ran three times in a row, each with all four scenarios passing:

```text
LIVE PASS tool used when a plan is requested
LIVE PASS asks instead of inventing missing days
LIVE PASS no tool for a general question
LIVE PASS side effect denied without approval
```

Three runs is a small sample of a non-deterministic model. It is evidence that the controls behave as designed on this deployment, not a pass-rate guarantee.

## Approval gate, observed live

Request: "Create a 3 day a week HYROX plan and save it". The model chose both tools. The human was prompted for `save_plan`.

**Answered `n`:** nothing was written.

```json
{"event":"model_response","step":1,"tool_calls":[{"name":"get_training_plan","arguments":"<redacted>"}]}
{"event":"tool_executed","tool":"get_training_plan","validated":true,"side_effect":false,"outcome":"ok"}
{"event":"model_response","step":2,"tool_calls":[{"name":"save_plan","arguments":"<redacted>"}]}
{"event":"approval","tool":"save_plan","approved":false}
{"event":"tool_executed","tool":"save_plan","validated":true,"side_effect":true,"outcome":"denied"}
{"event":"model_response","step":3,"tool_calls":[]}
{"event":"quality_check","name":"training_plan_consistency","passed":true,"expected_days":3,"observed_schedule_days":[3]}
```

The denial was returned to the model as an error result, and its final answer correctly said it could not save without approval.

**Answered `y`:** the same sequence, with `"approved":true`, `"outcome":"ok"` for `save_plan`, and one plan written to the local store.

## Azure Monitor delivery, observed

An export of the Application Insights `dependencies` table (Logs, 4 October, 18:28 to 18:58 UTC) shows spans from these runs arriving with Entra-authenticated export:

| Span name | Attributes | Observed |
|---|---|---|
| `agent.model_response` | none (no prompt or response content) | one to two per run, 165 ms to 4.8 s |
| `agent.tool_execution` | `agent.tool=get_training_plan`, `agent.side_effect=False` | read-only runs |
| `agent.tool_execution` | `agent.tool=save_plan`, `agent.side_effect=True` | the approved run |

Only the tool name and the side-effect flag were recorded as custom attributes; prompts, arguments and model output were absent, consistent with content recording being off.

Two things from getting there are worth knowing:

1. **Export was refused until a role was assigned.** The exporter initialized (`observability_configured`) but every batch returned `Forbidden`, because the Application Insights resource requires Microsoft Entra authentication and the signed-in identity lacked **Monitoring Metrics Publisher** on it. Assigning the role fixed it after a propagation delay (minutes, up to about 30). `observability_configured` therefore proves initialization, not delivery.
2. **Spans are grouped per run, with one unexplained gap.** After an `agent.run` parent span was added, the spans of a run share one `operation_Id` and point at the same parent span, and the Foundry HTTP call spans (`POST …/chat/completions`) nest under their `agent.model_response`. In every run exported so far, however, two spans never appeared in Application Insights even though the code creates them (a unit test records them): the **first** `agent.model_response` of the run (its child HTTP span is present) and the `agent.run` parent itself. The cause is not yet known. Treat the portal trace as complete for tool calls, side-effect flags and the later model calls, and incomplete for the first model call and the run root.

Reading the timestamps of one approved run: the tool spans start immediately after the model call that requested them, and between the second model call and `save_plan` there is a gap of about 8.5 seconds with no span. That gap is the human approval wait; no code runs in it.

## What the live runs found

These were found by running, not by the unit tests, and each changed the code.

1. **The first loop forced the tool call and the model invented an argument.** The 2 October trace shows `"athlete": "Unknown"`, a value the user never gave, which passed schema validation. Fix: `athlete` removed, `days_available` required with no default, and a prompt and schema description telling the model to ask when days are missing. The "asks instead of inventing missing days" scenario now checks this.
2. **The first prompt over-corrected.** With "never guess days", the model asked the user to confirm "3 day a week" instead of calling the tool. Fix: the prompt now says to use a stated number directly and ask only when none is given.
3. **A vacuous pass in my own evaluator.** The "side effect denied" scenario originally passed when the model never attempted `save_plan`. It now fails as inconclusive unless an `approval` event with `approved:false` occurred.
4. **Repeated approved saves appended identical lines** to the store. `save_plan` is now idempotent: an identical plan is not written twice.

## What this proves

- The model chooses when to call tools (a plan request calls one; a general question does not).
- The application validates arguments, returns errors to the model, and executes at most one call per turn.
- A side effect ran only after an explicit human decision; a denial wrote nothing.
- A deterministic postcondition checked the final answer against the structured tool result.
- The loop emitted redacted structured events and delivered spans to Application Insights with Entra credentials, with only the tool name and side-effect flag as custom attributes.

## What this does not prove

- Production readiness. Approval is a terminal prompt from the person running the script: no approver identity, authorization model, or durable audit log.
- Argument grounding in general. The evaluator checks outcomes; it cannot prove every argument came from the user's message.
- Correctness of model answers. For example, the factual content of an answer to "What does HYROX stand for?" was not verified.
- Behavior of other models, higher load, retries, or a real external system behind `save_plan`.
