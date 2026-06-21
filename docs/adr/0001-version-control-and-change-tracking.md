# ADR 0001: Version Control and Change Tracking

## Status

Accepted

## Context

The project is evolving phase-by-phase from proposal documentation into a local, observable, multi-agent compliance analyzer. The implementation needs to track both code changes and architectural decisions as the system moves from Phase 0 and Phase 1 scaffolding into validated data ingestion, hybrid retrieval, agent orchestration, HITL controls, and observability.

The project also expects material evolutionary changes, such as replacing deterministic placeholder embedding vectors with a real local semantic embedding model. These changes affect code, schema, data reset procedures, documentation, and demo query behavior.

## Decision

Use Git as the authoritative code and documentation change history.

Use GitHub as the public remote repository for collaboration, backup, tags, and future issue tracking.

Use phase-oriented tags to mark stable milestones, starting with `phase-0-1-baseline`.

Use `CHANGELOG.md` for human-readable change summaries.

Use Architecture Decision Records under `docs/adr/` for decisions that affect architecture, data contracts, model strategy, reset behavior, governance, or phase transitions.

## Consequences

- Every file-level change can be traced through Git commits.
- Phase milestones can be recovered using Git tags.
- Documentation changes and code changes are versioned together.
- Future model changes, such as replacing deterministic placeholder embeddings, must include a code diff, a changelog entry, and an ADR when the decision affects architecture or repeatability.
- GitHub is not required for local Git history, but the remote repository provides backup and makes the project easier to share.

## Change tracking rules

- Commit at meaningful phase checkpoints or feature boundaries.
- Keep commit messages explicit, for example `docs: document embedding strategy` or `feat(database): add ingestion script`.
- Update `CHANGELOG.md` when behavior, setup, schema, reset, or phase scope changes.
- Add an ADR when a decision changes architecture, technology selection, data contracts, reset behavior, governance controls, or model strategy.
- Tag validated milestones, not every small change.

## Example future change: real embedding model

When replacing deterministic placeholder vectors with real local semantic embeddings:

1. Update `database-layer/src/embedding.ts`.
2. Update `database-layer/prisma/schema.prisma` from `vector(8)` to the selected model dimension.
3. Update `EMBEDDING_DIMENSION` in environment examples.
4. Reset and re-ingest demo data.
5. Update `docs/06-setup-runbook.md`, `docs/03-schema-diagrams.md`, and `docs/04-technical-tool-interactions.md`.
6. Add a changelog entry.
7. Add a new ADR documenting the model choice, dimension, runtime requirements, and tradeoffs.
8. Commit and tag the validated milestone if retrieval behavior is accepted.
