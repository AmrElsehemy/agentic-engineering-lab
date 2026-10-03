"""Evaluate a live Foundry run without printing credentials or raw model content."""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).parent
AGENT = ROOT / "examples/01-single-agent-tool-calling/agent.py"


def main() -> None:
    required = ("FOUNDRY_PROJECT_ENDPOINT", "FOUNDRY_MODEL")
    missing = [name for name in required if not os.environ.get(name)]
    if missing:
        raise SystemExit(f"Missing live-evaluation configuration: {', '.join(missing)}")
    child_env = os.environ.copy()
    child_env["FOUNDRY_TRACE_CONTENT"] = "false"
    completed = subprocess.run([sys.executable, str(AGENT), "--goal", "Prepare a HYROX race plan using the controlled tool"], cwd=ROOT, text=True, capture_output=True, env=child_env, check=False)
    events = []
    for line in completed.stdout.splitlines():
        try:
            item = json.loads(line)
        except json.JSONDecodeError:
            continue
        if "event" in item:
            events.append(item)
    if completed.returncode != 0:
        diagnostic = completed.stderr.strip().splitlines()
        detail = diagnostic[-1] if diagnostic else "no stderr captured"
        raise SystemExit(f"Live agent process failed: {detail[:300]}")
    trace_requested = os.environ.get("FOUNDRY_TRACE", "").lower() in {"console", "azure-monitor"}
    minimum_events = 5 if trace_requested else 4
    if len(events) < minimum_events:
        raise SystemExit(f"Expected at least {minimum_events} trace events; received {[item.get('event') for item in events]}")
    first = next((item for item in events if item.get("event") == "model_response" and not item.get("phase")), None)
    tool = next((item for item in events if item.get("event") == "tool_executed"), None)
    final = next((item for item in events if item.get("event") == "model_response" and item.get("phase") == "final"), None)
    quality = next((item for item in events if item.get("event") == "quality_check"), None)
    configured = next((item for item in events if item.get("event") == "observability_configured"), None)
    failures = []
    if first is None:
        failures.append("model_response event with tool call is missing")
    elif not (first.get("tool_calls") or []) or first["tool_calls"][0].get("name") != "get_training_plan":
        failures.append("first model response did not request get_training_plan")
    if not tool or tool.get("tool") != "get_training_plan":
        failures.append("tool_executed event is missing or names the wrong tool")
    elif tool.get("validated") is not True:
        failures.append("tool execution was not marked validated")
    if final is None:
        failures.append("final model_response event is missing")
    if quality is None or quality.get("passed") is not True:
        failures.append("final response contradicts the structured tool result")
    if trace_requested and (not configured or configured.get("backend") != os.environ["FOUNDRY_TRACE"].lower()):
        failures.append("requested observability backend was not configured")
    if failures:
        raise SystemExit("Live evaluation failed: " + "; ".join(failures))
    print("LIVE PASS forced tool selection")
    print("LIVE PASS validated tool execution")
    print("LIVE PASS final model response after tool result")
    print("LIVE PASS final-answer consistency")
    if trace_requested:
        print(f"LIVE PASS observability configured: {os.environ['FOUNDRY_TRACE'].lower()}")


if __name__ == "__main__":
    main()
