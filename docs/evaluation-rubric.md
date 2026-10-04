# Evaluation rubric

The lab evaluates the agent at the control boundary, not only on whether a model returns fluent text. Each check below names where it runs: unit tests and `evaluate.py` need no model or credentials; `evaluate_live.py` runs against a Microsoft Foundry project.

| Check | Pass condition | Where |
|---|---|---|
| Tool allowlist | Unknown tools are rejected and returned to the model as an error, never executed | unit tests, `evaluate.py` |
| Argument validation | Malformed JSON, extra or missing keys, out-of-range, boolean and string values fail before execution | unit tests |
| Model chooses tools | A plan request calls a tool; a general question calls none | `evaluate_live.py` |
| No invented arguments | With no number of days given, no tool runs and the model asks | `evaluate_live.py` |
| Call budget | One tool call per turn; at most 4 model calls; the last runs with tools disabled | unit tests |
| Side-effect approval | `save_plan` runs only after explicit approval; the default is deny; after a denial nothing is written | unit tests, `evaluate_live.py` |
| Approval precedes nothing invalid | A call that fails validation never asks for approval | unit tests |
| Idempotent side effect | Saving an identical plan twice writes one record | unit tests |
| Final-answer consistency | Schedule claims in the final prose do not contradict the structured tool result | unit tests, `evaluate.py`, `evaluate_live.py` |
| Privacy | Default traces and events redact content, tool arguments and results | unit tests |
| Observability | With `FOUNDRY_TRACE` set, the requested backend initializes; spans for the run, model calls, approval and tool execution are emitted | unit tests, `evaluate_live.py` |

The live evaluator can fail for the right reasons: the denied-side-effect scenario reports an inconclusive result unless a denial actually happened, so a model that never attempts the save cannot pass it.

Note on observability: `observability_configured` means the exporter started, not that data arrived. Confirm delivery in Application Insights (see the example README).

Run the checks:

```bash
python -m unittest discover -s examples/01-single-agent-tool-calling/tests
python evaluate.py
python evaluate_live.py   # needs Foundry configuration; see the example README
```

The live evaluator prints pass/fail facts only. It does not print tokens, raw prompts, or raw model output.
