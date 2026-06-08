from agent_brain.orchestration.recommendation import (
    build_recommendation_draft,
    draft_recommendation,
    summarize_drafting_signals,
)
from agent_brain.orchestration.state import (
    AgentBrainState,
    ComplianceRiskContext,
    HumanApprovalStatus,
    LivePricingContext,
    RetrievedContext,
)


def _high_risk_state() -> AgentBrainState:
    return AgentBrainState(
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
        live_pricing=[
            LivePricingContext(
                software_code="SW-OPENAI-CHATGPT-ENT",
                software_name="ChatGPT Enterprise",
                requested_seats=120,
                estimated_annual_total_usd=41040.0,
                applied_discount_percent=5.0,
            )
        ],
    )


def test_summarize_drafting_signals_aggregates_state() -> None:
    signals = summarize_drafting_signals(_high_risk_state())

    assert signals.highest_priority_score == 68.64
    assert signals.maximum_annual_cost_usd == 43200.0
    assert signals.high_risk_count == 1
    assert signals.high_severity_count == 1
    assert signals.has_live_pricing


def test_build_recommendation_draft_requires_hitl_for_high_risk_context() -> None:
    state = _high_risk_state()
    draft = build_recommendation_draft(state, summarize_drafting_signals(state))

    assert draft.recommended_action == "Prepare renewal review for human approval"
    assert draft.requires_human_approval
    assert "Human approval is required" in draft.rationale


def test_draft_recommendation_sets_pending_approval_and_safety_flag() -> None:
    drafted_state = draft_recommendation(_high_risk_state())

    assert drafted_state.recommendation_draft is not None
    assert drafted_state.human_approval_status == HumanApprovalStatus.PENDING
    assert "HITL_REQUIRED" in drafted_state.safety_flags


def test_low_risk_state_does_not_require_human_approval() -> None:
    state = AgentBrainState(
        user_query="Summarize low-risk product posture.",
        retrieved_context=[
            RetrievedContext(
                vendor_name="Low Risk Vendor",
                software_name="Low Risk Product",
                subscription_code="SUB-LOW-001",
                annual_cost_usd=1000.0,
                renewal_date="2026-12-01T00:00:00+00:00",
                risk_tier="LOW",
                risk_category="SECURITY_CONTROLS",
                risk_severity="LOW",
                evidence_excerpt="standard controls",
                source_document="low-risk.txt",
                priority_score=10.0,
            )
        ],
        live_pricing=[
            LivePricingContext(
                software_code="SW-LOW",
                software_name="Low Risk Product",
                requested_seats=10,
                estimated_annual_total_usd=1000.0,
                applied_discount_percent=0.0,
            )
        ],
    )

    drafted_state = draft_recommendation(state)

    assert drafted_state.recommendation_draft is not None
    assert drafted_state.recommendation_draft.recommended_action == (
        "Monitor pricing and governance posture"
    )
    assert drafted_state.human_approval_status == HumanApprovalStatus.NOT_REQUIRED
