# Changelog

All notable project changes should be documented here as the implementation evolves across phases.

## Unreleased

- Applied [`database-layer/prisma/schema.prisma`](database-layer/prisma/schema.prisma) to local PostgreSQL, ran synthetic ingestion, verified persisted data and pgvector embeddings, and validated optimistic concurrency audit events.
- Validated Docker runtime services for PostgreSQL with pgvector and Neo4j; confirmed PostgreSQL health, pgvector extension availability, and Neo4j Cypher connectivity.
- Installed and locked [`database-layer`](database-layer/) Node dependencies, added `@types/pg`, and validated Prisma generation, Prisma schema validation, and TypeScript type checking.
- Added dependency and versioning strategy in [`docs/dependency-versioning-strategy.md`](docs/dependency-versioning-strategy.md) to govern cross-layer compatibility, lockfiles, Docker image tags, upgrade policy, and embedding model transitions.
- Added business product requirements document in [`docs/product-requirements.md`](docs/product-requirements.md) for product vision, roadmap, success metrics, risks, and product evolution policy.
- Planned: validate Prisma schema generation, PostgreSQL schema application, pgvector enablement, ingestion execution, and concurrency validation.
- Planned: add Phase 2 hybrid retrieval implementation using PostgreSQL vector search plus Neo4j graph traversal.
- Planned: replace deterministic placeholder embeddings with a real local semantic embedding model after the storage and reset pipeline is validated.

## phase-0-1-baseline

- Created the monorepo foundation for `database-layer`, `agent-brain`, `mock-pricing-api`, `docs`, `plans`, and `scripts`.
- Added local Docker service configuration for PostgreSQL with pgvector and Neo4j.
- Added TypeScript and Prisma database-layer scaffolding.
- Added initial Prisma schema for vendors, software, subscriptions, compliance documents, document chunks, compliance risks, and audit events.
- Added deterministic synthetic subscription JSON and compliance text fixtures.
- Added ingestion, pgvector enablement, and concurrency validation scaffolding.
- Added architecture, schema, technical tool interaction, query-scope, setup, reset, and embedding strategy documentation.
