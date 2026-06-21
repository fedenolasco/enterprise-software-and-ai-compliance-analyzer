from agent_brain.governance.hitl import HITLDecisionOutcome
from agent_brain.orchestration.state import AgentBrainState, RetrievedContext, create_initial_state
from agent_brain.orchestration.workflow import (
    LangGraphWorkflowState,
    agent_state_from_langgraph_state,
    build_langgraph_workflow,
    run_langgraph_workflow,
    workflow_state_from_agent_state,
)


def _high_risk_workflow_state() -> LangGraphWorkflowState:
    state = AgentBrainState(
        user_query="Should we renew OpenAI Enterprise?",
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
        trace_id="trace-langgraph-test",
    )
    return workflow_state_from_agent_state(state)


def test_langgraph_workflow_compiles() -> None:
    graph = build_langgraph_workflow()

    assert graph is not None


def test_workflow_round_trips_agent_state() -> None:
    original_state = _high_risk_workflow_state()

    agent_state = agent_state_from_langgraph_state(original_state)
    exported_state = workflow_state_from_agent_state(agent_state, original_state)

    assert exported_state["user_query"] == "Should we renew OpenAI Enterprise?"
    assert exported_state["retrieved_context"][0]["vendor_name"] == "OpenAI Enterprise"
    assert exported_state.get("trace_id") == "trace-langgraph-test"


def test_high_risk_workflow_requires_hitl_before_final_output() -> None:
    result = run_langgraph_workflow(_high_risk_workflow_state(), thread_id="hitl-required")

    assert result.get("workflow_status") == "HITL_REQUIRED"
    assert result["final_output"] is None
    hitl_pause = result.get("hitl_pause")
    assert hitl_pause is not None
    assert hitl_pause["required"] is True
    assert result["recommendation_draft"] is not None
    assert result["recommendation_draft"]["requires_human_approval"] is True
    assert "HITL_REQUIRED" in result.get("safety_flags", [])


def test_high_risk_workflow_finalizes_after_approval() -> None:
    state = _high_risk_workflow_state()
    state["finalization_decision"] = {
        "outcome": HITLDecisionOutcome.APPROVED.value,
        "reviewer": "Compliance reviewer",
        "rationale": "Approved for governed renewal review.",
    }

    result = run_langgraph_workflow(state, thread_id="hitl-approved")

    assert result.get("workflow_status") == "FINALIZED_WITH_HITL"
    assert result["final_output"] is not None
    assert "Approved by Compliance reviewer" in result["final_output"]
    assert "HITL_APPROVED" in result.get("safety_flags", [])


def test_low_risk_workflow_finalizes_without_hitl() -> None:
    state = workflow_state_from_agent_state(create_initial_state("Summarize governance posture."))

    result = run_langgraph_workflow(state, thread_id="no-hitl-required")

    assert result.get("workflow_status") == "FINALIZED_WITHOUT_HITL"
    assert result["final_output"] is not None
    assert result.get("hitl_pause") is None
