"""Unavailable-safe Phoenix and Langfuse compatible observability records."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from uuid import uuid4

from agent_brain.orchestration.model_adapter import ModelResponse
from agent_brain.orchestration.state import AgentBrainState


class AuditEventType(StrEnum):
    """Audit event types aligned to the Prisma AuditEvent enum."""

    HITL_DECISION = "HITL_DECISION"
    AGENT_RECOMMENDATION = "AGENT_RECOMMENDATION"


class AuditStatus(StrEnum):
    """Audit status values aligned to the Prisma AuditStatus enum."""

    SUCCESS = "SUCCESS"
    FAILURE = "FAILURE"
    PENDING = "PENDING"


@dataclass(frozen=True)
class PhoenixTraceSpan:
    """Phoenix-compatible trace span payload for future exporter wiring."""

    trace_id: str
    node_name: str
    started_at: str
    ended_at: str
    safety_flags: tuple[str, ...]
    metadata: dict[str, object] = field(default_factory=dict)

    def to_export_payload(self) -> dict[str, object]:
        """Return a JSON-serializable Phoenix-compatible payload."""

        return {
            "trace_id": self.trace_id,
            "node_name": self.node_name,
            "started_at": self.started_at,
            "ended_at": self.ended_at,
            "safety_flags": list(self.safety_flags),
            "metadata": dict(self.metadata),
        }


@dataclass(frozen=True)
class LangfuseUsageEvent:
    """Langfuse-compatible token usage and simulated cost payload."""

    trace_id: str
    model_name: str
    provider: str
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    simulated_cost_usd: float
    metadata: dict[str, object] = field(default_factory=dict)

    def to_export_payload(self) -> dict[str, object]:
        """Return a JSON-serializable Langfuse-compatible payload."""

        return {
            "trace_id": self.trace_id,
            "model_name": self.model_name,
            "provider": self.provider,
            "usage": {
                "prompt_tokens": self.prompt_tokens,
                "completion_tokens": self.completion_tokens,
                "total_tokens": self.total_tokens,
            },
            "simulated_cost_usd": self.simulated_cost_usd,
            "metadata": dict(self.metadata),
        }


@dataclass(frozen=True)
class SafetyFlagEvent:
    """Safety flag record emitted by governance-critical workflow steps."""

    trace_id: str
    flag: str
    risk_severity: str | None
    decision_outcome: str | None
    created_at: str

    def to_export_payload(self) -> dict[str, object]:
        """Return a JSON-serializable safety payload."""

        payload: dict[str, object] = {
            "trace_id": self.trace_id,
            "flag": self.flag,
            "created_at": self.created_at,
        }
        if self.risk_severity is not None:
            payload["risk_severity"] = self.risk_severity
        if self.decision_outcome is not None:
            payload["decision_outcome"] = self.decision_outcome
        return payload


@dataclass(frozen=True)
class GovernanceAuditEvent:
    """Local AuditEvent-compatible governance record."""

    event_type: AuditEventType
    status: AuditStatus
    actor: str
    trace_id: str
    message: str
    detail: dict[str, object]

    def to_prisma_insert(self) -> dict[str, object]:
        """Return keys matching the Prisma AuditEvent model."""

        return {
            "eventType": self.event_type.value,
            "status": self.status.value,
            "actor": self.actor,
            "traceId": self.trace_id,
            "message": self.message,
            "detail": self.detail,
        }


def ensure_trace_id(existing_trace_id: str | None = None) -> str:
    """Return an existing trace ID or create a deterministic-prefix local ID."""

    if existing_trace_id is not None and existing_trace_id.strip() != "":
        return existing_trace_id
    return f"trace-{uuid4()}"


def build_trace_span(
    state: AgentBrainState,
    node_name: str,
    *,
    metadata: dict[str, object] | None = None,
) -> PhoenixTraceSpan:
    """Build a Phoenix-compatible span from current agent state."""

    now = datetime.now(UTC).isoformat()
    return PhoenixTraceSpan(
        trace_id=ensure_trace_id(state.trace_id),
        node_name=node_name,
        started_at=now,
        ended_at=now,
        safety_flags=tuple(state.safety_flags),
        metadata=metadata or {},
    )


def build_usage_event(response: ModelResponse) -> LangfuseUsageEvent:
    """Build a Langfuse-compatible usage event from a model response."""

    return LangfuseUsageEvent(
        trace_id=ensure_trace_id(response.trace_id),
        model_name=response.model_name,
        provider=response.provider.value,
        prompt_tokens=response.prompt_tokens,
        completion_tokens=response.completion_tokens,
        total_tokens=response.total_tokens,
        simulated_cost_usd=response.simulated_cost_usd,
        metadata=dict(response.metadata),
    )


def build_safety_events(
    state: AgentBrainState,
    *,
    decision_outcome: str | None = None,
) -> list[SafetyFlagEvent]:
    """Create safety flag events from current workflow state."""

    trace_id = ensure_trace_id(state.trace_id)
    risk_severity = _highest_risk_severity(state)
    created_at = datetime.now(UTC).isoformat()
    return [
        SafetyFlagEvent(
            trace_id=trace_id,
            flag=flag,
            risk_severity=risk_severity,
            decision_outcome=decision_outcome,
            created_at=created_at,
        )
        for flag in state.safety_flags
    ]


def build_governance_audit_event(
    state: AgentBrainState,
    *,
    message: str,
    model_response: ModelResponse | None = None,
    decision_outcome: str | None = None,
) -> GovernanceAuditEvent:
    """Build an AuditEvent-compatible record for governance persistence."""

    trace_id = ensure_trace_id(state.trace_id)
    detail: dict[str, object] = {
        "human_approval_status": state.human_approval_status.value,
        "safety_flags": list(state.safety_flags),
        "risk_severity": _highest_risk_severity(state),
        "decision_outcome": decision_outcome,
        "final_output_present": state.final_output is not None,
    }
    if state.recommendation_draft is not None:
        detail["recommendation_draft"] = state.recommendation_draft.to_langgraph_dict()
    if model_response is not None:
        detail["model_usage"] = build_usage_event(model_response).to_export_payload()

    return GovernanceAuditEvent(
        event_type=AuditEventType.AGENT_RECOMMENDATION,
        status=AuditStatus.SUCCESS if state.final_output is not None else AuditStatus.PENDING,
        actor="agent-brain",
        trace_id=trace_id,
        message=message,
        detail=detail,
    )


def _highest_risk_severity(state: AgentBrainState) -> str | None:
    severity_order = {"LOW": 1, "MEDIUM": 2, "HIGH": 3, "CRITICAL": 4}
    severities = [
        risk.risk_severity.upper()
        for risk in state.compliance_risks
        if risk.risk_severity.upper() in severity_order
    ]
    severities.extend(
        context.risk_severity.upper()
        for context in state.retrieved_context
        if context.risk_severity is not None
        and context.risk_severity.upper() in severity_order
    )
    if not severities:
        return None
    return max(severities, key=lambda value: severity_order[value])
