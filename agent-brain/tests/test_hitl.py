from agent_brain.governance.hitl import (
    HITLDecision,
    HITLDecisionOutcome,
    build_hitl_pause,
    finalize_with_hitl,
)
from agent_brain.orchestration.recommendation import draft_recommendation
from agent_brain.orchestration.state import AgentBrainState, RetrievedContext


def _state_requiring_hitl() -> AgentBrainState:
    state = AgentBrainState(
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
        trace_id="trace-hitl-test",
    )
    return draft_recommendation(state)


def test_build_hitl_pause_marks_required_for_unapproved_high_risk_draft() -> None:
    pause = build_hitl_pause(_state_requiring_hitl())

    assert pause.required
    assert pause.trace_id == "trace-hitl-test"
    assert pause.recommended_action == "Prepare renewal review for human approval"
    assert "HITL_REQUIRED" in pause.safety_flags


def test_finalize_with_hitl_blocks_rejected_decision() -> None:
    decision = HITLDecision.create(
        HITLDecisionOutcome.REJECTED,
        reviewer="Compliance reviewer",
        rationale="Evidence requires more review.",
    )

    finalized = finalize_with_hitl(_state_requiring_hitl(), decision)

    assert finalized.final_output is None
    assert "FINALIZATION_BLOCKED" in finalized.safety_flags


def test_finalize_with_hitl_allows_approved_decision() -> None:
    decision = HITLDecision.create(
        HITLDecisionOutcome.APPROVED,
        reviewer="Compliance reviewer",
        rationale="Approved for governed renewal review.",
    )

    finalized = finalize_with_hitl(_state_requiring_hitl(), decision)

    assert finalized.final_output is not None
    assert "Approved by Compliance reviewer" in finalized.final_output
    assert "HITL_APPROVED" in finalized.safety_flags


def test_hitl_decision_audit_detail_is_serializable() -> None:
    decision = HITLDecision.create(
        HITLDecisionOutcome.APPROVED,
        reviewer="Reviewer",
        rationale="Approved.",
    )

    detail = decision.to_audit_detail()

    assert detail["outcome"] == "APPROVED"
    assert detail["reviewer"] == "Reviewer"
