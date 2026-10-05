"""Deterministic routing pattern with bounded specialist contracts."""
from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class Route:
    name: str
    reason: str


# Specialists are checked in priority order. A keyword matches the start of a word, so
# "agent" matches "agentic" and "agents" but not "management".
SPECIALISTS = (
    ("evaluation", ("evaluat", "regression", "quality"), "request asks about quality or regression"),
    ("production", ("deploy", "secur", "identity", "observ"), "request asks about operating a production system"),
    ("agent-pattern", ("tool", "function", "agent"), "request asks about an agent implementation pattern"),
)
FALLBACK = "human-review"


def _matches(text: str, stems: tuple[str, ...]) -> bool:
    return any(re.search(rf"\b{re.escape(stem)}", text) for stem in stems)


def route_request(request: str) -> Route:
    """Route a request using transparent keywords.

    - No specialist matches: the request goes to human review instead of being guessed.
    - Several specialists match: the highest-priority one is chosen and the reason names the others.
    """
    text = request.strip().lower()
    if not text:
        raise ValueError("request is required")
    matched = [(name, reason) for name, stems, reason in SPECIALISTS if _matches(text, stems)]
    if not matched:
        return Route(FALLBACK, "request did not match a bounded specialist contract")
    name, reason = matched[0]
    if len(matched) > 1:
        others = ", ".join(other for other, _ in matched[1:])
        reason = f"{reason}; also matched: {others} (priority order applies)"
    return Route(name, reason)


if __name__ == "__main__":
    import argparse
    import json

    parser = argparse.ArgumentParser()
    parser.add_argument("request")
    args = parser.parse_args()
    print(json.dumps(route_request(args.request).__dict__, indent=2))
