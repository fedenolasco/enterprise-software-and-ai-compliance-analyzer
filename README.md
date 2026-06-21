# Enterprise Software & AI Compliance Analyzer

Local-first monorepo for analyzing enterprise software subscriptions and AI compliance risk across structured billing data and unstructured compliance evidence.

## Recommended reading order

Read the repository from planning context to runnable implementation:

1. [`proposal/`](proposal/) — start with the proposal documents in numeric order to understand the project intent, setup roadmap, and learning path.
2. [`plans/`](plans/) — continue with the implementation plan, progress checklist, and curated query scope in numeric order.
3. [`docs/`](docs/) — review product requirements, architecture, schema diagrams, technical tool interactions, dependency strategy, setup, and demo runbooks in numeric order.
4. [`database-layer/`](database-layer/) — inspect the Prisma schema, synthetic data, ingestion scripts, and concurrency validation.
5. [`agent-brain/`](agent-brain/) — review retrieval, graph projection, orchestration, governance, and demo logic.
6. [`mock-pricing-api/`](mock-pricing-api/) — review the local pricing tool API used by agent workflows.
7. [`scripts/`](scripts/) — review shared operational helpers when present.

Within folders that use two-digit prefixes, read files in ascending numeric order, for example [`proposal/01-high-level-plan.md`](proposal/01-high-level-plan.md) before [`proposal/02-setup-plan-v3.md`](proposal/02-setup-plan-v3.md), and [`plans/01-implementation-plan.md`](plans/01-implementation-plan.md) before [`plans/02-implementation-plan-checklist.md`](plans/02-implementation-plan-checklist.md).

## Workstreams

- [`database-layer/`](database-layer/) — TypeScript, Prisma, PostgreSQL, pgvector, ingestion, and validation.
- [`agent-brain/`](agent-brain/) — Python retrieval, orchestration, notebooks, and governance integrations.
- [`mock-pricing-api/`](mock-pricing-api/) — Local FastAPI service for synthetic pricing lookups.
- [`docs/`](docs/) — architecture, contracts, and runbooks.
- [`plans/`](plans/) — implementation plans and phased execution notes.
- [`scripts/`](scripts/) — shared helper scripts and operational utilities.

## Implementation order

1. Phase 0: repository structure and local services.
2. Phase 1: Prisma schema, synthetic data, ingestion, and concurrency validation.
3. Phase 2: Neo4j and hybrid retrieval.
4. Phase 3: mock pricing API, LangGraph orchestration, and HITL.
5. Phase 4: observability, governance, and FinOps instrumentation.

## Primary planning documents

- [`proposal/01-high-level-plan.md`](proposal/01-high-level-plan.md)
- [`proposal/02-setup-plan-v3.md`](proposal/02-setup-plan-v3.md)
- [`plans/01-implementation-plan.md`](plans/01-implementation-plan.md)

## Demo documentation

- [`docs/07-demo-runbook.md`](docs/07-demo-runbook.md) — recommended stakeholder and technical demo order.
- [`docs/06-setup-runbook.md`](docs/06-setup-runbook.md) — detailed local setup and validation commands.

## Local services

Use `docker-compose.yml` with `.env.example` values to start PostgreSQL with pgvector and Neo4j.
