"""Deterministic routing pattern with bounded specialist contracts."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Route:
    name: str
    reason: str


def route_request(request: str) -> Route:
    """Route a request using transparent keywords; ambiguous requests go to review."""
    text = request.strip().lower()
    if not text:
        raise ValueError("request is required")
    if any(word in text for word in ("evaluate", "regression", "quality")):
        return Route("evaluation", "request asks about quality or regression")
    if any(word in text for word in ("deploy", "secure", "identity", "observability")):
        return Route("production", "request asks about operating a production system")
    if any(word in text for word in ("tool", "function", "agent")):
        return Route("agent-pattern", "request asks about an agent implementation pattern")
    return Route("human-review", "request did not match a bounded specialist contract")


if __name__ == "__main__":
    import argparse
    import json

    parser = argparse.ArgumentParser()
    parser.add_argument("request")
    args = parser.parse_args()
    print(json.dumps(route_request(args.request).__dict__, indent=2))
