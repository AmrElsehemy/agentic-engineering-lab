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
        raise SystemExit("Live agent process failed; inspect local stderr without sharing credentials.")
    if len(events) < 3:
        raise SystemExit("Expected model_response, tool_executed, and final model_response events.")
    first, tool, final = events[:3]
    assert first["event"] == "model_response"
    assert first["tool_calls"][0]["name"] == "get_training_plan"
    assert tool == {"event": "tool_executed", "tool": "get_training_plan", "validated": True, "result": {"redacted": True}}
    assert final["event"] == "model_response" and final.get("phase") == "final"
    print("LIVE PASS forced tool selection")
    print("LIVE PASS validated tool execution")
    print("LIVE PASS final model response after tool result")


if __name__ == "__main__":
    main()
