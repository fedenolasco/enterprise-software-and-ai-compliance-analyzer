# Demo Runbook

## Purpose

This runbook gives a presentation-ready order for demonstrating the Enterprise Software & AI Compliance Analyzer from a clean local checkout. It complements the operational setup details in [`docs/06-setup-runbook.md`](06-setup-runbook.md), the architecture diagrams in [`docs/04-technical-tool-interactions.md`](04-technical-tool-interactions.md), and the curated query definitions in [`plans/03-query-scope.md`](../plans/03-query-scope.md).

Use this document when preparing a stakeholder walkthrough, recorded demo, or technical validation session.

## What the demo proves

The recommended flow demonstrates that the repository can locally connect:

1. Synthetic enterprise software subscription data.
2. Synthetic AI compliance documents.
3. PostgreSQL relational persistence.
4. pgvector-compatible document chunk embeddings.
5. Neo4j graph relationships.
6. Hybrid graph and vector retrieval.
7. Mock live pricing lookups.
8. Deterministic recommendation drafting.
9. Mandatory human-in-the-loop controls.
10. Governance, observability, and FinOps scaffolding.

## Demo prerequisites

Before the live demo, confirm the following local tools are available:

| Tool | Why it is needed |
|---|---|
| Docker Desktop | Runs PostgreSQL, pgvector, Neo4j, and optional observability services from [`docker-compose.yml`](../docker-compose.yml). |
| Node.js and npm | Installs and runs the TypeScript/Prisma database layer in [`database-layer/`](../database-layer/). |
| Python and pip | Installs and runs [`agent-brain/`](../agent-brain/) and [`mock-pricing-api/`](../mock-pricing-api/). |
| Git | Confirms the demo is running from the expected committed source. |

Optional tools:

| Tool | Why it is useful |
|---|---|
| JupyterLab | Opens the stakeholder-facing Phase 2 notebook in [`agent-brain/notebooks/phase2-risk-to-cost-demo.ipynb`](../agent-brain/notebooks/phase2-risk-to-cost-demo.ipynb). |
| Phoenix and Langfuse containers | Shows optional Phase 4 observability UIs. |
| Microsoft Foundry Local | Future replacement target for the deterministic placeholder model adapter. |

## Recommended demonstration order

### 1. Present the repository story

Start with the high-level project context:

- [`README.md`](../README.md) for the monorepo and phase overview.
- [`docs/02-architecture-overview.md`](02-architecture-overview.md) for architecture narrative.
- [`docs/04-technical-tool-interactions.md`](04-technical-tool-interactions.md) for tool interaction diagrams.
- [`plans/02-implementation-plan-checklist.md`](../plans/02-implementation-plan-checklist.md) for implementation completion status.

Suggested talk track:

> This is a local-first compliance analyzer that joins structured software subscription data with unstructured AI compliance evidence, then uses hybrid retrieval, mock tool use, HITL governance, and observability scaffolding to demonstrate a governed enterprise AI pattern.

### 2. Start local infrastructure

From the repository root:

```cmd
copy .env.example .env
docker compose up -d
```

This starts the default local infrastructure: PostgreSQL with pgvector and Neo4j. The detailed setup order is documented in [`docs/06-setup-runbook.md`](06-setup-runbook.md).

### 3. Bootstrap and seed the database layer

From [`database-layer/`](../database-layer/):

```cmd
copy .env.example .env
npm install
npm run db:generate
npm run db:push
npm run db:enable-vector
npm run reset:demo
npm run ingest
npm run validate:concurrency
```

Demonstrate or explain the outputs:

- Prisma schema is applied from [`database-layer/prisma/schema.prisma`](../database-layer/prisma/schema.prisma).
- pgvector is enabled.
- Synthetic subscriptions and documents are ingested.
- Document chunks and deterministic placeholder embedding vectors are persisted.
- Audit events are written.
- Optimistic concurrency validation runs.

### 4. Validate the Python agent workstream

From [`agent-brain/`](../agent-brain/):

```cmd
python -m pip install -e .[dev]
python -m pytest
```

For a deeper technical validation, also run:

```cmd
python -m agent_brain.cli.validate_scaffold
python -m ruff check src tests
python -m mypy src tests
```

### 5. Project relational data into Neo4j

From [`agent-brain/`](../agent-brain/):

```cmd
python -m agent_brain.cli.project_graph
```

This demonstrates that relational records from PostgreSQL can be projected into a graph structure for relationship traversal.

Note: deterministic placeholder embedding vectors are used so the demo remains local-first, repeatable, inexpensive, and independent of external model services or network availability. They prove the ingestion, pgvector persistence, retrieval plumbing, and graph/vector integration paths without introducing nondeterministic semantic model behavior into stakeholder walkthroughs.

### 6. Demonstrate vector retrieval

From [`agent-brain/`](../agent-brain/):

```cmd
python -m agent_brain.cli.search_vectors "cross-border processing subprocessors outside the EU" --top-k 5
```

Explain that the current embeddings are deterministic placeholder embedding vectors. They validate the pgvector write/read path but are not production semantic embeddings. The limitation is documented in [`docs/04-technical-tool-interactions.md`](04-technical-tool-interactions.md).

### 7. Demonstrate graph traversal

From [`agent-brain/`](../agent-brain/):

```cmd
python -m agent_brain.cli.traverse_graph --risk-category DATA_RESIDENCY --limit 10
```

This demonstrates relationship-aware retrieval across vendors, software, subscriptions, compliance documents, document chunks, and risks.

### 8. Demonstrate hybrid retrieval

From [`agent-brain/`](../agent-brain/):

```cmd
python -m agent_brain.cli.hybrid_retrieve "cross-border processing subprocessors outside the EU" --top-k 5 --graph-limit 25
```

This is the main technical retrieval proof point: the result combines PostgreSQL vector evidence and Neo4j graph context into deterministic risk-to-cost rows.

### 9. Run the curated deterministic demo

From [`agent-brain/`](../agent-brain/):

```cmd
python -m agent_brain.cli.run_curated_demo
```

This is the strongest scripted demo step. It uses the curated query definitions in [`plans/03-query-scope.md`](../plans/03-query-scope.md), including:

1. High-risk AI vendors with renewal cost exposure.
2. Cost-weighted compliance review queue.
3. Data residency and international transfer exposure.
4. HITL-required cancellation or renewal candidates.

### 10. Optionally open the stakeholder notebook

From [`agent-brain/`](../agent-brain/):

```cmd
python -m pip install -e .[dev,notebook]
jupyter lab notebooks/phase2-risk-to-cost-demo.ipynb
```

Use the notebook when the audience benefits from a guided, cell-by-cell walkthrough instead of CLI output.

### 10a. Optionally open the Phase 3 LangGraph HITL education notebook

From [`agent-brain/`](../agent-brain/):

```cmd
python -m pip install -e .[dev,notebook]
jupyter lab notebooks/phase3-langgraph-hitl-demo.ipynb
```

Use this notebook when the audience needs to see the deterministic LangGraph runtime, HITL pause/block behavior, approved finalization, and low-risk finalization in a guided cell-by-cell walkthrough. The notebook is demo/education only: it imports reusable workflow code and does not add business logic, make LLM calls, use OpenAI Agents SDK behavior, or call live local services.

### 11. Demonstrate mock pricing tool readiness

From [`mock-pricing-api/`](../mock-pricing-api/):

```cmd
copy .env.example .env
python -m pip install -e .[dev]
python -m pytest
python -m mock_pricing_api.main
```

The pricing service runs on `http://127.0.0.1:8000` by default. Its contract is documented in [`docs/08-pricing-api-contract.md`](08-pricing-api-contract.md).

### 12. Demonstrate Phase 3 governance behavior

From [`agent-brain/`](../agent-brain/):

```cmd
python -m pytest tests/test_orchestration_state.py
python -m pytest tests/test_pricing_tool.py
python -m pytest tests/test_recommendation.py
python -m pytest tests/test_hitl.py
python -m pytest tests/test_langgraph_workflow.py
```

These tests demonstrate:

- LangGraph-ready state shape in [`agent-brain/src/agent_brain/orchestration/state.py`](../agent-brain/src/agent_brain/orchestration/state.py).
- Mock pricing tool wrapper behavior in [`agent-brain/src/agent_brain/tools/pricing.py`](../agent-brain/src/agent_brain/tools/pricing.py).
- Recommendation drafting in [`agent-brain/src/agent_brain/orchestration/recommendation.py`](../agent-brain/src/agent_brain/orchestration/recommendation.py).
- Mandatory HITL finalization controls in [`agent-brain/src/agent_brain/governance/hitl.py`](../agent-brain/src/agent_brain/governance/hitl.py).
- LangGraph runtime orchestration in [`agent-brain/src/agent_brain/orchestration/workflow.py`](../agent-brain/src/agent_brain/orchestration/workflow.py) without LLM calls or OpenAI Agents SDK behavior.

### 13. Demonstrate Phase 4 governance and observability scaffolding

From [`agent-brain/`](../agent-brain/):

```cmd
python -m pytest tests/test_model_adapter.py tests/test_observability.py tests/test_audit.py
```

These tests demonstrate:

- Microsoft Foundry Local adapter boundary in [`agent-brain/src/agent_brain/orchestration/model_adapter.py`](../agent-brain/src/agent_brain/orchestration/model_adapter.py).
- Deterministic placeholder local model fallback.
- Phoenix-compatible trace payloads in [`agent-brain/src/agent_brain/governance/observability.py`](../agent-brain/src/agent_brain/governance/observability.py).
- Langfuse-compatible token/cost payloads.
- Safety flag events.
- PostgreSQL [`AuditEvent`](../database-layer/prisma/schema.prisma)-compatible governance records.
- Audit persistence helpers in [`agent-brain/src/agent_brain/governance/audit.py`](../agent-brain/src/agent_brain/governance/audit.py).

### 14. Optionally start Phoenix and Langfuse UIs

This is optional for the current scaffold. Before starting the observability profile, copy [`.env.example`](../.env.example) to `.env` and replace the placeholder Langfuse secrets listed in [`docs/06-setup-runbook.md`](06-setup-runbook.md).

From the repository root:

```cmd
docker compose --profile observability up -d phoenix langfuse langfuse-worker
```

Expected local endpoints:

| Service | Endpoint |
|---|---|
| Phoenix UI and HTTP collector | `http://localhost:6006` |
| Phoenix OTLP gRPC collector | `http://localhost:4317` |
| Langfuse UI/API | `http://localhost:3100` |
| Langfuse MinIO API | `http://localhost:9090` |
| Langfuse MinIO console | `http://localhost:9091` |

## Demo readiness checklist

Use this checklist before a stakeholder walkthrough, recorded demo, or technical validation session. The core demo is ready when every required item is checked. Optional items are only needed when demonstrating the notebook, observability UIs, or a future concrete local model runtime.

### Required preflight

- [ ] The repository is on the expected branch and commit, and the working tree does not contain unrelated changes.
- [ ] Docker Desktop is running and has enough memory available for PostgreSQL, pgvector, and Neo4j.
- [ ] Node.js and npm are installed for [`database-layer/`](../database-layer/).
- [ ] Python `3.11.x` and pip are installed for local virtual environments in [`agent-brain/`](../agent-brain/) and [`mock-pricing-api/`](../mock-pricing-api/).
- [ ] Root [`.env.example`](../.env.example) has been copied to `.env`.
- [ ] [`database-layer/.env.example`](../database-layer/.env.example) has been copied to `database-layer/.env`.
- [ ] [`agent-brain/.env.example`](../agent-brain/.env.example) has been copied to `agent-brain/.env` when running agent commands directly.
- [ ] [`mock-pricing-api/.env.example`](../mock-pricing-api/.env.example) has been copied to `mock-pricing-api/.env` when showing the pricing API.

### Required service and data checks

- [ ] `docker compose up -d` has started PostgreSQL and Neo4j from [`docker-compose.yml`](../docker-compose.yml).
- [ ] PostgreSQL health checks pass and port `5432` is available.
- [ ] Neo4j HTTP and Bolt endpoints are available on ports `7474` and `7687`.
- [ ] [`database-layer/`](../database-layer/) dependencies are installed with `npm install`.
- [ ] Prisma Client generation has completed with `npm run db:generate`.
- [ ] The Prisma schema has been applied with `npm run db:push`.
- [ ] pgvector has been enabled with `npm run db:enable-vector`.
- [ ] Demo data has been reset with `npm run reset:demo`.
- [ ] Synthetic subscription and compliance fixtures have been ingested with `npm run ingest`.
- [ ] Concurrency validation has passed with `npm run validate:concurrency`.

### Required retrieval checks

- [ ] [`agent-brain/`](../agent-brain/) dependencies are installed with `python -m pip install -e .[dev]`.
- [ ] Agent validation and tests pass with `python -m agent_brain.cli.validate_scaffold` and `python -m pytest`.
- [ ] PostgreSQL records have been projected into Neo4j with `python -m agent_brain.cli.project_graph`.
- [ ] Vector retrieval returns ranked evidence rows with `python -m agent_brain.cli.search_vectors "cross-border processing subprocessors outside the EU" --top-k 5`.
- [ ] Graph traversal returns vendor, software, subscription, cost, risk, and evidence rows with `python -m agent_brain.cli.traverse_graph --risk-category DATA_RESIDENCY --limit 10`.
- [ ] Hybrid retrieval returns deterministic risk-to-cost rows with `python -m agent_brain.cli.hybrid_retrieve "cross-border processing subprocessors outside the EU" --top-k 5 --graph-limit 25`.
- [ ] Curated demo assertions pass with `python -m agent_brain.cli.run_curated_demo`.

### Required governance and pricing checks when showing Phase 3

- [ ] [`mock-pricing-api/`](../mock-pricing-api/) dependencies are installed with `python -m pip install -e .[dev]`.
- [ ] Mock pricing API tests pass with `python -m pytest` from [`mock-pricing-api/`](../mock-pricing-api/).
- [ ] The pricing service starts with `python -m mock_pricing_api.main` and responds on `http://127.0.0.1:8000`.
- [ ] Agent state, pricing wrapper, recommendation, and HITL tests pass from [`agent-brain/`](../agent-brain/): `tests/test_orchestration_state.py`, `tests/test_pricing_tool.py`, `tests/test_recommendation.py`, and `tests/test_hitl.py`.

### Optional walkthrough checks

- [ ] Notebook extras are installed with `python -m pip install -e .[dev,notebook]` before opening [`agent-brain/notebooks/phase2-risk-to-cost-demo.ipynb`](../agent-brain/notebooks/phase2-risk-to-cost-demo.ipynb).
- [ ] Langfuse placeholder secrets in `.env` have been replaced before starting the optional observability profile.
- [ ] Phoenix and Langfuse containers start with `docker compose --profile observability up -d phoenix langfuse langfuse-worker` when showing observability UIs.
- [ ] Phase 4 payload-builder tests pass with `python -m pytest tests/test_model_adapter.py tests/test_observability.py tests/test_audit.py` from [`agent-brain/`](../agent-brain/).
- [ ] A concrete Microsoft Foundry Local runtime is available only if switching from the placeholder provider to `microsoft-foundry-local` for a real model demo.
- [ ] An OpenAI API key is configured only if switching from the placeholder provider to `openai` for a real embedding and model demo.

### Known caveats to state during the demo

- The default embedding vectors are deterministic placeholders, not production semantic embeddings. Switch to `openai` or `microsoft-foundry-local` using [`scripts/setup-provider.ps1`](../scripts/setup-provider.ps1) or [`scripts/setup-provider.sh`](../scripts/setup-provider.sh) for real semantic embeddings.
- Phoenix and Langfuse live exporter clients are implemented in [`agent-brain/src/agent_brain/governance/exporters.py`](../agent-brain/src/agent_brain/governance/exporters.py) and fail gracefully when services are disabled or unreachable.
- Microsoft Foundry Local and OpenAI adapters are implemented, but require the respective runtime or API key to be configured before use.
- The current experience is CLI and notebook based; no polished user-facing UI is included.
- Local audit records remain the durable governance source of truth when optional observability services are disabled.

## What needs setup beyond the completed implementation

The implementation is complete in source control, but live demos still need runtime setup.

Required setup:

1. Copy root [`.env.example`](../.env.example) to `.env`.
2. Copy [`database-layer/.env.example`](../database-layer/.env.example) to `database-layer/.env`.
3. Start Docker services.
4. Install [`database-layer/`](../database-layer/) dependencies.
5. Apply the Prisma schema.
6. Enable pgvector.
7. Ingest deterministic demo fixtures.
8. Install [`agent-brain/`](../agent-brain/) dependencies.
9. Project graph data into Neo4j.
10. Install [`mock-pricing-api/`](../mock-pricing-api/) dependencies if showing pricing tool behavior.

Optional setup:

1. Install notebook extras for the Jupyter walkthrough.
2. Replace Langfuse secrets and start the Docker Compose `observability` profile.
3. Switch to a real model provider using [`scripts/setup-provider.ps1`](../scripts/setup-provider.ps1) or [`scripts/setup-provider.sh`](../scripts/setup-provider.sh):
   - `openai` for hosted OpenAI embeddings and LLM (requires API key).
   - `microsoft-foundry-local` for local Foundry Local embeddings and LLM (requires Foundry Local installed).
   - `placeholder` to return to deterministic offline mode.
4. After switching providers, reset and re-ingest demo data with [`scripts/reset-demo-environment.ps1`](../scripts/reset-demo-environment.ps1) or [`scripts/reset-demo-environment.sh`](../scripts/reset-demo-environment.sh) because the embedding vector dimension changes.
5. Open the Phase 3 LangGraph education notebook at [`agent-brain/notebooks/phase3-langgraph-hitl-demo.ipynb`](../agent-brain/notebooks/phase3-langgraph-hitl-demo.ipynb) when the audience needs a guided HITL workflow walkthrough.

## Recommended short demo path

If time is limited, use this order:

1. Show [`docs/04-technical-tool-interactions.md`](04-technical-tool-interactions.md).
2. Run PostgreSQL/Neo4j startup from [`docker-compose.yml`](../docker-compose.yml).
3. Run database ingestion and concurrency validation from [`database-layer/`](../database-layer/).
4. Run graph projection from [`agent-brain/`](../agent-brain/).
5. Run hybrid retrieval.
6. Run curated demo assertions.
7. Run HITL and Phase 4 governance tests.

This path demonstrates the core value without requiring optional Phoenix/Langfuse UIs or Microsoft Foundry Local.

## Known demo caveats

- The default embedding vectors are deterministic placeholders, not production semantic embeddings. Use [`scripts/setup-provider.ps1`](../scripts/setup-provider.ps1) or [`scripts/setup-provider.sh`](../scripts/setup-provider.sh) to switch to `openai` or `microsoft-foundry-local` for real semantic embeddings.
- Phoenix and Langfuse live exporter clients are implemented and fail gracefully when services are disabled or unreachable.
- Microsoft Foundry Local and OpenAI adapters are implemented, but require the respective runtime or API key to be configured before use.
- The notebooks are optional and require notebook dependencies.
- The strongest live proof point is the deterministic local flow: ingestion ? graph projection ? vector retrieval ? graph traversal ? hybrid retrieval ? curated demo ? governance validation.
