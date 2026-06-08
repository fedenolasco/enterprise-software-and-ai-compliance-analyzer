"""Deterministic recommendation drafting for Phase 3 workflow scaffolding."""

from __future__ import annotations

from dataclasses import dataclass

from agent_brain.orchestration.state import (
    AgentBrainState,
    HumanApprovalStatus,
    RecommendationDraft,
)

HIGH_RISK_TIERS = {"HIGH", "CRITICAL"}
HIGH_RISK_SEVERITIES = {"HIGH", "CRITICAL"}


@dataclass(frozen=True)
class DraftingSignals:
    """Aggregated deterministic signals used to draft a recommendation."""

    highest_priority_score: float
    maximum_annual_cost_usd: float
    high_risk_count: int
    high_severity_count: int
    has_pending_renewal: bool
    has_live_pricing: bool


def draft_recommendation(state: AgentBrainState) -> AgentBrainState:
    """Return state with a deterministic recommendation draft and HITL status."""

    signals = summarize_drafting_signals(state)
    draft = build_recommendation_draft(state, signals)
    approval_status = (
        HumanApprovalStatus.PENDING
        if draft.requires_human_approval
        else HumanApprovalStatus.NOT_REQUIRED
    )
    safety_flags = list(state.safety_flags)
    if draft.requires_human_approval and "HITL_REQUIRED" not in safety_flags:
        safety_flags.append("HITL_REQUIRED")

    return AgentBrainState(
        user_query=state.user_query,
        retrieved_context=list(state.retrieved_context),
        compliance_risks=list(state.compliance_risks),
        live_pricing=list(state.live_pricing),
        recommendation_draft=draft,
        human_approval_status=approval_status,
        final_output=state.final_output,
        trace_id=state.trace_id,
        safety_flags=safety_flags,
    )


def summarize_drafting_signals(state: AgentBrainState) -> DraftingSignals:
    """Summarize retrieval, risk, and pricing state for deterministic drafting."""

    highest_priority = max(
        (context.priority_score for context in state.retrieved_context),
        default=0.0,
    )
    maximum_cost = max(
        (context.annual_cost_usd or 0.0 for context in state.retrieved_context),
        default=0.0,
    )
    high_risk_count = sum(
        1
        for context in state.retrieved_context
        if (context.risk_tier or "").upper() in HIGH_RISK_TIERS
    )
    high_severity_count = sum(
        1
        for risk in state.compliance_risks
        if risk.risk_severity.upper() in HIGH_RISK_SEVERITIES
    )
    has_pending_renewal = any(
        "pending" in (context.subscription_code or "").lower()
        or "pending" in (context.risk_category or "").lower()
        for context in state.retrieved_context
    )
    return DraftingSignals(
        highest_priority_score=highest_priority,
        maximum_annual_cost_usd=maximum_cost,
        high_risk_count=high_risk_count,
        high_severity_count=high_severity_count,
        has_pending_renewal=has_pending_renewal,
        has_live_pricing=len(state.live_pricing) > 0,
    )


def build_recommendation_draft(
    state: AgentBrainState,
    signals: DraftingSignals,
) -> RecommendationDraft:
    """Build a deterministic recommendation draft from summarized workflow signals."""

    requires_hitl = _requires_human_approval(signals)
    action = _recommended_action(signals)
    summary = (
        f"Analyzed {len(state.retrieved_context)} retrieved context rows, "
        f"{len(state.compliance_risks)} compliance risks, and "
        f"{len(state.live_pricing)} live pricing records."
    )
    rationale = (
        f"Highest priority score is {signals.highest_priority_score:.2f}; "
        f"maximum annual exposure is ${signals.maximum_annual_cost_usd:,.2f}; "
        f"high-risk contexts={signals.high_risk_count}; "
        f"high-severity risks={signals.high_severity_count}; "
        f"live pricing available={signals.has_live_pricing}."
    )
    if requires_hitl:
        rationale += " Human approval is required before finalizing renewal or cancellation action."

    return RecommendationDraft(
        summary=summary,
        recommended_action=action,
        requires_human_approval=requires_hitl,
        rationale=rationale,
    )


def _requires_human_approval(signals: DraftingSignals) -> bool:
    return (
        signals.high_risk_count > 0
        or signals.high_severity_count > 0
        or signals.maximum_annual_cost_usd >= 25000
    )


def _recommended_action(signals: DraftingSignals) -> str:
    if _requires_human_approval(signals):
        return "Prepare renewal review for human approval"
    if signals.has_live_pricing:
        return "Monitor pricing and governance posture"
    return "Gather pricing before recommendation"
