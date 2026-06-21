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
| Agent brain | Python retrieval, LangGraph-ready state, Neo4j/PostgreSQL clients, governance helpers | [`agent-brain/pyproject.toml`](../agent-brain/pyproject.toml) | Future `uv.lock`, `poetry.lock`, or equivalent lockfile if dependency locking is introduced |
| Mock pricing API | Python FastAPI service and pricing fixture layer | [`mock-pricing-api/pyproject.toml`](../mock-pricing-api/pyproject.toml) | Future `uv.lock`, `poetry.lock`, or equivalent lockfile if dependency locking is introduced |
| Observability | Phoenix, Langfuse, trace adapters, token/cost logging | [`docker-compose.yml`](../docker-compose.yml), [`agent-brain/pyproject.toml`](../agent-brain/pyproject.toml), and [`docs/04-technical-tool-interactions.md`](04-technical-tool-interactions.md) | Future pinned exporter client dependencies when live exporters are wired |
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
| LangGraph-ready orchestration | Present as typed state and workflow boundaries | Full LangGraph runtime wiring remains a forward-looking hardening step. |
| FastAPI | Declared in [`mock-pricing-api/pyproject.toml`](../mock-pricing-api/pyproject.toml) | Validate local API startup and tests after dependency changes. |
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
- Use the existing project manifests in [`agent-brain/pyproject.toml`](../agent-brain/pyproject.toml) and [`mock-pricing-api/pyproject.toml`](../mock-pricing-api/pyproject.toml).
- Commit lockfiles such as `uv.lock` or equivalent once dependencies are installed.
- Pin LangGraph, LangChain, LlamaIndex, FastAPI, Uvicorn, Pydantic, PostgreSQL client, and Neo4j client versions when they become runtime-critical or when lockfiles are introduced.

For local virtual environments, use Python `3.11.x` unless an ADR or compatibility update changes the baseline. The manifests allow `>=3.11`, but Python 3.11.x is the recommended development and demo runtime for dependency stability.

Python versions newer than `3.11.x` may run the current test suite, but they are not the documented baseline. Dependency warnings emitted only under non-`3.11.x` interpreters, such as Neo4j driver deprecation warnings, should be tracked as compatibility observations and treated as blockers only if they become test failures or affect runtime behavior under the documented Python 3.11.x baseline.

Generated local dependency artifacts must not be committed. The root [`.gitignore`](../.gitignore) excludes Python virtual environments, Python tooling caches, Node `node_modules`, generated build folders, Jupyter checkpoints, and uncommitted `.env` files while preserving committed `.env.example` templates.

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
- Curated query expectations in [`plans/03-query-scope.md`](../plans/03-query-scope.md) still hold or are updated.

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
| [`plans/03-query-scope.md`](../plans/03-query-scope.md) | Revalidate expected retrieval matches. |
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

## Current dependency status and forward-looking notes

- [`database-layer/package-lock.json`](../database-layer/package-lock.json) is present, so Node dependency installation has been captured for the database layer.
- [`agent-brain/pyproject.toml`](../agent-brain/pyproject.toml) and [`mock-pricing-api/pyproject.toml`](../mock-pricing-api/pyproject.toml) are present for the Python workstreams.
- Python lockfiles are not currently present; add `uv.lock`, `poetry.lock`, or an equivalent lockfile if reproducible Python dependency resolution becomes a hard requirement.
- LangGraph Phase A runtime wiring is implemented with `langgraph==1.0.8` pinned in [`agent-brain/pyproject.toml`](../agent-brain/pyproject.toml). The workflow keeps deterministic governance logic authoritative per [`docs/adr/0004-langgraph-runtime-with-deterministic-governance.md`](adr/0004-langgraph-runtime-with-deterministic-governance.md).
- Live Phoenix and Langfuse exporter clients are not yet wired end to end; pin exporter SDKs when that integration is added.
- A concrete Microsoft Foundry Local client is still forward-looking; document runtime and dependency requirements when selected.

## Governance

This document is part of product and technical governance. Update it whenever the dependency baseline changes.

Dependency changes should be reflected in:

- This document.
- [`CHANGELOG.md`](../CHANGELOG.md).
- Relevant ADRs under [`docs/adr/`](adr/).
- Relevant setup or architecture docs.
- Git commits and milestone tags when phases are validated.
