# Enterprise Software & AI Compliance Analyzer

Local-first monorepo for analyzing enterprise software subscriptions and AI compliance risk across structured billing data and unstructured compliance evidence.

## Workstreams

- `database-layer/` — TypeScript, Prisma, PostgreSQL, pgvector, ingestion, and validation.
- `agent-brain/` — Python retrieval, orchestration, notebooks, and governance integrations.
- `mock-pricing-api/` — Local FastAPI service for synthetic pricing lookups.
- `docs/` — architecture, contracts, and runbooks.
- `plans/` — implementation plans and phased execution notes.
- `scripts/` — shared helper scripts and operational utilities.

## Implementation order

1. Phase 0: repository structure and local services.
2. Phase 1: Prisma schema, synthetic data, ingestion, and concurrency validation.
3. Phase 2: Neo4j and hybrid retrieval.
4. Phase 3: mock pricing API, LangGraph orchestration, and HITL.
5. Phase 4: observability, governance, and FinOps instrumentation.

## Primary planning documents

- `proposal/high-level-plan.md`
- `proposal/setup-plan-v3.md`
- `plans/implementation-plan.md`

## Demo documentation

- [`docs/07-demo-runbook.md`](docs/07-demo-runbook.md) — recommended stakeholder and technical demo order.
- [`docs/06-setup-runbook.md`](docs/06-setup-runbook.md) — detailed local setup and validation commands.

## Local services

Use `docker-compose.yml` with `.env.example` values to start PostgreSQL with pgvector and Neo4j.
