"""LangGraph-ready state model for governed recommendation workflows."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import NotRequired, TypedDict

from agent_brain.retrieval.hybrid import HybridRetrievalResult


class HumanApprovalStatus(StrEnum):
    """Human approval lifecycle for governed recommendation finalization."""

    NOT_REQUIRED = "NOT_REQUIRED"
    REQUIRED = "REQUIRED"
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


class LangGraphState(TypedDict):
    """TypedDict shape suitable for future LangGraph state graph integration."""

    user_query: str
    retrieved_context: list[dict[str, object]]
    compliance_risks: list[dict[str, object]]
    live_pricing: list[dict[str, object]]
    recommendation_draft: dict[str, object] | None
    human_approval_status: str
    final_output: str | None
    trace_id: NotRequired[str | None]
    safety_flags: NotRequired[list[str]]


@dataclass(frozen=True)
class RetrievedContext:
    """Retrieved evidence, cost, and graph context used by the agent workflow."""

    vendor_name: str
    software_name: str
    subscription_code: str | None
    annual_cost_usd: float | None
    renewal_date: str | None
    risk_tier: str | None
    risk_category: str | None
    risk_severity: str | None
    evidence_excerpt: str | None
    source_document: str | None
    priority_score: float

    @classmethod
    def from_hybrid_result(cls, result: HybridRetrievalResult) -> RetrievedContext:
        """Create retrieved context from a Phase 2 hybrid retrieval result."""

        return cls(
            vendor_name=result.vendor_name,
            software_name=result.software_name,
            subscription_code=result.subscription_code,
            annual_cost_usd=result.annual_cost_usd,
            renewal_date=result.renewal_date,
            risk_tier=result.risk_tier,
            risk_category=result.risk_category,
            risk_severity=result.risk_severity,
            evidence_excerpt=result.evidence_excerpt,
            source_document=result.source_document,
            priority_score=result.priority_score,
        )

    def to_langgraph_dict(self) -> dict[str, object]:
        """Return a JSON-serializable mapping for LangGraph state."""

        return _without_none(self.__dict__)


@dataclass(frozen=True)
class ComplianceRiskContext:
    """Normalized risk context extracted from retrieved evidence."""

    vendor_name: str
    risk_category: str
    risk_severity: str
    rationale: str
    evidence_source: str | None = None

    def to_langgraph_dict(self) -> dict[str, object]:
        """Return a JSON-serializable mapping for LangGraph state."""

        return _without_none(self.__dict__)


@dataclass(frozen=True)
class LivePricingContext:
    """Mock-pricing API context used by the future pricing tool wrapper."""

    software_code: str
    software_name: str
    requested_seats: int | None
    estimated_annual_total_usd: float
    applied_discount_percent: float
    source: str = "mock-pricing-api"

    def to_langgraph_dict(self) -> dict[str, object]:
        """Return a JSON-serializable mapping for LangGraph state."""

        return _without_none(self.__dict__)


@dataclass(frozen=True)
class RecommendationDraft:
    """Draft recommendation that must pass governance checks before final output."""

    summary: str
    recommended_action: str
    requires_human_approval: bool
    rationale: str

    def is_cancellation_or_renewal_decision(self) -> bool:
        """Return whether the draft touches cancellation or renewal finalization."""

        normalized = self.recommended_action.lower()
        return "cancel" in normalized or "renew" in normalized or "renewal" in normalized

    def to_langgraph_dict(self) -> dict[str, object]:
        """Return a JSON-serializable mapping for LangGraph state."""

        return dict(self.__dict__)


@dataclass
class AgentBrainState:
    """Mutable state container matching the planned Phase 3 LangGraph workflow fields."""

    user_query: str
    retrieved_context: list[RetrievedContext] = field(default_factory=list)
    compliance_risks: list[ComplianceRiskContext] = field(default_factory=list)
    live_pricing: list[LivePricingContext] = field(default_factory=list)
    recommendation_draft: RecommendationDraft | None = None
    human_approval_status: HumanApprovalStatus = HumanApprovalStatus.NOT_REQUIRED
    final_output: str | None = None
    trace_id: str | None = None
    safety_flags: list[str] = field(default_factory=list)

    def to_langgraph_state(self) -> LangGraphState:
        """Return the TypedDict shape expected by future LangGraph nodes."""

        state: LangGraphState = {
            "user_query": self.user_query,
            "retrieved_context": [
                context.to_langgraph_dict() for context in self.retrieved_context
            ],
            "compliance_risks": [risk.to_langgraph_dict() for risk in self.compliance_risks],
            "live_pricing": [pricing.to_langgraph_dict() for pricing in self.live_pricing],
            "recommendation_draft": (
                self.recommendation_draft.to_langgraph_dict()
                if self.recommendation_draft is not None
                else None
            ),
            "human_approval_status": self.human_approval_status.value,
            "final_output": self.final_output,
            "trace_id": self.trace_id,
            "safety_flags": list(self.safety_flags),
        }
        return state


def create_initial_state(user_query: str, trace_id: str | None = None) -> AgentBrainState:
    """Create an initial agent state for retrieval-first Phase 3 workflows."""

    if user_query.strip() == "":
        raise ValueError("user_query must not be empty.")
    return AgentBrainState(user_query=user_query, trace_id=trace_id)


def record_human_approval(
    state: AgentBrainState,
    status: HumanApprovalStatus,
) -> AgentBrainState:
    """Return a copy of state with updated human approval status."""

    return AgentBrainState(
        user_query=state.user_query,
        retrieved_context=list(state.retrieved_context),
        compliance_risks=list(state.compliance_risks),
        live_pricing=list(state.live_pricing),
        recommendation_draft=state.recommendation_draft,
        human_approval_status=status,
        final_output=state.final_output,
        trace_id=state.trace_id,
        safety_flags=list(state.safety_flags),
    )


def is_finalization_allowed(state: AgentBrainState) -> bool:
    """Enforce a hard stop before finalizing cancellation or renewal recommendations."""

    draft = state.recommendation_draft
    if draft is None:
        return False
    if not draft.requires_human_approval and not draft.is_cancellation_or_renewal_decision():
        return True
    return state.human_approval_status == HumanApprovalStatus.APPROVED


def _without_none(values: dict[str, object]) -> dict[str, object]:
    return {key: value for key, value in values.items() if value is not None}
