from typing import Any, cast

from agent_brain.governance.observability import (
    build_governance_audit_event,
    build_safety_events,
    build_trace_span,
    build_usage_event,
    ensure_trace_id,
)
from agent_brain.orchestration.model_adapter import ModelRequest, PlaceholderLocalModelAdapter
from agent_brain.orchestration.recommendation import draft_recommendation
from agent_brain.orchestration.state import (
    AgentBrainState,
    ComplianceRiskContext,
    RetrievedContext,
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
            trace_id="trace-observability-test",
        )
    )


def test_ensure_trace_id_preserves_existing_trace_id() -> None:
    assert ensure_trace_id("trace-existing") == "trace-existing"
    assert ensure_trace_id().startswith("trace-")


def test_build_trace_span_exports_phoenix_compatible_payload() -> None:
    span = build_trace_span(_governed_state(), "draft_recommendation")
    payload = span.to_export_payload()

    assert payload["trace_id"] == "trace-observability-test"
    assert payload["node_name"] == "draft_recommendation"
    assert payload["safety_flags"] == ["HITL_REQUIRED"]


def test_build_usage_event_exports_langfuse_compatible_payload() -> None:
    response = PlaceholderLocalModelAdapter().generate(
        ModelRequest(prompt="Draft a recommendation", trace_id="trace-usage")
    )

    usage = build_usage_event(response).to_export_payload()
    token_usage = cast(dict[str, int], usage["usage"])

    assert usage["trace_id"] == "trace-usage"
    assert usage["provider"] == "placeholder"
    assert token_usage["total_tokens"] == response.total_tokens
    assert usage["simulated_cost_usd"] == 0.0


def test_build_safety_events_include_risk_severity_and_decision() -> None:
    events = build_safety_events(_governed_state(), decision_outcome="PENDING")

    assert len(events) == 1
    payload = events[0].to_export_payload()
    assert payload["flag"] == "HITL_REQUIRED"
    assert payload["risk_severity"] == "HIGH"
    assert payload["decision_outcome"] == "PENDING"


def test_build_governance_audit_event_matches_prisma_shape() -> None:
    state = _governed_state()
    response = PlaceholderLocalModelAdapter().generate(
        ModelRequest(prompt="Draft a recommendation", trace_id=state.trace_id)
    )
    audit_event = build_governance_audit_event(
        state,
        message="Recommendation drafted with governance telemetry.",
        model_response=response,
        decision_outcome="PENDING",
    )
    insert = audit_event.to_prisma_insert()
    detail = cast(dict[str, Any], insert["detail"])
    model_usage = cast(dict[str, Any], detail["model_usage"])
    usage = cast(dict[str, int], model_usage["usage"])

    assert insert["eventType"] == "AGENT_RECOMMENDATION"
    assert insert["status"] == "PENDING"
    assert insert["actor"] == "agent-brain"
    assert insert["traceId"] == "trace-observability-test"
    assert detail["safety_flags"] == ["HITL_REQUIRED"]
    assert usage["total_tokens"] == response.total_tokens
