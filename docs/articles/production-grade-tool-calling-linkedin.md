# LinkedIn version: The difference between an agent demo and a production boundary

Most agent demos prove one thing:

A model can call a function.

Useful—but not the production problem.

The production problem is whether we can create a trustworthy boundary between probabilistic model behavior and deterministic software behavior.

That is what I’ve been building in the Agentic Engineering Lab.

The first example is intentionally small: one Microsoft Foundry model, two tools (one read-only, one with a side effect), one final response.

But the tool call is not trusted just because the model produced valid JSON.

The application:

- allowlists the tool
- validates every argument
- bounds the number of calls and the length of the loop
- rejects unknown tools
- requires a human decision before any side effect, and defaults to no
- emits structured execution events
- checks the final prose against structured tool truth
- runs deterministic checks without a live model
- exports the live trace through Entra-authenticated Azure Monitor

The live evaluation passed three runs in a row:

```text
LIVE PASS tool used when a plan is requested
LIVE PASS asks instead of inventing missing days
LIVE PASS no tool for a general question
LIVE PASS side effect denied without approval
```

The live runs also caught things my tests missed: the model invented a value for a field the user never gave, my first fix made it over-cautious, and my own evaluator passed a scenario where nothing was actually tested. Each one changed the code.

That does not mean the repository is “production-ready” for every use case.

It does mean one production-grade aspect is concrete and inspectable:

> The model may propose an action, but application code decides whether that action is allowed, valid, observable, and safe to hand back to the model.

This is the shift I care about:

From:

> “Look what this agent can do.”

To:

> “What is this agent allowed to do, how do we know what happened, and what fails closed when the model is wrong?”

Full article and implementation:

- Canonical article: `https://amrelsehemy.net/`
- Code and evidence: `https://github.com/AmrElsehemy/agentic-engineering-lab`

I’m building the next layer publicly: routing, human approval, orchestration, and eventually side-effecting workflows with explicit recovery and authorization.

What control do you consider non-negotiable before an agent reaches production?

#MicrosoftFoundry #AgenticAI #AIEngineering #Azure #MLOps
