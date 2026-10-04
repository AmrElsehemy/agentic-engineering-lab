"""Single agent with a read-only tool and an approval-gated side-effecting tool.

Run locally without credentials (scripted model, no network):
    python agent.py --demo            # save_plan is denied: nobody approved it
    python agent.py --demo --approve  # save_plan is approved and executed

Run against a Microsoft Foundry project with Microsoft Entra ID:
    pip install -r requirements.txt
    cp .env.example .env  # then export the variables
    python agent.py --goal "Create a 4 day a week HYROX plan"
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any, Callable

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from envfile import load_env
from controls import (
    MAX_STEPS,
    MAX_TOOL_CALLS_PER_TURN,
    SIDE_EFFECT_TOOLS,
    authorize_tool,
    require_approval_for_side_effect,
    validate_goal,
)
from observability import configure_tracing, span
from quality import check_training_plan_consistency

SYSTEM_PROMPT = """You are a careful training-planning assistant.
Use get_training_plan when the user asks for a training plan. Answer general questions directly.
Treat the tool result as the source of truth. If it says a number of training days,
do not state a different schedule length in your final response.
If the user states a number of training days anywhere in their message (for example "3 day a week"
or "four days"), use that number directly and do not ask them to confirm it. Only if no number of
days is given, ask how many days per week they can train before calling a tool; never guess.
Only call save_plan when the user asks to save a plan; the application asks the human for approval.
Never invent medical advice. Keep plans general, explain assumptions, and ask the user to
consult a qualified professional for pain, injury, medication, or medical conditions.
"""

DEFAULT_STORE = "saved_plans.jsonl"

Approver = Callable[[str, dict[str, Any]], bool]

SESSIONS = [
    {"day": 1, "focus": "easy aerobic base", "intensity": "conversational"},
    {"day": 2, "focus": "strength and movement quality", "intensity": "controlled"},
    {"day": 3, "focus": "functional conditioning", "intensity": "moderate"},
    {"day": 4, "focus": "long engine or race-specific transitions", "intensity": "steady"},
    {"day": 5, "focus": "mobility and recovery", "intensity": "easy"},
    {"day": 6, "focus": "optional aerobic technique", "intensity": "easy to moderate"},
    {"day": 7, "focus": "rest or active recovery", "intensity": "recovery"},
]


# --- Tools -------------------------------------------------------------------------------------

def get_training_plan(goal: str, days_available: int) -> dict[str, Any]:
    """Read-only tool: returns a bounded, transparent planning suggestion."""
    goal = validate_goal(goal)
    if isinstance(days_available, bool) or not isinstance(days_available, int):
        raise ValueError("days_available must be an integer")
    if not 1 <= days_available <= 7:
        raise ValueError("days_available must be between 1 and 7")
    return {
        "goal": goal,
        "days_available": days_available,
        "sessions": SESSIONS[:days_available],
        "limitations": [
            "This is an educational example, not medical or individualized coaching advice.",
            "Adjust volume for current fitness, recovery, and professional guidance.",
        ],
    }


def save_plan(goal: str, days_available: int, store: str | Path = DEFAULT_STORE) -> dict[str, Any]:
    """Side-effecting tool: appends a plan to a local file, once. The plan is regenerated here,
    never taken from model output, so the model cannot choose what gets persisted. Saving an
    identical plan again is a no-op, so a retried or repeated approval cannot duplicate it."""
    plan = get_training_plan(goal, days_available)
    line = json.dumps(plan)
    path = Path(store)
    if path.exists() and line in path.read_text(encoding="utf-8").splitlines():
        return {"saved": True, "already_saved": True, "days_available": plan["days_available"]}
    with open(path, "a", encoding="utf-8") as handle:
        handle.write(line + "\n")
    return {"saved": True, "already_saved": False, "days_available": plan["days_available"]}


def _tool(name: str, description: str) -> dict[str, Any]:
    return {
        "type": "function",
        "function": {
            "name": name,
            "description": description,
            "parameters": {
                "type": "object",
                "properties": {
                    "goal": {"type": "string", "description": "The user's training goal, e.g. HYROX."},
                    "days_available": {
                        "type": "integer", "minimum": 1, "maximum": 7,
                        "description": "Training days per week, exactly as the user stated. Never guess.",
                    },
                },
                "required": ["goal", "days_available"],
                "additionalProperties": False,
            },
        },
    }


TOOLS = [
    _tool("get_training_plan", "Create a bounded educational training-plan suggestion. Read-only."),
    _tool("save_plan", "Save a training plan to local storage. Side effect: requires human approval."),
]
ALLOWED_ARGUMENTS = {"goal", "days_available"}


# --- Approval ----------------------------------------------------------------------------------

def deny_all(name: str, arguments: dict[str, Any]) -> bool:
    return False


def approve_all(name: str, arguments: dict[str, Any]) -> bool:
    return True


def cli_approver(name: str, arguments: dict[str, Any]) -> bool:
    """Ask a human on the terminal. Without an interactive terminal the answer is always no."""
    if not sys.stdin.isatty():
        return False
    print(f"Approve {name}({json.dumps(arguments)})? [y/N] ", end="", file=sys.stderr, flush=True)
    return sys.stdin.readline().strip().lower() in {"y", "yes"}


# --- Tracing -----------------------------------------------------------------------------------

def emit_trace(event: str, **payload: Any) -> None:
    """Print one machine-readable event. Arguments, results and content are redacted unless
    FOUNDRY_TRACE_CONTENT=true (local debugging only)."""
    if os.environ.get("FOUNDRY_TRACE_CONTENT", "false").lower() != "true":
        for key in ("content", "arguments", "result"):
            if payload.get(key) is not None:
                payload[key] = "<redacted>"
        if "tool_calls" in payload:
            payload["tool_calls"] = [{**call, "arguments": "<redacted>"} for call in payload["tool_calls"]]
    print(json.dumps({"event": event, **payload}, default=str))


# --- Loop --------------------------------------------------------------------------------------

def execute_tool(name: str, raw_arguments: str, approver: Approver, store: str | Path) -> dict[str, Any]:
    """Validate and run one model-requested tool call. Never raises for bad model output:
    problems come back as {"error": ...} so the model can correct itself."""
    try:
        authorize_tool(name)
    except PermissionError as exc:
        emit_trace("tool_executed", tool=name, validated=False, outcome="blocked")
        return {"error": str(exc)}
    try:
        arguments = json.loads(raw_arguments)
        if not isinstance(arguments, dict):
            raise ValueError("arguments must be a JSON object")
        unexpected = set(arguments) - ALLOWED_ARGUMENTS
        if unexpected:
            raise ValueError(f"unexpected arguments: {', '.join(sorted(unexpected))}")
        if set(arguments) != ALLOWED_ARGUMENTS:
            raise ValueError("goal and days_available are required; ask the user if unknown")
        get_training_plan(**arguments)  # validate before any approval is requested
    except (ValueError, TypeError) as exc:
        emit_trace("tool_executed", tool=name, validated=False, outcome="invalid_arguments")
        return {"error": f"invalid arguments: {exc}"}

    side_effect = name in SIDE_EFFECT_TOOLS
    if side_effect:
        approved = approver(name, arguments)
        emit_trace("approval", tool=name, approved=approved)
        try:
            require_approval_for_side_effect(side_effect=True, approved=approved)
        except PermissionError as exc:
            emit_trace("tool_executed", tool=name, validated=True, side_effect=True, outcome="denied")
            return {"error": str(exc)}

    with span(None, "agent.tool_execution"):
        result = save_plan(**arguments, store=store) if side_effect else get_training_plan(**arguments)
    emit_trace("tool_executed", tool=name, validated=True, side_effect=side_effect, outcome="ok", result=result)
    return result


def _assistant_message(message: Any) -> dict[str, Any]:
    return {
        "role": "assistant",
        "content": message.content,
        "tool_calls": [
            {"id": c.id, "type": "function", "function": {"name": c.function.name, "arguments": c.function.arguments}}
            for c in message.tool_calls
        ],
    }


def run_agent(
    client: Any,
    model: str,
    goal: str,
    *,
    approver: Approver = deny_all,
    store: str | Path = DEFAULT_STORE,
    tracer: Any | None = None,
) -> str:
    """Run the loop: the model chooses tools (or none), the application validates, approves
    and executes them, for at most MAX_STEPS model calls."""
    messages: list[dict[str, Any]] = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": validate_goal(goal)},
    ]
    if os.environ.get("FOUNDRY_TRACE", "").lower() in {"console", "azure-monitor"}:
        emit_trace("observability_configured", backend=os.environ["FOUNDRY_TRACE"].lower())
    plan: dict[str, Any] | None = None
    for step in range(1, MAX_STEPS + 1):
        last_step = step == MAX_STEPS
        with span(tracer, "agent.model_response"):
            response = client.chat.completions.create(
                model=model, messages=messages, tools=TOOLS, tool_choice="none" if last_step else "auto"
            )
        message = response.choices[0].message
        calls = message.tool_calls or []
        emit_trace(
            "model_response",
            step=step,
            tool_calls=[{"id": c.id, "name": c.function.name, "arguments": c.function.arguments} for c in calls],
            content=message.content,
        )
        if not calls:
            final_text = message.content or ""
            if plan is not None:
                quality = check_training_plan_consistency(final_text, plan)
                emit_trace("quality_check", name="training_plan_consistency", **quality)
                if not quality["passed"]:
                    raise RuntimeError(
                        "Final response contradicts the structured tool result: "
                        f"expected {quality['expected_days']} days, observed {quality['conflicting_schedule_days']}"
                    )
            return final_text or "The agent returned no final content."

        messages.append(_assistant_message(message))
        for index, call in enumerate(calls):
            if index >= MAX_TOOL_CALLS_PER_TURN:
                result: dict[str, Any] = {"error": "only one tool call is allowed per turn; request it again if needed"}
                emit_trace("tool_executed", tool=call.function.name, validated=False, outcome="skipped")
            else:
                result = execute_tool(call.function.name, call.function.arguments, approver, store)
                if call.function.name == "get_training_plan" and "error" not in result:
                    plan = result
            messages.append({"role": "tool", "tool_call_id": call.id, "content": json.dumps(result)})
    raise RuntimeError("unreachable: the last step is called with tool_choice=none")


# --- Clients -----------------------------------------------------------------------------------

def create_model_client() -> tuple[Any, str, Any | None]:
    """Create an Entra-authenticated Foundry client, with API-key fallback for prototypes."""
    model = os.environ.get("FOUNDRY_MODEL") or os.environ.get("OPENAI_MODEL")
    project_endpoint = os.environ.get("FOUNDRY_PROJECT_ENDPOINT")
    if not model:
        raise SystemExit("Set FOUNDRY_MODEL to the exact deployed model name, or use --demo")

    if project_endpoint:
        try:
            from azure.ai.projects import AIProjectClient
            from azure.identity import DefaultAzureCredential
        except ImportError as exc:
            raise SystemExit("Install dependencies first: pip install -r requirements.txt") from exc
        project = AIProjectClient(endpoint=project_endpoint, credential=DefaultAzureCredential())
        return project.get_openai_client(), model, configure_tracing(project)

    base_url = os.environ.get("FOUNDRY_OPENAI_BASE_URL") or os.environ.get("OPENAI_BASE_URL")
    api_key = os.environ.get("FOUNDRY_API_KEY") or os.environ.get("OPENAI_API_KEY")
    if not all([base_url, api_key]):
        raise SystemExit(
            "Set FOUNDRY_PROJECT_ENDPOINT for Entra ID, or set FOUNDRY_OPENAI_BASE_URL and "
            "FOUNDRY_API_KEY for prototype key auth, or use --demo"
        )
    try:
        from openai import OpenAI
    except ImportError as exc:
        raise SystemExit("Install dependencies first: pip install -r requirements.txt") from exc
    return OpenAI(base_url=base_url, api_key=api_key), model, configure_tracing()


def demo(goal: str, approve: bool) -> str:
    """Scripted model: plans, then asks to save. Exercises the real loop, tools and approval."""
    from scripted_client import ScriptedClient, text, tool_call

    args = {"goal": goal, "days_available": 4}
    client = ScriptedClient([
        tool_call("get_training_plan", args, "call_1"),
        tool_call("save_plan", args, "call_2"),
        text("Here is a general 4-day plan. Saving it needed approval; see the trace for the outcome."),
    ])
    return run_agent(client, "scripted", goal, approver=approve_all if approve else deny_all)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--goal", default="Create a 4 day a week HYROX plan")
    parser.add_argument("--demo", action="store_true", help="Use a scripted model instead of a live endpoint")
    parser.add_argument("--approve", action="store_true", help="With --demo: approve the save_plan side effect")
    args = parser.parse_args()
    load_env()
    if args.demo:
        print(demo(args.goal, args.approve))
        return
    try:
        client, model, tracer = create_model_client()
    except RuntimeError as exc:
        raise SystemExit(f"Setup error: {exc}") from None
    store = os.environ.get("LAB_PLAN_STORE", DEFAULT_STORE)
    print(run_agent(client, model, args.goal, approver=cli_approver, store=store, tracer=tracer))


if __name__ == "__main__":
    main()
