# ADR 003: Model approval as a one-way state machine

- **Status:** Accepted
- **Date:** 2026-10-05
- **Scope:** example 03

## Decision

Represent approval as a request with three states (`pending`, `approved`, `rejected`). It can be decided once, and only `approved` allows execution.

## Why

- Pending and rejected are safe by construction: nothing can execute.
- A one-way transition prevents flipping a decision after the fact.
- The proposed action and reason stay attached to the decision, which is the minimum context an audit trail needs.

## Alternatives rejected

- **A boolean flag:** cannot distinguish "not yet decided" from "rejected".
- **Approval inside the agent:** the model must not approve its own action.

## Consequences

This is a pattern, not a production control. It has no persistence, approver identity, expiry or audit log. Example 01 uses an inline approval gate with a terminal prompt for its real side effect; the two are not yet unified.
