# Architecture Map

The lab grows from the smallest controllable loop toward production operations.

```mermaid
flowchart LR
    A[User request] --> B[Single agent]
    B --> C[Validated tool call]
    C --> D[Explicit route]
    D --> E{Side effect?}
    E -->|No| F[Return result]
    E -->|Yes| G[Human approval]
    G -->|Approved| H[Execute with authorization]
    G -->|Rejected| I[Safe terminal state]
    F --> J[Evaluation and regression checks]
    H --> J
    I --> J
    J --> K[Tracing, observability, and deployment]
```

The guiding rule is to introduce complexity only when the simpler pattern no longer satisfies the requirement. Each pattern must document its boundary, failure modes, and evaluation strategy.
