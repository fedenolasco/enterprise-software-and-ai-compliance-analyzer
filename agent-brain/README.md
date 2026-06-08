# Agent Brain

Python workstream for local hybrid retrieval, graph context, future LangGraph orchestration, and governance hooks.

## Current Phase 2 scope

This scaffold prepares `agent-brain` for the hybrid retrieval work described in [`plans/implementation-plan.md`](../plans/implementation-plan.md) and the curated demo queries in [`plans/query-scope.md`](../plans/query-scope.md).

The current implementation milestone includes:

- Load local PostgreSQL and Neo4j settings from environment variables.
- Keep Python runtime compatibility at `3.11+`.
- Provide package structure for retrieval, graph projection, and governance modules.
- Validate the scaffold without requiring live database connections.
- Project validated PostgreSQL vendors, software, subscriptions, compliance documents, and document chunks into Neo4j.
- Search PostgreSQL document chunks through pgvector using the deterministic placeholder embedding algorithm.
- Traverse Neo4j vendor, software, subscription, policy, and chunk relationships for risk-to-cost context.
- Merge PostgreSQL vector results and Neo4j graph traversal into deterministic hybrid risk-to-cost rows.
- Run the curated Phase 2 risk-to-cost demo queries from `plans/query-scope.md` with deterministic assertions.

## Setup

```powershell
cd agent-brain
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e .[dev,notebook]
copy .env.example .env
```

For `cmd.exe`, activate the virtual environment with:

```cmd
agent-brain\.venv\Scripts\activate.bat
```

## Validation

After installing dependencies, run:

```powershell
python -m agent_brain.cli.validate_scaffold
python -m pytest
python -m ruff check src tests
python -m mypy src
```

`agent-brain-validate` checks configuration parsing and package importability only.

## Neo4j graph projection

After the Docker services are running and the database layer has ingested demo data, project the relational and document evidence records into Neo4j:

```powershell
python -m agent_brain.cli.project_graph
```

The projection is idempotent. It creates uniqueness constraints and merges these graph nodes and relationships:

- `Vendor` nodes linked to `Software` with `SELLS`.
- `Vendor` and `Software` nodes linked to `Subscription` with `HAS_SUBSCRIPTION`.
- `Vendor` and `Software` nodes linked to `ComplianceDocument` with `HAS_POLICY`.
- `ComplianceDocument` nodes linked to `DocumentChunk` with `HAS_CHUNK`.
- `DocumentChunk` nodes linked back to `Software` with `EVIDENCES_RISK`.

## PostgreSQL vector retrieval

After ingestion has written document chunks and deterministic placeholder embeddings to PostgreSQL, run a local vector search with:

```powershell
python -m agent_brain.cli.search_vectors "cross-border processing subprocessors outside the EU" --top-k 5
```

This command embeds the query text with the same deterministic placeholder embedding algorithm used by ingestion, searches `DocumentChunk.embedding` with pgvector distance ordering, and prints ranked evidence rows with vendor, software, risk, distance, and excerpt columns.

The current vectors are deterministic placeholders for infrastructure validation. They are useful for proving the zero-ETL retrieval path and repeatable demo plumbing, but they are not production semantic embeddings.

## Neo4j graph traversal

After graph projection has populated Neo4j, run a local graph traversal with:

```powershell
python -m agent_brain.cli.traverse_graph --risk-category DATA_RESIDENCY --limit 10
```

Optional filters include `--vendor-code`, `--risk-category`, `--risk-severity`, and `--limit`. The command prints vendor, software, subscription cost, risk, and evidence excerpts from the projected graph. This validates that graph traversal connects compliance evidence to software and subscription exposure before the hybrid retriever combines graph and vector context.

## Hybrid retrieval

After PostgreSQL ingestion and Neo4j graph projection are complete, run hybrid retrieval with:

```powershell
python -m agent_brain.cli.hybrid_retrieve "cross-border processing subprocessors outside the EU" --top-k 5 --graph-limit 25
```

This command combines PostgreSQL vector evidence with Neo4j graph traversal context and returns the Phase 2 risk-to-cost result shape: vendor, software, subscription, annual cost, risk, recommended review action, matched sources, and deterministic priority score.

The current ranking is deterministic and aligned to [`plans/query-scope.md`](../plans/query-scope.md). It is intended for repeatable local validation and demo preparation before real semantic embeddings or model-generated ranking are introduced.

## Curated Phase 2 demo

After PostgreSQL ingestion, Neo4j projection, and hybrid retrieval are available, run the curated demo contract with:

```powershell
python -m agent_brain.cli.run_curated_demo
```

This command executes the four curated query definitions from [`plans/query-scope.md`](../plans/query-scope.md), prints result rows in the expected risk-to-cost shape, and asserts that the expected positive vendors appear for each curated query. The module behind the CLI is reusable by the future notebook so notebook cells can import the same query definitions, assertions, and row-shaping logic instead of duplicating demo behavior.

## Planned package layout

```text
src/agent_brain/
  config.py                 Environment-backed local settings.
  cli/                      Local validation and demo entry points.
  demo/                     Curated demo query definitions and reusable assertions.
  graph/                    Neo4j graph projection and traversal modules.
  retrieval/                PostgreSQL vector and hybrid retrieval modules.
  governance/               Future safety, HITL, audit, and observability hooks.
```
