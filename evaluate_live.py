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
    completed = subprocess.run(
        [sys.executable, str(AGENT), "--goal", "Prepare a HYROX race plan using the controlled tool"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        env=child_env,
        check=False,
    )
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
    if len(events) < 3:
        names = [item.get("event") for item in events]
        raise SystemExit(f"Expected 3 trace events; received {names}")
    first, tool, final = events[:3]
    failures = []
    if first.get("event") != "model_response":
        failures.append("first event is not model_response")
    tool_calls = first.get("tool_calls") or []
    if not tool_calls or tool_calls[0].get("name") != "get_training_plan":
        failures.append("first model response did not request get_training_plan")
    if tool.get("event") != "tool_executed" or tool.get("tool") != "get_training_plan":
        failures.append("tool_executed event is missing or names the wrong tool")
    if tool.get("validated") is not True:
        failures.append("tool execution was not marked validated")
    if final.get("event") != "model_response" or final.get("phase") != "final":
        failures.append("final model_response event is missing")
    if failures:
        raise SystemExit("Live evaluation failed: " + "; ".join(failures))
    print("LIVE PASS forced tool selection")
    print("LIVE PASS validated tool execution")
    print("LIVE PASS final model response after tool result")


if __name__ == "__main__":
    main()
