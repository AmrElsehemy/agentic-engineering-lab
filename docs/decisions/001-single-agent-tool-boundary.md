# ADR 001: Start with a single agent and one controlled tool

- **Status:** Accepted
- **Date:** 2026-10-02
- **Scope:** v0.1 first implementation

## Decision

Start with a single model-driven agent that can request one explicitly defined, locally executed tool: `get_training_plan`.

## Why

A small loop makes the most important production boundaries visible:

- tool schema and input validation
- model-to-tool handoff
- tool result handling
- unknown-tool blocking
- separation of planning from side effects
- future evaluation and tracing points

## Alternatives rejected

- **Multi-agent first:** adds coordination complexity before the basic loop is understood.
- **Autonomous external actions:** introduces side effects and authorization concerns too early.
- **Framework-heavy abstraction:** hides the underlying protocol we need to inspect and teach.

## Security boundary

The first tool is deterministic, local, bounded, and has no external side effects. Credentials are never passed to the model or committed to the repository.

## Follow-up

Add tests, structured traces, evaluation cases, and a Foundry-specific deployment path before expanding to routing or multi-agent patterns.
