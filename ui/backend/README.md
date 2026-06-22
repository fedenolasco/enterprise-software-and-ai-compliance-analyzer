# UI API

FastAPI backend for the Enterprise Software & AI Compliance Analyzer UI.

## Overview

This backend wraps the `agent_brain` Python package as REST and WebSocket endpoints, providing:

- Service health checks for PostgreSQL, Neo4j, Mock Pricing API, Phoenix, Langfuse, and Foundry Local
- Configuration display and editing
- Data browsing (vendors, software, subscriptions, documents, pricing, graph)
- Retrieval (vector, graph, hybrid)
- Workflow execution with WebSocket live updates
- HITL decision submission
- Observability (traces, usage, audit events) with provider filtering
- CLI command launcher
- Demo data reset at 4 granularity levels

## Setup

```bash
cd ui/backend
pip install -e ".[dev]"
```

## Run

```bash
python -m ui_api.main
```

Or via the console script:

```bash
ui-api
```

The API will be available at `http://localhost:3001`.

## Environment variables

The backend reads the same environment variables as `agent-brain`. See [`agent-brain/.env.example`](../../agent-brain/.env.example) for the full list.

Additional UI-specific variables:

| Variable | Default | Description |
|---|---|---|
| `UI_API_HOST` | `127.0.0.1` | Host for the UI API server |
| `UI_API_PORT` | `3001` | Port for the UI API server |
| `CORS_ORIGINS` | `http://localhost:3000` | Comma-separated allowed CORS origins |
