"""Small dependency-free regression checks for v0.1 patterns."""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).parent / "examples"


def load(relative: str, name: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / relative)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def main() -> None:
    agent = load("01-single-agent-tool-calling/agent.py", "agent")
    routing = load("02-routing/routing.py", "routing")
    approval = load("03-human-in-the-loop/approval.py", "approval")

    checks = {
        "tool_validates_input": False,
        "unknown_route_goes_to_review": routing.route_request("something unrelated").name == "human-review",
        "approval_starts_pending": approval.ApprovalRequest("x", "y").decision is approval.Decision.PENDING,
        "approval_rejects_execution": False,
    }
    try:
        agent.get_training_plan("athlete", "goal", 0)
    except ValueError:
        checks["tool_validates_input"] = True
    request = approval.ApprovalRequest("send", "requested")
    request.decide(approval.Decision.REJECTED)
    checks["approval_rejects_execution"] = not request.can_execute()

    failed = [name for name, passed in checks.items() if not passed]
    for name, passed in checks.items():
        print(f"{'PASS' if passed else 'FAIL'} {name}")
    if failed:
        raise SystemExit(f"Evaluation failed: {', '.join(failed)}")
    print(f"All {len(checks)} evaluation checks passed.")


if __name__ == "__main__":
    main()
