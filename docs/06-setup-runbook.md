# Setup Runbook

## Phase 0 and Phase 1 bootstrap

For a presentation-ready walkthrough sequence, use [`docs/07-demo-runbook.md`](07-demo-runbook.md). This setup runbook remains the detailed command reference for preparing and validating the local environment.

1. Copy [`.env.example`](../.env.example) to `.env` at the repository root.
2. Start local services with [`docker-compose.yml`](../docker-compose.yml).
3. Copy [`database-layer/.env.example`](../database-layer/.env.example) to `database-layer/.env`.
4. In [`database-layer/`](../database-layer/), install dependencies.
5. Run the Prisma client and schema bootstrap.
6. Enable pgvector.
7. Ingest synthetic fixtures.
8. Run the concurrency validator.

## Python virtual environment baseline

Use Python `3.11.x` for local virtual environments in the Python workstreams.

The Python workstreams require Python `3.11.x` as the local baseline because LangGraph local workflows and the current dependency set are documented against Python 3.11. The UI backend enforces this baseline at startup; starting it with another interpreter, such as Python 3.14, exits early with a remediation message.

Create separate virtual environments for each Python workstream:

- [`agent-brain/`](../agent-brain/)
- [`mock-pricing-api/`](../mock-pricing-api/)

On Windows, prefer the Python launcher so each virtual environment is created with Python 3.11 even if the default `python` command points to a newer interpreter:

```cmd
cd agent-brain
py -3.11 -m venv .venv
.venv\Scripts\activate.bat
python -m pip install --upgrade pip
python -m pip install -e .[dev,notebook]
```

For the mock pricing API:

```cmd
cd mock-pricing-api
py -3.11 -m venv .venv
.venv\Scripts\activate.bat
python -m pip install --upgrade pip
python -m pip install -e .[dev]
```

Python versions newer than the documented `3.11.x` baseline may execute the current tests, but they are not the supported local baseline. If dependency warnings appear when using a non-`3.11.x` interpreter, such as Neo4j driver deprecation warnings, treat them as runtime compatibility warnings unless they become test failures or affect runtime behavior. Re-run validation in a Python `3.11.x` virtual environment before treating those warnings as project defects.

For the UI backend, always start from the repository root with Python 3.11 so the backend, `agent-brain`, and Foundry Local SDK are loaded by the same interpreter:

```powershell
$env:PYTHONPATH="C:\app\enterprise-software-and-ai-compliance-analyzer\agent-brain\src;C:\app\enterprise-software-and-ai-compliance-analyzer\ui\backend\src"
py -3.11 -m ui_api.main
```

This avoids the common Windows issue where the SDK is installed in Python 3.11 but the backend is accidentally launched by a newer default `python` command.

Local virtual environments, caches, tool outputs, and uncommitted `.env` files are intentionally ignored by the root [`.gitignore`](../.gitignore). Before committing, run `git status --short` and confirm that generated folders such as `.venv`, `.venv-py311`, `.mypy_cache`, `.pytest_cache`, `.ruff_cache`, `node_modules`, and `.ipynb_checkpoints` are not staged.

Committed environment templates such as [`.env.example`](../.env.example), [`agent-brain/.env.example`](../agent-brain/.env.example), [`database-layer/.env.example`](../database-layer/.env.example), and [`mock-pricing-api/.env.example`](../mock-pricing-api/.env.example) remain tracked so users can recreate local settings without committing secrets.

## End-to-end local run order

Use this order when building or replaying the current validated local baseline from a clean checkout. Run commands from the repository root unless a step explicitly changes into a workstream directory.

### 1. Start local infrastructure

```cmd
copy .env.example .env
docker compose up -d
```

This starts PostgreSQL with pgvector support and Neo4j using the service definitions in [`docker-compose.yml`](../docker-compose.yml).

### 2. Bootstrap the PostgreSQL and pgvector data layer

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

This creates the Prisma client, applies the schema, enables pgvector, reloads deterministic fixtures, writes placeholder embeddings, creates risk/audit records, and validates optimistic concurrency behavior.

### 3. Validate the Python agent-brain package

```cmd
cd agent-brain
python -m pip install -e .[dev]
python -m agent_brain.cli.validate_scaffold
python -m pytest
python -m ruff check src tests
python -m mypy src
```

This validates local configuration, unit tests, linting, and strict typing before running end-user retrieval or graph commands.

Why these Python quality checks are required:

- `python -m pytest` runs the automated tests and confirms the package still behaves as expected after setup or code changes.
- `python -m ruff check src tests` checks the source and test code for common Python mistakes, unused code, import issues, and style problems before they become runtime defects.
- `python -m mypy src` checks the typed source code and catches mismatched data shapes, incorrect function inputs, and other type-related bugs before the code is executed.

Run all three because they answer different readiness questions: tests prove expected behavior, Ruff keeps the code clean and consistent, and mypy verifies that typed interfaces are being used safely. Passing all three gives confidence that the local demo, retrieval commands, graph workflows, pricing integration, and governance checks are running from a reliable Python baseline.

### 4. Project validated relational data into Neo4j

```cmd
cd agent-brain
python -m agent_brain.cli.project_graph
```

This runs the idempotent Phase 2 graph projection command. It creates Neo4j uniqueness constraints and merges `Vendor`, `Software`, `Subscription`, `ComplianceDocument`, and `DocumentChunk` nodes with relationships that support graph traversal.

### 5. Run PostgreSQL vector retrieval smoke test

```cmd
cd agent-brain
python -m agent_brain.cli.search_vectors "cross-border processing subprocessors outside the EU" --top-k 5
```

This runs the current Phase 2 vector retrieval entry point against PostgreSQL document chunks. It should print ranked evidence rows with vendor, software, risk, distance, and evidence excerpt columns. The ranking uses deterministic placeholder embedding vectors, so treat it as retrieval plumbing validation rather than final semantic retrieval quality.

### 6. Run Neo4j graph traversal smoke test

```cmd
cd agent-brain
python -m agent_brain.cli.traverse_graph --risk-category DATA_RESIDENCY --limit 10
```

This runs the current Phase 2 graph traversal entry point against projected Neo4j nodes and relationships. It should print vendor, software, subscription, annual cost, risk, and evidence excerpt columns. Run graph projection before this step whenever PostgreSQL fixture data has been reset or re-ingested.

### 7. Run hybrid retrieval smoke test

```cmd
cd agent-brain
python -m agent_brain.cli.hybrid_retrieve "cross-border processing subprocessors outside the EU" --top-k 5 --graph-limit 25
```

This runs the current Phase 2 hybrid retrieval entry point. It combines PostgreSQL vector evidence with Neo4j graph traversal context and prints deterministic risk-to-cost rows with priority score, vendor, software, subscription, annual cost, risk, recommended review action, and matched retrieval sources.

### 8. Run curated Phase 2 demo assertions

```cmd
cd agent-brain
python -m agent_brain.cli.run_curated_demo
```

This runs the reusable curated demo module aligned to [`plans/03-query-scope.md`](../plans/03-query-scope.md). It executes all four curated query definitions, prints rows in the expected risk-to-cost shape, and fails if any expected positive vendor is missing.

### 9. Open the documented Phase 2 notebook

```cmd
cd agent-brain
jupyter lab notebooks/phase2-risk-to-cost-demo.ipynb
```

The notebook imports the same reusable curated demo module used by the CLI. It documents prerequisites, environment assumptions, query definitions, result-row interpretation, assertion behavior, and limitations around deterministic placeholder embedding vectors.

### 10. Validate and run the Phase 3 mock pricing API

```cmd
cd mock-pricing-api
copy .env.example .env
python -m pip install -e .[dev]
python -m pytest
python -m ruff check src tests
python -m mypy src
python -m mock_pricing_api.main
```

The API starts on `http://127.0.0.1:8000` by default and serves deterministic synthetic pricing records from [`mock-pricing-api/src/mock_pricing_api/data/pricing.json`](../mock-pricing-api/src/mock_pricing_api/data/pricing.json). The contract is documented in [`docs/08-pricing-api-contract.md`](08-pricing-api-contract.md).

### 11. Validate the Phase 3 agent state model

```cmd
cd agent-brain
python -m pytest tests/test_orchestration_state.py
```

The state model in [`agent-brain/src/agent_brain/orchestration/state.py`](../agent-brain/src/agent_brain/orchestration/state.py) defines the LangGraph-ready workflow state and enforces that cancellation or renewal finalization requires human approval.

### 12. Validate the Phase 3 mock pricing tool wrapper

```cmd
cd agent-brain
python -m pytest tests/test_pricing_tool.py
```

The tool wrapper in [`agent-brain/src/agent_brain/tools/pricing.py`](../agent-brain/src/agent_brain/tools/pricing.py) calls `POST /pricing:lookup`, normalizes the response, and appends pricing context to `AgentBrainState`. Set `MOCK_PRICING_API_URL` if the pricing API is not running on `http://127.0.0.1:8000`.

### 13. Validate the Phase 3 recommendation drafting scaffold

```cmd
cd agent-brain
python -m pytest tests/test_recommendation.py
```

The recommendation drafting scaffold in [`agent-brain/src/agent_brain/orchestration/recommendation.py`](../agent-brain/src/agent_brain/orchestration/recommendation.py) creates deterministic recommendation drafts from retrieved context, compliance risks, and live pricing. High-risk, high-severity, or high-cost drafts require HITL approval before finalization.

### 14. Validate the mandatory HITL finalization gate

```cmd
cd agent-brain
python -m pytest tests/test_hitl.py
```

The HITL helpers in [`agent-brain/src/agent_brain/governance/hitl.py`](../agent-brain/src/agent_brain/governance/hitl.py) build a structured pause payload and block final output unless the human decision is approved.

### 15. Validate the LangGraph Phase A runtime workflow

```cmd
cd agent-brain
python -m pytest tests/test_langgraph_workflow.py
```

The LangGraph workflow in [`agent-brain/src/agent_brain/orchestration/workflow.py`](../agent-brain/src/agent_brain/orchestration/workflow.py) wraps the existing deterministic pricing, recommendation drafting, and HITL finalization logic. It uses LangGraph for node sequencing, conditional routing, and checkpoint-ready execution without introducing LLM calls or OpenAI Agents SDK behavior.

### 16. Open the documented Phase 3 LangGraph HITL notebook

```cmd
cd agent-brain
jupyter lab notebooks/phase3-langgraph-hitl-demo.ipynb
```

The notebook imports the reusable workflow functions from [`agent-brain/src/agent_brain/orchestration/workflow.py`](../agent-brain/src/agent_brain/orchestration/workflow.py). It is a demo/education artifact only: it demonstrates deterministic LangGraph execution, HITL pause/block behavior, approved finalization, and low-risk finalization without adding business logic, making LLM calls, using OpenAI Agents SDK behavior, or calling live local services.

### 17. Run future documented demo entry points

Future end-user scripts and notebooks must be added to this runbook when implemented. Each new entry point must document:

- Purpose and expected audience.
- Prerequisite services and prior commands.
- Exact command or notebook path.
- Required environment variables.
- Expected deterministic outputs or assertions.
- Known limitations, especially when deterministic placeholder embeddings are still in use.

Future Phase 3 extensions that call live local services from [`agent-brain/notebooks/phase3-langgraph-hitl-demo.ipynb`](../agent-brain/notebooks/phase3-langgraph-hitl-demo.ipynb) must update this runbook first with exact service prerequisites, environment variables, checkpoint reset notes, and validation expectations.

## Expected validation outcomes

- PostgreSQL accepts schema creation and vector extension enablement.
- Synthetic vendors, software records, subscriptions, documents, chunks, risks, and audit events are stored.
- Document chunks receive deterministic placeholder embedding vectors for pgvector write-path validation.
- The concurrency validator demonstrates optimistic updates without lock-induced failure.
- Audit events capture ingestion and concurrency details for later observability work.

## Embedding note for Phase 1

Phase 1 uses deterministic placeholder embedding vectors. These are generated locally by [`createDeterministicEmbedding()`](../database-layer/src/embedding.ts) and stored in the pgvector-compatible [`DocumentChunk.embedding`](../database-layer/prisma/schema.prisma) field.

These vectors are not production semantic embeddings. They exist to validate that ingestion, PostgreSQL, pgvector, reset, and re-ingestion all work before a real local embedding model is selected.

When a real local embedding model is introduced, update the embedding generator, update `EMBEDDING_DIMENSION`, change the Prisma vector dimension from `vector(8)` to the selected model dimension, reset the demo data, and re-ingest all document chunks.

## Repeatable demo reset strategy

The curated demo queries in [`plans/03-query-scope.md`](../plans/03-query-scope.md) are intentionally aligned to the synthetic fixtures in [`database-layer/data/subscriptions.json`](../database-layer/data/subscriptions.json) and [`database-layer/data/documents/`](../database-layer/data/documents/). To keep every demo run deterministic, persisted runtime state should be treated as rebuildable demo output, not as source data.

### Reset objectives

The reset process should restore the environment to a clean state where:

- The source of truth is only the committed fixture and schema files.
- PostgreSQL contains no stale rows from previous ingestion, validation, or agent runs.
- pgvector contains only deterministic placeholder embeddings regenerated from the current text fixtures until a real local embedding model is introduced.
- Neo4j contains only graph nodes and relationships projected from the current PostgreSQL fixture load.
- The mock pricing API serves the committed synthetic pricing fixture once that layer is implemented.
- Agent state, HITL decisions, traces, token logs, and simulated cost records from prior demo runs do not affect the next run.

### Source-of-truth files

Use these files as the reset baseline:

| Source | Purpose |
|---|---|
| [`database-layer/prisma/schema.prisma`](../database-layer/prisma/schema.prisma) | Authoritative relational schema and pgvector field definition. |
| [`database-layer/data/subscriptions.json`](../database-layer/data/subscriptions.json) | Structured vendor, software, and subscription fixture data. |
| [`database-layer/data/documents/`](../database-layer/data/documents/) | Synthetic SLA, GDPR, AI policy, DPA, and risk-register text fixtures. |
| [`plans/03-query-scope.md`](../plans/03-query-scope.md) | Curated query definitions and expected positive matches. |
| Future pricing fixture under [`mock-pricing-api/`](../mock-pricing-api/) | Synthetic pricing baseline for tool-call demonstrations. |

### Runtime artifacts that may be reset

| Artifact | Reset reason |
|---|---|
| PostgreSQL rows | Removes stale vendors, software, subscriptions, documents, chunks, risks, and audit events. |
| pgvector embeddings | Ensures vector search reflects the current document chunks and embedding logic. In Phase 1 these are deterministic placeholder embeddings, not final semantic embeddings. |
| Neo4j graph nodes and relationships | Prevents graph traversal from using stale projections. |
| Mock pricing API runtime state | Ensures pricing comparisons match the committed pricing fixture. |
| LangGraph checkpoints or local agent state | Prevents prior recommendations or HITL approvals from affecting the next run. |
| Phoenix traces | Keeps trace review focused on the current demo run. |
| Langfuse token and cost logs | Keeps FinOps reporting focused on the current demo run. |
| Local audit events | Optional for hard resets; useful to clear before a recorded or stakeholder demo. |

### Recommended reset levels

| Reset level | Scope | Use when |
|---|---|---|
| Soft reset | Delete application rows, vector embeddings, graph projection, agent checkpoints, and mutable mock state. | Re-running the curated demo during normal development. |
| Hard reset | Remove Docker volumes for PostgreSQL and Neo4j, then recreate schema and services. | Schema, extension, graph projection, or migration behavior changes. |
| Fixture reset | Reapply committed JSON, document, pricing, and query-scope fixtures. | Preparing for a recorded demo, walkthrough, or regression test. |

### PostgreSQL reset order

When resetting the Prisma-managed data without dropping the database, delete child records before parent records to avoid foreign-key conflicts:

1. `AuditEvent`
2. `ComplianceRisk`
3. `DocumentChunk`
4. `ComplianceDocument`
5. `Subscription`
6. `Software`
7. `Vendor`

After deleting these records, run ingestion again so that all relational rows, compliance chunks, risk rows, vector embeddings, and audit entries are regenerated from the current fixtures.

### Repeatable demo loop

```mermaid
flowchart TD
  A[Reset demo state] --> B[Start local services]
  B --> C[Apply Prisma schema]
  C --> D[Enable pgvector]
  D --> E[Ingest synthetic fixtures]
  E --> F[Generate document chunks and embeddings]
  F --> G[Project graph into Neo4j]
  G --> H[Run curated query from query scope]
  H --> I[Fetch mock pricing data]
  I --> J[Run agent workflow]
  J --> K[Pause at HITL gate]
  K --> L[Persist audit and trace records]
  L --> M[Review deterministic demo output]
```

### Reset scripts and demo entry points

The following scripts and entry points support repeatable demo reset and validation. Keep this table updated as demo automation matures:

| Script | Status | Purpose |
|---|---|---|
| [`database-layer/scripts/reset-demo-data.ts`](../database-layer/scripts/reset-demo-data.ts) | Present | Delete Prisma-managed rows in dependency-safe order and prepare PostgreSQL for fixture re-ingestion. |
| [`agent-brain/src/agent_brain/cli/project_graph.py`](../agent-brain/src/agent_brain/cli/project_graph.py) | Present | Project validated PostgreSQL records into Neo4j for Phase 2 graph traversal. |
| [`agent-brain/src/agent_brain/cli/search_vectors.py`](../agent-brain/src/agent_brain/cli/search_vectors.py) | Present | Run PostgreSQL pgvector retrieval against compliance document chunks for Phase 2 retrieval validation. |
| [`agent-brain/src/agent_brain/cli/traverse_graph.py`](../agent-brain/src/agent_brain/cli/traverse_graph.py) | Present | Traverse projected Neo4j relationships to connect vendors, software, subscriptions, and evidence chunks. |
| [`agent-brain/src/agent_brain/cli/hybrid_retrieve.py`](../agent-brain/src/agent_brain/cli/hybrid_retrieve.py) | Present | Merge PostgreSQL vector evidence and Neo4j graph context into deterministic risk-to-cost rows. |
| [`agent-brain/src/agent_brain/cli/run_curated_demo.py`](../agent-brain/src/agent_brain/cli/run_curated_demo.py) | Present | Run the curated Phase 2 query-scope demo and assert expected positive vendor matches. |
| [`agent-brain/src/agent_brain/orchestration/state.py`](../agent-brain/src/agent_brain/orchestration/state.py) | Present | Define LangGraph-ready state fields and HITL finalization checks for Phase 3 workflows. |
| [`agent-brain/src/agent_brain/orchestration/recommendation.py`](../agent-brain/src/agent_brain/orchestration/recommendation.py) | Present | Draft deterministic recommendations from retrieval, pricing, and risk context. |
| [`agent-brain/src/agent_brain/tools/pricing.py`](../agent-brain/src/agent_brain/tools/pricing.py) | Present | Call the local mock pricing API and append normalized pricing context to agent state. |
| [`agent-brain/src/agent_brain/governance/hitl.py`](../agent-brain/src/agent_brain/governance/hitl.py) | Present | Enforce mandatory HITL pause and approval before final recommendation output. |
| [`agent-brain/notebooks/phase2-risk-to-cost-demo.ipynb`](../agent-brain/notebooks/phase2-risk-to-cost-demo.ipynb) | Present | Import the reusable curated demo module and present the risk-to-cost retrieval demo from [`plans/03-query-scope.md`](../plans/03-query-scope.md). |
| [`agent-brain/notebooks/phase3-langgraph-hitl-demo.ipynb`](../agent-brain/notebooks/phase3-langgraph-hitl-demo.ipynb) | Present | Demonstrate deterministic LangGraph workflow execution and HITL finalization behavior without adding business logic. |
| [`mock-pricing-api/src/mock_pricing_api/main.py`](../mock-pricing-api/src/mock_pricing_api/main.py) | Present | Run the local FastAPI mock pricing service for Phase 3 tool-use validation. |
| [`agent-brain/scripts/reset_graph.py`](../agent-brain/scripts/reset_graph.py) | Present | Delete Neo4j demo graph nodes and relationships, then allow graph projection to rebuild from the current PostgreSQL fixture load. |
| [`mock-pricing-api/scripts/reset_pricing_fixture.py`](../mock-pricing-api/scripts/reset_pricing_fixture.py) | Present | Reload or validate committed pricing fixtures if pricing state becomes mutable. |
| [`scripts/reset-demo-environment.ps1`](../scripts/reset-demo-environment.ps1) | Present | Root-level Windows orchestration script that runs the repeatable reset path from PostgreSQL reset through ingestion, graph reset/projection, pricing fixture reset, and validation smoke tests. |
| [`scripts/reset-demo-environment.sh`](../scripts/reset-demo-environment.sh) | Present | Root-level WSL/Linux equivalent of the Windows reset orchestration script. |
| [`scripts/setup-provider.ps1`](../scripts/setup-provider.ps1) | Present | Windows script to securely configure the OpenAI API key and switch between placeholder, Foundry Local, and OpenAI providers. |
| [`scripts/setup-provider.sh`](../scripts/setup-provider.sh) | Present | WSL/Linux equivalent of the provider setup script. |

Reset scripts must be documented here before they are considered demo-ready. Each script should state whether it performs a soft reset or hard reset, which services must already be running, which environment variables it reads, what data it deletes or regenerates, and which validation command proves the reset succeeded.

Current reset responsibilities:

- [`agent-brain/scripts/reset_graph.py`](../agent-brain/scripts/reset_graph.py) clears only demo-owned Neo4j nodes and relationships, leaving service configuration intact. After it runs, rebuild graph state with [`agent-brain/src/agent_brain/cli/project_graph.py`](../agent-brain/src/agent_brain/cli/project_graph.py).
- [`mock-pricing-api/scripts/reset_pricing_fixture.py`](../mock-pricing-api/scripts/reset_pricing_fixture.py) restores or validates the mock pricing baseline from committed fixture data and verifies that pricing records remain loadable.
- [`scripts/reset-demo-environment.ps1`](../scripts/reset-demo-environment.ps1) is the preferred Windows entry point for a full repeatable demo reset.
- [`scripts/reset-demo-environment.sh`](../scripts/reset-demo-environment.sh) provides the same reset order for WSL/Linux environments.

### Full reset orchestration commands

On Windows PowerShell, run the full reset orchestration from the repository root:

```powershell
.\scripts\reset-demo-environment.ps1
```

Use `-SkipDocker` when PostgreSQL and Neo4j are already running, and use `-SkipValidation` when you only need to reset and rebuild state without running retrieval smoke tests:

```powershell
.\scripts\reset-demo-environment.ps1 -SkipDocker -SkipValidation
```

On WSL or Linux, run the equivalent shell script from the repository root:

```bash
bash scripts/reset-demo-environment.sh
```

Use `--skip-docker` and `--skip-validation` for the same optional behavior:

```bash
bash scripts/reset-demo-environment.sh --skip-docker --skip-validation
```

The root reset orchestration performs a soft reset. It starts local services unless skipped, applies the Prisma schema, enables pgvector, resets and re-ingests PostgreSQL fixture rows, resets and rebuilds the Neo4j graph projection, validates the mock pricing fixture, and optionally runs vector, graph, hybrid, and curated-demo smoke checks.

### Targeted reset commands

Reset only the Neo4j demo graph from [`agent-brain/`](../agent-brain/) when PostgreSQL fixture data has already been reset or re-ingested:

```text
cd agent-brain
python scripts/reset_graph.py --yes
python -m agent_brain.cli.project_graph
```

Reset or validate only the mock pricing fixture from [`mock-pricing-api/`](../mock-pricing-api/):

```text
cd mock-pricing-api
python scripts/reset_pricing_fixture.py
```

### Provider configuration

The project supports three model and embedding providers. Use the setup scripts to securely configure the OpenAI API key and switch between providers:

| Provider | `MODEL_PROVIDER` | LLM | Embeddings | API key | Offline |
|---|---|---|---|---|---|
| Placeholder | `placeholder` | Deterministic | 8-dim placeholder | None | Yes |
| Microsoft Foundry Local | `microsoft-foundry-local` | Phi-3.5-mini / Qwen2.5 | all-MiniLM-L6-v2 (384-dim) | None | Yes |
| OpenAI | `openai` | gpt-4o-mini | text-embedding-3-small (1536-dim) | Required | No |

On Windows PowerShell:

```powershell
.\scripts\setup-provider.ps1 -SwitchTo openai
.\scripts\setup-provider.ps1 -SwitchTo foundry
.\scripts\setup-provider.ps1 -SwitchTo placeholder
```

On WSL/Linux:

```bash
bash scripts/setup-provider.sh --switch-to openai
bash scripts/setup-provider.sh --switch-to foundry
bash scripts/setup-provider.sh --switch-to placeholder
```

The setup script prompts for the OpenAI API key with masked input when switching to OpenAI. The key is written only to gitignored `.env` files and is never printed, logged, or transmitted. Use `-SkipKey` (PowerShell) or `--skip-key` (bash) to switch to OpenAI without re-entering the key if it is already configured.

Switching embedding providers changes the vector dimension. After switching, reset and re-ingest demo data:

```powershell
.\scripts\reset-demo-environment.ps1
```

### Microsoft Foundry Local setup

Microsoft Foundry Local is a native install that runs AI models directly on your device using local hardware (CPU, GPU, or NPU). It is **not** a Docker service — it needs direct hardware access for inference. The project's [`docker-compose.yml`](../docker-compose.yml) runs PostgreSQL, pgvector, and Neo4j as data services; Foundry Local runs natively alongside them.

#### Hardware requirements

| Specification | Minimum | Recommended |
|---|---|---|
| RAM | 8 GB | 16 GB |
| Free disk space | 3 GB | 15 GB |
| GPU | Not required (CPU works) | GPU or NPU for faster inference |
| Network | Required for model download | Not needed after models are cached |
| OS | Windows 10/11, macOS | Windows 11 with NPU for best acceleration |

Foundry Local automatically detects available hardware and selects the best execution provider:

| Hardware | Execution provider | Performance |
|---|---|---|
| NPU (Neural Processing Unit) | QNN (Qualcomm) or OpenVINO (Intel) | Best for laptops with NPUs |
| GPU (NVIDIA/AMD) | CUDA or DirectML | Fast inference |
| CPU only | ONNX Runtime | Works everywhere, slower |

#### Installation

The current UI integration uses the Foundry Local Python SDK. On Windows, install `foundry-local-sdk-winml` into the same Python environment that runs the UI backend; this package enables Windows ML hardware acceleration when supported by local hardware.

If the UI backend is running, the Configuration page exposes the exact interpreter-specific install command from `GET /api/provider/foundry-status`. It will look like:

```cmd
"C:\Path\To\python.exe" -m pip install foundry-local-sdk-winml==1.2.3
```

For a clean Windows setup using the project baseline Python 3.11:

```cmd
py -3.11 -m pip install foundry-local-sdk-winml==1.2.3
```

On macOS/Linux, install the non-Windows SDK package into the backend interpreter:

```bash
python -m pip install foundry-local-sdk==1.2.3
```

Restart the UI backend after installing the SDK so the running process can import `foundry_local_sdk`.

The older native CLI can still be useful for manual inspection where available, but the UI path uses the Python SDK first and only falls back to CLI commands for compatibility.

On macOS, if you need the optional legacy CLI:

```bash
brew tap microsoft/foundrylocal
brew install foundrylocal
```

Use `foundry-local-sdk-winml` on Windows for hardware acceleration via Windows ML. On macOS/Linux, use `foundry-local-sdk` instead.

#### Downloading models

The Configuration page can download/load the selected model through the SDK. For a quick-start local model, select `qwen2.5-0.5b` and use the Download/Load controls on the page.

If you have the optional legacy CLI installed, you can also inspect or download models manually:

```cmd
foundry model load qwen2.5-0.5b
foundry model load all-MiniLM-L6-v2
```

List available models in the catalog:

```cmd
foundry model ls
```

Run a quick test to verify a model works:

```cmd
foundry model run phi-3.5-mini-instruct
```

Recommended models for this project:

| Role | Model | Approximate download size | RAM when loaded | Why |
|---|---|---|---|---|
| LLM (recommendation drafting) | `phi-3.5-mini-instruct` | ~2.5 GB | ~3.5 GB | Strong reasoning, small footprint, good for compliance text |
| LLM (alternative, larger) | `qwen2.5-7b-instruct` | ~4.5 GB | ~8 GB | Better quality, needs more RAM |
| Embeddings | `all-MiniLM-L6-v2` | ~90 MB | ~200 MB | 384-dim, fast, good semantic quality, very small |

For the minimum setup (Phi-3.5-mini + MiniLM), you need approximately 3 GB disk space and 8 GB RAM.

#### Starting Foundry Local

When `MODEL_PROVIDER=microsoft-foundry-local`, the Configuration page starts the SDK-managed Foundry Local web service as needed through `PUT /api/provider/foundry-model`. SDK-managed endpoints are process/session scoped; after restarting the UI backend, the Configuration page may show "Start Service Now" again even though the SDK is installed. Click the button to restart the local service and load the selected model.

If you are using an optional legacy CLI service instead, it can be started manually:

```cmd
foundry service start
```

The legacy service commonly runs on `http://localhost:5272`. SDK-managed services may choose a local dynamic port; the UI writes the active endpoint to `.env` when it changes.

#### Switching the project to Foundry Local

After installing Foundry Local and downloading models, switch the project to the Foundry Local provider:

```powershell
.\scripts\setup-provider.ps1 -SwitchTo foundry
```

```bash
bash scripts/setup-provider.sh --switch-to foundry
```

This updates the `.env` files with:

```text
EMBEDDING_PROVIDER=microsoft-foundry-local
EMBEDDING_MODEL=all-MiniLM-L6-v2
EMBEDDING_DIMENSION=384
MODEL_PROVIDER=microsoft-foundry-local
LOCAL_MODEL_NAME=qwen2.5-0.5b
FOUNDRY_LOCAL_ENDPOINT=<active-local-foundry-endpoint>
```

Then reset and re-ingest demo data because the embedding dimension changes from 8 to 384:

```powershell
.\scripts\reset-demo-environment.ps1
```

### Current reset command

Use the database-layer reset script before re-running ingestion or before building Phase 2 graph projections from a clean relational baseline:

```text
cd database-layer
set DATABASE_URL=postgresql://compliance_user:compliance_password@localhost:5432/compliance_analyzer?schema=public
npm run reset:demo
npm run ingest
```

After re-ingestion, run the graph projection if Neo4j traversal or the Phase 2 demo is part of the current validation scope:

```text
cd agent-brain
python -m agent_brain.cli.project_graph
```

Run the vector retrieval smoke test if PostgreSQL retrieval behavior is part of the current validation scope:

```text
cd agent-brain
python -m agent_brain.cli.search_vectors "cross-border processing subprocessors outside the EU" --top-k 5
```

Run the graph traversal smoke test if Neo4j traversal behavior is part of the current validation scope:

```text
cd agent-brain
python -m agent_brain.cli.traverse_graph --risk-category DATA_RESIDENCY --limit 10
```

Run the hybrid retrieval smoke test if merged risk-to-cost context is part of the current validation scope:

```text
cd agent-brain
python -m agent_brain.cli.hybrid_retrieve "cross-border processing subprocessors outside the EU" --top-k 5 --graph-limit 25
```

Run the curated demo assertions if the Phase 2 demo contract is part of the current validation scope:

```text
cd agent-brain
python -m agent_brain.cli.run_curated_demo
```

Open the notebook when a documented stakeholder-facing walkthrough is needed:

```text
cd agent-brain
jupyter lab notebooks/phase2-risk-to-cost-demo.ipynb
```

The reset script deletes records in dependency-safe order and reports counts before deletion, deleted counts, and counts after deletion.

### Optional Phase 4 observability Docker stack

Phoenix and Langfuse are optional Phase 4 services. They run through the Docker Compose `observability` profile so the Phase 0 through Phase 3 workflow remains lightweight and does not require observability containers.

Before starting the observability profile, copy [`.env.example`](../.env.example) to `.env` and replace the local placeholder secrets for Langfuse:

- `LANGFUSE_NEXTAUTH_SECRET`
- `LANGFUSE_SALT`
- `LANGFUSE_ENCRYPTION_KEY`
- `LANGFUSE_POSTGRES_PASSWORD`
- `LANGFUSE_CLICKHOUSE_PASSWORD`
- `LANGFUSE_REDIS_PASSWORD`
- `LANGFUSE_MINIO_ROOT_PASSWORD`

Start Phoenix, Langfuse, and Langfuse support services with:

```text
docker compose --profile observability up -d phoenix langfuse langfuse-worker
```

The profile also starts the required Langfuse PostgreSQL, ClickHouse, Redis, MinIO, and bucket-initialization services declared in [`docker-compose.yml`](../docker-compose.yml).

Expected local endpoints are:

| Service | Endpoint | Purpose |
|---|---|---|
| Phoenix UI and HTTP collector | `http://localhost:6006` | Trace review and Phoenix-compatible collection. |
| Phoenix OTLP gRPC collector | `http://localhost:4317` | Trace export from future agent instrumentation. |
| Langfuse UI/API | `http://localhost:3100` | Token usage and simulated cost telemetry review. |
| Langfuse MinIO API | `http://localhost:9090` | Local object storage for Langfuse event payloads. |
| Langfuse MinIO console | `http://localhost:9091` | Local object storage inspection. |

Stop only the optional observability profile with:

```text
docker compose --profile observability stop phoenix langfuse langfuse-worker langfuse-postgres langfuse-clickhouse langfuse-redis langfuse-minio
```

If Phoenix or Langfuse are stopped, the agent workflow should continue with `PHOENIX_ENABLED=false` and `LANGFUSE_ENABLED=false`; local audit persistence remains the durable governance record.

### Live observability exporters

When Phoenix and Langfuse are running and enabled, the live exporter clients in [`agent-brain/src/agent_brain/governance/exporters.py`](../agent-brain/src/agent_brain/governance/exporters.py) send payloads to the running services:

| Exporter | Target | Payload | When enabled |
|---|---|---|---|
| `export_phoenix_spans()` | Phoenix HTTP collector (`/v1/spans`) | `PhoenixTraceSpan` payloads | `PHOENIX_ENABLED=true` |
| `export_langfuse_usage()` | Langfuse API (`/api/public/ingestion`) | `LangfuseUsageEvent` payloads with token usage and cost | `LANGFUSE_ENABLED=true` |
| `export_safety_events()` | Phoenix HTTP collector (`/v1/spans`) | `SafetyFlagEvent` payloads | `PHOENIX_ENABLED=true` |

All exporters fail gracefully — if the service is unreachable, disabled, or returns an error, the exporter logs a warning and returns a failed `ExportResult` without raising. The agent workflow continues and local audit persistence remains the durable governance record.

To enable live exporters, set these environment variables in `agent-brain/.env`:

```text
PHOENIX_ENABLED=true
PHOENIX_ENDPOINT=http://localhost:6006
LANGFUSE_ENABLED=true
LANGFUSE_HOST=http://localhost:3100
LANGFUSE_PUBLIC_KEY=pk-lf-local-development-placeholder
LANGFUSE_SECRET_KEY=sk-lf-local-development-placeholder
```

Replace the Langfuse placeholder keys with the actual keys from your local Langfuse instance (visible in the Langfuse UI under Settings > API Keys).

The Phase 4 Python payload builders and live exporters can be validated without running Phoenix or Langfuse:

```text
cd agent-brain
python -m pytest tests/test_model_adapter.py tests/test_observability.py tests/test_audit.py tests/test_exporters.py
```

These tests validate the multi-provider model adapters, Phoenix-compatible trace payloads, Langfuse-compatible token/cost payloads, safety flag records, PostgreSQL AuditEvent-compatible governance records, and live exporter client behavior with mocked HTTP calls.

### Integration tests against live PostgreSQL

Integration tests that persist governance audit events against a live local PostgreSQL database are in [`agent-brain/tests/test_audit_integration.py`](../agent-brain/tests/test_audit_integration.py). These tests are marked with `@pytest.mark.integration` and are skipped by default when running `pytest -m "not integration"`.

Prerequisites for running integration tests:

1. Docker services running (`docker compose up -d`).
2. Prisma schema applied (`npm run db:push` from [`database-layer/`](../database-layer/)).
3. `DATABASE_URL` environment variable set or `.env` file present.

Run integration tests from [`agent-brain/`](../agent-brain/):

```text
python -m pytest tests/test_audit_integration.py -v -m integration
```

Run all tests including integration tests:

```text
python -m pytest tests/ -v
```

Run all tests excluding integration tests (default for CI and offline validation):

```text
python -m pytest tests/ -v -m "not integration"
```

The integration tests verify:

- Single governance audit event persistence to live PostgreSQL.
- Multiple governance audit event persistence in a single transaction.
- Audit event with model usage detail (token counts, cost, safety flags).
- Empty event list is a no-op.
- Audit events survive as the durable governance record when observability services are disabled.
- Each test cleans up its own audit events by trace ID to remain idempotent.

## Notebook and end-user script documentation standard

Every end-user script or notebook added for a demo must be self-documenting and linked from this runbook. Notebook markdown cells should explain each executable section before code is run.

Required documentation sections for notebooks are:

1. Demo objective and business question.
2. Source fixture and query-scope links.
3. Prerequisite runbook steps.
4. Environment variables and local service assumptions.
5. Query inputs and expected positive matches.
6. Step-by-step execution for structured filtering, vector retrieval, graph traversal, result merging, ranking, and assertions.
7. Output interpretation with evidence excerpts and cost/renewal context.
8. Limitations and reset instructions.

Required documentation for script-style entry points is:

- Module docstring describing purpose and side effects.
- CLI help or README/runbook command example.
- Deterministic output summary.
- Unit or integration validation command.
- Runbook update in this file before the script is considered end-user ready.

### Validation after reset

After a reset and re-ingestion, validate that:

- The structured fixtures produce the expected vendors, software products, and subscriptions.
- Compliance documents are chunked and linked to their source records.
- pgvector embeddings are regenerated for all document chunks.
- PostgreSQL vector retrieval returns ranked evidence rows with document, vendor, software, subscription, and risk metadata.
- Curated queries in [`plans/03-query-scope.md`](../plans/03-query-scope.md) return the expected positive matches.
- Neo4j graph projections match the current PostgreSQL identifiers.
- Neo4j graph traversal connects vendors, software, subscriptions, documents, chunks, and risk metadata.
- Hybrid retrieval returns deterministic risk-to-cost rows with priority scores and recommended review actions.
- Curated Phase 2 demo assertions pass for expected positive vendor matches.
- The Phase 2 notebook imports reusable demo code and documents prerequisites, outputs, and limitations.
- The Phase 3 LangGraph HITL notebook imports reusable workflow code and documents deterministic HITL workflow behavior without adding business logic.
- Mock pricing API health, listing, detail, and lookup endpoints return deterministic synthetic pricing data.
- Agent state exports LangGraph-ready fields and blocks cancellation or renewal finalization without approval.
- Mock pricing tool wrapper calls the pricing API contract and appends normalized live pricing context.
- Recommendation drafting creates deterministic drafts and flags HITL-required high-risk decisions.
- HITL finalization gate blocks final output unless a human decision approves the draft.
- HITL and observability records from previous demo runs do not alter the current recommendation flow.
