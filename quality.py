"""Postconditions for comparing final agent prose with structured tool output."""
from __future__ import annotations

import re
from typing import Any

SCHEDULE_PATTERN = re.compile(r"\b(\d+)\s*[- ]\s*days?(?:/week)?\b", re.IGNORECASE)


def check_training_plan_consistency(text: str, tool_result: dict[str, Any]) -> dict[str, Any]:
    expected = int(tool_result["days_available"])
    observed = [int(value) for value in SCHEDULE_PATTERN.findall(text or "")]
    conflicting = sorted({value for value in observed if value != expected})
    return {
        "passed": not conflicting,
        "expected_days": expected,
        "observed_schedule_days": sorted(set(observed)),
        "conflicting_schedule_days": conflicting,
        "explicit_schedule_claim_found": bool(observed),
    }
