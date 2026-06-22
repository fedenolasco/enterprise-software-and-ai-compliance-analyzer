"""Live exporter clients for Phoenix and Langfuse observability services.

These exporters wire the existing payload builders in
``agent_brain.governance.observability`` to live Phoenix and Langfuse
services.  When the services are disabled or unreachable, the exporters
fail gracefully and return ``False`` without raising, so the agent
workflow continues with local audit persistence as the durable fallback.
"""

from __future__ import annotations

import logging
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any

from agent_brain.config import AgentBrainSettings, get_settings
from agent_brain.governance.observability import (
    LangfuseUsageEvent,
    PhoenixTraceSpan,
    SafetyFlagEvent,
)

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ExportResult:
    """Result of an observability export attempt."""

    service: str
    success: bool
    events_sent: int
    error: str | None = None


def export_phoenix_spans(
    spans: Sequence[PhoenixTraceSpan],
    settings: AgentBrainSettings | None = None,
) -> ExportResult:
    """Export Phoenix-compatible trace spans to a live Phoenix collector.

    Uses the Phoenix HTTP collector endpoint.  When ``phoenix_enabled`` is
    ``False`` or the export fails, returns a failed ``ExportResult`` without
    raising so the agent workflow continues.
    """

    active_settings = settings or get_settings()

    if not active_settings.phoenix_enabled:
        return ExportResult(
            service="phoenix",
            success=False,
            events_sent=0,
            error="phoenix_enabled is false",
        )

    if not spans:
        return ExportResult(service="phoenix", success=True, events_sent=0)

    try:
        import httpx  # noqa: PLC0415 — deferred import for optional dependency

        endpoint = f"{active_settings.phoenix_endpoint.rstrip('/')}/v1/spans"
        payloads = [span.to_export_payload() for span in spans]

        with httpx.Client(timeout=10.0) as client:
            response = client.post(endpoint, json=payloads)
            response.raise_for_status()

        return ExportResult(
            service="phoenix",
            success=True,
            events_sent=len(spans),
        )
    except Exception as exc:  # noqa: BLE001 — graceful degradation
        logger.warning("Phoenix export failed: %s", exc)
        return ExportResult(
            service="phoenix",
            success=False,
            events_sent=0,
            error=str(exc),
        )


def export_langfuse_usage(
    events: Sequence[LangfuseUsageEvent],
    settings: AgentBrainSettings | None = None,
) -> ExportResult:
    """Export Langfuse-compatible usage events to a live Langfuse service.

    Uses the Langfuse HTTP API with public/secret key authentication.  When
    ``langfuse_enabled`` is ``False`` or the export fails, returns a failed
    ``ExportResult`` without raising.
    """

    active_settings = settings or get_settings()

    if not active_settings.langfuse_enabled:
        return ExportResult(
            service="langfuse",
            success=False,
            events_sent=0,
            error="langfuse_enabled is false",
        )

    if not active_settings.langfuse_public_key or not active_settings.langfuse_secret_key:
        return ExportResult(
            service="langfuse",
            success=False,
            events_sent=0,
            error="langfuse_public_key or langfuse_secret_key is not configured",
        )

    if not events:
        return ExportResult(service="langfuse", success=True, events_sent=0)

    try:
        import httpx  # noqa: PLC0415 — deferred import for optional dependency

        endpoint = f"{active_settings.langfuse_host.rstrip('/')}/api/public/ingestion"
        payloads: list[dict[str, Any]] = []
        for event in events:
            payload = event.to_export_payload()
            payloads.append(
                {
                    "id": payload["trace_id"],
                    "type": "trace-create",
                    "body": {
                        "id": payload["trace_id"],
                        "name": "model-usage",
                        "metadata": {
                            "model_name": payload["model_name"],
                            "provider": payload["provider"],
                            "simulated_cost_usd": payload["simulated_cost_usd"],
                        },
                        "usage": {
                            "input": payload["usage"]["prompt_tokens"],  # type: ignore[index]
                            "output": payload["usage"]["completion_tokens"],  # type: ignore[index]
                            "total": payload["usage"]["total_tokens"],  # type: ignore[index]
                        },
                    },
                }
            )

        with httpx.Client(timeout=10.0) as client:
            response = client.post(
                endpoint,
                json={"batch": payloads},
                auth=(
                    active_settings.langfuse_public_key,
                    active_settings.langfuse_secret_key,
                ),
            )
            response.raise_for_status()

        return ExportResult(
            service="langfuse",
            success=True,
            events_sent=len(events),
        )
    except Exception as exc:  # noqa: BLE001 — graceful degradation
        logger.warning("Langfuse export failed: %s", exc)
        return ExportResult(
            service="langfuse",
            success=False,
            events_sent=0,
            error=str(exc),
        )


def export_safety_events(
    events: Sequence[SafetyFlagEvent],
    settings: AgentBrainSettings | None = None,
) -> ExportResult:
    """Export safety flag events to Phoenix as span attributes.

    Safety events are exported as Phoenix spans when Phoenix is enabled.
    When Phoenix is disabled, the events are still captured by local audit
    persistence.
    """

    active_settings = settings or get_settings()

    if not active_settings.phoenix_enabled:
        return ExportResult(
            service="phoenix-safety",
            success=False,
            events_sent=0,
            error="phoenix_enabled is false",
        )

    if not events:
        return ExportResult(service="phoenix-safety", success=True, events_sent=0)

    try:
        import httpx  # noqa: PLC0415 — deferred import for optional dependency

        endpoint = f"{active_settings.phoenix_endpoint.rstrip('/')}/v1/spans"
        payloads = [event.to_export_payload() for event in events]

        with httpx.Client(timeout=10.0) as client:
            response = client.post(endpoint, json=payloads)
            response.raise_for_status()

        return ExportResult(
            service="phoenix-safety",
            success=True,
            events_sent=len(events),
        )
    except Exception as exc:  # noqa: BLE001 — graceful degradation
        logger.warning("Phoenix safety export failed: %s", exc)
        return ExportResult(
            service="phoenix-safety",
            success=False,
            events_sent=0,
            error=str(exc),
        )
