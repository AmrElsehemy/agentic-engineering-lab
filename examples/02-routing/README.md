# 02 — Routing and Orchestration

This example routes a request to one of three bounded specialist contracts:

- `evaluation`
- `production`
- `agent-pattern`

Requests that do not match clearly go to `human-review` instead of being guessed.

## Run

```bash
python routing.py "How should we evaluate tool selection?"
python routing.py "How do we secure and observe deployment?"
python routing.py "Show me a tool-calling pattern"
```

The implementation is deliberately deterministic before adding an LLM router. This makes route choices explainable and gives us a baseline for later model-based routing evaluation.

## Production questions

- What is the acceptable confidence threshold for automated routing?
- What happens when multiple routes match?
- How are route changes regression-tested?
- Which requests must always go to human review?
