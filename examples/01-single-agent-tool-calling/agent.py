"""Minimal single-agent + controlled-tool example.

Run locally without credentials:
    python agent.py --demo

Run against a Microsoft Foundry project with Microsoft Entra ID:
    pip install -r requirements.txt
    cp .env.example .env  # then export the variables
    python agent.py --goal "prepare for a HYROX race"
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from controls import MAX_TOOL_CALLS_PER_TURN, authorize_tool, validate_goal
from observability import configure_tracing, span
from quality import check_training_plan_consistency


SYSTEM_PROMPT = """You are a careful training-planning assistant.
Use the get_training_plan tool when the user asks for a plan.
Treat the tool result as the source of truth. If it says a number of training days,
do not state a different schedule length in your final response.
Never invent medical advice. Keep the plan general, explain assumptions,
and ask the user to consult a qualified professional for pain, injury,
medication, or medical conditions.
"""


def get_training_plan(athlete: str, goal: str, days_available: int = 3) -> dict[str, Any]:
    """Controlled tool: returns a bounded, transparent planning suggestion."""
    if not athlete.strip() or not goal.strip():
        raise ValueError("athlete and goal are required")
    if not 1 <= days_available <= 7:
        raise ValueError("days_available must be between 1 and 7")
    return {
        "athlete": athlete.strip(),
        "goal": goal.strip(),
        "days_available": days_available,
        "sessions": [
            {"day": 1, "focus": "easy aerobic base", "intensity": "conversational"},
            {"day": 2, "focus": "strength and movement quality", "intensity": "controlled"},
            {"day": 3, "focus": "functional conditioning", "intensity": "moderate"},
            {"day": 4, "focus": "long engine or race-specific transitions", "intensity": "steady"},
            {"day": 5, "focus": "mobility and recovery", "intensity": "easy"},
            {"day": 6, "focus": "optional aerobic technique", "intensity": "easy to moderate"},
            {"day": 7, "focus": "rest or active recovery", "intensity": "recovery"},
        ][:days_available],
        "limitations": [
            "This is an educational example, not medical or individualized coaching advice.",
            "Adjust volume for current fitness, recovery, and professional guidance.",
        ],
    }


TOOL = {
    "type": "function",
    "function": {
        "name": "get_training_plan",
        "description": "Create a bounded educational training-plan suggestion.",
        "parameters": {
            "type": "object",
            "properties": {
                "athlete": {"type": "string"},
                "goal": {"type": "string"},
                "days_available": {"type": "integer", "minimum": 1, "maximum": 7},
            },
            "required": ["athlete", "goal"],
            "additionalProperties": False,
        },
    },
}


def demo(goal: str) -> None:
    result = get_training_plan("demo athlete", goal, 3)
    emit_trace("model_response", mode="demo", tool_calls=[{"name": "get_training_plan", "arguments": {"athlete": "demo athlete", "goal": goal, "days_available": 3}}])
    emit_trace("tool_executed", tool="get_training_plan", validated=True, result=result)
    print(json.dumps({"mode": "demo", "tool": "get_training_plan", "result": result}, indent=2))


def emit_trace(event: str, **payload: Any) -> None:
    """Print one machine-readable execution event without credentials or token contents."""
    if os.environ.get("FOUNDRY_TRACE_CONTENT", "false").lower() != "true":
        if "content" in payload and payload["content"] is not None:
            payload["content"] = "<redacted; set FOUNDRY_TRACE_CONTENT=true for local debugging>"
        if "result" in payload:
            payload["result"] = {"redacted": True}
    print(json.dumps({"event": event, **payload}, default=str))


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


def run_with_model(goal: str) -> None:
    goal = validate_goal(goal)
    client, model, tracer = create_model_client()
    if os.environ.get("FOUNDRY_TRACE", "").lower() in {"console", "azure-monitor"}:
        emit_trace("observability_configured", backend=os.environ["FOUNDRY_TRACE"].lower())
    messages: list[dict[str, Any]] = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": goal},
    ]
    with span(tracer, "agent.model_response") as model_span:
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            tools=[TOOL],
            tool_choice={"type": "function", "function": {"name": "get_training_plan"}},
        )
    if model_span:
        model_span.set_attribute("agent.model", model)
        model_span.set_attribute("agent.tool_choice", "required:get_training_plan")
    message = response.choices[0].message
    emit_trace(
        "model_response",
        tool_calls=[
            {"id": call.id, "name": call.function.name, "arguments": json.loads(call.function.arguments)}
            for call in (message.tool_calls or [])
        ],
        content=message.content,
    )
    if not message.tool_calls:
        raise RuntimeError("Forced tool call was not returned by the model")

    messages.append(message.model_dump())
    if len(message.tool_calls) > MAX_TOOL_CALLS_PER_TURN:
        raise RuntimeError("Blocked multiple tool calls in one turn")
    for call in message.tool_calls:
        authorize_tool(call.function.name)
        args = json.loads(call.function.arguments)
        with span(tracer, "agent.tool_execution") as tool_span:
            result = get_training_plan(**args)
        if tool_span:
            tool_span.set_attribute("agent.tool", call.function.name)
            tool_span.set_attribute("agent.validation", "passed")
        emit_trace("tool_executed", tool=call.function.name, validated=True, result=result)
        messages.append({"role": "tool", "tool_call_id": call.id, "content": json.dumps(result)})

    with span(tracer, "agent.final_response"):
        final = client.chat.completions.create(model=model, messages=messages)
    final_text = final.choices[0].message.content or ""
    emit_trace("model_response", phase="final", tool_calls=[], content=final_text)
    quality = check_training_plan_consistency(final_text, result)
    emit_trace("quality_check", name="training_plan_consistency", **quality)
    if not quality["passed"]:
        raise RuntimeError(
            "Final response contradicts the structured tool result: "
            f"expected {quality['expected_days']} days, observed {quality['conflicting_schedule_days']}"
        )
    print(final_text or "The agent returned no final content.")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--goal", default="prepare for a HYROX race")
    parser.add_argument("--demo", action="store_true", help="Run the controlled tool without an LLM endpoint")
    args = parser.parse_args()
    demo(args.goal) if args.demo else run_with_model(args.goal)


if __name__ == "__main__":
    main()
