# Demo Runbook

## Purpose

This runbook gives a presentation-ready order for demonstrating the Enterprise Software & AI Compliance Analyzer from a clean local checkout. It complements the operational setup details in [`docs/setup-runbook.md`](setup-runbook.md), the architecture diagrams in [`docs/technical-tool-interactions.md`](technical-tool-interactions.md), and the curated query definitions in [`plans/query-scope.md`](../plans/query-scope.md).

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
- [`docs/architecture-overview.md`](architecture-overview.md) for architecture narrative.
- [`docs/technical-tool-interactions.md`](technical-tool-interactions.md) for tool interaction diagrams.
- [`plans/implementation-plan-checklist.md`](../plans/implementation-plan-checklist.md) for implementation completion status.

Suggested talk track:

> This is a local-first compliance analyzer that joins structured software subscription data with unstructured AI compliance evidence, then uses hybrid retrieval, mock tool use, HITL governance, and observability scaffolding to demonstrate a governed enterprise AI pattern.

### 2. Start local infrastructure

From the repository root:

```cmd
copy .env.example .env
docker compose up -d
```

This starts the default local infrastructure: PostgreSQL with pgvector and Neo4j. The detailed setup order is documented in [`docs/setup-runbook.md`](setup-runbook.md).

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

### 6. Demonstrate vector retrieval

From [`agent-brain/`](../agent-brain/):

```cmd
python -m agent_brain.cli.search_vectors "cross-border processing subprocessors outside the EU" --top-k 5
```

Explain that the current embeddings are deterministic placeholder embedding vectors. They validate the pgvector write/read path but are not production semantic embeddings. The limitation is documented in [`docs/technical-tool-interactions.md`](technical-tool-interactions.md).

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

This is the strongest scripted demo step. It uses the curated query definitions in [`plans/query-scope.md`](../plans/query-scope.md), including:

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

### 11. Demonstrate mock pricing tool readiness

From [`mock-pricing-api/`](../mock-pricing-api/):

```cmd
copy .env.example .env
python -m pip install -e .[dev]
python -m pytest
python -m mock_pricing_api.main
```

The pricing service runs on `http://127.0.0.1:8000` by default. Its contract is documented in [`docs/pricing-api-contract.md`](pricing-api-contract.md).

### 12. Demonstrate Phase 3 governance behavior

From [`agent-brain/`](../agent-brain/):

```cmd
python -m pytest tests/test_orchestration_state.py
python -m pytest tests/test_pricing_tool.py
python -m pytest tests/test_recommendation.py
python -m pytest tests/test_hitl.py
```

These tests demonstrate:

- LangGraph-ready state shape in [`agent-brain/src/agent_brain/orchestration/state.py`](../agent-brain/src/agent_brain/orchestration/state.py).
- Mock pricing tool wrapper behavior in [`agent-brain/src/agent_brain/tools/pricing.py`](../agent-brain/src/agent_brain/tools/pricing.py).
- Recommendation drafting in [`agent-brain/src/agent_brain/orchestration/recommendation.py`](../agent-brain/src/agent_brain/orchestration/recommendation.py).
- Mandatory HITL finalization controls in [`agent-brain/src/agent_brain/governance/hitl.py`](../agent-brain/src/agent_brain/governance/hitl.py).

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

This is optional for the current scaffold. Before starting the observability profile, copy [`.env.example`](../.env.example) to `.env` and replace the placeholder Langfuse secrets listed in [`docs/setup-runbook.md`](setup-runbook.md).

From the repository root:

```cmd
docker compose --profile observability up -d phoenix langfuse langfuse-worker
```

Expected local endpoints:

| Service | Endpoint |
|---|---|
| Phoenix UI and HTTP collector | `http://localhost:6006` |
| Phoenix OTLP gRPC collector | `http://localhost:4317` |
| Langfuse UI/API | `http://localhost:3000` |
| Langfuse MinIO API | `http://localhost:9090` |
| Langfuse MinIO console | `http://localhost:9091` |

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
3. Add a concrete Microsoft Foundry Local runtime when replacing the placeholder model adapter.

## Recommended short demo path

If time is limited, use this order:

1. Show [`docs/technical-tool-interactions.md`](technical-tool-interactions.md).
2. Run PostgreSQL/Neo4j startup from [`docker-compose.yml`](../docker-compose.yml).
3. Run database ingestion and concurrency validation from [`database-layer/`](../database-layer/).
4. Run graph projection from [`agent-brain/`](../agent-brain/).
5. Run hybrid retrieval.
6. Run curated demo assertions.
7. Run HITL and Phase 4 governance tests.

This path demonstrates the core value without requiring optional Phoenix/Langfuse UIs or Microsoft Foundry Local.

## Known demo caveats

- The embedding vectors are deterministic placeholders, not production semantic embeddings.
- Phoenix and Langfuse payload compatibility is implemented, but live exporter clients are not yet wired end-to-end.
- Microsoft Foundry Local is represented by an adapter boundary, not a concrete model client.
- The notebook is optional and requires notebook dependencies.
- The strongest live proof point is the deterministic local flow: ingestion → graph projection → vector retrieval → graph traversal → hybrid retrieval → curated demo → governance validation.
