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

## Run with a Microsoft Foundry-compatible endpoint

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export FOUNDRY_OPENAI_BASE_URL="https://your-resource.openai.azure.com/openai/v1/"
export FOUNDRY_API_KEY="..."
export FOUNDRY_MODEL="your-deployment-name"
python agent.py --goal "prepare for a HYROX race"
```

Use the endpoint and authentication method appropriate for your Foundry project. Never commit credentials.

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
- There is no persistence, authentication, tracing, or evaluation harness yet.
- The output is not medical advice or individualized coaching.
- A production implementation needs stronger input validation, authorization, observability, and tests.
