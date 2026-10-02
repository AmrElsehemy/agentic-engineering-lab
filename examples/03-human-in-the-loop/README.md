# 03 — Human-in-the-Loop Approval

This example makes approval an explicit state transition. The agent may propose an action, but a separate decision is required before execution.

## Run

```bash
python approval.py
```

The example does not execute a real external side effect. It demonstrates the control boundary that must exist before adding one.

## Production requirements still missing

A production implementation needs an authenticated approver, durable state, an audit trail, expiry handling, authorization checks, idempotency, and clear behavior when approval is unavailable.
