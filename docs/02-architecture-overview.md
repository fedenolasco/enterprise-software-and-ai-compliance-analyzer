# Architecture Overview

## Core design principles

- 100% local execution.
- Type-safe schema boundaries.
- Zero-ETL retrieval with PostgreSQL and pgvector.
- Hybrid graph plus vector context.
- Mandatory human-in-the-loop approval before cancellation recommendations.
- Local observability for traces, safety flags, and simulated cost.

## Runtime topology

```text
User Query
   |
   v
agent-brain
   |----> PostgreSQL + pgvector (structured data + chunk embeddings)
   |----> Neo4j (relationship graph)
   |----> mock-pricing-api (synthetic live pricing tool)
   |
   +----> HITL approval gate
   |
   +----> Final recommendation + audit trail
```

## Phase ownership

- `database-layer/`: schema, migrations, seeds, ingestion, concurrency tests.
- `agent-brain/`: retrieval, orchestration, state handling, governance hooks.
- `mock-pricing-api/`: pricing tool contract and local API implementation.

## Product requirements

See [`docs/01-product-requirements.md`](01-product-requirements.md) for the business product requirements document. It defines product vision, target users, roadmap, success metrics, risks, and the change-control policy for product evolution.

## Schema documentation

See [`docs/03-schema-diagrams.md`](03-schema-diagrams.md) for Mermaid diagrams, metadata descriptions, relationship intent, and business logic for the Prisma schema in [`database-layer/prisma/schema.prisma`](../database-layer/prisma/schema.prisma).

## Technical tool interaction documentation

See [`docs/04-technical-tool-interactions.md`](04-technical-tool-interactions.md) for high-level Mermaid diagrams and metadata explaining technology I/O across documentation, data ingestion, PostgreSQL, pgvector, Neo4j, LangGraph, the mock pricing API, HITL, and observability layers.

## Dependency and versioning documentation

See [`docs/05-dependency-versioning-strategy.md`](05-dependency-versioning-strategy.md) for the compatibility matrix, version pinning policy, lockfile policy, Docker image policy, upgrade policy, and embedding model transition policy.

## Repeatable demo reset strategy

See [`docs/06-setup-runbook.md`](06-setup-runbook.md) for the repeatable demo reset strategy. The reset strategy treats PostgreSQL rows, pgvector embeddings, Neo4j graph projections, mock pricing runtime state, agent checkpoints, HITL decisions, traces, and simulated cost logs as rebuildable demo artifacts. The source of truth remains the committed fixtures and schema files.

## Initial service ports

- PostgreSQL: `5432`
- Neo4j HTTP: `7474`
- Neo4j Bolt: `7687`
- Mock pricing API: `8000`
