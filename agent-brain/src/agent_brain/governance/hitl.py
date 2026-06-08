"""Human-in-the-loop controls for governed recommendation finalization."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum

from agent_brain.orchestration.state import (
    AgentBrainState,
    HumanApprovalStatus,
    is_finalization_allowed,
    record_human_approval,
)


class HITLDecisionOutcome(StrEnum):
    """Allowed human decisions for recommendation finalization."""

    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    REVISION_REQUESTED = "REVISION_REQUESTED"


@dataclass(frozen=True)
class HITLPause:
    """Structured pause payload presented before governed finalization."""

    required: bool
    reason: str
    draft_summary: str | None
    recommended_action: str | None
    trace_id: str | None
    safety_flags: tuple[str, ...]


@dataclass(frozen=True)
class HITLDecision:
    """Human approval decision captured for audit and finalization logic."""

    outcome: HITLDecisionOutcome
    reviewer: str
    rationale: str
    decided_at: str

    @classmethod
    def create(
        cls,
        outcome: HITLDecisionOutcome,
        reviewer: str,
        rationale: str,
    ) -> HITLDecision:
        """Create a timestamped decision record."""

        if reviewer.strip() == "":
            raise ValueError("reviewer must not be empty.")
        if rationale.strip() == "":
            raise ValueError("rationale must not be empty.")
        return cls(
            outcome=outcome,
            reviewer=reviewer,
            rationale=rationale,
            decided_at=datetime.now(UTC).isoformat(),
        )

    def to_audit_detail(self) -> dict[str, object]:
        """Return JSON-serializable audit detail for future persistence."""

        return {
            "outcome": self.outcome.value,
            "reviewer": self.reviewer,
            "rationale": self.rationale,
            "decided_at": self.decided_at,
        }


def build_hitl_pause(state: AgentBrainState) -> HITLPause:
    """Build a mandatory pause payload when a draft cannot be finalized automatically."""

    draft = state.recommendation_draft
    required = not is_finalization_allowed(state)
    reason = "Human approval required before finalization." if required else "Finalization allowed."
    return HITLPause(
        required=required,
        reason=reason,
        draft_summary=draft.summary if draft else None,
        recommended_action=draft.recommended_action if draft else None,
        trace_id=state.trace_id,
        safety_flags=tuple(state.safety_flags),
    )


def finalize_with_hitl(state: AgentBrainState, decision: HITLDecision) -> AgentBrainState:
    """Apply a human decision and return state with final output only when approved."""

    approval_status = _approval_status_from_decision(decision)
    reviewed_state = record_human_approval(state, approval_status)
    if not is_finalization_allowed(reviewed_state):
        return AgentBrainState(
            user_query=reviewed_state.user_query,
            retrieved_context=list(reviewed_state.retrieved_context),
            compliance_risks=list(reviewed_state.compliance_risks),
            live_pricing=list(reviewed_state.live_pricing),
            recommendation_draft=reviewed_state.recommendation_draft,
            human_approval_status=reviewed_state.human_approval_status,
            final_output=None,
            trace_id=reviewed_state.trace_id,
            safety_flags=_append_flag(reviewed_state.safety_flags, "FINALIZATION_BLOCKED"),
        )

    draft = reviewed_state.recommendation_draft
    final_output = (
        f"Final recommendation: {draft.recommended_action}. {draft.rationale} "
        f"Approved by {decision.reviewer}."
        if draft is not None
        else None
    )
    return AgentBrainState(
        user_query=reviewed_state.user_query,
        retrieved_context=list(reviewed_state.retrieved_context),
        compliance_risks=list(reviewed_state.compliance_risks),
        live_pricing=list(reviewed_state.live_pricing),
        recommendation_draft=reviewed_state.recommendation_draft,
        human_approval_status=reviewed_state.human_approval_status,
        final_output=final_output,
        trace_id=reviewed_state.trace_id,
        safety_flags=_append_flag(reviewed_state.safety_flags, "HITL_APPROVED"),
    )


def _approval_status_from_decision(decision: HITLDecision) -> HumanApprovalStatus:
    if decision.outcome == HITLDecisionOutcome.APPROVED:
        return HumanApprovalStatus.APPROVED
    return HumanApprovalStatus.REJECTED


def _append_flag(flags: list[str], flag: str) -> list[str]:
    next_flags = list(flags)
    if flag not in next_flags:
        next_flags.append(flag)
    return next_flags
