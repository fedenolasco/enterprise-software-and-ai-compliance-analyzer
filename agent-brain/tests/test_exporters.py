"""Tests for live Phoenix and Langfuse exporter clients."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from agent_brain.config import AgentBrainSettings
from agent_brain.governance.exporters import (
    ExportResult,
    export_langfuse_usage,
    export_phoenix_spans,
    export_safety_events,
)
from agent_brain.governance.observability import (
    LangfuseUsageEvent,
    PhoenixTraceSpan,
    SafetyFlagEvent,
)


def _enabled_settings() -> AgentBrainSettings:
    return AgentBrainSettings(
        phoenix_enabled=True,
        phoenix_endpoint="http://localhost:6006",
        langfuse_enabled=True,
        langfuse_host="http://localhost:3000",
        langfuse_public_key="pk-test",
        langfuse_secret_key="sk-test",
    )


def _disabled_settings() -> AgentBrainSettings:
    return AgentBrainSettings(
        phoenix_enabled=False,
        langfuse_enabled=False,
    )


def _sample_span() -> PhoenixTraceSpan:
    return PhoenixTraceSpan(
        trace_id="trace-export-1",
        node_name="draft_recommendation",
        started_at="2026-06-22T10:00:00+00:00",
        ended_at="2026-06-22T10:00:01+00:00",
        safety_flags=("HITL_REQUIRED",),
    )


def _sample_usage() -> LangfuseUsageEvent:
    return LangfuseUsageEvent(
        trace_id="trace-export-1",
        model_name="gpt-4o-mini",
        provider="openai",
        prompt_tokens=10,
        completion_tokens=5,
        total_tokens=15,
        simulated_cost_usd=0.001,
    )


def _sample_safety() -> SafetyFlagEvent:
    return SafetyFlagEvent(
        trace_id="trace-export-1",
        flag="HITL_REQUIRED",
        risk_severity="HIGH",
        decision_outcome="PENDING",
        created_at="2026-06-22T10:00:00+00:00",
    )


# --- Phoenix span export tests ---


def test_export_phoenix_spans_returns_disabled_when_not_enabled() -> None:
    result = export_phoenix_spans([_sample_span()], _disabled_settings())

    assert result.service == "phoenix"
    assert result.success is False
    assert result.events_sent == 0
    assert "phoenix_enabled is false" in (result.error or "")


def test_export_phoenix_spans_returns_success_when_no_spans() -> None:
    result = export_phoenix_spans([], _enabled_settings())

    assert result.success is True
    assert result.events_sent == 0


def test_export_phoenix_spans_sends_payloads_to_collector() -> None:
    with patch("httpx.Client") as mock_client_class:
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_client.post.return_value = mock_response
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client_class.return_value = mock_client

        result = export_phoenix_spans([_sample_span()], _enabled_settings())

    assert result.success is True
    assert result.events_sent == 1
    mock_client.post.assert_called_once()
    call_args = mock_client.post.call_args
    assert "http://localhost:6006/v1/spans" == call_args.args[0]


def test_export_phoenix_spans_fails_gracefully_on_error() -> None:
    with patch("httpx.Client") as mock_client_class:
        mock_client = MagicMock()
        mock_client.post.side_effect = ConnectionError("Connection refused")
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client_class.return_value = mock_client

        result = export_phoenix_spans([_sample_span()], _enabled_settings())

    assert result.success is False
    assert result.events_sent == 0
    assert "Connection refused" in (result.error or "")


# --- Langfuse usage export tests ---


def test_export_langfuse_usage_returns_disabled_when_not_enabled() -> None:
    result = export_langfuse_usage([_sample_usage()], _disabled_settings())

    assert result.service == "langfuse"
    assert result.success is False
    assert "langfuse_enabled is false" in (result.error or "")


def test_export_langfuse_usage_returns_missing_keys_error() -> None:
    settings = AgentBrainSettings(
        langfuse_enabled=True,
        langfuse_host="http://localhost:3000",
        langfuse_public_key=None,
        langfuse_secret_key=None,
    )
    result = export_langfuse_usage([_sample_usage()], settings)

    assert result.success is False
    assert "langfuse_public_key" in (result.error or "")


def test_export_langfuse_usage_returns_success_when_no_events() -> None:
    result = export_langfuse_usage([], _enabled_settings())

    assert result.success is True
    assert result.events_sent == 0


def test_export_langfuse_usage_sends_batch_to_api() -> None:
    with patch("httpx.Client") as mock_client_class:
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_client.post.return_value = mock_response
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client_class.return_value = mock_client

        result = export_langfuse_usage([_sample_usage()], _enabled_settings())

    assert result.success is True
    assert result.events_sent == 1
    mock_client.post.assert_called_once()
    call_args = mock_client.post.call_args
    assert "http://localhost:3000/api/public/ingestion" == call_args.args[0]
    assert call_args.kwargs["auth"] == ("pk-test", "sk-test")


def test_export_langfuse_usage_fails_gracefully_on_error() -> None:
    with patch("httpx.Client") as mock_client_class:
        mock_client = MagicMock()
        mock_client.post.side_effect = TimeoutError("Request timed out")
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client_class.return_value = mock_client

        result = export_langfuse_usage([_sample_usage()], _enabled_settings())

    assert result.success is False
    assert result.events_sent == 0
    assert "Request timed out" in (result.error or "")


# --- Safety event export tests ---


def test_export_safety_events_returns_disabled_when_not_enabled() -> None:
    result = export_safety_events([_sample_safety()], _disabled_settings())

    assert result.service == "phoenix-safety"
    assert result.success is False
    assert "phoenix_enabled is false" in (result.error or "")


def test_export_safety_events_returns_success_when_no_events() -> None:
    result = export_safety_events([], _enabled_settings())

    assert result.success is True
    assert result.events_sent == 0


def test_export_safety_events_sends_to_phoenix() -> None:
    with patch("httpx.Client") as mock_client_class:
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_client.post.return_value = mock_response
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client_class.return_value = mock_client

        result = export_safety_events([_sample_safety()], _enabled_settings())

    assert result.success is True
    assert result.events_sent == 1


def test_export_safety_events_fails_gracefully_on_error() -> None:
    with patch("httpx.Client") as mock_client_class:
        mock_client = MagicMock()
        mock_client.post.side_effect = OSError("Network error")
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client_class.return_value = mock_client

        result = export_safety_events([_sample_safety()], _enabled_settings())

    assert result.success is False
    assert result.events_sent == 0
    assert "Network error" in (result.error or "")


# --- ExportResult dataclass tests ---


def test_export_result_defaults() -> None:
    result = ExportResult(service="test", success=True, events_sent=5)
    assert result.service == "test"
    assert result.success is True
    assert result.events_sent == 5
    assert result.error is None
