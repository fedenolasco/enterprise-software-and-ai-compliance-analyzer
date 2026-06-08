import pytest

from agent_brain.orchestration.state import (
    AgentBrainState,
    ComplianceRiskContext,
    HumanApprovalStatus,
    LivePricingContext,
    RecommendationDraft,
    RetrievedContext,
    create_initial_state,
    is_finalization_allowed,
    record_human_approval,
)


def test_create_initial_state_requires_user_query() -> None:
    with pytest.raises(ValueError, match="user_query must not be empty"):
        create_initial_state("   ")


def test_agent_state_exports_langgraph_ready_shape() -> None:
    state = AgentBrainState(
        user_query="Should we renew Notion AI?",
        retrieved_context=[
            RetrievedContext(
                vendor_name="Notion AI",
                software_name="Notion AI",
                subscription_code="SUB-PM-NOTION-001",
                annual_cost_usd=17280.0,
                renewal_date="2026-07-01T00:00:00+00:00",
                risk_tier="HIGH",
                risk_category="DATA_RESIDENCY",
                risk_severity="HIGH",
                evidence_excerpt="outside the EU evidence",
                source_document="notion-ai-sla.txt",
                priority_score=83.46,
            )
        ],
        compliance_risks=[
            ComplianceRiskContext(
                vendor_name="Notion AI",
                risk_category="DATA_RESIDENCY",
                risk_severity="HIGH",
                rationale="Evidence references non-EU processing.",
            )
        ],
        live_pricing=[
            LivePricingContext(
                software_code="SW-NOTION-AI",
                software_name="Notion AI",
                requested_seats=80,
                estimated_annual_total_usd=16761.6,
                applied_discount_percent=3.0,
            )
        ],
        human_approval_status=HumanApprovalStatus.PENDING,
        trace_id="trace-demo",
        safety_flags=["HITL_REQUIRED"],
    )

    exported = state.to_langgraph_state()

    assert exported["user_query"] == "Should we renew Notion AI?"
    assert exported["retrieved_context"][0]["vendor_name"] == "Notion AI"
    assert exported["compliance_risks"][0]["risk_category"] == "DATA_RESIDENCY"
    assert exported["live_pricing"][0]["source"] == "mock-pricing-api"
    assert exported["human_approval_status"] == "PENDING"
    assert exported["trace_id"] == "trace-demo"


def test_finalization_requires_approval_for_cancellation_or_renewal() -> None:
    state = create_initial_state("Should we cancel Notion AI?")
    state.recommendation_draft = RecommendationDraft(
        summary="Draft cancellation recommendation.",
        recommended_action="Cancel subscription",
        requires_human_approval=True,
        rationale="High risk and low utilization.",
    )
    state.human_approval_status = HumanApprovalStatus.PENDING

    assert not is_finalization_allowed(state)

    approved_state = record_human_approval(state, HumanApprovalStatus.APPROVED)

    assert is_finalization_allowed(approved_state)


def test_low_risk_non_renewal_draft_can_finalize_without_approval() -> None:
    state = create_initial_state("Summarize governance posture.")
    state.recommendation_draft = RecommendationDraft(
        summary="Monitor vendor controls.",
        recommended_action="Monitor controls",
        requires_human_approval=False,
        rationale="No cancellation or renewal decision is being finalized.",
    )

    assert is_finalization_allowed(state)
