"""Deterministic stand-in for a chat-completions client.

Used by --demo and by the tests so the full agent loop (tool selection, validation,
approval, error handling) runs in CI without credentials or network access.
"""
from __future__ import annotations

import json
from types import SimpleNamespace
from typing import Any


def text(content: str) -> SimpleNamespace:
    return _response(content, [])


def tool_call(name: str, arguments: Any, call_id: str = "call_1", content: str | None = None) -> SimpleNamespace:
    raw = arguments if isinstance(arguments, str) else json.dumps(arguments)
    return _response(content, [SimpleNamespace(id=call_id, function=SimpleNamespace(name=name, arguments=raw))])


def tool_calls(*calls: tuple[str, Any]) -> SimpleNamespace:
    built = [
        SimpleNamespace(id=f"call_{i}", function=SimpleNamespace(name=n, arguments=a if isinstance(a, str) else json.dumps(a)))
        for i, (n, a) in enumerate(calls, 1)
    ]
    return _response(None, built)


def _response(content: str | None, calls: list[Any]) -> SimpleNamespace:
    message = SimpleNamespace(content=content, tool_calls=calls or None)
    return SimpleNamespace(choices=[SimpleNamespace(message=message)])


class ScriptedClient:
    """Returns pre-scripted responses in order and records every request it receives."""

    def __init__(self, responses: list[SimpleNamespace]) -> None:
        self._responses = list(responses)
        self.calls: list[dict[str, Any]] = []
        self.chat = SimpleNamespace(completions=SimpleNamespace(create=self._create))

    def _create(self, **kwargs: Any) -> SimpleNamespace:
        self.calls.append({**kwargs, "messages": [dict(m) for m in kwargs["messages"]]})
        if not self._responses:
            raise AssertionError("ScriptedClient ran out of scripted responses")
        return self._responses.pop(0)
