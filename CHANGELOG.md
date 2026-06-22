# Changelog

All notable project changes should be documented here as the implementation evolves across phases.

## Unreleased

- Added reset scripts for repeatable demo automation:
  - [`agent-brain/scripts/reset_graph.py`](agent-brain/scripts/reset_graph.py) to delete demo-owned Neo4j graph nodes and relationships.
  - [`mock-pricing-api/scripts/reset_pricing_fixture.py`](mock-pricing-api/scripts/reset_pricing_fixture.py) to validate or restore committed pricing fixtures.
  - [`scripts/reset-demo-environment.ps1`](scripts/reset-demo-environment.ps1) for Windows full demo reset orchestration.
  - [`scripts/reset-demo-environment.sh`](scripts/reset-demo-environment.sh) for WSL/Linux equivalent.
- Updated [`docs/06-setup-runbook.md`](docs/06-setup-runbook.md) with present status for all reset scripts, full and targeted reset command guidance, and an explanation of why Python quality checks (`pytest`, `ruff`, `mypy`) are required.
- Updated [`docs/07-demo-runbook.md`](docs/07-demo-runbook.md) with a note on why deterministic placeholder embedding vectors are used.
- Added Phase 3 LangGraph HITL education notebook at [`agent-brain/notebooks/phase3-langgraph-hitl-demo.ipynb`](agent-brain/notebooks/phase3-langgraph-hitl-demo.ipynb) and corresponding test at [`agent-brain/tests/test_phase3_langgraph_notebook.py`](agent-brain/tests/test_phase3_langgraph_notebook.py).
- Updated [`agent-brain/README.md`](agent-brain/README.md) and [`plans/02-implementation-plan-checklist.md`](plans/02-implementation-plan-checklist.md) to reflect the Phase 3 notebook.

## v0.1.0 — Phase 0 through Phase 4 complete

### Phase 0: Monorepo foundation

- Created the monorepo foundation for `database-layer`, `agent-brain`, `mock-pricing-api`, `docs`, `plans`, and `scripts`.
- Added local Docker service configuration for PostgreSQL with pgvector and Neo4j.
- Added root and workstream `.env.example` templates.
- Added architecture, schema, technical tool interaction, query-scope, setup, reset, and embedding strategy documentation.

### Phase 1: Local data foundations and zero-ETL architecture

- Added TypeScript and Prisma database-layer scaffolding.
- Added initial Prisma schema for vendors, software, subscriptions, compliance documents, document chunks, compliance risks, and audit events.
- Added deterministic synthetic subscription JSON and compliance text fixtures.
- Added ingestion, pgvector enablement, and concurrency validation scripts.
- Applied Prisma schema to local PostgreSQL, ran synthetic ingestion, verified persisted data and pgvector embeddings, and validated optimistic concurrency audit events.
- Validated Docker runtime services for PostgreSQL with pgvector and Neo4j.
- Installed and locked [`database-layer`](database-layer/) Node dependencies, added `@types/pg`, and validated Prisma generation, Prisma schema validation, and TypeScript type checking.
- Added dependency and versioning strategy in [`docs/05-dependency-versioning-strategy.md`](docs/05-dependency-versioning-strategy.md).
- Added business product requirements document in [`docs/01-product-requirements.md`](docs/01-product-requirements.md).
- Added repeatable demo reset script [`database-layer/scripts/reset-demo-data.ts`](database-layer/scripts/reset-demo-data.ts).

### Phase 2: Local hybrid context architecture

- Initialized the [`agent-brain`](agent-brain/) Python project scaffold with pinned dependencies, local environment template, configuration module, validation CLI, and package structure.
- Added Neo4j graph projection from validated PostgreSQL records.
- Added PostgreSQL vector retrieval module using pgvector distance ordering.
- Added Neo4j graph traversal module connecting vendors, software, subscriptions, documents, chunks, and risks.
- Added hybrid retrieval function combining PostgreSQL vector evidence and Neo4j graph context into deterministic risk-to-cost rows.
- Documented curated positive demo query scope in [`plans/03-query-scope.md`](plans/03-query-scope.md).
- Added reusable curated demo module and CLI at [`agent-brain/src/agent_brain/cli/run_curated_demo.py`](agent-brain/src/agent_brain/cli/run_curated_demo.py).
- Added Phase 2 stakeholder notebook at [`agent-brain/notebooks/phase2-risk-to-cost-demo.ipynb`](agent-brain/notebooks/phase2-risk-to-cost-demo.ipynb).

### Phase 3: Agentic orchestration and mock tool use

- Initialized FastAPI project in [`mock-pricing-api/`](mock-pricing-api/) with synthetic pricing fixture, typed models, tests, and pricing contract documentation.
- Added LangGraph-ready agent state model in [`agent-brain/src/agent_brain/orchestration/state.py`](agent-brain/src/agent_brain/orchestration/state.py).
- Added mock pricing tool wrapper in [`agent-brain/src/agent_brain/tools/pricing.py`](agent-brain/src/agent_brain/tools/pricing.py).
- Added recommendation drafting scaffold in [`agent-brain/src/agent_brain/orchestration/recommendation.py`](agent-brain/src/agent_brain/orchestration/recommendation.py).
- Added mandatory HITL finalization gate in [`agent-brain/src/agent_brain/governance/hitl.py`](agent-brain/src/agent_brain/governance/hitl.py).
- Added LangGraph runtime workflow in [`agent-brain/src/agent_brain/orchestration/workflow.py`](agent-brain/src/agent_brain/orchestration/workflow.py) without LLM calls or OpenAI Agents SDK behavior.
- Added Phase 3 LangGraph HITL education notebook at [`agent-brain/notebooks/phase3-langgraph-hitl-demo.ipynb`](agent-brain/notebooks/phase3-langgraph-hitl-demo.ipynb).

### Phase 4: Governance, observability, and FinOps

- Added local model adapter boundary for Microsoft Foundry Local readiness in [`agent-brain/src/agent_brain/orchestration/model_adapter.py`](agent-brain/src/agent_brain/orchestration/model_adapter.py).
- Added Phoenix-compatible trace payload builders in [`agent-brain/src/agent_brain/governance/observability.py`](agent-brain/src/agent_brain/governance/observability.py).
- Added Langfuse-compatible token usage and simulated cost payload builders.
- Added safety flag logging.
- Added audit persistence helpers in [`agent-brain/src/agent_brain/governance/audit.py`](agent-brain/src/agent_brain/governance/audit.py).
- Added optional Docker Compose `observability` profile for Phoenix and Langfuse.
- Documented local fallback behavior when optional observability tools are not installed.
- Added ADRs for version control, placeholder embedding strategy, Microsoft Foundry Local model provider, and LangGraph runtime with deterministic governance.

### Known limitations (by design for the current phase)

- Embedding vectors are deterministic placeholders, not production semantic embeddings.
- Phoenix and Langfuse payload compatibility is implemented, but live exporter clients are not yet wired end-to-end.
- Microsoft Foundry Local is represented by an adapter boundary, not a concrete model client.
- The current experience is CLI and notebook based; no polished user-facing UI is included.
- Local audit records remain the durable governance source of truth when optional observability services are disabled.
