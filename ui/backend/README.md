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

Use Python `3.11.x` for the UI backend. This is enforced at startup so the backend and Foundry Local SDK use the same project baseline interpreter.

For a clean Windows PowerShell environment, create and use a local Python 3.11 virtual environment in this directory:

```powershell
cd C:\app\enterprise-software-and-ai-compliance-analyzer\ui\backend

if (-not (Test-Path .\.venv\Scripts\python.exe)) {
  py -3.11 -m venv .venv
}

.\.venv\Scripts\python.exe --version
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -e '.[dev]'
```

Run backend tests through the virtual environment, not the global `python` command:

```powershell
cd C:\app\enterprise-software-and-ai-compliance-analyzer\ui\backend
.\.venv\Scripts\python.exe -m pytest tests
```

The expected interpreter is Python `3.11.x`. Running tests with Python `3.14` or another non-baseline interpreter can produce large dependency warning floods that do not reflect the supported backend runtime.

If you want an activated shell:

```powershell
cd C:\app\enterprise-software-and-ai-compliance-analyzer\ui\backend
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
python --version
python -m pytest tests
```

Legacy editable install from the repository root is also supported:

```powershell
cd C:\app\enterprise-software-and-ai-compliance-analyzer
py -3.11 -m pip install -e .\agent-brain -e .\ui\backend
```

## Run

```powershell
cd C:\app\enterprise-software-and-ai-compliance-analyzer\ui\backend
$env:PYTHONPATH="C:\app\enterprise-software-and-ai-compliance-analyzer\agent-brain\src;C:\app\enterprise-software-and-ai-compliance-analyzer\ui\backend\src"
.\.venv\Scripts\python.exe -m ui_api.main
```

Or via the console script:

```bash
ui-api
```

The API will be available at `http://localhost:3001`.

If the backend is accidentally started with another Python version, such as Python 3.14, it exits with a clear message. This prevents the Foundry Local SDK from being installed into Python 3.11 while the backend is running from a different interpreter.

## Environment variables

The backend reads the same environment variables as `agent-brain`. See [`agent-brain/.env.example`](../../agent-brain/.env.example) for the full list.

Additional UI-specific variables:

| Variable | Default | Description |
|---|---|---|
| `UI_API_HOST` | `127.0.0.1` | Host for the UI API server |
| `UI_API_PORT` | `3001` | Port for the UI API server |
| `CORS_ORIGINS` | `http://localhost:3000` | Comma-separated allowed CORS origins |
