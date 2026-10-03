"""Opt-in Foundry/OpenTelemetry tracing helpers.

Content recording is intentionally disabled by default. Set FOUNDRY_TRACE=console
for local spans or FOUNDRY_TRACE=azure-monitor for Foundry/Azure Monitor export.
"""
from __future__ import annotations

import os
from contextlib import nullcontext
from typing import Any


def configure_tracing(project: Any | None = None) -> Any | None:
    mode = os.environ.get("FOUNDRY_TRACE", "").lower()
    if mode not in {"console", "azure-monitor"}:
        return None
    os.environ.setdefault("AZURE_EXPERIMENTAL_ENABLE_GENAI_TRACING", "true")
    try:
        from azure.ai.projects.telemetry import AIProjectInstrumentor
        from opentelemetry import trace
        if mode == "azure-monitor":
            if project is None:
                raise RuntimeError("Azure Monitor tracing requires a Foundry project client")
            from azure.monitor.opentelemetry import configure_azure_monitor
            try:
                connection_string = project.telemetry.get_application_insights_connection_string()
            except Exception as exc:
                if exc.__class__.__name__ == "ResourceNotFoundError":
                    raise RuntimeError(
                        "No Application Insights connection found for this Foundry project. "
                        "In Foundry open Agents > Traces > Connect, connect or create Application Insights; "
                        "then rerun with FOUNDRY_TRACE=azure-monitor."
                    ) from exc
                raise
            configure_azure_monitor(connection_string=connection_string)
        else:
            from opentelemetry.sdk.trace import TracerProvider
            from opentelemetry.sdk.trace.export import ConsoleSpanExporter, SimpleSpanProcessor
            provider = TracerProvider()
            provider.add_span_processor(SimpleSpanProcessor(ConsoleSpanExporter()))
            trace.set_tracer_provider(provider)
        AIProjectInstrumentor().instrument()
        return trace.get_tracer("agentic-engineering-lab")
    except ImportError as exc:
        raise RuntimeError("Install tracing dependencies: pip install -r requirements.txt") from exc


def span(tracer: Any | None, name: str):
    return tracer.start_as_current_span(name) if tracer else nullcontext()
