# 01 — Single Agent + Controlled Tool Call

This example demonstrates a small agent loop with the controls a production system needs around tool use:

1. The model **chooses** whether to call a tool (`tool_choice=auto`); a general question gets a direct answer.
2. The application allowlists, parses and validates every tool call. Bad calls are returned to the model as errors, never crash the loop, and never run.
3. A read-only tool (`get_training_plan`) runs automatically.
4. A side-effecting tool (`save_plan`) runs only after explicit human approval. No terminal means no approval.
5. The loop is bounded: at most 4 model calls, and the last one runs with tools disabled.
6. Every step emits a redacted trace event.

The example is self-contained: it needs only this directory plus the shared `controls.py` and `observability.py` at the repo root.

## Run the deterministic demo

A scripted model drives the real loop, tools and approval gate. No credentials, no network.

```bash
python agent.py --demo            # save_plan is denied
python agent.py --demo --approve  # save_plan is approved and appends to saved_plans.jsonl
python -m unittest discover -s tests -v
```

## Run with Microsoft Foundry and Microsoft Entra ID

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export FOUNDRY_PROJECT_ENDPOINT="https://your-resource.services.ai.azure.com/api/projects/your-project"
export FOUNDRY_MODEL="your-deployment-name"
az login
python check_foundry_auth.py
python agent.py --goal "Create a 4 day a week HYROX plan"
```

`DefaultAzureCredential` uses the Azure CLI identity locally. The Entra token scope is `https://ai.azure.com/.default`. Your signed-in identity needs the **Foundry User** role for inference. Add **Azure Monitor Reader** later when we implement tracing and observability evidence.

The project endpoint must have this format:

```text
https://<resource-name>.services.ai.azure.com/api/projects/<project-name>
```

The model value must be the exact **deployment name**, not only the underlying model family name. Never commit credentials.

The preflight command only requests an Entra token and prints its expiry; it never prints the token itself.

The live loop prints one JSON trace event per step. Arguments, results and content are redacted by default:

```text
{"event": "model_response", "step": 1, "tool_calls": [{"id": "...", "name": "get_training_plan", "arguments": "<redacted>"}], "content": null}
{"event": "tool_executed", "tool": "get_training_plan", "validated": true, "side_effect": false, "outcome": "ok", "result": "<redacted>"}
{"event": "model_response", "step": 2, "tool_calls": [], "content": "<redacted>"}
```

`outcome` is one of `ok`, `blocked` (unknown tool), `invalid_arguments`, `denied` (no approval) or `skipped` (extra call in one turn). When a human is asked, an `approval` event records the decision.

`python evaluate_live.py` (from the repo root) runs three live scenarios and asserts on those events: a tool is used for a plan request, no tool is used for a general question, and a save request is denied without approval. Model behaviour is non-deterministic, so re-run a failure before drawing conclusions.

## Opt-in Foundry observability

The agent includes OpenTelemetry hooks compatible with Microsoft Foundry tracing. Content is redacted by default.

For local console spans:

```bash
export FOUNDRY_TRACE=console
python agent.py --goal "Create a 4 day a week HYROX plan"
```

For Foundry/Azure Monitor export, connect an Application Insights resource to the Foundry project, grant the identity appropriate monitoring access, and run:

```bash
export FOUNDRY_TRACE=azure-monitor
python agent.py --goal "Create a 4 day a week HYROX plan"
```

Do not enable `FOUNDRY_TRACE_CONTENT=true` for production. It records prompts, tool arguments, and model output and is intended only for controlled local debugging.

## Production controls in this example

| Control | Where | Tested by |
|---|---|---|
| Tool allowlist | `controls.authorize_tool` | `test_unknown_tool_blocked` |
| Argument validation, extra/missing/malformed rejected | `execute_tool` | `test_bad_arguments_return_errors_instead_of_crashing`, `test_missing_days_is_not_invented` |
| One tool call per turn | `run_agent` | `test_only_first_tool_call_runs` |
| Bounded loop, final call with tools off | `run_agent` | `test_loop_is_bounded_and_last_call_has_no_tools` |
| Side effects need approval, default deny | `execute_tool`, `cli_approver` | `test_side_effect_denied_by_default`, `test_side_effect_runs_once_when_approved` |
| No approval prompt for invalid input | `execute_tool` | `test_invalid_save_never_asks_for_approval` |
| Model cannot choose persisted content | `save_plan` regenerates the plan | by construction |
| Redacted traces | `emit_trace` | `test_trace_is_redacted_by_default` |
| Goal length cap | `controls.validate_goal` | `test_long_goal_rejected_before_any_model_call` |

## Prototype-only API-key fallback

For a short-lived test environment only, you can use the Azure OpenAI v1 endpoint and a resource key:

```bash
export FOUNDRY_OPENAI_BASE_URL="https://your-resource.openai.azure.com/openai/v1/"
export FOUNDRY_API_KEY="..."
export FOUNDRY_MODEL="your-deployment-name"
python agent.py --goal "Create a 4 day a week HYROX plan"
```

Microsoft recommends Entra ID for production because API keys are broad, difficult to scope, and harder to audit.

## Architecture

```text
User goal
   |
   v
Model (tool_choice=auto) --- no tool --> direct answer
   |
   +--> tool call --> allowlist --> parse + validate --> error? --> back to model
                                         |
                       read-only tool <--+--> side-effect tool --> human approval --> deny: error to model
                       (runs)                                                  \--> approve: runs
   |                                                                                  |
   +<------------------------------ tool result ------------------------------------+
   v
Final answer (max 4 model calls)
```

## Production questions exposed by this example

- Which tool calls are safe to execute automatically, and which need a human?
- What happens when the model supplies a plausible but invented argument? Schema validation alone does not catch it; this example removes the field the model used to invent (`athlete`) and instructs it to ask for `days_available`, but the prompt is a mitigation, not a guarantee.
- What should be logged for replay and audit, and what must never be logged?
- How would evaluation detect an unsafe or low-quality plan?

## Known limitations

- Both tools are deterministic and educational; `save_plan` writes a local file, not a real external system.
- Approval is a terminal prompt by the person running the script. There is no approver identity, authorization model or durable audit log.
- Argument validation checks type, range and shape, not whether the model took the value from the user's message. `evaluate_live.py` checks outcomes, not argument grounding.
- No persistence of conversation state, retries or rate limiting.
- Tracing is opt-in and tested only locally; Azure Monitor export is not covered by CI.
- The output is not medical advice or individualized coaching.
