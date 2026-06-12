# Dependency and Versioning Strategy

## Purpose

This document defines how software dependencies, runtime versions, Docker image versions, lockfiles, and cross-layer compatibility decisions are tracked for the Enterprise Software & AI Compliance Analyzer.

The product has multiple technology layers. Each layer can evolve independently, but compatibility must be managed centrally so that Phase 1 data validation, Phase 2 hybrid retrieval, Phase 3 agent orchestration, and Phase 4 observability remain reproducible.

This document must be updated when dependency versions, runtime versions, Docker images, model runtimes, embedding dimensions, or major libraries change.

## Dependency governance goals

- Keep the local prototype reproducible across machines.
- Avoid incompatible upgrades between database, ORM, agent, API, and observability layers.
- Make every version-sensitive decision traceable through documentation, Git commits, changelog entries, and ADRs.
- Keep Docker service versions explicit rather than relying on floating `latest` tags.
- Treat embedding model changes as schema and reset events because vector dimensions affect stored data.

## Layer ownership matrix

| Layer | Responsibility | Current source of truth | Future lock or manifest |
|---|---|---|---|
| Root infrastructure | Docker Compose, PostgreSQL, pgvector, Neo4j, root environment variables | [`docker-compose.yml`](../docker-compose.yml), [`.env.example`](../.env.example) | Docker image tags and optional Compose override files |
| Database layer | Node.js, TypeScript, Prisma, Prisma Client, `pg`, `zod`, `tsx` | [`database-layer/package.json`](../database-layer/package.json), [`database-layer/tsconfig.json`](../database-layer/tsconfig.json) | `package-lock.json` after dependency installation |
| Database schema | Prisma models, enums, pgvector field, relations | [`database-layer/prisma/schema.prisma`](../database-layer/prisma/schema.prisma) | Prisma migrations after runtime validation |
| Synthetic data | Structured subscription data and compliance document fixtures | [`database-layer/data/subscriptions.json`](../database-layer/data/subscriptions.json), [`database-layer/data/documents/`](../database-layer/data/documents/) | Versioned fixture updates and reset validation |
| Agent brain | Python retrieval, LangGraph, LangChain, LlamaIndex, Neo4j/PostgreSQL clients | Future [`agent-brain/`](../agent-brain/) project manifest | Future `pyproject.toml`, `uv.lock`, or equivalent lockfile |
| Mock pricing API | Python FastAPI service and pricing fixture layer | Future [`mock-pricing-api/`](../mock-pricing-api/) project manifest | Future `pyproject.toml`, `uv.lock`, or equivalent lockfile |
| Observability | Phoenix, Langfuse, trace adapters, token/cost logging | Future agent dependency manifest and docs | Future pinned observability dependencies |
| Documentation and governance | Product, architecture, ADRs, changelog, setup, query scope | [`docs/`](../docs/), [`plans/`](../plans/), [`CHANGELOG.md`](../CHANGELOG.md) | Git commits, tags, and ADR history |

## Context7 compatibility findings

### Prisma

Context7 documentation for Prisma confirms the following compatibility constraints and design implications:

- Current Prisma ORM documentation lists Node.js requirements of `^20.19.0`, `^22.12.0`, or `^24.0.0`.
- TypeScript users should use TypeScript `5.4+`.
- Unsupported database types can be represented using Prisma `Unsupported(...)` fields.
- pgvector is represented safely as an unsupported field type in Prisma schema when native scalar support is unavailable.

This supports the current scaffold choice in [`database-layer/prisma/schema.prisma`](../database-layer/prisma/schema.prisma), where `DocumentChunk.embedding` uses `Unsupported("vector(8)")`.

### LangGraph

Context7 documentation for LangGraph confirms the following compatibility constraints:

- LangGraph local CLI and local server workflows require Python `3.11+`.
- LangChain generally supports Python `3.10+`, but this project should standardize on Python `3.11+` to keep LangGraph local development compatible.

## Current baseline recommendations

| Tool or runtime | Current or recommended baseline | Source or rationale |
|---|---|---|
| Node.js | `22 LTS` or another Prisma-supported active LTS | Aligns with current Prisma requirements. |
| TypeScript | `^5.7.2` | Already declared in [`database-layer/package.json`](../database-layer/package.json). |
| Prisma | `^5.16.2` currently declared | Scaffold baseline; revisit before production-like validation because Prisma docs now reference newer requirements. |
| Prisma Client | `^5.16.2` currently declared | Should match Prisma CLI major/minor where practical. |
| PostgreSQL | `16` | Matches `pgvector/pgvector:pg16` in [`docker-compose.yml`](../docker-compose.yml). |
| pgvector | Bundled in selected Docker image | Tied to `pgvector/pgvector:pg16` image. |
| Neo4j | `5.21` | Explicit image in [`docker-compose.yml`](../docker-compose.yml). |
| Python | `3.11+` | Required for LangGraph local CLI and local server workflows. |
| LangGraph | Pin during Phase 2 | Do not leave floating once [`agent-brain/`](../agent-brain/) is initialized. |
| FastAPI | Pin during Phase 3 | Do not leave floating once [`mock-pricing-api/`](../mock-pricing-api/) is initialized. |
| Embedding model | Deterministic placeholder for now | Documented in [`docs/adr/0002-placeholder-embedding-strategy.md`](adr/0002-placeholder-embedding-strategy.md). |

## Version pinning policy

### Node and TypeScript layer

- Declare direct dependencies in [`database-layer/package.json`](../database-layer/package.json).
- Commit `package-lock.json` after dependency installation.
- Keep Prisma CLI and Prisma Client versions aligned unless a documented compatibility reason exists.
- Do not upgrade Prisma without running Prisma validation and documenting schema impact.
- Do not change TypeScript module settings without validating scripts in [`database-layer/scripts/`](../database-layer/scripts/).

### Python layers

- Use Python `3.11+` for [`agent-brain/`](../agent-brain/) and [`mock-pricing-api/`](../mock-pricing-api/).
- Use a project manifest such as `pyproject.toml` when those layers are scaffolded.
- Commit lockfiles such as `uv.lock` or equivalent once dependencies are installed.
- Pin LangGraph, LangChain, LlamaIndex, FastAPI, Uvicorn, Pydantic, PostgreSQL client, and Neo4j client versions when introduced.

### Docker services

- Keep Docker image tags explicit.
- Avoid `latest` tags for PostgreSQL, pgvector, Neo4j, Phoenix, Langfuse, or other stateful services.
- Treat Docker image upgrades as compatibility events.
- Document image upgrades in [`CHANGELOG.md`](../CHANGELOG.md).
- Add an ADR when the upgrade changes architecture, storage, graph behavior, or observability behavior.

## Lockfile policy

| Layer | Lockfile expectation | Commit policy |
|---|---|---|
| [`database-layer/`](../database-layer/) | `package-lock.json` | Commit after `npm install`. |
| [`agent-brain/`](../agent-brain/) | `uv.lock`, `poetry.lock`, or equivalent | Commit after Python dependency scaffold. |
| [`mock-pricing-api/`](../mock-pricing-api/) | `uv.lock`, `poetry.lock`, or equivalent | Commit after Python API scaffold. |
| Root Docker services | Explicit image tags in Compose | Commit every image tag change. |

## Compatibility validation checklist

Before accepting dependency or runtime changes, validate:

- The relevant dependency manifest is updated.
- The relevant lockfile is updated.
- The change is reflected in this document when compatibility assumptions change.
- [`CHANGELOG.md`](../CHANGELOG.md) includes a human-readable summary.
- An ADR is added under [`docs/adr/`](adr/) when the change affects architecture, model strategy, schema, data reset, graph projection, HITL, or observability.
- The reset strategy in [`docs/06-setup-runbook.md`](06-setup-runbook.md) still works.
- Curated query expectations in [`plans/query-scope.md`](../plans/query-scope.md) still hold or are updated.

## Embedding model transition policy

Changing from deterministic placeholder embeddings to real semantic embeddings is a cross-layer compatibility event.

When this transition occurs, update:

| Artifact | Required update |
|---|---|
| [`database-layer/src/embedding.ts`](../database-layer/src/embedding.ts) | Replace placeholder generator with local embedding model integration. |
| [`database-layer/prisma/schema.prisma`](../database-layer/prisma/schema.prisma) | Change `vector(8)` to the selected model dimension. |
| [`database-layer/.env.example`](../database-layer/.env.example) | Update `EMBEDDING_DIMENSION`. |
| [`.env.example`](../.env.example) | Update root `EMBEDDING_DIMENSION`. |
| [`docs/06-setup-runbook.md`](06-setup-runbook.md) | Document reset and re-ingestion requirement. |
| [`docs/03-schema-diagrams.md`](03-schema-diagrams.md) | Update vector metadata and field semantics. |
| [`docs/04-technical-tool-interactions.md`](04-technical-tool-interactions.md) | Update embedding flow and technology metadata. |
| [`plans/query-scope.md`](../plans/query-scope.md) | Revalidate expected retrieval matches. |
| [`CHANGELOG.md`](../CHANGELOG.md) | Record the model transition. |
| [`docs/adr/`](adr/) | Add ADR documenting model, dimension, runtime, and tradeoffs. |

After the transition, run a full demo reset and re-ingestion because old placeholder vectors are no longer compatible with the new model dimension or semantics.

## Upgrade policy

### Patch upgrades

Patch upgrades can be accepted if validation passes and no schema, reset, query, or runtime behavior changes.

### Minor upgrades

Minor upgrades require checking release notes and validating scripts, schemas, and local services.

### Major upgrades

Major upgrades require:

- ADR entry.
- Changelog entry.
- Updated compatibility matrix.
- Reset strategy review.
- Relevant phase checklist updates.
- New Git commit and, if validated, a milestone tag.

## Phase-specific dependency gates

| Phase | Dependency gate |
|---|---|
| Phase 1 | Install Node dependencies, commit lockfile, validate Prisma schema, validate TypeScript scripts. |
| Phase 2 | Create Python agent manifest, pin LangGraph stack, validate Python version `3.11+`. |
| Phase 3 | Create mock API manifest, pin FastAPI stack, validate local API startup. |
| Phase 4 | Pin observability libraries and document Phoenix/Langfuse compatibility. |

## Current unresolved dependency notes

- [`database-layer/tsconfig.json`](../database-layer/tsconfig.json) references Node types via `types: ["node"]`.
- [`@types/node`](../database-layer/package.json) is declared but not installed until dependency installation is approved.
- The visible TypeScript diagnostic is expected until `npm install` is run in [`database-layer/`](../database-layer/).
- Dependency installation is intentionally deferred until scaffolding is ready and approved.

## Governance

This document is part of product and technical governance. Update it whenever the dependency baseline changes.

Dependency changes should be reflected in:

- This document.
- [`CHANGELOG.md`](../CHANGELOG.md).
- Relevant ADRs under [`docs/adr/`](adr/).
- Relevant setup or architecture docs.
- Git commits and milestone tags when phases are validated.
