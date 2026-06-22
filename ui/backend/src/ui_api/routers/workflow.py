"""Workflow router for LangGraph workflow execution and HITL decisions."""

from __future__ import annotations

import uuid
from typing import Any, cast

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

router = APIRouter(prefix="/api/workflow", tags=["workflow"])

# In-memory store for workflow states (thread_id -> state)
_workflow_states: dict[str, dict[str, Any]] = {}


class WorkflowRunRequest(BaseModel):
    """Request to start a workflow run."""

    user_query: str = Field(..., min_length=1, description="The user query for the workflow.")
    retrieved_context: list[dict[str, Any]] = Field(
        default_factory=list, description="Pre-retrieved context rows."
    )
    compliance_risks: list[dict[str, Any]] = Field(
        default_factory=list, description="Pre-identified compliance risks."
    )
    pricing_software_code: str | None = Field(
        default=None, description="Software code for pricing lookup."
    )
    pricing_requested_seats: int | None = Field(
        default=None, ge=0, description="Requested seats for pricing lookup."
    )


class HitlDecisionRequest(BaseModel):
    """Request to submit a HITL decision."""

    outcome: str = Field(..., description="APPROVED, REJECTED, or REVISION_REQUESTED.")
    reviewer: str = Field(..., min_length=1, description="Reviewer name.")
    rationale: str = Field(..., min_length=1, description="Rationale for the decision.")


@router.post("/run")
async def run_workflow(request: WorkflowRunRequest) -> dict[str, Any]:
    """Start a LangGraph workflow run."""
    try:
        from agent_brain.orchestration.state import create_initial_state
        from agent_brain.orchestration.workflow import run_langgraph_workflow

        thread_id = f"thread-{uuid.uuid4()}"
        initial_state = create_initial_state(request.user_query, trace_id=thread_id)

        # Build the LangGraph workflow state
        workflow_state: dict[str, Any] = {
            "user_query": initial_state.user_query,
            "retrieved_context": request.retrieved_context,
            "compliance_risks": request.compliance_risks,
            "live_pricing": [],
            "recommendation_draft": None,
            "human_approval_status": "PENDING",
            "final_output": None,
            "trace_id": thread_id,
            "safety_flags": [],
        }

        # Add pricing request if provided
        if request.pricing_software_code:
            workflow_state["pricing_request"] = {
                "software_code": request.pricing_software_code,
                "requested_seats": request.pricing_requested_seats,
            }

        result = run_langgraph_workflow(workflow_state, thread_id=thread_id)  # type: ignore[arg-type]
        _workflow_states[thread_id] = result  # type: ignore[assignment]

        return {
            "thread_id": thread_id,
            "state": result,
            "workflow_status": result.get("workflow_status", "UNKNOWN"),
            "hitl_pause": result.get("hitl_pause"),
            "cli_equivalent": "agent-brain workflow (LangGraph runtime)",
        }
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail={
                "error": str(exc),
                "trace_id": thread_id if "thread_id" in locals() else None,
            },
        ) from exc


@router.get("/state/{thread_id}")
async def get_workflow_state(thread_id: str) -> dict[str, Any]:
    """Get current workflow state by thread ID."""
    if thread_id not in _workflow_states:
        raise HTTPException(
            status_code=404,
            detail=f"Workflow thread not found: {thread_id}",
        )
    return {
        "thread_id": thread_id,
        "state": _workflow_states[thread_id],
        "workflow_status": _workflow_states[thread_id].get("workflow_status", "UNKNOWN"),
    }


@router.post("/hitl/{thread_id}")
async def submit_hitl_decision(
    thread_id: str, request: HitlDecisionRequest
) -> dict[str, Any]:
    """Submit a HITL decision for a paused workflow."""
    if thread_id not in _workflow_states:
        raise HTTPException(
            status_code=404,
            detail=f"Workflow thread not found: {thread_id}",
        )

    try:
        from agent_brain.orchestration.workflow import run_langgraph_workflow

        state = _workflow_states[thread_id]
        state["finalization_decision"] = {
            "outcome": request.outcome,
            "reviewer": request.reviewer,
            "rationale": request.rationale,
        }

        result = run_langgraph_workflow(state, thread_id=thread_id)  # type: ignore[arg-type]
        _workflow_states[thread_id] = result  # type: ignore[assignment]

        return {
            "thread_id": thread_id,
            "state": result,
            "workflow_status": result.get("workflow_status", "UNKNOWN"),
            "final_output": result.get("final_output"),
            "hitl_pause": result.get("hitl_pause"),
        }
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail={
                "error": str(exc),
                "trace_id": thread_id,
            },
        ) from exc


@router.get("/active")
async def get_active_workflows() -> dict[str, Any]:
    """Get all active workflow threads."""
    return {
        "workflows": [
            {
                "thread_id": tid,
                "workflow_status": state.get("workflow_status", "UNKNOWN"),
                "user_query": state.get("user_query", ""),
                "has_final_output": state.get("final_output") is not None,
            }
            for tid, state in _workflow_states.items()
        ],
        "count": len(_workflow_states),
    }


@router.delete("/state/{thread_id}")
async def clear_workflow_state(thread_id: str) -> dict[str, Any]:
    """Clear a workflow session state."""
    if thread_id in _workflow_states:
        del _workflow_states[thread_id]
        return {"thread_id": thread_id, "cleared": True}
    raise HTTPException(
        status_code=404,
        detail=f"Workflow thread not found: {thread_id}",
    )
