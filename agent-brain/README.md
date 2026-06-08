# Agent Brain

Python workstream for local hybrid retrieval, graph context, future LangGraph orchestration, and governance hooks.

## Current Phase 2 scope

This scaffold prepares `agent-brain` for the hybrid retrieval work described in [`plans/implementation-plan.md`](../plans/implementation-plan.md) and the curated demo queries in [`plans/query-scope.md`](../plans/query-scope.md).

The first implementation milestone is intentionally small:

- Load local PostgreSQL and Neo4j settings from environment variables.
- Keep Python runtime compatibility at `3.11+`.
- Provide package structure for retrieval, graph projection, and governance modules.
- Validate the scaffold without requiring live database connections.

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

`agent-brain-validate` checks configuration parsing and package importability only. Live PostgreSQL and Neo4j connectivity checks will be added with the graph projection and retrieval modules.

## Planned package layout

```text
src/agent_brain/
  config.py                 Environment-backed local settings.
  cli/                      Local validation and demo entry points.
  graph/                    Neo4j graph projection and traversal modules.
  retrieval/                PostgreSQL vector and hybrid retrieval modules.
  governance/               Future safety, HITL, audit, and observability hooks.
```
