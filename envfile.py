"""Tiny .env loader (stdlib only). Real environment variables always win over file values.

Search order: $LAB_ENV_FILE, examples/01-single-agent-tool-calling/.env, repo-root .env.
The files are gitignored; keep secrets such as the Application Insights connection string there.
"""
from __future__ import annotations

import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def parse(text: str) -> dict[str, str]:
    values: dict[str, str] = {}
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        if line.startswith("export "):
            line = line[len("export "):]
        key, _, value = line.partition("=")
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
            value = value[1:-1]
        values[key.strip()] = value
    return values


def load_env() -> list[Path]:
    """Load the first-found-wins variables from each existing file; return the files used."""
    candidates = [
        Path(p) for p in [os.environ.get("LAB_ENV_FILE")] if p
    ] + [ROOT / "examples/01-single-agent-tool-calling/.env", ROOT / ".env"]
    loaded = []
    for path in candidates:
        if path.is_file():
            for key, value in parse(path.read_text(encoding="utf-8")).items():
                os.environ.setdefault(key, value)
            loaded.append(path)
    return loaded
