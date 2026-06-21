"""LangGraph runtime wrapper for deterministic governed recommendation workflows."""

from __future__ import annotations

from typing import Any, NotRequired, SupportsFloat, SupportsInt, TypedDict, cast

from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, StateGraph

from agent_brain.governance.hitl import (
    HITLDecision,
    HITLDecisionOutcome,
    build_hitl_pause,
    finalize_with_hitl,
)
from agent_brain.orchestration.recommendation import draft_recommendation
from agent_brain.orchestration.state import (
    AgentBrainState,
    ComplianceRiskContext,
    HumanApprovalStatus,
    LangGraphState,
    LivePricingContext,
    RecommendationDraft,
    RetrievedContext,
    is_finalization_allowed,
)
from agent_brain.tools.pricing import add_pricing_to_state


class PricingRequest(TypedDict):
    """Optional pricing request accepted by the deterministic LangGraph workflow."""

    software_code: str
    requested_seats: NotRequired[int | None]


class HITLDecisionInput(TypedDict):
    """Serializable human decision input accepted by the workflow."""

    outcome: str
    reviewer: str
    rationale: str


class LangGraphWorkflowState(LangGraphState):
    """Serializable LangGraph workflow state plus runtime control fields."""

    pricing_request: NotRequired[PricingRequest | None]
    finalization_decision: NotRequired[HITLDecisionInput | None]
    hitl_pause: NotRequired[dict[str, object] | None]
    workflow_status: NotRequired[str]


def build_langgraph_workflow(checkpointer: InMemorySaver | None = None) -> Any:
    """Build a compiled LangGraph workflow around deterministic Python nodes."""

    builder = StateGraph(LangGraphWorkflowState)
    builder.add_node("pricing", _pricing_node)
    builder.add_node("draft_recommendation", _draft_recommendation_node)
    builder.add_node("build_hitl_pause", _build_hitl_pause_node)
    builder.add_node("finalize_without_hitl", _finalize_without_hitl_node)
    builder.add_node("finalize_with_hitl", _finalize_with_hitl_node)

    builder.add_edge(START, "pricing")
    builder.add_edge("pricing", "draft_recommendation")
    builder.add_conditional_edges(
        "draft_recommendation",
        _route_after_draft,
        {
            "build_hitl_pause": "build_hitl_pause",
            "finalize_without_hitl": "finalize_without_hitl",
            "finalize_with_hitl": "finalize_with_hitl",
        },
    )
    builder.add_edge("build_hitl_pause", END)
    builder.add_edge("finalize_without_hitl", END)
    builder.add_edge("finalize_with_hitl", END)

    return builder.compile(checkpointer=checkpointer)


def build_memory_checkpointer() -> InMemorySaver:
    """Create the default in-memory checkpointer for local workflow runs."""

    return InMemorySaver()


def run_langgraph_workflow(
    state: LangGraphWorkflowState,
    thread_id: str = "agent-brain-local-thread",
) -> LangGraphWorkflowState:
    """Run the deterministic LangGraph workflow with an in-memory checkpointer."""

    graph = build_langgraph_workflow(checkpointer=build_memory_checkpointer())
    result = graph.invoke(state, {"configurable": {"thread_id": thread_id}})
    return cast(LangGraphWorkflowState, result)


def agent_state_from_langgraph_state(state: LangGraphWorkflowState) -> AgentBrainState:
    """Convert serializable LangGraph workflow state into AgentBrainState."""

    return AgentBrainState(
        user_query=state["user_query"],
        retrieved_context=[
            RetrievedContext(
                vendor_name=str(context["vendor_name"]),
                software_name=str(context["software_name"]),
                subscription_code=_optional_str(context.get("subscription_code")),
                annual_cost_usd=_optional_float(context.get("annual_cost_usd")),
                renewal_date=_optional_str(context.get("renewal_date")),
                risk_tier=_optional_str(context.get("risk_tier")),
                risk_category=_optional_str(context.get("risk_category")),
                risk_severity=_optional_str(context.get("risk_severity")),
                evidence_excerpt=_optional_str(context.get("evidence_excerpt")),
                source_document=_optional_str(context.get("source_document")),
                priority_score=_required_float(context["priority_score"]),
            )
            for context in state.get("retrieved_context", [])
        ],
        compliance_risks=[
            ComplianceRiskContext(
                vendor_name=str(risk["vendor_name"]),
                risk_category=str(risk["risk_category"]),
                risk_severity=str(risk["risk_severity"]),
                rationale=str(risk["rationale"]),
                evidence_source=_optional_str(risk.get("evidence_source")),
            )
            for risk in state.get("compliance_risks", [])
        ],
        live_pricing=[
            LivePricingContext(
                software_code=str(pricing["software_code"]),
                software_name=str(pricing["software_name"]),
                requested_seats=_optional_int(pricing.get("requested_seats")),
                estimated_annual_total_usd=_required_float(
                    pricing["estimated_annual_total_usd"]
                ),
                applied_discount_percent=_required_float(
                    pricing["applied_discount_percent"]
                ),
                source=str(pricing.get("source", "mock-pricing-api")),
            )
            for pricing in state.get("live_pricing", [])
        ],
        recommendation_draft=_recommendation_draft_from_dict(state.get("recommendation_draft")),
        human_approval_status=HumanApprovalStatus(state["human_approval_status"]),
        final_output=_optional_str(state.get("final_output")),
        trace_id=_optional_str(state.get("trace_id")),
        safety_flags=[str(flag) for flag in state.get("safety_flags", [])],
    )


def workflow_state_from_agent_state(
    state: AgentBrainState,
    source_state: LangGraphWorkflowState | None = None,
) -> LangGraphWorkflowState:
    """Convert AgentBrainState into serializable LangGraph workflow state."""

    next_state = cast(LangGraphWorkflowState, state.to_langgraph_state())
    if source_state is not None:
        if "pricing_request" in source_state:
            next_state["pricing_request"] = source_state.get("pricing_request")
        if "finalization_decision" in source_state:
            next_state["finalization_decision"] = source_state.get("finalization_decision")
        if "hitl_pause" in source_state:
            next_state["hitl_pause"] = source_state.get("hitl_pause")
        if "workflow_status" in source_state:
            next_state["workflow_status"] = source_state.get("workflow_status", "")
    return next_state


def _pricing_node(state: LangGraphWorkflowState) -> LangGraphWorkflowState:
    pricing_request = state.get("pricing_request")
    if pricing_request is None:
        skipped_state = cast(LangGraphWorkflowState, dict(state))
        skipped_state["workflow_status"] = "PRICING_SKIPPED"
        return skipped_state

    agent_state = agent_state_from_langgraph_state(state)
    priced_state = add_pricing_to_state(
        agent_state,
        pricing_request["software_code"],
        pricing_request.get("requested_seats"),
    )
    next_state: LangGraphWorkflowState = workflow_state_from_agent_state(priced_state, state)
    next_state["workflow_status"] = "PRICING_COMPLETE"
    return next_state


def _draft_recommendation_node(state: LangGraphWorkflowState) -> LangGraphWorkflowState:
    drafted_state = draft_recommendation(agent_state_from_langgraph_state(state))
    next_state = workflow_state_from_agent_state(drafted_state, state)
    next_state["workflow_status"] = "DRAFT_READY"
    return next_state


def _route_after_draft(state: LangGraphWorkflowState) -> str:
    if state.get("finalization_decision") is not None:
        return "finalize_with_hitl"
    if is_finalization_allowed(agent_state_from_langgraph_state(state)):
        return "finalize_without_hitl"
    return "build_hitl_pause"


def _build_hitl_pause_node(state: LangGraphWorkflowState) -> LangGraphWorkflowState:
    pause = build_hitl_pause(agent_state_from_langgraph_state(state))
    next_state = dict(state)
    next_state["hitl_pause"] = {
        "required": pause.required,
        "reason": pause.reason,
        "draft_summary": pause.draft_summary,
        "recommended_action": pause.recommended_action,
        "trace_id": pause.trace_id,
        "safety_flags": list(pause.safety_flags),
    }
    next_state["final_output"] = None
    next_state["workflow_status"] = "HITL_REQUIRED" if pause.required else "FINALIZATION_READY"
    return cast(LangGraphWorkflowState, next_state)


def _finalize_without_hitl_node(state: LangGraphWorkflowState) -> LangGraphWorkflowState:
    agent_state = agent_state_from_langgraph_state(state)
    draft = agent_state.recommendation_draft
    final_output = (
        f"Final recommendation: {draft.recommended_action}. {draft.rationale}"
        if draft is not None
        else None
    )
    next_state = dict(state)
    next_state["final_output"] = final_output
    next_state["hitl_pause"] = None
    next_state["workflow_status"] = "FINALIZED_WITHOUT_HITL"
    return cast(LangGraphWorkflowState, next_state)


def _finalize_with_hitl_node(state: LangGraphWorkflowState) -> LangGraphWorkflowState:
    decision_input = state.get("finalization_decision")
    if decision_input is None:
        raise ValueError("finalization_decision is required for HITL finalization.")

    finalized_state = finalize_with_hitl(
        agent_state_from_langgraph_state(state),
        HITLDecision.create(
            HITLDecisionOutcome(decision_input["outcome"]),
            reviewer=decision_input["reviewer"],
            rationale=decision_input["rationale"],
        ),
    )
    next_state = workflow_state_from_agent_state(finalized_state, state)
    next_state["hitl_pause"] = (
        None if finalized_state.final_output is not None else state.get("hitl_pause")
    )
    next_state["workflow_status"] = (
        "FINALIZED_WITH_HITL"
        if finalized_state.final_output is not None
        else "FINALIZATION_BLOCKED"
    )
    return next_state


def _recommendation_draft_from_dict(value: dict[str, object] | None) -> RecommendationDraft | None:
    if value is None:
        return None
    return RecommendationDraft(
        summary=str(value["summary"]),
        recommended_action=str(value["recommended_action"]),
        requires_human_approval=bool(value["requires_human_approval"]),
        rationale=str(value["rationale"]),
    )


def _optional_str(value: object) -> str | None:
    return None if value is None else str(value)


def _optional_float(value: object) -> float | None:
    return None if value is None else _required_float(value)


def _optional_int(value: object) -> int | None:
    return None if value is None else _required_int(value)


def _required_float(value: object) -> float:
    return float(cast(str | SupportsFloat, value))


def _required_int(value: object) -> int:
    return int(cast(str | SupportsInt, value))
