# Changelog

All notable project changes should be documented here as the implementation evolves across phases.

## Unreleased

- Improved Configuration page security and UX:
  - Fixed redacted OpenAI API key overlap by using fixed-length masking (5 asterisks) instead of one asterisk per character.
  - Marked `database_url` as sensitive and added dedicated connection-string masking that redacts the password while keeping host/db visible.
  - Added `break-all` CSS to prevent long values from overflowing grid cells.
  - See [ADR 0007](docs/adr/0007-foundry-local-integration-and-config-ui.md) for full details.
- Reorganized Configuration page layout:
  - Moved "OpenAI API Key & Model" section inside the Model Provider Switcher card (only shown when `openai` is active).
  - Moved Embeddings config table inside the Embedding Provider Switcher card.
  - Added Foundry Local Model selector (only shown when `microsoft-foundry-local` is active).
  - Removed duplicate parameters already shown in status cards or switcher active states.
  - Removed irrelevant CLI equivalent message from the Embedding Provider Switcher.
- Synced embedding parameters on provider switch:
  - `EMBEDDING_MODEL` and `EMBEDDING_DIMENSION` now update automatically when switching embedding providers.
- Added Foundry Local integration:
  - Curated catalog of Foundry Local models with device information.
  - `PUT /api/provider/foundry-model` endpoint: checks service, starts if needed, downloads model if needed, updates `.env`.
  - `GET /api/provider/foundry-status` endpoint: checks SDK availability, service status, cache directory.
  - `POST /api/provider/foundry-install` endpoint: installs the Foundry Local Python SDK into the backend interpreter, using `foundry-local-sdk-winml` on Windows for Windows ML hardware acceleration.
  - `PUT /api/provider/foundry-cache` endpoint: changes model cache directory.
  - Auto-starts Foundry Local service when switching to `microsoft-foundry-local` (does NOT auto-stop when switching away).
  - Frontend shows install button, step-by-step progress, and folder picker for cache directory.
  - Keeps Foundry Local service management on the Configuration page rather than duplicating it on the Dashboard health grid.
  - Uses the backend Python interpreter for SDK installation so the running UI API can import the SDK after restart.
  - Notes that SDK-managed service endpoints are process/session scoped and may need restart after backend restarts.
- Improved Dashboard service health:
  - Hid the redundant Foundry Local health card because Foundry usage is provider-dependent and managed on the Configuration page.
  - Added the mock Pricing API to required-service auto-start.
  - Fixed Pricing API startup from the UI by launching it with Python 3.11 and a source-tree `PYTHONPATH`.
  - Shortened the Pricing API healthy message to use the port-based style used by other services.
- Fixed scroll position loss on provider switch:
  - `fetchAll` now accepts a `silent` parameter to skip the loading spinner on refetches.
  - All post-action refetches use `fetchAll(true)` to preserve scroll position.
- Updated `.gitignore` to exclude large Foundry Local model files (`.onnx`, `.gguf`, `.bin`, model caches, Docker volumes).
- Added [ADR 0007](docs/adr/0007-foundry-local-integration-and-config-ui.md) documenting all architectural decisions.

- Added integration tests against live PostgreSQL:
  - Added [`agent-brain/tests/test_audit_integration.py`](agent-brain/tests/test_audit_integration.py) with 5 integration tests marked `@pytest.mark.integration`.
  - Tests verify single and multiple audit event persistence, model usage detail, empty event no-op, and durable audit when observability is disabled.
  - Each test cleans up its own audit events by trace ID for idempotency.
  - Added `integration` pytest marker to [`agent-brain/pyproject.toml`](agent-brain/pyproject.toml).
  - Run with `pytest -m integration` (requires live PostgreSQL); skip with `pytest -m "not integration"`.
- Wired live Phoenix and Langfuse exporter clients:
  - Added [`agent-brain/src/agent_brain/governance/exporters.py`](agent-brain/src/agent_brain/governance/exporters.py) with `export_phoenix_spans()`, `export_langfuse_usage()`, and `export_safety_events()`.
  - Exporters use `httpx` to send payloads to live Phoenix and Langfuse HTTP endpoints.
  - All exporters fail gracefully — disabled or unreachable services return a failed `ExportResult` without raising.
  - Added `httpx` dependency to [`agent-brain/pyproject.toml`](agent-brain/pyproject.toml).
  - Added 14 tests covering enabled/disabled states, successful exports, and graceful failure.
- Implemented multi-provider model and embedding adapters (Option C):
  - Added `OpenAIModelAdapter` using the OpenAI Responses API as primary with Chat Completions API fallback.
  - Implemented concrete `MicrosoftFoundryLocalAdapter` using Chat Completions API against the local Foundry Local endpoint.
  - Added `OPENAI` to the `ModelProvider` enum and `build_model_adapter()` factory.
  - Added real embedding functions (OpenAI and Foundry Local) to both [`database-layer/src/embedding.ts`](database-layer/src/embedding.ts) and [`agent-brain/src/agent_brain/retrieval/vector.py`](agent-brain/src/agent_brain/retrieval/vector.py).
  - Updated [`agent-brain/src/agent_brain/config.py`](agent-brain/src/agent_brain/config.py) with `embedding_provider`, `embedding_model`, `openai_api_key`, `openai_model`, and `openai_base_url` settings.
  - Updated [`database-layer/scripts/ingest.ts`](database-layer/scripts/ingest.ts) to use async `createEmbedding()`.
  - Added `openai` dependency to [`agent-brain/pyproject.toml`](agent-brain/pyproject.toml).
  - Updated environment templates (`.env.example`, `agent-brain/.env.example`, `database-layer/.env.example`) with new provider variables.
  - Added 16 tests covering placeholder, Foundry Local, OpenAI Responses API, and Chat Completions fallback.
- Added provider setup scripts for secure API key configuration and provider switching:
  - [`scripts/setup-provider.ps1`](scripts/setup-provider.ps1) for Windows PowerShell.
  - [`scripts/setup-provider.sh`](scripts/setup-provider.sh) for WSL/Linux.
  - Supports switching between `placeholder`, `foundry`, and `openai` providers.
  - API key is entered with masked input and written only to gitignored `.env` files.
- Added ADRs:
  - [ADR 0005](docs/adr/0005-multi-provider-model-and-embedding-strategy.md): Multi-provider model and embedding strategy.
  - [ADR 0006](docs/adr/0006-openai-responses-api-strategy.md): OpenAI Responses API as primary with Chat Completions fallback.
  - Updated [ADR 0002](docs/adr/0002-placeholder-embedding-strategy.md) status to superseded by ADR 0005.
  - Updated [ADR 0003](docs/adr/0003-microsoft-foundry-local-model-provider.md) status to reflect implemented multi-provider support.
- Added [`plans/05-forward-looking-implementation-plan.md`](plans/05-forward-looking-implementation-plan.md) documenting remaining implementation priorities.
- Documented Foundry Local setup in [`docs/06-setup-runbook.md`](docs/06-setup-runbook.md) including hardware requirements, installation, model download, and configuration.
- Updated [`docs/06-setup-runbook.md`](docs/06-setup-runbook.md) with provider configuration section, setup script references, and explanation of why Python quality checks are required.
- Updated [`docs/07-demo-runbook.md`](docs/07-demo-runbook.md) with provider switching guidance and updated caveats.
- Updated [`README.md`](README.md) with model and embedding provider table.
- Updated [`CONTRIBUTING.md`](CONTRIBUTING.md) with provider configuration section.
- Added reset scripts for repeatable demo automation:
  - [`agent-brain/scripts/reset_graph.py`](agent-brain/scripts/reset_graph.py) to delete demo-owned Neo4j graph nodes and relationships.
  - [`mock-pricing-api/scripts/reset_pricing_fixture.py`](mock-pricing-api/scripts/reset_pricing_fixture.py) to validate or restore committed pricing fixtures.
  - [`scripts/reset-demo-environment.ps1`](scripts/reset-demo-environment.ps1) for Windows full demo reset orchestration.
  - [`scripts/reset-demo-environment.sh`](scripts/reset-demo-environment.sh) for WSL/Linux equivalent.
- Added tests for reset scripts (32 tests across both scripts).
- Added Phase 3 LangGraph HITL education notebook at [`agent-brain/notebooks/phase3-langgraph-hitl-demo.ipynb`](agent-brain/notebooks/phase3-langgraph-hitl-demo.ipynb) and corresponding test.
- Added MIT [`LICENSE`](LICENSE) file and updated license declarations in both `pyproject.toml` files.
- Added [`CONTRIBUTING.md`](CONTRIBUTING.md) with setup, validation, branch, commit, and pull request guidance.
- Consolidated [`CHANGELOG.md`](CHANGELOG.md) into v0.1.0 release covering Phase 0 through Phase 4.

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
