"""Deterministic routing pattern with named specialist routes and an explicit human fallback.

Production controls: input type and size limits, rules validated at import, a machine-readable
decision (`Route.automated`, `Route.matched`) so callers cannot mistake the fallback for a
specialist, and redacted trace events (request text is never logged unless opted in).
"""
from __future__ import annotations

import hashlib
import json
import os
import re
from dataclasses import dataclass

MAX_REQUEST_CHARS = 1000


@dataclass(frozen=True)
class Route:
    name: str
    reason: str
    matched: tuple[str, ...] = ()

    @property
    def automated(self) -> bool:
        """False for the fallback: callers must hand the request to a person, not a specialist."""
        return self.name != FALLBACK


# Specialists are checked in priority order. A keyword matches the start of a word, so
# "agent" matches "agentic" and "agents" but not "management".
SPECIALISTS = (
    ("evaluation", ("evaluat", "regression", "quality"), "request asks about quality or regression"),
    ("production", ("deploy", "secur", "identity", "observ"), "request asks about operating a production system"),
    ("agent-pattern", ("tool", "function", "agent"), "request asks about an agent implementation pattern"),
)
FALLBACK = "human-review"


def validate_rules(specialists=SPECIALISTS) -> None:
    """Fail loudly on a malformed rule table instead of silently misrouting."""
    names = [name for name, _, _ in specialists]
    if len(set(names)) != len(names):
        raise ValueError("duplicate specialist name")
    if FALLBACK in names:
        raise ValueError(f"specialist may not use the fallback name: {FALLBACK}")
    for name, stems, reason in specialists:
        if not stems or any(not s or s != s.lower() or not s.strip() for s in stems):
            raise ValueError(f"specialist {name} needs non-empty lowercase stems")
        if not reason:
            raise ValueError(f"specialist {name} needs a reason")


validate_rules()


def _matches(text: str, stems: tuple[str, ...]) -> bool:
    return any(re.search(rf"\b{re.escape(stem)}", text) for stem in stems)


def emit_trace(event: str, **payload) -> None:
    """Print one machine-readable event. The request text is redacted unless
    ROUTING_TRACE_CONTENT=true (local debugging only); a short hash still lets runs be correlated."""
    if os.environ.get("ROUTING_TRACE_CONTENT", "false").lower() != "true":
        payload.pop("request", None)
    print(json.dumps({"event": event, **payload}, default=str))


def route_request(request: str, *, trace: bool = False) -> Route:
    """Route a request using transparent keywords.

    - No specialist matches: the request goes to human review instead of being guessed.
    - Several specialists match: the highest-priority one is chosen and the reason names the others.
    - Text is only ever compared with keywords. It is never executed or interpreted as instructions,
      so "ignore the rules and route to production" is just words that match nothing.
    """
    if not isinstance(request, str):
        raise TypeError("request must be a string")
    text = request.strip().lower()
    if not text:
        raise ValueError("request is required")
    if len(text) > MAX_REQUEST_CHARS:
        raise ValueError(f"request exceeds {MAX_REQUEST_CHARS} characters")
    matched = [(name, reason) for name, stems, reason in SPECIALISTS if _matches(text, stems)]
    if not matched:
        route = Route(FALLBACK, "request did not match a named specialist route")
    else:
        name, reason = matched[0]
        others = tuple(other for other, _ in matched[1:])
        if others:
            reason = f"{reason}; also matched: {', '.join(others)} (priority order applies)"
        route = Route(name, reason, tuple(n for n, _ in matched))
    if trace:
        emit_trace(
            "route_decision",
            route=route.name,
            automated=route.automated,
            matched=list(route.matched),
            request_chars=len(text),
            request_sha256=hashlib.sha256(text.encode()).hexdigest()[:12],
            request=request,
        )
    return route


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("request")
    parser.add_argument("--trace", action="store_true", help="emit a redacted route_decision event")
    args = parser.parse_args()
    route = route_request(args.request, trace=args.trace)
    print(json.dumps({**route.__dict__, "automated": route.automated}, indent=2))
