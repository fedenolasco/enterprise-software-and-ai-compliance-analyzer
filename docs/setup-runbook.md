# Setup Runbook

## Phase 0 and Phase 1 bootstrap

1. Copy [`.env.example`](../.env.example) to `.env` at the repository root.
2. Start local services with [`docker-compose.yml`](../docker-compose.yml).
3. Copy [`database-layer/.env.example`](../database-layer/.env.example) to `database-layer/.env`.
4. In [`database-layer/`](../database-layer/), install dependencies.
5. Run the Prisma client and schema bootstrap.
6. Enable pgvector.
7. Ingest synthetic fixtures.
8. Run the concurrency validator.

## End-to-end local run order

Use this order when building or replaying the current validated local baseline from a clean checkout. Run commands from the repository root unless a step explicitly changes into a workstream directory.

### 1. Start local infrastructure

```cmd
copy .env.example .env
docker compose up -d
```

This starts PostgreSQL with pgvector support and Neo4j using the service definitions in [`docker-compose.yml`](../docker-compose.yml).

### 2. Bootstrap the PostgreSQL and pgvector data layer

```cmd
cd database-layer
copy .env.example .env
npm install
npm run db:generate
npm run db:push
npm run db:enable-vector
npm run reset:demo
npm run ingest
npm run validate:concurrency
```

This creates the Prisma client, applies the schema, enables pgvector, reloads deterministic fixtures, writes placeholder embeddings, creates risk/audit records, and validates optimistic concurrency behavior.

### 3. Validate the Python agent-brain package

```cmd
cd agent-brain
python -m pip install -e .[dev]
python -m agent_brain.cli.validate_scaffold
python -m pytest
python -m ruff check src tests
python -m mypy src
```

This validates local configuration, unit tests, linting, and strict typing before running end-user retrieval or graph commands.

### 4. Project validated relational data into Neo4j

```cmd
cd agent-brain
python -m agent_brain.cli.project_graph
```

This runs the idempotent Phase 2 graph projection command. It creates Neo4j uniqueness constraints and merges `Vendor`, `Software`, `Subscription`, `ComplianceDocument`, and `DocumentChunk` nodes with relationships that support graph traversal.

### 5. Run PostgreSQL vector retrieval smoke test

```cmd
cd agent-brain
python -m agent_brain.cli.search_vectors "cross-border processing subprocessors outside the EU" --top-k 5
```

This runs the current Phase 2 vector retrieval entry point against PostgreSQL document chunks. It should print ranked evidence rows with vendor, software, risk, distance, and evidence excerpt columns. The ranking uses deterministic placeholder embedding vectors, so treat it as retrieval plumbing validation rather than final semantic retrieval quality.

### 6. Run Neo4j graph traversal smoke test

```cmd
cd agent-brain
python -m agent_brain.cli.traverse_graph --risk-category DATA_RESIDENCY --limit 10
```

This runs the current Phase 2 graph traversal entry point against projected Neo4j nodes and relationships. It should print vendor, software, subscription, annual cost, risk, and evidence excerpt columns. Run graph projection before this step whenever PostgreSQL fixture data has been reset or re-ingested.

### 7. Run hybrid retrieval smoke test

```cmd
cd agent-brain
python -m agent_brain.cli.hybrid_retrieve "cross-border processing subprocessors outside the EU" --top-k 5 --graph-limit 25
```

This runs the current Phase 2 hybrid retrieval entry point. It combines PostgreSQL vector evidence with Neo4j graph traversal context and prints deterministic risk-to-cost rows with priority score, vendor, software, subscription, annual cost, risk, recommended review action, and matched retrieval sources.

### 8. Run curated Phase 2 demo assertions

```cmd
cd agent-brain
python -m agent_brain.cli.run_curated_demo
```

This runs the reusable curated demo module aligned to [`plans/query-scope.md`](../plans/query-scope.md). It executes all four curated query definitions, prints rows in the expected risk-to-cost shape, and fails if any expected positive vendor is missing.

### 9. Open the documented Phase 2 notebook

```cmd
cd agent-brain
jupyter lab notebooks/phase2-risk-to-cost-demo.ipynb
```

The notebook imports the same reusable curated demo module used by the CLI. It documents prerequisites, environment assumptions, query definitions, result-row interpretation, assertion behavior, and limitations around deterministic placeholder embedding vectors.

### 10. Validate and run the Phase 3 mock pricing API

```cmd
cd mock-pricing-api
copy .env.example .env
python -m pip install -e .[dev]
python -m pytest
python -m ruff check src tests
python -m mypy src
python -m mock_pricing_api.main
```

The API starts on `http://127.0.0.1:8000` by default and serves deterministic synthetic pricing records from [`mock-pricing-api/src/mock_pricing_api/data/pricing.json`](../mock-pricing-api/src/mock_pricing_api/data/pricing.json). The contract is documented in [`docs/pricing-api-contract.md`](pricing-api-contract.md).

### 11. Validate the Phase 3 agent state model

```cmd
cd agent-brain
python -m pytest tests/test_orchestration_state.py
```

The state model in [`agent-brain/src/agent_brain/orchestration/state.py`](../agent-brain/src/agent_brain/orchestration/state.py) defines the LangGraph-ready workflow state and enforces that cancellation or renewal finalization requires human approval.

### 12. Validate the Phase 3 mock pricing tool wrapper

```cmd
cd agent-brain
python -m pytest tests/test_pricing_tool.py
```

The tool wrapper in [`agent-brain/src/agent_brain/tools/pricing.py`](../agent-brain/src/agent_brain/tools/pricing.py) calls `POST /pricing:lookup`, normalizes the response, and appends pricing context to `AgentBrainState`. Set `MOCK_PRICING_API_URL` if the pricing API is not running on `http://127.0.0.1:8000`.

### 13. Validate the Phase 3 recommendation drafting scaffold

```cmd
cd agent-brain
python -m pytest tests/test_recommendation.py
```

The recommendation drafting scaffold in [`agent-brain/src/agent_brain/orchestration/recommendation.py`](../agent-brain/src/agent_brain/orchestration/recommendation.py) creates deterministic recommendation drafts from retrieved context, compliance risks, and live pricing. High-risk, high-severity, or high-cost drafts require HITL approval before finalization.

### 14. Validate the mandatory HITL finalization gate

```cmd
cd agent-brain
python -m pytest tests/test_hitl.py
```

The HITL helpers in [`agent-brain/src/agent_brain/governance/hitl.py`](../agent-brain/src/agent_brain/governance/hitl.py) build a structured pause payload and block final output unless the human decision is approved.

### 15. Run future documented demo entry points

Future end-user scripts and notebooks must be added to this runbook when implemented. Each new entry point must document:

- Purpose and expected audience.
- Prerequisite services and prior commands.
- Exact command or notebook path.
- Required environment variables.
- Expected deterministic outputs or assertions.
- Known limitations, especially when deterministic placeholder embeddings are still in use.

## Expected validation outcomes

- PostgreSQL accepts schema creation and vector extension enablement.
- Synthetic vendors, software records, subscriptions, documents, chunks, risks, and audit events are stored.
- Document chunks receive deterministic placeholder embedding vectors for pgvector write-path validation.
- The concurrency validator demonstrates optimistic updates without lock-induced failure.
- Audit events capture ingestion and concurrency details for later observability work.

## Embedding note for Phase 1

Phase 1 uses deterministic placeholder embedding vectors. These are generated locally by [`createDeterministicEmbedding()`](../database-layer/src/embedding.ts) and stored in the pgvector-compatible [`DocumentChunk.embedding`](../database-layer/prisma/schema.prisma) field.

These vectors are not production semantic embeddings. They exist to validate that ingestion, PostgreSQL, pgvector, reset, and re-ingestion all work before a real local embedding model is selected.

When a real local embedding model is introduced, update the embedding generator, update `EMBEDDING_DIMENSION`, change the Prisma vector dimension from `vector(8)` to the selected model dimension, reset the demo data, and re-ingest all document chunks.

## Repeatable demo reset strategy

The curated demo queries in [`plans/query-scope.md`](../plans/query-scope.md) are intentionally aligned to the synthetic fixtures in [`database-layer/data/subscriptions.json`](../database-layer/data/subscriptions.json) and [`database-layer/data/documents/`](../database-layer/data/documents/). To keep every demo run deterministic, persisted runtime state should be treated as rebuildable demo output, not as source data.

### Reset objectives

The reset process should restore the environment to a clean state where:

- The source of truth is only the committed fixture and schema files.
- PostgreSQL contains no stale rows from previous ingestion, validation, or agent runs.
- pgvector contains only deterministic placeholder embeddings regenerated from the current text fixtures until a real local embedding model is introduced.
- Neo4j contains only graph nodes and relationships projected from the current PostgreSQL fixture load.
- The mock pricing API serves the committed synthetic pricing fixture once that layer is implemented.
- Agent state, HITL decisions, traces, token logs, and simulated cost records from prior demo runs do not affect the next run.

### Source-of-truth files

Use these files as the reset baseline:

| Source | Purpose |
|---|---|
| [`database-layer/prisma/schema.prisma`](../database-layer/prisma/schema.prisma) | Authoritative relational schema and pgvector field definition. |
| [`database-layer/data/subscriptions.json`](../database-layer/data/subscriptions.json) | Structured vendor, software, and subscription fixture data. |
| [`database-layer/data/documents/`](../database-layer/data/documents/) | Synthetic SLA, GDPR, AI policy, DPA, and risk-register text fixtures. |
| [`plans/query-scope.md`](../plans/query-scope.md) | Curated query definitions and expected positive matches. |
| Future pricing fixture under [`mock-pricing-api/`](../mock-pricing-api/) | Synthetic pricing baseline for tool-call demonstrations. |

### Runtime artifacts that may be reset

| Artifact | Reset reason |
|---|---|
| PostgreSQL rows | Removes stale vendors, software, subscriptions, documents, chunks, risks, and audit events. |
| pgvector embeddings | Ensures vector search reflects the current document chunks and embedding logic. In Phase 1 these are deterministic placeholder embeddings, not final semantic embeddings. |
| Neo4j graph nodes and relationships | Prevents graph traversal from using stale projections. |
| Mock pricing API runtime state | Ensures pricing comparisons match the committed pricing fixture. |
| LangGraph checkpoints or local agent state | Prevents prior recommendations or HITL approvals from affecting the next run. |
| Phoenix traces | Keeps trace review focused on the current demo run. |
| Langfuse token and cost logs | Keeps FinOps reporting focused on the current demo run. |
| Local audit events | Optional for hard resets; useful to clear before a recorded or stakeholder demo. |

### Recommended reset levels

| Reset level | Scope | Use when |
|---|---|---|
| Soft reset | Delete application rows, vector embeddings, graph projection, agent checkpoints, and mutable mock state. | Re-running the curated demo during normal development. |
| Hard reset | Remove Docker volumes for PostgreSQL and Neo4j, then recreate schema and services. | Schema, extension, graph projection, or migration behavior changes. |
| Fixture reset | Reapply committed JSON, document, pricing, and query-scope fixtures. | Preparing for a recorded demo, walkthrough, or regression test. |

### PostgreSQL reset order

When resetting the Prisma-managed data without dropping the database, delete child records before parent records to avoid foreign-key conflicts:

1. `AuditEvent`
2. `ComplianceRisk`
3. `DocumentChunk`
4. `ComplianceDocument`
5. `Subscription`
6. `Software`
7. `Vendor`

After deleting these records, run ingestion again so that all relational rows, compliance chunks, risk rows, vector embeddings, and audit entries are regenerated from the current fixtures.

### Repeatable demo loop

```mermaid
flowchart TD
  A[Reset demo state] --> B[Start local services]
  B --> C[Apply Prisma schema]
  C --> D[Enable pgvector]
  D --> E[Ingest synthetic fixtures]
  E --> F[Generate document chunks and embeddings]
  F --> G[Project graph into Neo4j]
  G --> H[Run curated query from query scope]
  H --> I[Fetch mock pricing data]
  I --> J[Run agent workflow]
  J --> K[Pause at HITL gate]
  K --> L[Persist audit and trace records]
  L --> M[Review deterministic demo output]
```

### Future reset scripts and demo entry points

The following scripts should be added as implementation matures:

| Script | Purpose |
|---|---|
| [`database-layer/scripts/reset-demo-data.ts`](../database-layer/scripts/reset-demo-data.ts) | Delete Prisma-managed rows in dependency-safe order and prepare PostgreSQL for fixture re-ingestion. |
| [`agent-brain/src/agent_brain/cli/project_graph.py`](../agent-brain/src/agent_brain/cli/project_graph.py) | Project validated PostgreSQL records into Neo4j for Phase 2 graph traversal. |
| [`agent-brain/src/agent_brain/cli/search_vectors.py`](../agent-brain/src/agent_brain/cli/search_vectors.py) | Run PostgreSQL pgvector retrieval against compliance document chunks for Phase 2 retrieval validation. |
| [`agent-brain/src/agent_brain/cli/traverse_graph.py`](../agent-brain/src/agent_brain/cli/traverse_graph.py) | Traverse projected Neo4j relationships to connect vendors, software, subscriptions, and evidence chunks. |
| [`agent-brain/src/agent_brain/cli/hybrid_retrieve.py`](../agent-brain/src/agent_brain/cli/hybrid_retrieve.py) | Merge PostgreSQL vector evidence and Neo4j graph context into deterministic risk-to-cost rows. |
| [`agent-brain/src/agent_brain/cli/run_curated_demo.py`](../agent-brain/src/agent_brain/cli/run_curated_demo.py) | Run the curated Phase 2 query-scope demo and assert expected positive vendor matches. |
| [`agent-brain/src/agent_brain/orchestration/state.py`](../agent-brain/src/agent_brain/orchestration/state.py) | Define LangGraph-ready state fields and HITL finalization checks for Phase 3 workflows. |
| [`agent-brain/src/agent_brain/orchestration/recommendation.py`](../agent-brain/src/agent_brain/orchestration/recommendation.py) | Draft deterministic recommendations from retrieval, pricing, and risk context. |
| [`agent-brain/src/agent_brain/tools/pricing.py`](../agent-brain/src/agent_brain/tools/pricing.py) | Call the local mock pricing API and append normalized pricing context to agent state. |
| [`agent-brain/src/agent_brain/governance/hitl.py`](../agent-brain/src/agent_brain/governance/hitl.py) | Enforce mandatory HITL pause and approval before final recommendation output. |
| `agent-brain/scripts/reset_graph.py` | Delete Neo4j demo graph nodes and relationships. |
| [`agent-brain/notebooks/phase2-risk-to-cost-demo.ipynb`](../agent-brain/notebooks/phase2-risk-to-cost-demo.ipynb) | Import the reusable curated demo module and present the risk-to-cost retrieval demo from [`plans/query-scope.md`](../plans/query-scope.md). |
| [`mock-pricing-api/src/mock_pricing_api/main.py`](../mock-pricing-api/src/mock_pricing_api/main.py) | Run the local FastAPI mock pricing service for Phase 3 tool-use validation. |
| `mock-pricing-api/scripts/reset_pricing_fixture.py` | Reload pricing fixtures if pricing state becomes mutable. |
| `scripts/reset-demo-environment.ps1` | Root-level Windows orchestration script for repeatable demos. |
| `scripts/reset-demo-environment.sh` | Optional WSL/Linux equivalent. |

### Current reset command

Use the database-layer reset script before re-running ingestion or before building Phase 2 graph projections from a clean relational baseline:

```text
cd database-layer
set DATABASE_URL=postgresql://compliance_user:compliance_password@localhost:5432/compliance_analyzer?schema=public
npm run reset:demo
npm run ingest
```

After re-ingestion, run the graph projection if Neo4j traversal or the Phase 2 demo is part of the current validation scope:

```text
cd agent-brain
python -m agent_brain.cli.project_graph
```

Run the vector retrieval smoke test if PostgreSQL retrieval behavior is part of the current validation scope:

```text
cd agent-brain
python -m agent_brain.cli.search_vectors "cross-border processing subprocessors outside the EU" --top-k 5
```

Run the graph traversal smoke test if Neo4j traversal behavior is part of the current validation scope:

```text
cd agent-brain
python -m agent_brain.cli.traverse_graph --risk-category DATA_RESIDENCY --limit 10
```

Run the hybrid retrieval smoke test if merged risk-to-cost context is part of the current validation scope:

```text
cd agent-brain
python -m agent_brain.cli.hybrid_retrieve "cross-border processing subprocessors outside the EU" --top-k 5 --graph-limit 25
```

Run the curated demo assertions if the Phase 2 demo contract is part of the current validation scope:

```text
cd agent-brain
python -m agent_brain.cli.run_curated_demo
```

Open the notebook when a documented stakeholder-facing walkthrough is needed:

```text
cd agent-brain
jupyter lab notebooks/phase2-risk-to-cost-demo.ipynb
```

The reset script deletes records in dependency-safe order and reports counts before deletion, deleted counts, and counts after deletion.

### Optional Phase 4 observability Docker stack

Phoenix and Langfuse are optional Phase 4 services. They run through the Docker Compose `observability` profile so the Phase 0 through Phase 3 workflow remains lightweight and does not require observability containers.

Before starting the observability profile, copy [`.env.example`](../.env.example) to `.env` and replace the local placeholder secrets for Langfuse:

- `LANGFUSE_NEXTAUTH_SECRET`
- `LANGFUSE_SALT`
- `LANGFUSE_ENCRYPTION_KEY`
- `LANGFUSE_POSTGRES_PASSWORD`
- `LANGFUSE_CLICKHOUSE_PASSWORD`
- `LANGFUSE_REDIS_PASSWORD`
- `LANGFUSE_MINIO_ROOT_PASSWORD`

Start Phoenix, Langfuse, and Langfuse support services with:

```text
docker compose --profile observability up -d phoenix langfuse langfuse-worker
```

The profile also starts the required Langfuse PostgreSQL, ClickHouse, Redis, MinIO, and bucket-initialization services declared in [`docker-compose.yml`](../docker-compose.yml).

Expected local endpoints are:

| Service | Endpoint | Purpose |
|---|---|---|
| Phoenix UI and HTTP collector | `http://localhost:6006` | Trace review and Phoenix-compatible collection. |
| Phoenix OTLP gRPC collector | `http://localhost:4317` | Trace export from future agent instrumentation. |
| Langfuse UI/API | `http://localhost:3000` | Token usage and simulated cost telemetry review. |
| Langfuse MinIO API | `http://localhost:9090` | Local object storage for Langfuse event payloads. |
| Langfuse MinIO console | `http://localhost:9091` | Local object storage inspection. |

Stop only the optional observability profile with:

```text
docker compose --profile observability stop phoenix langfuse langfuse-worker langfuse-postgres langfuse-clickhouse langfuse-redis langfuse-minio
```

If Phoenix or Langfuse are stopped, the agent workflow should continue with `PHOENIX_ENABLED=false` and `LANGFUSE_ENABLED=false`; local audit persistence remains the durable governance record.

The Phase 4 Python payload builders can be validated without running Phoenix or Langfuse:

```text
cd agent-brain
python -m pytest tests/test_model_adapter.py tests/test_observability.py tests/test_audit.py
```

These tests validate the Microsoft Foundry Local adapter boundary, deterministic placeholder model fallback, Phoenix-compatible trace payloads, Langfuse-compatible token/cost payloads, safety flag records, and PostgreSQL AuditEvent-compatible governance records.

## Notebook and end-user script documentation standard

Every end-user script or notebook added for a demo must be self-documenting and linked from this runbook. Notebook markdown cells should explain each executable section before code is run.

Required documentation sections for notebooks are:

1. Demo objective and business question.
2. Source fixture and query-scope links.
3. Prerequisite runbook steps.
4. Environment variables and local service assumptions.
5. Query inputs and expected positive matches.
6. Step-by-step execution for structured filtering, vector retrieval, graph traversal, result merging, ranking, and assertions.
7. Output interpretation with evidence excerpts and cost/renewal context.
8. Limitations and reset instructions.

Required documentation for script-style entry points is:

- Module docstring describing purpose and side effects.
- CLI help or README/runbook command example.
- Deterministic output summary.
- Unit or integration validation command.
- Runbook update in this file before the script is considered end-user ready.

### Validation after reset

After a reset and re-ingestion, validate that:

- The structured fixtures produce the expected vendors, software products, and subscriptions.
- Compliance documents are chunked and linked to their source records.
- pgvector embeddings are regenerated for all document chunks.
- PostgreSQL vector retrieval returns ranked evidence rows with document, vendor, software, subscription, and risk metadata.
- Curated queries in [`plans/query-scope.md`](../plans/query-scope.md) return the expected positive matches.
- Neo4j graph projections match the current PostgreSQL identifiers.
- Neo4j graph traversal connects vendors, software, subscriptions, documents, chunks, and risk metadata.
- Hybrid retrieval returns deterministic risk-to-cost rows with priority scores and recommended review actions.
- Curated Phase 2 demo assertions pass for expected positive vendor matches.
- The Phase 2 notebook imports reusable demo code and documents prerequisites, outputs, and limitations.
- Mock pricing API health, listing, detail, and lookup endpoints return deterministic synthetic pricing data.
- Agent state exports LangGraph-ready fields and blocks cancellation or renewal finalization without approval.
- Mock pricing tool wrapper calls the pricing API contract and appends normalized live pricing context.
- Recommendation drafting creates deterministic drafts and flags HITL-required high-risk decisions.
- HITL finalization gate blocks final output unless a human decision approves the draft.
- HITL and observability records from previous demo runs do not alter the current recommendation flow.
