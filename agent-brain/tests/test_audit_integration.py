"""Integration tests for governance audit event persistence against live PostgreSQL.

These tests require a running local PostgreSQL instance with the Prisma schema
applied. They are marked with ``@pytest.mark.integration`` so they can be
skipped in CI or offline environments using ``pytest -m "not integration"``.

Prerequisites:
- Docker services running (``docker compose up -d``)
- Prisma schema applied (``npm run db:push`` from ``database-layer/``)
- ``DATABASE_URL`` environment variable set or ``.env`` file present
"""

from __future__ import annotations

import os
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

import pytest

from agent_brain.config import DEFAULT_DATABASE_URL
from agent_brain.governance.audit import persist_governance_audit_events
from agent_brain.governance.observability import build_governance_audit_event
from agent_brain.orchestration.model_adapter import ModelRequest, PlaceholderLocalModelAdapter
from agent_brain.orchestration.recommendation import draft_recommendation
from agent_brain.orchestration.state import (
    AgentBrainState,
    ComplianceRiskContext,
    RetrievedContext,
)

pytestmark = pytest.mark.integration


def _database_url() -> str:
    return os.getenv("DATABASE_URL", DEFAULT_DATABASE_URL)


def _psycopg_conninfo(database_url: str) -> str:
    """Remove Prisma-only query parameters before connecting with psycopg."""

    parts = urlsplit(database_url)
    query_pairs = [(key, value) for key, value in parse_qsl(parts.query) if key != "schema"]
    return urlunsplit(
        (parts.scheme, parts.netloc, parts.path, urlencode(query_pairs), parts.fragment)
    )


def _governed_state() -> AgentBrainState:
    return draft_recommendation(
        AgentBrainState(
            user_query="Should we renew OpenAI?",
            retrieved_context=[
                RetrievedContext(
                    vendor_name="OpenAI Enterprise",
                    software_name="ChatGPT Enterprise",
                    subscription_code="SUB-ENG-OPENAI-001",
                    annual_cost_usd=43200.0,
                    renewal_date="2026-10-15T00:00:00+00:00",
                    risk_tier="HIGH",
                    risk_category="DATA_RESIDENCY",
                    risk_severity="HIGH",
                    evidence_excerpt="cross-border evidence",
                    source_document="openai-enterprise-sla.txt",
                    priority_score=68.64,
                )
            ],
            compliance_risks=[
                ComplianceRiskContext(
                    vendor_name="OpenAI Enterprise",
                    risk_category="DATA_RESIDENCY",
                    risk_severity="HIGH",
                    rationale="Cross-border processing evidence requires review.",
                )
            ],
            trace_id="trace-integration-test",
        )
    )


def _cleanup_audit_events(database_url: str, trace_id: str) -> None:
    """Delete test audit events to keep tests idempotent."""

    from psycopg import Connection

    with Connection.connect(_psycopg_conninfo(database_url)) as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                'DELETE FROM "AuditEvent" WHERE "traceId" = %s',
                (trace_id,),
            )
        connection.commit()


def _count_audit_events(database_url: str, trace_id: str) -> int:
    """Count audit events for a given trace ID."""

    from psycopg import Connection

    with Connection.connect(_psycopg_conninfo(database_url)) as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                'SELECT count(*) FROM "AuditEvent" WHERE "traceId" = %s',
                (trace_id,),
            )
            row = cursor.fetchone()
            return int(row[0]) if row else 0


def _read_audit_events(database_url: str, trace_id: str) -> list[dict[str, object]]:
    """Read audit events for a given trace ID."""

    from psycopg import Connection
    from psycopg.rows import dict_row

    with Connection.connect(_psycopg_conninfo(database_url), row_factory=dict_row) as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                'SELECT * FROM "AuditEvent" WHERE "traceId" = %s ORDER BY "createdAt" ASC',
                (trace_id,),
            )
            return [dict(row) for row in cursor.fetchall()]


def test_persist_single_governance_audit_event_to_live_postgres() -> None:
    database_url = _database_url()
    trace_id = "trace-integration-single"

    _cleanup_audit_events(database_url, trace_id)
    try:
        state = AgentBrainState(
            user_query="Test query",
            trace_id=trace_id,
        )
        event = build_governance_audit_event(
            state,
            message="Integration test: single event persistence.",
        )

        inserted = persist_governance_audit_events(database_url, [event])

        assert inserted == 1
        assert _count_audit_events(database_url, trace_id) == 1

        events = _read_audit_events(database_url, trace_id)
        assert events[0]["eventType"] == "AGENT_RECOMMENDATION"
        assert events[0]["status"] == "PENDING"
        assert events[0]["actor"] == "agent-brain"
        assert events[0]["traceId"] == trace_id
    finally:
        _cleanup_audit_events(database_url, trace_id)


def test_persist_multiple_governance_audit_events_to_live_postgres() -> None:
    database_url = _database_url()
    trace_id = "trace-integration-multi"

    _cleanup_audit_events(database_url, trace_id)
    try:
        state = AgentBrainState(
            user_query="Test query",
            trace_id=trace_id,
        )
        events = [
            build_governance_audit_event(
                state,
                message="Integration test: first event.",
            ),
            build_governance_audit_event(
                state,
                message="Integration test: second event.",
            ),
        ]

        inserted = persist_governance_audit_events(database_url, events)

        assert inserted == 2
        assert _count_audit_events(database_url, trace_id) == 2

        rows = _read_audit_events(database_url, trace_id)
        assert rows[0]["message"] == "Integration test: first event."
        assert rows[1]["message"] == "Integration test: second event."
    finally:
        _cleanup_audit_events(database_url, trace_id)


def test_persist_governance_audit_event_with_model_usage_detail() -> None:
    database_url = _database_url()
    trace_id = "trace-integration-usage"

    _cleanup_audit_events(database_url, trace_id)
    try:
        state = _governed_state()
        response = PlaceholderLocalModelAdapter().generate(
            ModelRequest(prompt="Draft a recommendation", trace_id=state.trace_id)
        )
        event = build_governance_audit_event(
            state,
            message="Integration test: event with model usage.",
            model_response=response,
            decision_outcome="PENDING",
        )

        inserted = persist_governance_audit_events(database_url, [event])

        assert inserted == 1

        rows = _read_audit_events(database_url, trace_id)
        detail = rows[0]["detail"]
        assert isinstance(detail, dict)
        assert detail["safety_flags"] == ["HITL_REQUIRED"]
        assert detail["risk_severity"] == "HIGH"
        assert detail["decision_outcome"] == "PENDING"
        assert "model_usage" in detail
        model_usage = detail["model_usage"]
        assert model_usage["provider"] == "placeholder"
        assert model_usage["usage"]["total_tokens"] == response.total_tokens
    finally:
        _cleanup_audit_events(database_url, trace_id)


def test_persist_empty_event_list_is_noop() -> None:
    database_url = _database_url()
    trace_id = "trace-integration-empty"

    _cleanup_audit_events(database_url, trace_id)
    try:
        inserted = persist_governance_audit_events(database_url, [])

        assert inserted == 0
        assert _count_audit_events(database_url, trace_id) == 0
    finally:
        _cleanup_audit_events(database_url, trace_id)


def test_audit_events_survive_when_observability_disabled() -> None:
    """Verify local audit persistence is the durable record when Phoenix/Langfuse are off."""

    database_url = _database_url()
    trace_id = "trace-integration-durable"

    _cleanup_audit_events(database_url, trace_id)
    try:
        state = _governed_state()
        event = build_governance_audit_event(
            state,
            message="Integration test: durable audit without observability.",
        )

        inserted = persist_governance_audit_events(database_url, [event])

        assert inserted == 1
        assert _count_audit_events(database_url, trace_id) == 1

        # Verify the event is readable even though no observability export was attempted
        rows = _read_audit_events(database_url, trace_id)
        assert rows[0]["traceId"] == trace_id
        assert rows[0]["status"] == "PENDING"
    finally:
        _cleanup_audit_events(database_url, trace_id)
