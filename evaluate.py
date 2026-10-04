"""Small dependency-free regression checks for v0.1 patterns."""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).parent / "examples"
REPO_ROOT = Path(__file__).parent


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
    controls = load(str(REPO_ROOT / "controls.py"), "controls")
    quality = load(str(REPO_ROOT / "quality.py"), "quality")

    checks = {
        "tool_validates_input": False,
        "unknown_route_goes_to_review": routing.route_request("something unrelated").name == "human-review",
        "approval_starts_pending": approval.ApprovalRequest("x", "y").decision is approval.Decision.PENDING,
        "approval_rejects_execution": False,
        "days_match_sessions": len(agent.get_training_plan("goal", 4)["sessions"]) == 4,
        "unknown_tool_blocked": False,
        "long_goal_rejected": False,
        "side_effect_needs_approval": False,
        "consistent_final_answer_passes": quality.check_training_plan_consistency("A 4-day/week plan", {"days_available": 4})["passed"],
        "contradictory_final_answer_fails": not quality.check_training_plan_consistency("A 5-day/week plan", {"days_available": 4})["passed"],
    }
    try:
        agent.get_training_plan("goal", 0)
    except ValueError:
        checks["tool_validates_input"] = True
    request = approval.ApprovalRequest("send", "requested")
    request.decide(approval.Decision.REJECTED)
    checks["approval_rejects_execution"] = not request.can_execute()
    try:
        controls.authorize_tool("delete_everything")
    except PermissionError:
        checks["unknown_tool_blocked"] = True
    try:
        controls.validate_goal("x" * 501)
    except ValueError:
        checks["long_goal_rejected"] = True
    try:
        controls.require_approval_for_side_effect(side_effect=True)
    except PermissionError:
        checks["side_effect_needs_approval"] = True

    failed = [name for name, passed in checks.items() if not passed]
    for name, passed in checks.items():
        print(f"{'PASS' if passed else 'FAIL'} {name}")
    if failed:
        raise SystemExit(f"Evaluation failed: {', '.join(failed)}")
    print(f"All {len(checks)} evaluation checks passed.")


if __name__ == "__main__":
    main()
