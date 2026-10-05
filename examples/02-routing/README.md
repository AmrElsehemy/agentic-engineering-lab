# 02 — Routing

A deterministic router that sends a request to one of three bounded specialist contracts, or to a human when none applies.

## Contract

| Route | Chosen when the request mentions (word starts) |
|---|---|
| `evaluation` | evaluat…, regression, quality |
| `production` | deploy…, secur…, identity, observ… |
| `agent-pattern` | tool…, function…, agent… |
| `human-review` | none of the above (the fallback) |

`route_request(request)` returns a `Route(name, reason)`. The reason always says why.

## Behavior

- **No match:** the request goes to `human-review`. It is never guessed.
- **Several matches:** the highest-priority specialist wins (`evaluation`, then `production`, then `agent-pattern`) and the reason names the others, for example `also matched: agent-pattern (priority order applies)`.
- **Word starts only:** `agent` matches "agentic" and "agents" but not "management".
- **Empty input:** raises `ValueError`.

## Run

```bash
python routing.py "How should we evaluate tool selection?"
python routing.py "How do we secure and observe deployment?"
python routing.py "Show me a tool-calling pattern"
python -m unittest discover -s tests -v
```

## Failure modes and limitations

- Keyword routing misses paraphrases ("how do we know it still works?") and sends them to human review. That is the safe direction, but it is a coverage gap.
- Priority order is a design choice, not a correctness guarantee: a request that is mostly about deployment but mentions "evaluate" goes to `evaluation`.
- There is no confidence score, so there is no threshold to tune and no way to rank near-misses.
- No model is involved. This is the deterministic baseline against which a model-based router would later be evaluated.
- The router is not connected to the agent in example 01.

## Production questions

- What confidence threshold should allow automated routing?
- Which requests must always go to human review?
- How are route changes regression-tested?

See [ADR 002](../../docs/decisions/002-deterministic-routing-first.md).
