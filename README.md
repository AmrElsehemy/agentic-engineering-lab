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

## Repository status

**Current status:** Foundation release in progress  
**Target:** v0.1 on 8 October 2026

The first release will prioritize a small number of understandable, runnable patterns over a large collection of unfinished examples.

## v0.1 scope

1. Single agent
2. Tool calling
3. Routing
4. Human-in-the-loop or basic multi-agent flow

Each example should include:

- A clear problem statement
- Architecture and trade-offs
- Setup instructions
- Runnable code or an explicit implementation note
- Failure modes and limitations
- Evaluation considerations
- A link to related public writing or video when available

## Quick start

The first runnable pattern is [`01 — Single Agent + Controlled Tool Call`](examples/01-single-agent-tool-calling/README.md). It includes a deterministic demo that runs without credentials:

```bash
cd examples/01-single-agent-tool-calling
python agent.py --demo --goal "prepare for a HYROX race"
```

The same example can call a Microsoft Foundry-compatible OpenAI endpoint when the required environment variables are configured. The implementation deliberately starts with a bounded local tool so the tool contract, validation, and handoff are visible before adding external side effects.

Additional deterministic patterns are now available:

- [`02 — Routing`](examples/02-routing/README.md)
- [`03 — Human-in-the-Loop Approval`](examples/03-human-in-the-loop/README.md)
- [`Dependency-free evaluation checks`](evaluate.py)

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

## Roadmap

See [`docs/architecture-map.md`](docs/architecture-map.md) for the v0.1 system view, [`docs/architecture-taxonomy.md`](docs/architecture-taxonomy.md) for the working taxonomy, and [`docs/v0.1-definition-of-done.md`](docs/v0.1-definition-of-done.md) for the release standard. The current foundation release notes are in [`docs/releases/v0.0.1-foundation.md`](docs/releases/v0.0.1-foundation.md).

## Contributing

Issues, corrections, examples, and technical discussion are welcome. Read [`CONTRIBUTING.md`](CONTRIBUTING.md) before opening a pull request.

## License

MIT. See [`LICENSE`](LICENSE).
