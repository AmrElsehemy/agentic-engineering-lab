# Agent Architecture Taxonomy

This is a working taxonomy, not a prescription. Choose the simplest pattern that satisfies the requirements.

| Pattern | Use when | Main risk to evaluate |
|---|---|---|
| Single agent | One decision loop with a bounded tool set is enough | Unclear tool boundaries and uncontrolled scope |
| Tool calling | The model needs controlled access to external actions or data | Authorization, validation, and side effects |
| Routing | Requests need different specialists or workflows | Misclassification and inconsistent contracts |
| Sequential workflow | Steps have a known order and dependencies | State loss and brittle handoffs |
| Parallel workflow | Independent tasks can run concurrently | Aggregation quality and partial failure |
| Human-in-the-loop | A person must approve, review, or resolve uncertainty | Approval latency and auditability |
| Multi-agent system | Separate roles genuinely improve the solution | Coordination overhead and emergent failure |
| Evaluation loop | Quality must be measured and protected over time | Optimizing a proxy instead of the real outcome |
| Observability | The system has multiple steps, tools, or production users | Missing traces and incomplete incident context |

Every implementation should document why the selected pattern is appropriate and what simpler alternative was rejected.
