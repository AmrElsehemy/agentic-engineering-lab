# 02 — Routing

A deterministic router that sends a request to one of three named specialist routes, or to a human when none applies.

## Contract

| Route | Chosen when the request mentions (word starts) |
|---|---|
| `evaluation` | evaluat…, regression, quality |
| `production` | deploy…, secur…, identity, observ… |
| `agent-pattern` | tool…, function…, agent… |
| `human-review` | none of the above (the fallback) |

`route_request(request)` returns a `Route(name, reason, matched)`. The reason always says why, `matched` lists every specialist that matched, and `route.automated` is `False` for the fallback so a caller cannot mistake it for a specialist.

## Behavior

- **No match:** the request goes to `human-review`. It is never guessed.
- **Several matches:** the highest-priority specialist wins (`evaluation`, then `production`, then `agent-pattern`) and the reason names the others, for example `also matched: agent-pattern (priority order applies)`.
- **Word starts only:** `agent` matches "agentic" and "agents" but not "management".
- **Invalid input:** empty or over 1000 characters raises `ValueError`; non-string raises `TypeError`.

## Production controls in this example

| Control | Where | Tested by |
|---|---|---|
| Fallback to a person, never a guess | `route_request` | `test_unmatched_request_goes_to_human_review` |
| Fallback is machine-readable (`automated=False`) | `Route.automated` | `test_fallback_is_not_automated_and_specialists_are` |
| Overlaps are explicit, with fixed priority | `route_request` | `test_overlapping_matches_use_priority_and_say_so` |
| Request text cannot steer routing | keyword comparison only | `test_instructions_in_the_request_do_not_steer_routing` |
| Type and size limits (1000 chars) | `route_request` | `test_overlong_request_is_rejected`, `test_non_string_request_is_rejected` |
| Malformed rule table fails at import | `validate_rules` | `test_rule_table_validation` |
| Redacted traces, opt-in content | `emit_trace` | `test_trace_redacts_request_by_default`, `test_trace_includes_request_only_when_opted_in` |
| Quality gate on a labelled set | `evaluate_routing.py` | `EvaluatorTests`, CI |
| Deterministic | pure function | `test_routing_is_deterministic` |

## Evaluation

`golden.json` is the labelled set. `evaluate_routing.py` reports accuracy, fallback rate and wrong-route rate, and fails CI if accuracy drops below 0.9 or any request goes to the wrong specialist. A wrong route is worse than a fallback, so it has the tighter threshold. Cases marked `known_gap` are paraphrases the keyword router cannot handle; they are listed in the report and excluded from the thresholds, so the gap stays visible instead of silently lowering or inflating the score.

Changing a rule means changing `golden.json` on purpose.

## Tracing

`route_request(text, trace=True)` (or `--trace` on the command line) prints a `route_decision` event with the route, matched specialists, request length and a 12-character hash for correlation. The request text is redacted unless `ROUTING_TRACE_CONTENT=true` (local debugging only).

## Run

```bash
python routing.py "How should we evaluate tool selection?"
python routing.py "How do we secure and observe deployment?"
python routing.py "Show me a tool-calling pattern"
python routing.py --trace "How do we secure deployment?"
python evaluate_routing.py
python -m unittest discover -s tests -v
```

## Failure modes and limitations

- Keyword routing misses paraphrases ("how do we know it still works?") and sends them to human review. That is the safe direction, but it is a coverage gap.
- Priority order is a design choice, not a correctness guarantee: a request that is mostly about deployment but mentions "evaluate" goes to `evaluation`.
- The labelled set is small and written by the author. It guards against regressions; it does not estimate accuracy on real traffic. Build a set from real requests before trusting the numbers.
- English keywords only; other languages fall back to human review.
- There is no confidence score, so there is no threshold to tune and no way to rank near-misses.
- No model is involved. This is the deterministic baseline against which a model-based router would later be evaluated.
- The router is not connected to the agent in example 01.

## Production questions

- What confidence threshold should allow automated routing (needs a model router; none here)?
- Which requests must always go to human review? (Today: anything unmatched. Sensitive topics would need an explicit deny list.)
- Who owns `golden.json`, and who approves a rule change?
- What does the receiving specialist do with a request it should not have received?

See [ADR 002](../../docs/decisions/002-deterministic-routing-first.md).
