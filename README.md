# Agentic Engineering Lab

Production-grade AI agent architecture patterns on Microsoft.

This is a public, runnable lab for exploring how AI agents move from impressive demos to systems that teams can **trust, operate, evaluate, observe, secure, and improve**.

The lab documents both what works and what fails. It is not a claim that there is one universal way to build agents.

## What this lab covers

- Single agents and tool calling
- Routing and orchestration
- Human-in-the-loop workflows
- Multi-agent systems
- MCP and interoperability
- Evaluation and regression testing
- Identity, security, and observability
- Production deployment

Microsoft-first implementations will use Microsoft Foundry, Agent Framework, Azure AI, Entra ID, managed identity, and Azure observability where appropriate.

## Examples

1. [`01 — Single agent with controlled tool calls`](examples/01-single-agent-tool-calling/README.md): a model-driven loop with a read-only tool and an approval-gated side effect, with tests, a live evaluator and optional tracing.
2. [`02 — Routing`](examples/02-routing/README.md): deterministic routing with a human-review fallback.
3. [`03 — Human-in-the-loop approval`](examples/03-human-in-the-loop/README.md): an explicit approval state machine.

Each example documents its problem statement, architecture and trade-offs, setup, failure modes and limitations, and evaluation considerations.

## Quick start

The first runnable pattern is [`01 — Single Agent + Controlled Tool Call`](examples/01-single-agent-tool-calling/README.md). It includes a deterministic demo that runs without credentials:

```bash
cd examples/01-single-agent-tool-calling
python agent.py --demo
```

The same example can call a Microsoft Foundry project when the required environment variables are configured (copy `.env.example` to `.env`; it is gitignored and loaded automatically). Its tools are deliberately small and local so the controls around them stay visible.

Checks:

- [`evaluate.py`](evaluate.py): dependency-free control checks.
- [`evaluate_live.py`](evaluate_live.py): live evaluation against Foundry.
- Unit tests: `python -m unittest discover -s examples/01-single-agent-tool-calling/tests`
- [`docs/evaluation-rubric.md`](docs/evaluation-rubric.md): what is checked and where.

## Why this exists

Models and frameworks change quickly. The hard production questions are more stable:

- How do we handle human approval?
- How do we recover from failure?
- How do we know an agent made a good decision?
- How do we secure tools and data?
- How do we observe a multi-step workflow?
- How do we keep the system reliable after the demo?

This lab is an attempt to make those questions concrete through small experiments and reusable patterns.

## Safety and responsible use

Examples are educational and should be reviewed before use in production. Do not use the lab with confidential data, credentials, personal health information, or other sensitive data unless the relevant security, privacy, and compliance controls have been independently implemented and validated.

## Documentation

- [`docs/architecture-map.md`](docs/architecture-map.md): the system view.
- [`docs/architecture-taxonomy.md`](docs/architecture-taxonomy.md): the working taxonomy of agent patterns.
- [`docs/decisions/`](docs/decisions/): architecture decision records.
- [`docs/evaluation-rubric.md`](docs/evaluation-rubric.md): the evaluation rubric.

## Contributing

Issues, corrections, examples, and technical discussion are welcome. Read [`CONTRIBUTING.md`](CONTRIBUTING.md) before opening a pull request.

## License

MIT. See [`LICENSE`](LICENSE).
