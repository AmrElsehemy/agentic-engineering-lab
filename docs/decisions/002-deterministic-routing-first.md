# ADR 002: Route deterministically before adding a model router

- **Status:** Accepted
- **Date:** 2026-10-05
- **Scope:** example 02

## Decision

Route requests with transparent keyword rules and a human-review fallback. Keywords match word starts, specialists have a fixed priority, and the reason for every route is returned.

## Why

- Route choices are explainable and testable without a model or credentials.
- The baseline gives a model-based router something to be evaluated against.
- An unmatched request going to a person is safer than a confident wrong route.

## Controls added for production use

- `Route.automated` marks the fallback so downstream code cannot treat it as a specialist.
- Request length and type are limited; the rule table is validated at import.
- Quality is gated in CI by `evaluate_routing.py` on a labelled set (accuracy and wrong-route rate), with known paraphrase misses reported separately.
- Traces redact request text by default.

## Alternatives rejected

- **Model-based router first:** adds nondeterminism before there is a baseline or a regression suite.
- **First match silently wins without saying so:** hides overlap. The reason now names the other matches.
- **Reject overlapping requests:** would send most real questions ("evaluate tool selection") to a human.

## Consequences

Paraphrases fall through to human review. There is no confidence score. Both are known limits, listed in the example README.
