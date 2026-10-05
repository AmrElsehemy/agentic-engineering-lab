# 03 — Human-in-the-loop approval

Approval as an explicit state transition: an agent may propose an action, but a separate decision is required before anything executes.

## Contract

`ApprovalRequest(action, reason)` starts as `pending`. `decide(approved | rejected)` moves it once. `can_execute()` is true only after approval.

- **Pending** and **rejected** requests cannot execute.
- A decision cannot be changed or repeated.
- `pending` is not a valid decision.
- The proposed action, the reason and the decision stay together on the request.

## Run

```bash
python approval.py
python -m unittest discover -s tests -v
```

The example performs no real side effect. It shows the control boundary that must exist before adding one.

## Relationship to example 01

Example 01 has its own inline approval gate in front of a real (local) side effect, with a terminal prompt and default-deny behavior. This example is the standalone state machine; it is not wired into that loop.

## Failure modes and limitations

- The state lives in memory only. A restart loses pending requests.
- No approver identity or authorization: anyone who can call `decide` can approve.
- No audit trail beyond the object itself, no timestamps and no expiry. A request can stay pending forever.
- No idempotency for the action that follows approval.
- Nothing defines what happens when approval is unavailable.

These are the requirements for a production implementation.

See [ADR 003](../../docs/decisions/003-approval-as-state-machine.md).
