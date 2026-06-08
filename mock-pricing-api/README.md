# Mock Pricing API

Local FastAPI service for synthetic software pricing lookups used by Phase 3 agent tool-call demonstrations.

## Purpose

The service keeps pricing data local and deterministic. It lets the future agent workflow practice tool use without calling external vendor pricing systems.

## Setup

```powershell
cd mock-pricing-api
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e .[dev]
copy .env.example .env
```

For `cmd.exe`, activate the virtual environment with:

```cmd
mock-pricing-api\.venv\Scripts\activate.bat
```

## Run locally

```powershell
python -m mock_pricing_api.main
```

The API starts on `http://127.0.0.1:8000` by default.

## Endpoints

- `GET /health` — service health and fixture count.
- `GET /pricing` — all synthetic pricing records.
- `GET /pricing/{software_code}` — pricing record for one software code.
- `POST /pricing:lookup` — typed lookup by `software_code` with optional requested seats.

## Validation

```powershell
python -m pytest
python -m ruff check src tests
python -m mypy src
```

## Fixture

The default fixture is [`src/mock_pricing_api/data/pricing.json`](src/mock_pricing_api/data/pricing.json). It currently includes synthetic pricing for OpenAI Enterprise, Microsoft 365 Copilot, and Notion AI to match the Phase 2 subscription fixtures.
