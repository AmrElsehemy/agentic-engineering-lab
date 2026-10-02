# Agent Evaluation Rubric

The lab evaluates the agent at the control boundary, not only on whether a model returns fluent text.

| Check | Pass condition |
|---|---|
| Forced tool selection | The first model response contains `get_training_plan` as a structured tool call |
| Tool authorization | The tool is allowlisted and unknown tools are rejected |
| Argument validation | Invalid days or oversized goals fail before execution |
| Tool execution | The validated local tool executes exactly once |
| Handoff | The tool result is added to the conversation |
| Final response | A second model response is generated after the tool result |
| Privacy | Default traces redact content and tool results |
| Side-effect boundary | Any future side-effecting tool requires explicit approval |

Run dependency-free checks with:

```bash
python evaluate.py
```

Run the live Foundry check after Entra configuration with:

```bash
python evaluate_live.py
```

The live evaluator prints pass/fail facts only. It does not print tokens, raw prompts, or raw model output.
