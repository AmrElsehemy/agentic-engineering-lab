# 01 — Single Agent + Controlled Tool Call

This example demonstrates the smallest useful agent loop:

1. Receive a user goal.
2. Let the model request one explicitly defined tool.
3. Validate and execute the tool locally.
4. Return the tool result to the model.
5. Produce a final answer.

The tool is deliberately bounded. It does not call external systems or perform side effects.

## Run the deterministic demo

From this directory:

```bash
python agent.py --demo --goal "prepare for a HYROX race"
```

The demo requires no API key and proves that the tool contract and validation path work.

## Run with Microsoft Foundry and Microsoft Entra ID

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export FOUNDRY_PROJECT_ENDPOINT="https://your-resource.services.ai.azure.com/api/projects/your-project"
export FOUNDRY_MODEL="your-deployment-name"
az login
python check_foundry_auth.py
python agent.py --goal "prepare for a HYROX race"
```

`DefaultAzureCredential` uses the Azure CLI identity locally. The Entra token scope is `https://ai.azure.com/.default`. Your signed-in identity needs the **Foundry User** role for inference. Add **Azure Monitor Reader** later when we implement tracing and observability evidence.

The project endpoint must have this format:

```text
https://<resource-name>.services.ai.azure.com/api/projects/<project-name>
```

The model value must be the exact **deployment name**, not only the underlying model family name. Never commit credentials.

The preflight command only requests an Entra token and prints its expiry; it never prints the token itself.

The live loop uses a **required** `get_training_plan` tool choice. It fails if the model does not return that tool call; a direct text response is not accepted as an agent execution. The program prints JSON trace events for inspection:

```text
{"event": "model_response", "tool_calls": [{"name": "get_training_plan", "arguments": {...}}]}
{"event": "tool_executed", "tool": "get_training_plan", "validated": true, "result": {...}}
{"event": "model_response", "phase": "final", "tool_calls": [], "content": "..."}
```

## Opt-in Foundry observability

The agent includes OpenTelemetry hooks compatible with Microsoft Foundry tracing. Content is redacted by default.

For local console spans:

```bash
export FOUNDRY_TRACE=console
python agent.py --goal "prepare for a HYROX race"
```

For Foundry/Azure Monitor export, connect an Application Insights resource to the Foundry project, grant the identity appropriate monitoring access, and run:

```bash
export FOUNDRY_TRACE=azure-monitor
python agent.py --goal "prepare for a HYROX race"
```

Do not enable `FOUNDRY_TRACE_CONTENT=true` for production. It records prompts, tool arguments, and model output and is intended only for controlled local debugging.

## Production controls in this example

The loop allowlists `get_training_plan`, rejects unknown tools, permits only one tool call per turn, bounds the goal length, validates tool arguments, and has no side-effecting tool. Any future side-effecting tool must pass through explicit human approval before execution.

## Prototype-only API-key fallback

For a short-lived test environment only, you can use the Azure OpenAI v1 endpoint and a resource key:

```bash
export FOUNDRY_OPENAI_BASE_URL="https://your-resource.openai.azure.com/openai/v1/"
export FOUNDRY_API_KEY="..."
export FOUNDRY_MODEL="your-deployment-name"
python agent.py --goal "prepare for a HYROX race"
```

Microsoft recommends Entra ID for production because API keys are broad, difficult to scope, and harder to audit.

## Architecture

```text
User goal
   |
   v
Model with tool schema
   |
   +--> get_training_plan (validated local tool)
   |          |
   |          v
   +---- tool result ------> Model final response
```

## Production questions exposed by this example

- What inputs are allowed into the tool?
- Which tool calls are safe to execute automatically?
- How are side effects separated from planning?
- What should be logged for replay and audit?
- How would evaluation detect an unsafe or low-quality plan?

## Known limitations

- The tool is deterministic and educational.
- There is no persistence, tracing, or Foundry evaluation integration yet.
- The output is not medical advice or individualized coaching.
- A production implementation needs stronger input validation, authorization, observability, and tests.
