"""Small production-control boundary used by the agent example."""
from __future__ import annotations

ALLOWED_TOOLS = frozenset({"get_training_plan"})
MAX_TOOL_CALLS_PER_TURN = 1
MAX_GOAL_CHARS = 500


def authorize_tool(name: str) -> None:
    if name not in ALLOWED_TOOLS:
        raise PermissionError(f"Tool is not allowlisted: {name}")


def validate_goal(goal: str) -> str:
    goal = goal.strip()
    if not goal:
        raise ValueError("goal is required")
    if len(goal) > MAX_GOAL_CHARS:
        raise ValueError(f"goal exceeds {MAX_GOAL_CHARS} characters")
    return goal


def require_approval_for_side_effect(*, side_effect: bool, approved: bool = False) -> None:
    if side_effect and not approved:
        raise PermissionError("Side effects require explicit human approval")
