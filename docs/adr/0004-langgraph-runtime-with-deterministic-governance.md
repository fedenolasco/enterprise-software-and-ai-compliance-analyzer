# ADR 0004: LangGraph Runtime with Deterministic Governance

## Status

Accepted for Phase A runtime implementation

## Context

The current [`agent-brain/`](../../agent-brain/) implementation has LangGraph-ready state models, pricing tool wrappers, deterministic recommendation drafting, and mandatory HITL finalization controls. The implementation does not yet use the LangGraph Python runtime.

The project needs a clearer runtime boundary for workflow orchestration, checkpoint-ready state, conditional routing, and future HITL pause/resume behavior. At the same time, the compliance-sensitive parts of the workflow must remain deterministic, auditable, and testable.

## Decision

Adopt LangGraph as the orchestration runtime for the `agent-brain` workflow while retaining deterministic Python domain logic as the compliance authority.

LangGraph will coordinate workflow nodes, conditional routing, and checkpoint-ready execution. It will not decide whether a recommendation can be finalized. Finalization authority remains in deterministic HITL logic.

Phase A will not introduce OpenAI Agents SDK, LLM calls, or cloud model dependencies.

## Implementation boundaries

LangGraph nodes should delegate to existing deterministic functions:

- [`add_pricing_to_state()`](../../agent-brain/src/agent_brain/tools/pricing.py) for mock pricing lookup and state updates.
- [`draft_recommendation()`](../../agent-brain/src/agent_brain/orchestration/recommendation.py) for recommendation drafting.
- [`is_finalization_allowed()`](../../agent-brain/src/agent_brain/orchestration/state.py) for finalization gating.
- [`build_hitl_pause()`](../../agent-brain/src/agent_brain/governance/hitl.py) for the HITL pause payload.
- [`finalize_with_hitl()`](../../agent-brain/src/agent_brain/governance/hitl.py) for approved finalization.

## Consequences

- The project can truthfully claim LangGraph runtime orchestration after implementation and validation.
- The workflow remains local-first and deterministic for Phase A.
- Existing state, recommendation, pricing, and HITL unit tests remain relevant.
- Additional tests are required for graph compilation, routing, pause behavior, and approved finalization.
- Dependency governance must be updated when LangGraph is added to [`agent-brain/pyproject.toml`](../../agent-brain/pyproject.toml).

## Deferred decisions

- Whether to add OpenAI Agents SDK for optional planning, routing, or explanation.
- Whether to add LLM calls through Microsoft Foundry Local or another local model runtime.
- Whether to add a dedicated Phase 3 LangGraph notebook or CLI demo after runtime validation.
