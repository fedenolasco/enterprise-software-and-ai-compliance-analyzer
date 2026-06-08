# Enterprise Software & AI Compliance Analyzer Progress Checklist

## Purpose

This checklist tracks implementation progress against the roadmap in [`plans/implementation-plan.md`](implementation-plan.md), [`proposal/high-level-plan.md`](../proposal/high-level-plan.md), and [`proposal/setup-plan-v3.md`](../proposal/setup-plan-v3.md). It is intended as the user-facing progress tracker for each implementation round.

## Status legend

- `[x]` Completed in the repository.
- `[-]` In progress or partially implemented.
- `[ ]` Not started.

## Round 1 progress summary

Round 1 created the written implementation plan and began Phase 0 and Phase 1 scaffolding. The repository now has monorepo folders, Docker service configuration, database-layer TypeScript/Prisma structure, synthetic fixtures, ingestion scaffolding, concurrency validation scaffolding, and setup documentation.

## Phase 0: Monorepo foundation

- [x] Review roadmap source documents in [`proposal/high-level-plan.md`](../proposal/high-level-plan.md) and [`proposal/setup-plan-v3.md`](../proposal/setup-plan-v3.md).
- [x] Create written implementation plan in [`plans/implementation-plan.md`](implementation-plan.md).
- [x] Create user-facing progress checklist in [`plans/implementation-plan-checklist.md`](implementation-plan-checklist.md).
- [x] Create top-level workstream directories for `database-layer`, `agent-brain`, `mock-pricing-api`, `docs`, `scripts`, and `plans`.
- [x] Add repository overview in [`README.md`](../README.md).
- [x] Add root environment template in [`.env.example`](../.env.example).
- [x] Add local Docker service configuration in [`docker-compose.yml`](../docker-compose.yml).
- [x] Add architecture overview in [`docs/architecture-overview.md`](../docs/architecture-overview.md).
- [x] Add business product requirements document in [`docs/product-requirements.md`](../docs/product-requirements.md).
- [x] Add dependency and versioning strategy in [`docs/dependency-versioning-strategy.md`](../docs/dependency-versioning-strategy.md).
- [x] Add schema diagrams and business logic documentation in [`docs/schema-diagrams.md`](../docs/schema-diagrams.md).
- [x] Add technical tool interaction diagrams and metadata in [`docs/technical-tool-interactions.md`](../docs/technical-tool-interactions.md).
- [x] Add setup runbook in [`docs/setup-runbook.md`](../docs/setup-runbook.md).
- [x] Add repeatable demo reset strategy in [`docs/setup-runbook.md`](../docs/setup-runbook.md).
- [x] Cross-reference repeatable demo reset strategy from [`docs/architecture-overview.md`](../docs/architecture-overview.md) and [`docs/technical-tool-interactions.md`](../docs/technical-tool-interactions.md).

## Phase 1: Local data foundations and zero-ETL architecture

### Phase 1.1: Database design

- [x] Define initial vendor entity in [`database-layer/prisma/schema.prisma`](../database-layer/prisma/schema.prisma).
- [x] Define initial software entity in [`database-layer/prisma/schema.prisma`](../database-layer/prisma/schema.prisma).
- [x] Define initial subscription entity in [`database-layer/prisma/schema.prisma`](../database-layer/prisma/schema.prisma).
- [x] Define initial compliance document entity in [`database-layer/prisma/schema.prisma`](../database-layer/prisma/schema.prisma).
- [x] Define initial document chunk entity with pgvector-compatible embedding field in [`database-layer/prisma/schema.prisma`](../database-layer/prisma/schema.prisma).
- [x] Define initial compliance risk entity in [`database-layer/prisma/schema.prisma`](../database-layer/prisma/schema.prisma).
- [x] Define initial audit event entity in [`database-layer/prisma/schema.prisma`](../database-layer/prisma/schema.prisma).
- [x] Generate and validate the Prisma client from [`database-layer/prisma/schema.prisma`](../database-layer/prisma/schema.prisma).
- [x] Apply schema to local PostgreSQL.

### Phase 1.2: Docker data infrastructure

- [x] Configure PostgreSQL with pgvector image in [`docker-compose.yml`](../docker-compose.yml).
- [x] Configure Neo4j service placeholder for Phase 2 in [`docker-compose.yml`](../docker-compose.yml).
- [x] Add pgvector enablement script in [`database-layer/scripts/enable-pgvector.ts`](../database-layer/scripts/enable-pgvector.ts).
- [x] Start Docker services locally.
- [x] Confirm PostgreSQL health check passes.
- [x] Confirm Neo4j health check passes.
- [x] Run pgvector extension enablement against local PostgreSQL.

### Phase 1.3: Prisma ORM and TypeScript setup

- [x] Add database-layer package manifest in [`database-layer/package.json`](../database-layer/package.json).
- [x] Add TypeScript configuration in [`database-layer/tsconfig.json`](../database-layer/tsconfig.json).
- [x] Add database-layer environment template in [`database-layer/.env.example`](../database-layer/.env.example).
- [x] Add database-layer documentation in [`database-layer/README.md`](../database-layer/README.md).
- [x] Add deterministic embedding helper in [`database-layer/src/embedding.ts`](../database-layer/src/embedding.ts).
- [x] Add document chunking and risk inference helpers in [`database-layer/src/document-utils.ts`](../database-layer/src/document-utils.ts).
- [x] Install database-layer dependencies.
- [x] Run TypeScript type checking.
- [x] Run Prisma validation.

### Phase 1.4: Synthetic data generation

- [x] Add structured subscription fixture in [`database-layer/data/subscriptions.json`](../database-layer/data/subscriptions.json).
- [x] Add synthetic OpenAI SLA text fixture in [`database-layer/data/documents/openai-enterprise-sla.txt`](../database-layer/data/documents/openai-enterprise-sla.txt).
- [x] Add synthetic OpenAI GDPR text fixture in [`database-layer/data/documents/openai-gdpr-policy.txt`](../database-layer/data/documents/openai-gdpr-policy.txt).
- [x] Add synthetic Microsoft DPA text fixture in [`database-layer/data/documents/microsoft-copilot-dpa.txt`](../database-layer/data/documents/microsoft-copilot-dpa.txt).
- [x] Add synthetic Microsoft responsible AI text fixture in [`database-layer/data/documents/microsoft-copilot-ai-policy.txt`](../database-layer/data/documents/microsoft-copilot-ai-policy.txt).
- [x] Add synthetic Notion SLA text fixture in [`database-layer/data/documents/notion-ai-sla.txt`](../database-layer/data/documents/notion-ai-sla.txt).
- [x] Add synthetic Notion GDPR text fixture in [`database-layer/data/documents/notion-ai-gdpr-policy.txt`](../database-layer/data/documents/notion-ai-gdpr-policy.txt).
- [x] Add synthetic vendor risk register text fixture in [`database-layer/data/documents/vendor-risk-register.txt`](../database-layer/data/documents/vendor-risk-register.txt).
- [x] Validate fixture keys against ingestion schema.

### Phase 1.5: Data ingestion and concurrency validation

- [x] Add ingestion script in [`database-layer/scripts/ingest.ts`](../database-layer/scripts/ingest.ts).
- [x] Wire seed script to ingestion in [`database-layer/scripts/seed.ts`](../database-layer/scripts/seed.ts).
- [x] Add repeatable demo reset script in [`database-layer/scripts/reset-demo-data.ts`](../database-layer/scripts/reset-demo-data.ts).
- [x] Add optimistic concurrency validation script in [`database-layer/scripts/validate-concurrency.ts`](../database-layer/scripts/validate-concurrency.ts).
- [x] Run ingestion against local PostgreSQL.
- [x] Verify vendors, software, subscriptions, documents, chunks, risks, and audit events are persisted.
- [x] Verify embeddings are written to pgvector-compatible column.
- [x] Run concurrency validation against local PostgreSQL.
- [x] Review audit events produced by ingestion and concurrency validation.

## Phase 2: Local hybrid context architecture

- [x] Initialize Python project structure in `agent-brain`.
- [x] Add Neo4j graph mapping for vendors, software, subscriptions, and document chunks.
- [x] Add PostgreSQL vector retrieval module.
- [ ] Add Neo4j graph traversal module.
- [ ] Add hybrid retrieval function combining graph and vector context.
- [x] Document curated positive demo query scope in [`plans/query-scope.md`](query-scope.md).
- [ ] Add reusable Python script/module demonstrating curated risk-to-cost retrieval based on [`plans/query-scope.md`](query-scope.md).
- [ ] Add Jupyter notebook that imports the reusable scripts/modules and presents the curated Phase 2 risk-to-cost demo.

## Phase 3: Agentic orchestration and mock tool use

- [ ] Initialize FastAPI project in `mock-pricing-api`.
- [ ] Add synthetic pricing API data.
- [ ] Document GraphQL-style pricing contract in `docs`.
- [ ] Add LangGraph agent state model.
- [ ] Add mock pricing tool wrapper.
- [ ] Add recommendation drafting workflow.
- [ ] Add mandatory HITL pause before cancellation recommendation finalization.

## Phase 4: Governance, observability, and FinOps

- [ ] Add local model adapter boundary for Microsoft Foundry Local readiness.
- [ ] Add Phoenix-compatible trace hook placeholders.
- [ ] Add safety flag logging.
- [ ] Add Langfuse-compatible token usage and simulated cost logging.
- [ ] Persist governance-critical events to audit tables.
- [ ] Document local fallback behavior when optional observability tools are not installed.

## Current completion snapshot

| Area | Status | Notes |
|---|---|---|
| Planning | Completed | Implementation plan and progress checklist exist. |
| Monorepo foundation | Completed | Core folders and initial docs are present. |
| Local service configuration | Completed | PostgreSQL with pgvector and Neo4j are configured and runtime-validated. |
| Prisma schema | Completed | Initial schema exists, Prisma Client generation passed, and schema was applied to local PostgreSQL. |
| Synthetic data | Completed | JSON and text fixtures were validated through successful ingestion. |
| Ingestion | Completed | Runtime execution validated against local PostgreSQL. |
| Concurrency validation | Completed | Optimistic concurrency validation executed successfully and audit events were reviewed. |
| Agent brain | In progress | Python package scaffold, validation CLI, Neo4j graph projection, PostgreSQL vector retrieval, and unit tests are present. |
| Mock pricing API | Not started | Planned for Phase 3. |
| Governance and FinOps | Not started | Planned for Phase 4. |

## Next recommended implementation steps

1. Run [`agent-brain/`](../agent-brain/) Neo4j graph projection and PostgreSQL vector retrieval against live local services.
2. Add Neo4j graph traversal module.
3. Add a hybrid retrieval function combining graph and vector context.
4. Implement reusable Python scripts/modules for the curated risk-to-cost retrieval demo from [`plans/query-scope.md`](query-scope.md).
5. Add a Jupyter notebook that imports those modules and presents the curated demo results.
