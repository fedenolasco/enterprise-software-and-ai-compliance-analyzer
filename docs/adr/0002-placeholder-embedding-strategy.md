# ADR 0002: Deterministic Placeholder Embedding Strategy

## Status

Superseded by [ADR 0005](0005-multi-provider-model-and-embedding-strategy.md). The placeholder strategy remains as the default provider, but the project now supports Foundry Local and OpenAI as configurable alternatives.

## Context

Phase 1 needs to validate that document chunks can be ingested into PostgreSQL and that pgvector-compatible values can be written to the `DocumentChunk.embedding` field before a real local embedding model is selected.

The current implementation uses `createDeterministicEmbedding()` in `database-layer/src/embedding.ts`. This creates repeatable placeholder vectors from source text and stores them in the Prisma `Unsupported("vector(8)")` field.

## Decision

Use deterministic placeholder embedding vectors during Phase 1 only.

These vectors are used to validate:

- pgvector extension enablement.
- Vector write-path behavior.
- Reset and re-ingestion repeatability.
- Schema and ingestion plumbing.

They are not considered production semantic embeddings and must not be used as the final retrieval quality benchmark.

## Consequences

- Phase 1 can proceed without choosing or installing a real embedding model.
- Demo reset remains deterministic because the same text produces the same placeholder vector.
- Curated query tests can validate infrastructure, but not final semantic quality.
- Future replacement with a real model requires a vector dimension migration, reset, and re-ingestion.

## Future decision required

A later ADR must select the real local embedding model. That ADR should document:

- Model name and runtime.
- Vector dimension.
- Hardware requirements.
- Licensing considerations.
- Expected retrieval quality.
- Reset and migration steps.
