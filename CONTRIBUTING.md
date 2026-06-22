# Contributing

Thank you for your interest in contributing to the Enterprise Software & AI Compliance Analyzer. This guide explains how to set up a local development environment, run validation checks, and submit changes.

## Project overview

This is a local-first monorepo with three workstreams:

- [`database-layer/`](database-layer/) — TypeScript, Prisma, PostgreSQL, pgvector, ingestion, and validation.
- [`agent-brain/`](agent-brain/) — Python retrieval, orchestration, notebooks, and governance integrations.
- [`mock-pricing-api/`](mock-pricing-api/) — Local FastAPI service for synthetic pricing lookups.

Read [`README.md`](README.md) for the recommended reading order and [`docs/06-setup-runbook.md`](docs/06-setup-runbook.md) for detailed setup instructions.

## Prerequisites

- Docker Desktop (runs PostgreSQL, pgvector, and Neo4j)
- Node.js and npm (for the database layer)
- Python `3.11.x` and pip (for agent-brain and mock-pricing-api)
- Git

## Local setup

### 1. Start local infrastructure

```cmd
copy .env.example .env
docker compose up -d
```

### 2. Database layer

```cmd
cd database-layer
copy .env.example .env
npm install
npm run db:generate
npm run db:push
npm run db:enable-vector
npm run reset:demo
npm run ingest
npm run validate:concurrency
```

### 3. Agent brain

```cmd
cd agent-brain
py -3.11 -m venv .venv
.venv\Scripts\activate.bat
python -m pip install --upgrade pip
python -m pip install -e .[dev]
copy .env.example .env
```

### 4. Mock pricing API

```cmd
cd mock-pricing-api
py -3.11 -m venv .venv
.venv\Scripts\activate.bat
python -m pip install --upgrade pip
python -m pip install -e .[dev]
copy .env.example .env
```

## Validation checks

Before submitting changes, run the relevant quality checks for each workstream you modified.

### Database layer

```cmd
cd database-layer
npm run typecheck
```

### Agent brain

```cmd
cd agent-brain
python -m agent_brain.cli.validate_scaffold
python -m pytest
python -m ruff check src tests scripts
python -m mypy src
```

### Mock pricing API

```cmd
cd mock-pricing-api
python -m pytest
python -m ruff check src tests scripts
python -m mypy src
```

### Why these checks are required

- `pytest` runs the automated tests and confirms the package still behaves as expected after changes.
- `ruff check` catches common Python mistakes, unused code, import issues, and style problems before they become runtime defects.
- `mypy` checks typed source code and catches mismatched data shapes, incorrect function inputs, and other type-related bugs before the code is executed.

All three must pass because they answer different readiness questions: tests prove expected behavior, Ruff keeps the code clean and consistent, and mypy verifies that typed interfaces are being used safely.

## Branch and commit conventions

- Create a branch from `main` for your changes.
- Use a descriptive branch name, for example `feat/add-embedding-model` or `fix/graph-projection-duplicate-nodes`.
- Write clear commit messages with a type prefix:
  - `feat:` for new features
  - `fix:` for bug fixes
  - `docs:` for documentation changes
  - `chore:` for maintenance tasks
  - `refactor:` for code restructuring without behavior changes

## Pull request checklist

Before opening a pull request, confirm:

- [ ] All relevant validation checks pass (pytest, ruff, mypy, typecheck).
- [ ] No `.env` files, virtual environments, caches, or generated artifacts are staged.
- [ ] New scripts or notebooks are documented in [`docs/06-setup-runbook.md`](docs/06-setup-runbook.md).
- [ ] [`CHANGELOG.md`](CHANGELOG.md) includes a human-readable summary of the change.
- [ ] An ADR is added under [`docs/adr/`](docs/adr/) when the change affects architecture, model strategy, schema, data reset, graph projection, HITL, or observability.

## Generated files

The root [`.gitignore`](.gitignore) excludes:

- `.env` files (only `.env.example` templates are committed)
- Python virtual environments (`.venv`, `.venv-py311`)
- Python caches (`.mypy_cache`, `.pytest_cache`, `.ruff_cache`, `__pycache__`)
- Node dependencies (`node_modules`)
- Jupyter checkpoints (`.ipynb_checkpoints`)
- Build outputs (`dist`, `build`)

Before committing, run `git status --short` and confirm none of these are staged.

## Reset scripts

For a full repeatable demo reset, use the root orchestration scripts:

- Windows: `.\scripts\reset-demo-environment.ps1`
- WSL/Linux: `bash scripts/reset-demo-environment.sh`

For targeted resets, see [`docs/06-setup-runbook.md`](docs/06-setup-runbook.md).

## License

By contributing, you agree that your contributions will be licensed under the [MIT License](LICENSE).
