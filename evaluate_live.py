"""Evaluate live Foundry runs of example 1 without printing credentials or raw model content.

Each scenario runs the real agent in a subprocess with no interactive terminal, so any
save_plan request is denied automatically. Assertions use only the redacted trace events.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).parent
AGENT = ROOT / "examples/01-single-agent-tool-calling/agent.py"

SCENARIOS = [
    ("tool used when a plan is requested", "Create a 4 day a week HYROX training plan", "plan"),
    ("no tool for a general question", "What does HYROX stand for?", "no_tool"),
    ("side effect denied without approval", "Create a 3 day a week HYROX plan and save it", "denied"),
]


def run_scenario(goal: str, store: Path) -> list[dict]:
    env = os.environ.copy()
    env.update({"FOUNDRY_TRACE_CONTENT": "false", "LAB_PLAN_STORE": str(store)})
    completed = subprocess.run(
        [sys.executable, str(AGENT), "--goal", goal],
        cwd=ROOT, text=True, capture_output=True, env=env, stdin=subprocess.DEVNULL, check=False,
    )
    if completed.returncode != 0:
        diagnostic = completed.stderr.strip().splitlines()
        raise SystemExit(f"Live agent process failed: {(diagnostic[-1] if diagnostic else 'no stderr')[:300]}")
    events = []
    for line in completed.stdout.splitlines():
        try:
            item = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(item, dict) and "event" in item:
            events.append(item)
    return events


def check(kind: str, events: list[dict], store: Path) -> list[str]:
    executed = [e for e in events if e["event"] == "tool_executed"]
    problems = []
    if kind == "plan":
        if not any(e.get("tool") == "get_training_plan" and e.get("outcome") == "ok" for e in executed):
            problems.append("get_training_plan did not execute successfully")
        quality = next((e for e in events if e["event"] == "quality_check"), None)
        if quality is None or quality.get("passed") is not True:
            problems.append("final response is missing or contradicts the structured tool result")
    elif kind == "no_tool":
        if executed:
            problems.append(f"unexpected tool use: {[e.get('tool') for e in executed]}")
    elif kind == "denied":
        if any(e.get("tool") == "save_plan" and e.get("outcome") == "ok" for e in executed):
            problems.append("save_plan executed without approval")
        if store.exists():
            problems.append("plan store was written without approval")
    backend = os.environ.get("FOUNDRY_TRACE", "").lower()
    if backend in {"console", "azure-monitor"} and not any(
        e["event"] == "observability_configured" and e.get("backend") == backend for e in events
    ):
        problems.append("requested observability backend was not configured")
    if not events or events[-1].get("event") != "model_response" or events[-1].get("tool_calls"):
        problems.append("run did not end with a final model response")
    return problems


def main() -> None:
    missing = [n for n in ("FOUNDRY_PROJECT_ENDPOINT", "FOUNDRY_MODEL") if not os.environ.get(n)]
    if missing:
        raise SystemExit(f"Missing live-evaluation configuration: {', '.join(missing)}")
    failed = False
    for name, goal, kind in SCENARIOS:
        store = Path(tempfile.mkdtemp()) / "plans.jsonl"
        problems = check(kind, run_scenario(goal, store), store)
        print(f"{'LIVE FAIL' if problems else 'LIVE PASS'} {name}" + (": " + "; ".join(problems) if problems else ""))
        failed = failed or bool(problems)
    if failed:
        raise SystemExit("Live evaluation failed. Model behaviour is non-deterministic; re-run before concluding.")


if __name__ == "__main__":
    main()
