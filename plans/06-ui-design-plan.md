# Priority 4: Polished User-Facing UI — Design Plan

## Confirmed decisions

| Decision | Choice | Rationale |
|---|---|---|
| UI stack | FastAPI backend + React/Next.js frontend | Most polished and production-feel, explicit API contract, rich component libraries |
| Primary audience | All — demos, education, and development | UI must serve stakeholder demos, educational walkthroughs, and developer use equally |
| Real-time model | Hybrid — WebSocket for workflow/HITL, request-response for data/config | Live node highlighting during workflow execution, simpler REST for browsing |
| Deployment | Docker service in docker-compose.yml | One-command startup alongside PostgreSQL, Neo4j, and pricing API |

## Purpose

This plan designs a polished, user-friendly UI for the Enterprise Software & AI Compliance Analyzer. The UI must expose config parameters, show the state of connected interfaces, provide a visual guided oversight of data and components, let users launch CLI-equivalent commands through the UI, and show all inputs and outputs. The UI must remain robust and include helper guidance explaining what the system is doing and why.

This plan resolves the caveat: "The current experience is CLI and notebook based; no polished user-facing UI is included."

## Current system context

The system is a local-first, zero-cloud-dependency monorepo with three main workstreams:

| Workstream | Language | Role |
|---|---|---|
| [`database-layer/`](../database-layer/) | TypeScript / Prisma | PostgreSQL + pgvector relational and vector data, ingestion, concurrency validation |
| [`agent-brain/`](../agent-brain/) | Python | LangGraph workflow, hybrid retrieval, HITL governance, observability, model adapters |
| [`mock-pricing-api/`](../mock-pricing-api/) | Python / FastAPI | Local synthetic pricing API on port 8000 |

### Existing CLI entry points the UI must mirror

| CLI command | Module | What it does |
|---|---|---|
| `agent-brain-validate` | [`agent_brain.cli.validate_scaffold`](../agent-brain/src/agent_brain/cli/validate_scaffold.py) | Validates scaffold and configuration |
| `agent-brain-project-graph` | [`agent_brain.cli.project_graph`](../agent-brain/src/agent_brain/cli/project_graph.py) | Projects PostgreSQL data into Neo4j graph |
| `agent-brain-search-vectors` | [`agent_brain.cli.search_vectors`](../agent-brain/src/agent_brain/cli/search_vectors.py) | PostgreSQL pgvector semantic search |
| `agent-brain-traverse-graph` | [`agent_brain.cli.traverse_graph`](../agent-brain/src/agent_brain/cli/traverse_graph.py) | Neo4j graph traversal with optional filters |
| `agent-brain-hybrid-retrieve` | [`agent_brain.cli.hybrid_retrieve`](../agent-brain/src/agent_brain/cli/hybrid_retrieve.py) | Combined vector + graph retrieval |
| `agent-brain-run-curated-demo` | [`agent_brain.cli.run_curated_demo`](../agent-brain/src/agent_brain/cli/run_curated_demo.py) | Runs curated Phase 2 demo queries with assertions |

### Config parameters the UI must surface

From [`agent-brain/src/agent_brain/config.py`](../agent-brain/src/agent_brain/config.py):

| Parameter | Default | Category |
|---|---|---|
| `database_url` | `postgresql://...localhost:5432/compliance_analyzer` | Database |
| `neo4j_uri` | `bolt://localhost:7687` | Graph |
| `neo4j_username` / `neo4j_password` | `neo4j` / `compliance_password` | Graph |
| `mock_pricing_api_url` | `http://127.0.0.1:8000` | Pricing API |
| `embedding_dimension` | `8` | Embeddings |
| `embedding_model` | `deterministic-placeholder` | Embeddings |
| `embedding_provider` | `placeholder` | Embeddings |
| `vector_top_k` | `5` | Retrieval |
| `graph_result_limit` | `25` | Retrieval |
| `model_provider` | `placeholder` | Model |
| `foundry_local_endpoint` | `None` | Model |
| `local_model_name` | `deterministic-placeholder-local-model` | Model |
| `openai_api_key` | `None` | Model |
| `openai_model` | `gpt-4o-mini` | Model |
| `openai_base_url` | `https://api.openai.com/v1` | Model |
| `phoenix_enabled` | `False` | Observability |
| `phoenix_endpoint` | `http://localhost:6006` | Observability |
| `phoenix_grpc_endpoint` | `http://localhost:4317` | Observability |
| `langfuse_enabled` | `False` | Observability |
| `langfuse_host` | `http://localhost:3100` | Observability |
| `langfuse_public_key` / `langfuse_secret_key` | `None` | Observability |

### Connected interfaces the UI must show state for

| Interface | Port | Health check |
|---|---|---|
| PostgreSQL + pgvector | `5432` | Connection test |
| Neo4j | `7687` (bolt) | Connection test |
| Mock Pricing API | `8000` | `GET /health` |
| Phoenix (optional) | `6006` | HTTP reachability |
| Langfuse (optional) | `3000` | HTTP reachability |
| Microsoft Foundry Local (optional) | `5272` | HTTP reachability |

### LangGraph workflow the UI must visualize

From [`agent-brain/src/agent_brain/orchestration/workflow.py`](../agent-brain/src/agent_brain/orchestration/workflow.py):

```mermaid
flowchart TD
    A[Start] --> B[Pricing node]
    B --> C[Draft recommendation node]
    C --> D{Route after draft}
    D -- Has HITL decision --> E[Finalize with HITL]
    D -- Finalization allowed --> F[Finalize without HITL]
    D -- HITL required --> G[Build HITL pause]
    G --> H[End - awaiting human decision]
    E --> I[End - finalized]
    F --> I
```

### HITL governance the UI must enforce

From [`agent-brain/src/agent_brain/governance/hitl.py`](../agent-brain/src/agent_brain/governance/hitl.py):

- `HITLDecision` with outcomes: `APPROVED`, `REJECTED`, `REVISION_REQUESTED`
- `build_hitl_pause()` produces a structured pause payload
- `finalize_with_hitl()` applies the human decision and returns final output only when approved
- The UI must never bypass this gate — it calls the same Python functions

## UI stack options

### Option A: Streamlit (Python-native, rapid)

**Description:** A single Streamlit application that imports `agent_brain` Python modules directly. No separate backend API needed.

**Pros:**
- Fastest path to a working UI — same language as agent-brain
- Direct Python imports, no API bridge layer
- Built-in components for tables, charts, forms, and sidebars
- Good for demos and educational walkthroughs
- Minimal new dependencies

**Cons:**
- Limited control over layout and polish
- Not ideal for complex multi-page workflows with real-time updates
- Session state management can be tricky for long-running workflows
- Less "production-feel" for stakeholders

**Best for:** Rapid prototyping, educational demos, internal validation

### Option B: FastAPI backend + React/Next.js frontend

**Description:** A FastAPI backend layer that wraps `agent_brain` Python functions as REST endpoints, with a React or Next.js frontend consuming those APIs.

**Pros:**
- Full control over UI polish, layout, and user experience
- Clean separation of concerns — API contract is explicit
- Can use rich component libraries (shadcn/ui, Ant Design, MUI)
- Real-time updates via WebSocket or Server-Sent Events
- Scales to a production-grade experience

**Cons:**
- More setup and boilerplate (two projects, API design, CORS)
- Requires TypeScript/JavaScript knowledge alongside Python
- Longer development cycle
- More moving parts to maintain

**Best for:** Polished stakeholder demos, production-feel, long-term extensibility

### Option C: FastAPI backend + HTMX/Jinja2 frontend

**Description:** A FastAPI backend with server-rendered HTML using Jinja2 templates and HTMX for interactivity. No separate frontend build step.

**Pros:**
- Python-only stack — no JavaScript framework needed
- Server-rendered pages are simple to reason about
- HTMX provides interactivity without a heavy SPA framework
- Good middle ground between Streamlit's limitations and React's complexity
- Fast iteration cycle

**Cons:**
- Less polished than a full React SPA
- Limited real-time update patterns compared to WebSocket-driven React
- Fewer pre-built UI components
- Custom styling required for a polished look

**Best for:** Balanced approach, Python team, moderate polish needs

### Option D: Gradio (Python-native, ML-focused)

**Description:** A Gradio application with custom blocks for each UI section.

**Pros:**
- Designed for ML/AI demos
- Python-native, direct imports
- Built-in sharing and deployment options
- Good for form-based interactions

**Cons:**
- Less flexible layout than Streamlit
- Styling is more constrained
- Not ideal for complex multi-step workflows with oversight dashboards
- Feels more like a "demo tool" than a "product"

**Best for:** Quick ML model demos, simple form-based interactions

## Recommended functional areas

The UI should be organized into these functional areas:

### 1. Dashboard / Overview page

- **Service health panel:** Real-time status of PostgreSQL, Neo4j, Mock Pricing API, Phoenix, Langfuse, Foundry Local
- **Config summary:** Current model provider, embedding provider, observability status
- **Quick actions:** Launch curated demo, reset demo data, run validation
- **Recent audit events:** Latest governance events from the audit table

### 2. Configuration page

- **Editable config view:** Display all config parameters from [`config.py`](../agent-brain/src/agent_brain/config.py) with descriptions
- **Environment file editor:** View and edit `.env` values (read-only or with save-to-file)
- **Provider switcher:** Toggle between placeholder, Foundry Local, and OpenAI
- **Helper guidance:** Tooltips and inline explanations for each parameter

### 3. Data & Components oversight page

- **Vendor / Software / Subscription browser:** Table view of relational data from PostgreSQL
- **Compliance document corpus:** List of ingested documents and chunks
- **Neo4j graph visualization:** Visual representation of graph nodes and relationships
- **Pricing data browser:** Table view of mock pricing records
- **Component dependency diagram:** Visual map of how data flows through the system

### 4. Retrieval & Query page

- **Query interface:** Natural-language input with optional structured filters
- **Curated query presets:** Pre-built queries from [`plans/03-query-scope.md`](03-query-scope.md)
- **Results table:** Hybrid retrieval results with priority scores, risk, cost, evidence
- **Evidence viewer:** Expandable excerpts with source document links
- **CLI equivalent display:** Shows the equivalent CLI command for each action

### 5. Workflow & HITL page

- **LangGraph workflow visualization:** Visual graph of the workflow with current node highlighted
- **State inspector:** View current `AgentBrainState` fields
- **Pricing lookup form:** Software code + seats input, shows pricing API response
- **Recommendation draft viewer:** Shows drafted recommendation with risk, cost, evidence context
- **HITL approval panel:** Mandatory pause screen with reviewer name, rationale, and decision buttons
- **Final output display:** Shows final output only after approval

### 6. Observability & Governance page

- **Phoenix trace viewer:** Trace IDs, node names, safety flags
- **Langfuse usage viewer:** Token usage, simulated costs, model metadata
- **Audit event log:** Governance audit events from PostgreSQL
- **Safety flag dashboard:** Current safety flags and risk severity

### 7. CLI Command Launcher page

- **Command palette:** List of all 6 CLI commands with descriptions
- **Parameter forms:** Dynamic forms for each command's arguments
- **Output viewer:** Shows command output (stdout/stderr) in a terminal-like panel
- **Command history:** Log of executed commands and their results

## Demo data reset and management

The system already has 4 reset scripts with different granularities. The UI must expose all of them with appropriate confirmation gates and progress feedback.

### Existing reset capabilities

| Reset scope | Script | What it resets | Confirmation required |
|---|---|---|---|
| PostgreSQL demo data | [`database-layer/scripts/reset-demo-data.ts`](../database-layer/scripts/reset-demo-data.ts) | Deletes all vendors, software, subscriptions, compliance documents, document chunks, compliance risks, and audit events | `--yes` flag or `RESET_DEMO_DATA=true` |
| Neo4j graph state | [`agent-brain/scripts/reset_graph.py`](../agent-brain/scripts/reset_graph.py) | Deletes demo-owned nodes (Vendor, Software, Subscription, ComplianceDocument, DocumentChunk) and relationships (SELLS, HAS_SUBSCRIPTION, HAS_POLICY, HAS_CHUNK, EVIDENCES_RISK) | `--yes` flag or `RESET_GRAPH=true` |
| Mock pricing fixture | [`mock-pricing-api/scripts/reset_pricing_fixture.py`](../mock-pricing-api/scripts/reset_pricing_fixture.py) | Restores pricing JSON fixture from committed source, validates records | None (safe — restores committed data) |
| Full demo environment | [`scripts/reset-demo-environment.ps1`](../scripts/reset-demo-environment.ps1) / [`scripts/reset-demo-environment.sh`](../scripts/reset-demo-environment.sh) | Orchestrates all 3 resets above plus re-ingestion, graph projection, and smoke validation | Starts Docker, runs full reset pipeline |

### UI reset granularity

The UI will expose reset actions at **4 granularity levels**, mirroring the existing scripts:

#### Level 1: Full environment reset (nuclear option)

- **UI location:** Dashboard page → "Reset Demo Environment" button (red, prominent)
- **What it does:** Runs the full reset pipeline — start Docker services, reset PostgreSQL, re-ingest fixtures, reset Neo4j graph, rebuild graph projection, reset pricing fixture, run smoke validation
- **Confirmation:** Two-step confirmation modal: "This will delete ALL data and rebuild from committed fixtures. Are you sure?" → "Type RESET to confirm"
- **Progress feedback:** Real-time progress log showing each step with pass/fail status
- **CLI equivalent displayed:** `./scripts/reset-demo-environment.ps1` (or `.sh` on Linux)
- **Post-reset:** Shows summary of records ingested, graph nodes projected, and validation results

#### Level 2: Individual component reset

- **UI location:** Dashboard page → "Reset" section with 3 buttons
- **Options:**
  - "Reset PostgreSQL data" — deletes and re-ingests relational data only
  - "Reset Neo4j graph" — deletes and re-projects graph nodes/relationships only
  - "Reset pricing fixture" — restores committed pricing JSON
- **Confirmation:** Single confirmation modal per action with description of what will be deleted
- **Progress feedback:** Status indicator (pending → running → complete/failed) with record counts
- **CLI equivalent displayed:** Shows the specific script command for each action

#### Level 3: Audit event cleanup

- **UI location:** Observability & Governance page → "Clear Audit Events" button
- **What it does:** Deletes only `AuditEvent` records from PostgreSQL, preserving all vendor, software, subscription, document, and risk data
- **Confirmation:** "This will delete all audit events. Governance data will be lost. Continue?"
- **Use case:** Clearing workflow run history between demos without re-ingesting all data
- **CLI equivalent displayed:** Custom Prisma query (not an existing script — new capability)

#### Level 4: Workflow state reset

- **UI location:** Workflow & HITL page → "Reset Workflow State" button
- **What it does:** Clears the current workflow session state (in-memory checkpointer), discarding any in-progress workflow without affecting database data
- **Confirmation:** "This will discard the current workflow session. Database data is not affected. Continue?"
- **Use case:** Starting a fresh workflow run without resetting data
- **CLI equivalent displayed:** N/A (session-level reset, no CLI equivalent)

### Reset safety guarantees

1. **Never silent:** Every reset action requires explicit confirmation with a description of what will be deleted
2. **Never partial:** If a reset step fails, the UI shows exactly which step failed and what state the system is in (e.g., "PostgreSQL reset succeeded but Neo4j reset failed — graph may be stale")
3. **Audit trail:** All reset actions are logged as audit events before and after execution
4. **Service dependency awareness:** The full reset button is disabled if Docker services are not running, with a tooltip explaining why
5. **Dry-run preview:** Before executing, the UI shows a summary of what will be affected (e.g., "This will delete: 3 vendors, 3 software products, 3 subscriptions, 7 documents, 42 chunks, 15 risks, 28 audit events")

### Reset API endpoints

| Method | Path | Purpose |
|---|---|---|
| `POST` | `/api/reset/full` | Full environment reset (Level 1) |
| `POST` | `/api/reset/postgresql` | Reset PostgreSQL demo data only (Level 2) |
| `POST` | `/api/reset/graph` | Reset Neo4j graph only (Level 2) |
| `POST` | `/api/reset/pricing` | Reset pricing fixture only (Level 2) |
| `POST` | `/api/reset/audit` | Clear audit events only (Level 3) |
| `POST` | `/api/reset/workflow-state` | Clear workflow session state (Level 4) |
| `GET` | `/api/reset/preview` | Dry-run preview of what each reset would affect |

## Input/Output matrix

The UI must allow the user to manage **all** system inputs and view **all** system outputs from within the interface. This matrix maps every input and output to its UI location.

### Inputs managed through the UI

| Input | Where entered | Backing function or API |
|---|---|---|
| Query text for vector search | Retrieval & Query page | `vector_search()` in [`vector.py`](../agent-brain/src/agent_brain/retrieval/vector.py) |
| `top_k` parameter | Retrieval & Query page | `vector_search(query, top_k=...)` |
| Query text for hybrid retrieval | Retrieval & Query page | `hybrid_retrieve()` in [`hybrid.py`](../agent-brain/src/agent_brain/retrieval/hybrid.py) |
| `graph_limit` parameter | Retrieval & Query page | `hybrid_retrieve(query, graph_limit=...)` |
| Graph traversal filters (vendor code, risk category, risk severity, limit) | Retrieval & Query page | `traverse_risk_context()` in [`traversal.py`](../agent-brain/src/agent_brain/graph/traversal.py) |
| Curated query preset selection | Retrieval & Query page | `run_curated_demo()` in [`curated_risk_to_cost.py`](../agent-brain/src/agent_brain/demo/curated_risk_to_cost.py) |
| Pricing lookup — software code | Workflow & HITL page | `add_pricing_to_state()` in [`pricing.py`](../agent-brain/src/agent_brain/tools/pricing.py) |
| Pricing lookup — requested seats | Workflow & HITL page | `add_pricing_to_state(state, software_code, requested_seats)` |
| Workflow initial state — user query | Workflow & HITL page | `create_initial_state()` in [`state.py`](../agent-brain/src/agent_brain/orchestration/state.py) |
| Workflow initial state — retrieved context | Workflow & HITL page | `AgentBrainState.retrieved_context` |
| Workflow initial state — compliance risks | Workflow & HITL page | `AgentBrainState.compliance_risks` |
| HITL decision — outcome (APPROVED/REJECTED/REVISION_REQUESTED) | Workflow & HITL page | `HITLDecision.create()` in [`hitl.py`](../agent-brain/src/agent_brain/governance/hitl.py) |
| HITL decision — reviewer name | Workflow & HITL page | `HITLDecision.create(outcome, reviewer, rationale)` |
| HITL decision — rationale | Workflow & HITL page | `HITLDecision.create(outcome, reviewer, rationale)` |
| CLI command arguments (query, top-k, vendor-code, risk-category, etc.) | CLI Command Launcher page | All 6 CLI entry points in [`cli/`](../agent-brain/src/agent_brain/cli/) |
| Config parameter changes (read-only display initially, editable in future) | Configuration page | [`config.py`](../agent-brain/src/agent_brain/config.py) `get_settings()` |

### Outputs displayed in the UI

| Output | Where displayed | Source |
|---|---|---|
| Vector search results (vendor, software, risk, distance, evidence excerpt) | Retrieval & Query page | `vector_search()` return value |
| Graph traversal results (vendor, software, subscription, cost, risk, evidence) | Retrieval & Query page | `traverse_risk_context()` return value |
| Hybrid retrieval results (priority score, all merged fields, matched sources) | Retrieval & Query page | `hybrid_retrieve()` return value |
| Evidence excerpts with source document links | Retrieval & Query page (expandable rows) | `HybridRetrievalResult.evidence_excerpt` and `source_document` |
| Curated demo results with assertion pass/fail | Retrieval & Query page / Dashboard | `run_curated_demo()` return value |
| Pricing API response (pricing record, discount, estimated annual total) | Workflow & HITL page | `add_pricing_to_state()` return value |
| Recommendation draft (summary, action, requires approval, rationale) | Workflow & HITL page | `draft_recommendation()` in [`recommendation.py`](../agent-brain/src/agent_brain/orchestration/recommendation.py) |
| HITL pause payload (required, reason, draft summary, safety flags) | Workflow & HITL page | `build_hitl_pause()` in [`hitl.py`](../agent-brain/src/agent_brain/governance/hitl.py) |
| Final output (only after approval) | Workflow & HITL page | `finalize_with_hitl()` return value |
| Full workflow state (all `AgentBrainState` fields) | Workflow & HITL page (state inspector) | `AgentBrainState.to_langgraph_state()` |
| Workflow node transitions (live) | Workflow & HITL page (react-flow viz) | WebSocket stream from `run_langgraph_workflow()` |
| Service health status (6 services) | Dashboard | Health check endpoints |
| Config parameter values (21 parameters) | Configuration page | `get_settings()` |
| Vendor records | Data & Components page | PostgreSQL `Vendor` table |
| Software records | Data & Components page | PostgreSQL `Software` table |
| Subscription records (cost, renewal, status) | Data & Components page | PostgreSQL `Subscription` table |
| Compliance document corpus | Data & Components page | PostgreSQL `ComplianceDocument` and `DocumentChunk` tables |
| Pricing records | Data & Components page | Mock Pricing API `GET /pricing` |
| Neo4j graph structure (nodes and relationships) | Data & Components page | `traverse_risk_context()` summary |
| Graph projection summary (counts) | Data & Components page / CLI Launcher | `project_graph()` return value |
| Phoenix trace spans (trace ID, node name, safety flags, timestamps) | Observability & Governance page | `PhoenixTraceSpan` payloads |
| Langfuse usage events (tokens, cost, model metadata) | Observability & Governance page | `LangfuseUsageEvent` payloads |
| Audit events (type, status, actor, trace ID, message, detail) | Observability & Governance page | PostgreSQL `AuditEvent` table via [`audit.py`](../agent-brain/src/agent_brain/governance/audit.py) |
| Safety flag events (flag, risk severity, decision outcome) | Observability & Governance page | `SafetyFlagEvent` payloads |
| CLI command stdout/stderr output | CLI Command Launcher page | Subprocess capture from CLI entry points |
| CLI command execution status | CLI Command Launcher page | Subprocess return code |
| Command history (executed commands and results) | CLI Command Launcher page | UI session state |

### Input/Output flow guarantee

The UI guarantees full input/output visibility through three mechanisms:

1. **CLI equivalent transparency:** Every UI action displays the equivalent CLI command and its arguments, so the user always knows what input is being sent and can verify the mapping.

2. **Output mirroring:** Every API response is displayed in full — no output is silently consumed. The state inspector on the Workflow page shows the complete `AgentBrainState` after each node transition.

3. **Audit trail:** All UI-triggered actions that modify state or produce governance decisions are persisted as audit events in PostgreSQL, viewable on the Observability page. This creates a permanent record of who did what, when, and why.

## Educational guidance system

The UI must ensure the user understands **every interaction and why it matters**. This is achieved through a multi-layered guidance system that provides the right level of explanation at the right time, without overwhelming experienced users.

### Guidance layers

The UI uses **6 layers of educational guidance**, each serving a different user need:

```mermaid
flowchart TD
    A[Layer 1: Onboarding Tour] --> B[Layer 2: Page Intros]
    B --> C[Layer 3: Inline Tooltips]
    C --> D[Layer 4: Why-This-Matters Callouts]
    D --> E[Layer 5: Step-by-Step Workflow Guide]
    E --> F[Layer 6: CLI Equivalent Transparency]
```

### Layer 1: Onboarding tour

A first-visit guided walkthrough that explains the system's purpose and architecture.

- **Trigger:** First visit (detected via localStorage flag), or manually via "Take Tour" button in header
- **Format:** Highlighted elements with speech-bubble explanations, "Next" / "Skip" buttons
- **Steps:**
  1. "Welcome! This is the Enterprise Software & AI Compliance Analyzer — a local-first tool that connects software subscription costs with AI compliance risk evidence."
  2. "This Dashboard shows the health of all connected services. Green means running, red means unavailable, yellow means optional and disabled."
  3. "The Configuration page shows all parameters controlling the system — model provider, embedding provider, observability tools, and database connections."
  4. "The Data & Components page lets you browse vendors, software, subscriptions, and compliance documents stored in PostgreSQL and Neo4j."
  5. "The Retrieval & Query page is where you search for compliance evidence using natural language. The system combines vector search and graph traversal."
  6. "The Workflow & HITL page is where you run the LangGraph agent workflow. Recommendations that involve cancellation or renewal require human approval before finalization."
  7. "The Observability & Governance page shows traces, token usage, costs, and audit events — all stored locally."
  8. "The CLI Command Launcher lets you run any CLI command from the UI, with the same arguments as the terminal."
- **Persistence:** "Don't show again" checkbox; can be re-triggered from Settings

### Layer 2: Page intros

Each page has a collapsible intro panel at the top explaining what the page does and why it exists.

| Page | Intro text |
|---|---|
| Dashboard | "This is your command center. Monitor service health, review current configuration, launch quick actions, and check recent governance events — all in one place." |
| Configuration | "These parameters control how the system operates. The model provider determines whether you use deterministic placeholders (offline), Microsoft Foundry Local (local AI), or OpenAI (cloud API). Switching providers preserves all observability data for comparison." |
| Data & Components | "Browse the synthetic enterprise software data that powers the compliance analyzer. Vendors, software products, subscriptions, and compliance documents are stored in PostgreSQL. Their relationships are projected into Neo4j for graph traversal." |
| Retrieval & Query | "Search for compliance evidence using natural language. The system embeds your query, searches document chunks in PostgreSQL using pgvector, and traverses vendor-to-evidence relationships in Neo4j. Results are merged and ranked by a deterministic priority score." |
| Workflow & HITL | "Run the LangGraph agent workflow from retrieval to recommendation. The workflow is deterministic — no LLM decides compliance status. Recommendations involving cancellation or renewal require explicit human approval (HITL) before finalization. This is a governance guarantee, not a UI convenience." |
| Observability & Governance | "Every workflow run emits traces (Phoenix), token usage and cost data (Langfuse), and audit events (PostgreSQL). All data is stored locally. Use the provider filter to compare behavior across placeholder, Foundry Local, and OpenAI providers." |
| CLI Command Launcher | "Every action in this UI has an equivalent CLI command. This page lets you run those commands directly, with the same arguments. Use this to verify UI behavior or run commands not yet exposed in the UI." |

- **Behavior:** Collapsed by default after first visit (remembered per page via localStorage), expandable via "Show intro" link

### Layer 3: Inline tooltips

Hover explanations for technical terms, parameters, and fields. Implemented as info icons next to labels.

| Term / Field | Tooltip text |
|---|---|
| pgvector | "A PostgreSQL extension that enables similarity search over vector embeddings. The system stores document chunk embeddings as vectors and finds the most similar chunks to your query." |
| LangGraph | "A framework for building stateful, multi-step agent workflows as directed graphs. Each node performs a deterministic function (pricing lookup, recommendation drafting, HITL evaluation)." |
| HITL | "Human-in-the-Loop. A governance gate that requires a human to approve certain decisions before they are finalized. This prevents automated cancellation or renewal recommendations without oversight." |
| Embedding provider | "The service that converts text into numerical vectors for similarity search. 'placeholder' uses deterministic 8-dimensional vectors for offline validation. 'openai' uses text-embedding-3-small (1536 dimensions) for real semantic search." |
| Model provider | "The service that generates LLM responses. 'placeholder' returns deterministic responses for offline validation. 'microsoft-foundry-local' uses a local Phi-3.5-mini model. 'openai' uses gpt-4o-mini via the OpenAI API." |
| Priority score | "A deterministic ranking score combining AI risk tier weight, evidence severity weight, annual cost weight, renewal urgency weight, and pending renewal bonus. Higher scores indicate higher-priority review candidates." |
| Vector distance | "The cosine distance between your query embedding and a document chunk embedding. Lower distance means higher semantic similarity." |
| Matched sources | "Indicates which retrieval methods contributed to this result: 'vector' (PostgreSQL pgvector search), 'graph' (Neo4j traversal), or both." |
| Trace ID | "A unique identifier for a single workflow run. Used to correlate Phoenix traces, Langfuse usage events, and audit events across observability systems." |
| Safety flags | "Tags attached to workflow state when governance conditions are met (e.g., 'HITL_REQUIRED', 'FINALIZATION_BLOCKED', 'HITL_APPROVED'). These flags are persisted in audit events for compliance traceability." |
| `database_url` | "The PostgreSQL connection string. Defaults to a local Docker container. Changing this requires a service restart." |
| `vector_top_k` | "Maximum number of vector search results to retrieve from PostgreSQL. Higher values return more evidence but may include less relevant matches." |
| `graph_result_limit` | "Maximum number of graph traversal rows to return from Neo4j. Higher values return more vendor-to-evidence paths but increase query time." |
| Phoenix | "Arize Phoenix is an open-source LLM observability tool. When enabled, the system emits trace spans for each workflow node, visible in the Phoenix UI at localhost:6006." |
| Langfuse | "Langfuse is an open-source LLM engineering platform. When enabled, the system emits token usage and simulated cost events, visible in the Langfuse UI at localhost:3100." |
| Microsoft Foundry Local | "A local model runtime that runs AI models on your machine without cloud APIs. When configured, the system uses Phi-3.5-mini for LLM responses and all-MiniLM-L6-v2 for embeddings." |

### Layer 4: Why-this-matters callouts

Contextual boxes that appear at key decision points explaining **why** a specific behavior is happening.

| Location | Trigger | Callout text |
|---|---|---|
| Workflow page — HITL pause | Recommendation requires human approval | "Human approval required. This recommendation involves a cancellation or renewal decision for a vendor with HIGH AI risk tier and material annual spend. The system cannot finalize this recommendation without explicit human approval. This is a governance guarantee enforced by the LangGraph workflow, not just a UI confirmation." |
| Workflow page — finalization blocked | User attempts to bypass HITL | "Finalization blocked. The HITL gate has blocked finalization because no approved human decision is present. This is enforced by `is_finalization_allowed()` in the workflow state — the UI cannot override it." |
| Retrieval page — hybrid results | Results include both vector and graph sources | "Hybrid retrieval. These results combine PostgreSQL vector search (semantic similarity) with Neo4j graph traversal (relationship context). The 'Sources' column shows which method contributed to each result." |
| Retrieval page — vector-only fallback | Neo4j unavailable, showing vector-only results | "Graph unavailable. Neo4j is not running, so only vector search results are shown. Graph traversal adds vendor-to-evidence relationship context. Start Neo4j to see full hybrid results." |
| Config page — provider switch | User switches model provider | "Provider switched. Previous observability data is preserved and tagged with the previous provider. New workflow runs will use the new provider. Visit the Observability page to compare providers side-by-side." |
| Config page — embedding dimension mismatch | User switches embedding provider with different dimensions | "Embedding dimension change detected. Switching from 8-dim (placeholder) to 1536-dim (OpenAI) requires a schema migration, data reset, and re-ingestion. Existing vector data is incompatible. Run 'Reset PostgreSQL data' after switching." |
| Dashboard — placeholder mode | System running with placeholder provider | "Running in placeholder mode. The system is using deterministic placeholder responses and 8-dimensional embeddings. This is the default offline mode. Switch to Foundry Local or OpenAI on the Configuration page for real AI responses." |
| Observability page — provider comparison | User views comparison table | "Provider comparison. This table aggregates data from Phoenix traces, Langfuse usage events, and PostgreSQL audit events. Each column shows metrics for workflow runs tagged with that provider. Use this to compare token usage, cost, and behavior across providers." |
| Reset — full reset confirmation | User clicks full reset | "Full environment reset. This will delete ALL data (vendors, software, subscriptions, documents, chunks, risks, audit events), reset the Neo4j graph, restore the pricing fixture, and re-ingest from committed fixtures. This cannot be undone. Type RESET to confirm." |
| CLI Launcher — command execution | User runs a CLI command | "CLI command executed. This is the same command available from the terminal. The output below matches what you would see running `agent-brain-hybrid-retrieve` directly. The UI wraps the same Python functions." |

### Layer 5: Step-by-step workflow guide

A visual progress indicator during workflow execution that explains each node as it runs.

Displayed as a vertical stepper on the Workflow & HITL page during active workflow runs:

| Step | Node name | Guide text | Status indicator |
|---|---|---|---|
| 1 | Pricing node | "Looking up live pricing from the Mock Pricing API. This adds cost context to the recommendation." | Running then Complete then Skipped if no pricing request |
| 2 | Draft recommendation | "Analyzing retrieved evidence, compliance risks, and pricing data to draft a recommendation. This is deterministic — no LLM decides the recommendation." | Running then Complete |
| 3 | Route after draft | "Evaluating whether this recommendation can be finalized automatically or requires human approval. The decision is based on risk tier, severity, cost, and whether it involves cancellation/renewal." | Evaluating |
| 4a | Finalize without HITL | "Finalizing recommendation. No human approval required because this recommendation does not meet HITL thresholds." | Finalized |
| 4b | Build HITL pause | "Pausing for human approval. This recommendation meets HITL criteria (HIGH risk, material cost, or cancellation/renewal decision). A human must review and approve before finalization." | Awaiting decision |
| 4c | Finalize with HITL | "Applying human decision. If approved, the final recommendation is produced. If rejected, finalization is blocked." | Approved or Rejected |

- **Real-time updates:** The stepper updates live via WebSocket as the workflow progresses
- **Click to expand:** Each step is expandable to show the full state after that node executed

### Layer 6: CLI equivalent transparency

Every UI action that triggers a backend operation displays the equivalent CLI command, so users always understand the mapping between UI and terminal.

| UI action | CLI equivalent shown |
|---|---|
| Run vector search | `agent-brain-search-vectors "cross-border processing" --top-k 5` |
| Run graph traversal | `agent-brain-traverse-graph --risk-category DATA_RESIDENCY --limit 10` |
| Run hybrid retrieval | `agent-brain-hybrid-retrieve "cross-border processing" --top-k 5 --graph-limit 25` |
| Run curated demo | `agent-brain-run-curated-demo` |
| Project graph | `agent-brain-project-graph` |
| Validate scaffold | `agent-brain-validate` |
| Reset PostgreSQL | `cd database-layer and npm run reset:demo -- --yes` |
| Reset Neo4j graph | `cd agent-brain and python scripts/reset_graph.py --yes` |
| Reset pricing fixture | `cd mock-pricing-api and python scripts/reset_pricing_fixture.py` |
| Full environment reset | `./scripts/reset-demo-environment.ps1` |

- **Display format:** Monospace font in a subtle gray box below the action button or in a side panel
- **Copy button:** Each CLI equivalent has a "Copy" button for easy terminal use
- **Toggle:** Users can hide CLI equivalents via a "Show CLI commands" toggle in the header

### Guidance content management

All educational text is managed through a centralized content system to ensure consistency:

```text
ui/
└── frontend/
    └── src/
        ├── lib/
        │   └── guidance.ts          # All tooltip, callout, and intro text
        └── components/
            └── common/
                ├── Tooltip.tsx       # Reusable tooltip component
                ├── Callout.tsx       # Reusable callout component
                ├── PageIntro.tsx     # Collapsible page intro panel
                ├── OnboardingTour.tsx # First-visit tour component
                ├── WorkflowStepper.tsx # Step-by-step workflow guide
                └── CliEquivalent.tsx # CLI command display with copy button
```

### Guidance preferences — user control

The user can enable, disable, or customize each guidance layer independently. This ensures experienced users are not overwhelmed while new users get full support.

#### Settings page — Guidance Preferences section

A dedicated "Guidance Preferences" panel on the Configuration page (or a Settings modal accessible from the header) with the following toggles:

| Preference | Default | Description |
|---|---|---|
| Show onboarding tour | On (first visit) | Controls whether the first-visit tour appears. Can be re-triggered via "Take Tour" button. |
| Show page intros | On | Controls whether collapsible intro panels appear at the top of each page. When off, intros are hidden but can be re-enabled. |
| Show inline tooltips | On | Controls whether info icons and hover tooltips appear next to technical terms and parameters. When off, info icons are hidden. |
| Show why-this-matters callouts | On | Controls whether contextual callout boxes appear at decision points. When off, callouts are suppressed. |
| Show workflow stepper guide | On | Controls whether the step-by-step stepper appears during workflow execution. When off, only the workflow graph visualization is shown without per-node explanations. |
| Show CLI equivalent commands | On | Controls whether CLI command boxes appear below UI actions. When off, CLI equivalents are hidden. |
| Guidance detail level | "Full" | Three levels: "Full" (all callouts and tooltips), "Essential" (only warnings and errors, no info callouts), "Minimal" (only error remediation, no educational content) |

#### Guidance detail levels

The "Guidance detail level" setting provides a quick way to adjust the overall verbosity:

| Level | Tooltips | Info callouts | Warning callouts | Error callouts | Page intros | CLI equivalents | Workflow stepper |
|---|---|---|---|---|---|---|---|
| **Full** (default) | All | All | All | All | All | All | All |
| **Essential** | All | Hidden | All | All | Hidden | All | Node names only (no guide text) |
| **Minimal** | Hidden | Hidden | Hidden | All | Hidden | Hidden | Hidden |

- **Full:** Best for new users, demos, and educational walkthroughs
- **Essential:** Best for experienced users who still want warnings and CLI transparency
- **Minimal:** Best for developers who only want to see errors and remediation

#### Per-callout dismiss

In addition to global preferences, individual callouts can be dismissed:

- Each callout has an "X" dismiss button in the top-right corner
- Dismissed callouts are remembered per callout type (via localStorage)
- Dismissed callouts can be re-enabled via "Reset dismissed callouts" button in Guidance Preferences
- Critical safety callouts (e.g., HITL finalization blocked, embedding dimension mismatch) cannot be dismissed — they always appear regardless of preferences

#### Persistence

All guidance preferences are stored in localStorage under a `ui-guidance-preferences` key:

```json
{
  "showOnboardingTour": false,
  "showPageIntros": true,
  "showInlineTooltips": true,
  "showWhyThisMattersCallouts": true,
  "showWorkflowStepper": true,
  "showCliEquivalentCommands": true,
  "guidanceDetailLevel": "full",
  "dismissedCallouts": ["provider-switch", "placeholder-mode"],
  "tourCompleted": true
}
```

- Preferences persist across sessions and page reloads
- A "Reset to defaults" button restores all preferences to their initial state
- Preferences are per-browser (localStorage), not per-user account

#### Header quick toggle

The header includes a quick-access guidance toggle button (book icon) that cycles through the three detail levels: Full → Essential → Minimal → Full. This provides one-click control without navigating to Settings.

### Accessibility considerations

- All tooltips are accessible via keyboard (focus + Tab to show)
- Callouts use ARIA roles (`role="alert"` for warnings, `role="status"` for info)
- Onboarding tour is keyboard-navigable (Tab to move, Enter for Next, Escape to skip)
- CLI equivalent text is selectable and screen-reader friendly
- Color is never the sole indicator — icons and text accompany all status indicators
- Guidance preference toggles are accessible via keyboard and screen readers
- Dismissed callouts remain accessible to screen readers via an "Announcements" log in Settings

## Observability data persistence across provider switches

### The problem

When a user switches between `placeholder`, `microsoft-foundry-local`, and `openai` model providers, the observability data (Phoenix traces, Langfuse usage events, audit events) is valuable for comparison. The user should be able to:

1. **Keep** observability data when switching providers — so they can compare token usage, cost, and trace behavior across providers
2. **Reset** observability data if they want a clean slate for a new provider
3. **Filter** observability data by provider — so they can view only the data from a specific provider

### Current data storage

| Data type | Storage | Provider-tagged? |
|---|---|---|
| Phoenix trace spans | Phoenix container (in-memory or local DB) | No — trace spans contain `node_name` and `safety_flags` but not `provider` |
| Langfuse usage events | Langfuse container (local DB) | Yes — `LangfuseUsageEvent` has `provider` field in [`observability.py`](../agent-brain/src/agent_brain/governance/observability.py) |
| Audit events | PostgreSQL `AuditEvent` table | Partially — `detail` JSON may contain `model_usage.provider` |

### Design: Provider-tagged observability

The UI will implement a **provider-aware observability layer** that ensures all observability data is tagged with the provider that produced it, and persists across provider switches.

#### 1. Enrich Phoenix trace spans with provider metadata

Update `build_trace_span()` in [`observability.py`](../agent-brain/src/agent_brain/governance/observability.py) to include `provider` in the span metadata:

```python
def build_trace_span(state, node_name, *, metadata=None):
    now = datetime.now(UTC).isoformat()
    return PhoenixTraceSpan(
        trace_id=ensure_trace_id(state.trace_id),
        node_name=node_name,
        started_at=now,
        ended_at=now,
        safety_flags=tuple(state.safety_flags),
        metadata={
            **(metadata or {}),
            "provider": get_settings().model_provider,
            "embedding_provider": get_settings().embedding_provider,
        },
    )
```

This ensures every Phoenix span is tagged with the model and embedding provider that was active when it was created.

#### 2. Langfuse usage events already have provider

`LangfuseUsageEvent` already includes `provider` and `model_name` fields. No change needed — the UI just needs to surface this in the filter UI.

#### 3. Enrich audit events with provider metadata

Update `build_governance_audit_event()` in [`observability.py`](../agent-brain/src/agent_brain/governance/observability.py) to include provider in the `detail` JSON:

```python
detail = {
    "human_approval_status": state.human_approval_status.value,
    "safety_flags": list(state.safety_flags),
    "risk_severity": _highest_risk_severity(state),
    "decision_outcome": decision_outcome,
    "final_output_present": state.final_output is not None,
    "model_provider": get_settings().model_provider,        # NEW
    "embedding_provider": get_settings().embedding_provider, # NEW
}
```

Since audit events are stored in PostgreSQL, they persist across provider switches automatically.

### UI behavior for provider switching

#### Configuration page — provider switch flow

When the user switches providers on the Configuration page:

1. **No data is deleted** — switching providers does not clear Phoenix, Langfuse, or audit data
2. **Info banner shown** — "Provider switched from `placeholder` to `openai`. Previous observability data is preserved. New workflow runs will be tagged with `openai`."
3. **New runs tagged** — all subsequent workflow runs, trace spans, usage events, and audit events will be tagged with the new provider
4. **Comparison enabled** — the Observability page now supports filtering by provider

#### Observability page — provider filter

The Observability & Governance page will include a **provider filter dropdown** on each tab:

| Tab | Filter | Behavior |
|---|---|---|
| Phoenix traces | Filter by `metadata.provider` | Show traces from selected provider, or "All providers" |
| Langfuse usage | Filter by `provider` field | Show usage events from selected provider, or "All providers" |
| Audit events | Filter by `detail.model_provider` | Show audit events from selected provider, or "All providers" |

#### Provider comparison view

A new **"Provider Comparison"** sub-tab on the Observability page will show a side-by-side comparison table:

| Metric | Placeholder | Foundry Local | OpenAI |
|---|---|---|---|
| Total workflow runs | 5 | 3 | 2 |
| Total prompt tokens | 0 | 1,240 | 890 |
| Total completion tokens | 0 | 2,100 | 1,450 |
| Total simulated cost (USD) | $0.00 | $0.00 | $0.03 |
| Avg trace duration (ms) | 12ms | 340ms | 890ms |
| HITL approvals | 2 | 1 | 1 |
| Safety flags raised | 3 | 2 | 1 |

This allows users to compare provider behavior using the same workflow inputs.

### Observability data reset options

The UI will offer **granular reset options** for observability data, separate from demo data reset:

| Reset option | What it clears | Where in UI |
|---|---|---|
| Clear Phoenix traces | All Phoenix trace spans | Observability page → "Clear Phoenix Data" button |
| Clear Langfuse usage | All Langfuse usage events | Observability page → "Clear Langfuse Data" button |
| Clear audit events | All `AuditEvent` records in PostgreSQL | Observability page → "Clear Audit Events" button (also in Level 3 reset) |
| Clear observability for specific provider | Traces/usage/audit tagged with a specific provider | Observability page → provider filter → "Clear data for this provider" |
| Clear all observability | Phoenix + Langfuse + audit events | Observability page → "Clear All Observability" button |

Each reset option requires confirmation and shows a dry-run preview of what will be deleted.

### New API endpoints for observability management

| Method | Path | Purpose |
|---|---|---|
| `GET` | `/api/observability/providers` | List all providers that have observability data |
| `GET` | `/api/observability/traces?provider=placeholder` | Filter traces by provider |
| `GET` | `/api/observability/usage?provider=openai` | Filter usage events by provider |
| `GET` | `/api/observability/audit?provider=microsoft-foundry-local` | Filter audit events by provider |
| `GET` | `/api/observability/comparison` | Side-by-side provider comparison summary |
| `DELETE` | `/api/observability/traces` | Clear Phoenix traces (optionally filtered by provider) |
| `DELETE` | `/api/observability/usage` | Clear Langfuse usage events (optionally filtered by provider) |
| `DELETE` | `/api/observability/audit?provider=placeholder` | Clear audit events for a specific provider |

### Data flow diagram

```mermaid
flowchart TD
    A[User switches provider on Config page] --> B[No data deleted]
    B --> C[Info banner: data preserved]
    C --> D[New workflow runs tagged with new provider]
    D --> E[Phoenix spans include provider in metadata]
    D --> F[Langfuse events include provider field]
    D --> G[Audit events include provider in detail JSON]
    E --> H[Observability page: filter by provider]
    F --> H
    G --> H
    H --> I[Provider comparison view]
    H --> J[Granular reset by provider]
```

### Implementation notes

- The `provider` enrichment is additive — it does not break existing observability payloads
- Phoenix and Langfuse containers store their own data; the UI reads via their APIs and applies provider filtering client-side or via query parameters
- Audit events in PostgreSQL persist indefinitely until explicitly cleared
- The provider comparison view aggregates data from all three sources (Phoenix, Langfuse, PostgreSQL audit)
- If Phoenix or Langfuse is not running, the comparison view shows data from available sources only with a note about missing sources

## Robustness requirements

### Core robustness principles

1. **Graceful degradation:** UI must function even when optional services (Phoenix, Langfuse, Foundry Local) are unavailable
2. **Connection retry:** Health checks should retry with backoff, not fail permanently
3. **Error boundaries:** UI errors should not crash the entire application
4. **Loading states:** All async operations must show loading indicators
5. **Audit trail:** All UI-triggered actions must produce audit events
6. **HITL enforcement:** The UI must never bypass the HITL gate — it calls the same Python governance functions
7. **Input validation:** All form inputs must be validated before submission
8. **Session management:** Workflow state must persist across page navigation

### Graceful degradation matrix

The system has a mix of **required** and **optional** services. The UI must handle each unavailability scenario gracefully and guide the user toward remediation.

| Service | Required? | UI behavior when unavailable | Remediation guidance shown to user |
|---|---|---|---|
| PostgreSQL + pgvector | **Required** | Dashboard shows red health card. Data, Retrieval, Workflow, and Observability pages show "Database unavailable" banner. Actions that need DB are disabled with tooltip. | "Start PostgreSQL: `docker compose up postgres`" + link to [`docs/06-setup-runbook.md`](../docs/06-setup-runbook.md) |
| Neo4j | **Required** | Dashboard shows red health card. Graph traversal and hybrid retrieval show "Neo4j unavailable" banner. Vector-only search remains available. | "Start Neo4j: `docker compose up neo4j`" + link to setup runbook |
| Mock Pricing API | **Required** | Dashboard shows red health card. Pricing lookup form on Workflow page is disabled. Workflow can still run without pricing (pricing node skips). | "Start pricing API: `cd mock-pricing-api && python -m mock_pricing_api.main`" + link to [`mock-pricing-api/README.md`](../mock-pricing-api/README.md) |
| Phoenix | Optional | Dashboard shows yellow "disabled" badge. Observability page shows "Phoenix not enabled" placeholder with explanation. Traces tab hidden or shows empty state. | "To enable Phoenix: set `PHOENIX_ENABLED=true` and run `docker compose --profile observability up`" + link to [`docs/04-technical-tool-interactions.md`](../docs/04-technical-tool-interactions.md) |
| Langfuse | Optional | Dashboard shows yellow "disabled" badge. Observability page shows "Langfuse not enabled" placeholder. Usage tab shows empty state. | "To enable Langfuse: set `LANGFUSE_ENABLED=true` and run `docker compose --profile observability up`" + link to setup runbook |
| Microsoft Foundry Local | Optional | Config page shows "Not configured" for Foundry Local endpoint. Model provider dropdown defaults to `placeholder`. Workflow runs with deterministic placeholder responses. | "To use Foundry Local: install Foundry Local, set `MODEL_PROVIDER=microsoft-foundry-local` and `FOUNDRY_LOCAL_ENDPOINT=http://localhost:5272/v1`" + link to [`scripts/setup-provider.ps1`](../scripts/setup-provider.ps1) |
| OpenAI API | Optional | Config page shows "No API key set" for OpenAI. Model provider dropdown shows OpenAI as disabled with tooltip "Requires `OPENAI_API_KEY`". | "To use OpenAI: set `OPENAI_API_KEY` in `.env` and set `MODEL_PROVIDER=openai`" + link to setup runbook |

### Degradation behavior by scenario

**Scenario 1: No API keys, no Foundry Local, no observability (bare minimum)**

This is the default out-of-the-box state. The UI must fully function with:
- Model provider: `placeholder` (deterministic responses)
- Embedding provider: `placeholder` (8-dim deterministic vectors)
- Phoenix: disabled
- Langfuse: disabled
- Foundry Local: not configured
- OpenAI: no API key

The UI shows a "Running in offline/placeholder mode" info banner on the Dashboard with a link to the Configuration page for upgrade instructions. All core functionality (retrieval, workflow, HITL, audit) works with deterministic placeholder data.

**Scenario 2: PostgreSQL down**

- Dashboard: red health card for PostgreSQL
- All pages: "Database unavailable" banner at top
- Data page: disabled with message "Start PostgreSQL to browse data"
- Retrieval page: disabled with message "Start PostgreSQL to run queries"
- Workflow page: disabled with message "Start PostgreSQL to run workflows"
- Observability page: audit tab shows "Database unavailable", Phoenix/Langfuse tabs remain functional if those services are up
- CLI Launcher: commands that need DB show error output with remediation

**Scenario 3: Neo4j down, PostgreSQL up**

- Dashboard: red health card for Neo4j, green for PostgreSQL
- Data page: fully functional (relational data from PostgreSQL)
- Retrieval page: vector search works, graph traversal disabled, hybrid retrieval shows warning "Graph unavailable — showing vector-only results"
- Workflow page: functional (workflow does not require Neo4j directly)
- CLI Launcher: `agent-brain-traverse-graph` and `agent-brain-hybrid-retrieve` show error, others work

**Scenario 4: Foundry Local not installed, OpenAI key missing**

- Config page: model provider shows `placeholder` as active, Foundry Local and OpenAI shown as "Not configured" with setup instructions
- Workflow page: runs with deterministic placeholder model responses
- Observability: Langfuse usage events show `provider: placeholder` with zero real token cost
- No errors, no crashes — the system is designed for this default state

**Scenario 5: User switches to OpenAI provider but key is invalid**

- Config page: provider switcher attempts to save, backend validates key format
- If key is missing: form validation prevents submission, shows "OPENAI_API_KEY is required for OpenAI provider"
- If key is invalid (API returns 401): workflow page shows error toast "OpenAI API authentication failed. Check your API key or switch to placeholder provider." with a link back to Config page
- System does not crash — the error is caught and surfaced with remediation

### Remediation guidance UI patterns

The UI uses three patterns to guide users toward resolving missing dependencies:

1. **Health card with action button:** Each service health card on the Dashboard includes a "How to fix" expandable section with the exact command to run and a link to the relevant documentation.

2. **Contextual empty states:** When a page cannot load data due to a missing service, it shows a friendly empty state with an icon, explanation, and action button (e.g., "Start Neo4j to see graph data" with a copy-paste command).

3. **Configuration wizard:** The Configuration page includes a "Setup wizard" button that checks all services, identifies what is missing, and presents a step-by-step guide to getting each service running, with copy-paste commands and links to documentation.

### Error handling implementation

| Error type | Backend behavior | Frontend behavior |
|---|---|---|
| Service connection refused | Return `503 Service Unavailable` with `{"service": "...", "remediation": "..."}` | Show error toast with remediation message, disable affected actions |
| Service timeout | Return `504 Gateway Timeout` with service name | Show "Service timed out" with retry button |
| Invalid input | Return `422 Unprocessable Entity` with field errors | Show inline form validation errors |
| Workflow execution error | Return `500 Internal Server Error` with trace ID | Show error modal with trace ID, "Copy error details" button, and link to Observability page |
| WebSocket disconnect | Log error, attempt reconnect | Show "Connection lost" banner with auto-reconnect indicator |
| HITL gate bypass attempt | Return `403 Forbidden` with "HITL approval required" | Show warning modal explaining why finalization is blocked |

### Startup self-check

When the UI backend starts, it runs a self-check sequence:

1. Check PostgreSQL connectivity — if fails, log warning but continue (UI will show degraded state)
2. Check Neo4j connectivity — if fails, log warning but continue
3. Check Mock Pricing API — if fails, log warning but continue
4. Check Phoenix endpoint — if fails or disabled, log info and continue
5. Check Langfuse endpoint — if fails or disabled, log info and continue
6. Check Foundry Local endpoint — if fails or not configured, log info and continue
7. Check OpenAI API key presence — if missing, log info and continue

The self-check results are cached and exposed via `GET /api/health` so the frontend can display the full status on the Dashboard immediately on load.

## High-level directory structure

```text
ui/
├── README.md
├── backend/                # FastAPI backend (Python)
│   ├── pyproject.toml
│   ├── src/ui_api/
│   └── tests/
└── frontend/               # Next.js frontend (TypeScript)
    ├── package.json
    ├── src/
    └── tests/
```

See the detailed backend and frontend structure sections below for the full tree.

## Mermaid: UI architecture overview

```mermaid
flowchart TD
    subgraph Frontend
        UI[UI Application]
    end
    subgraph Backend
        API[API Layer - FastAPI or direct Python imports]
    end
    subgraph Services
        PG[(PostgreSQL + pgvector)]
        NEO[(Neo4j)]
        PRICE[Mock Pricing API]
        PHX[Phoenix - optional]
        LANG[Langfuse - optional]
        FOUNDRY[Foundry Local - optional]
    end
    subgraph AgentBrain
        WF[LangGraph Workflow]
        RET[Hybrid Retrieval]
        HITL[HITL Governance]
        OBS[Observability]
        AUD[Audit Persistence]
    end
    UI --> API
    API --> WF
    API --> RET
    API --> HITL
    API --> OBS
    API --> AUD
    WF --> RET
    WF --> HITL
    WF --> OBS
    RET --> PG
    RET --> NEO
    HITL --> AUD
    AUD --> PG
    OBS --> PHX
    OBS --> LANG
    WF --> FOUNDRY
    PRICE --> WF
```

## Mermaid: User journey through the UI

```mermaid
flowchart LR
    A[Dashboard] --> B[Check service health]
    B --> C[Review config]
    C --> D[Browse data and components]
    D --> E[Run retrieval query]
    E --> F[Review results and evidence]
    F --> G[Launch workflow]
    G --> H[Review recommendation draft]
    H --> I{HITL required?}
    I -- Yes --> J[Approval panel]
    I -- No --> K[Final output]
    J --> L[Submit decision]
    L --> K
    K --> M[Review observability and audit]
```

## Confirmed architecture decisions

All key questions have been resolved with the user:

1. **UI stack:** FastAPI backend + React/Next.js frontend — chosen for polish, explicit API contract, and rich component libraries.
2. **Primary audience:** All audiences — the UI must serve stakeholder demos, educational walkthroughs, and developer use equally.
3. **Real-time model:** Hybrid — WebSocket for workflow execution and HITL, request-response for data browsing and config.
4. **Deployment:** Docker service in `docker-compose.yml` for one-command startup alongside existing services.

## Detailed FastAPI backend design

### Backend structure

```text
ui/
├── backend/
│   ├── pyproject.toml
│   ├── src/
│   │   └── ui_api/
│   │       ├── __init__.py
│   │       ├── app.py              # FastAPI app factory
│   │       ├── config.py           # UI API settings
│   │       ├── routers/
│   │       │   ├── __init__.py
│   │       │   ├── health.py       # Service health checks
│   │       │   ├── config.py       # Config parameter display and editing
│   │       │   ├── data.py         # Data browsing endpoints
│   │       │   ├── retrieval.py    # Hybrid retrieval query endpoints
│   │       │   ├── workflow.py     # LangGraph workflow execution
│   │       │   ├── hitl.py         # HITL decision endpoints
│   │       │   ├── observability.py # Phoenix, Langfuse, audit events
│   │       │   └── cli.py           # CLI command launcher
│   │       ├── services/
│   │       │   ├── __init__.py
│   │       │   ├── health_checker.py  # Connection tests for all services
│   │       │   ├── workflow_runner.py  # LangGraph workflow execution wrapper
│   │       │   └── audit_reader.py    # Read audit events from PostgreSQL
│   │       └── websocket/
│   │           ├── __init__.py
│   │           └── workflow_ws.py  # WebSocket handler for live workflow updates
│   └── tests/
│       └── ...
```

### REST API endpoints

| Method | Path | Purpose |
|---|---|---|
| `GET` | `/api/health` | Aggregate health of all connected services |
| `GET` | `/api/health/{service}` | Health of a specific service (postgres, neo4j, pricing, phoenix, langfuse, foundry) |
| `GET` | `/api/config` | Current config parameters from [`config.py`](../agent-brain/src/agent_brain/config.py) |
| `GET` | `/api/data/vendors` | Browse vendors from PostgreSQL |
| `GET` | `/api/data/software` | Browse software products |
| `GET` | `/api/data/subscriptions` | Browse subscriptions with cost and renewal info |
| `GET` | `/api/data/documents` | Browse compliance document corpus |
| `GET` | `/api/data/pricing` | Browse mock pricing records |
| `GET` | `/api/data/graph` | Neo4j graph node and relationship summary |
| `POST` | `/api/retrieval/vector` | Run vector search (equivalent to `agent-brain-search-vectors`) |
| `POST` | `/api/retrieval/graph` | Run graph traversal (equivalent to `agent-brain-traverse-graph`) |
| `POST` | `/api/retrieval/hybrid` | Run hybrid retrieval (equivalent to `agent-brain-hybrid-retrieve`) |
| `GET` | `/api/retrieval/curated` | Get curated demo query presets from [`plans/03-query-scope.md`](03-query-scope.md) |
| `POST` | `/api/workflow/run` | Start a LangGraph workflow run |
| `GET` | `/api/workflow/state/{thread_id}` | Get current workflow state |
| `POST` | `/api/workflow/hitl/{thread_id}` | Submit a HITL decision |
| `GET` | `/api/observability/traces` | Phoenix trace spans |
| `GET` | `/api/observability/usage` | Langfuse usage events |
| `GET` | `/api/observability/audit` | Audit events from PostgreSQL |
| `POST` | `/api/cli/{command}` | Launch a CLI command and return output |
| `POST` | `/api/reset/full` | Full environment reset (all data + graph + pricing + re-ingest) |
| `POST` | `/api/reset/postgresql` | Reset PostgreSQL demo data only |
| `POST` | `/api/reset/graph` | Reset Neo4j graph only |
| `POST` | `/api/reset/pricing` | Reset pricing fixture only |
| `POST` | `/api/reset/audit` | Clear audit events only |
| `POST` | `/api/reset/workflow-state` | Clear workflow session state |
| `GET` | `/api/reset/preview` | Dry-run preview of what each reset would affect |

### WebSocket endpoint

| Path | Purpose |
|---|---|
| `ws://localhost:3001/ws/workflow/{thread_id}` | Live workflow execution updates — node transitions, state changes, HITL pause events |

### Backend dependencies

```toml
[project]
dependencies = [
  "fastapi==0.115.0",
  "uvicorn[standard]==0.34.0",
  "websockets==14.0",
  "httpx==0.28.1",        # reuse from agent-brain
  "psycopg[binary]==3.2.13",  # reuse from agent-brain
  "neo4j==5.21.0",        # reuse from agent-brain
  "python-dotenv==1.0.1",
]
```

The backend imports `agent_brain` directly as a path dependency or installed package, wrapping its functions as API endpoints without duplicating logic.

## Detailed React/Next.js frontend design

### Frontend structure

```text
ui/
├── frontend/
│   ├── package.json
│   ├── next.config.js
│   ├── tsconfig.json
│   ├── tailwind.config.ts
│   ├── src/
│   │   ├── app/                    # Next.js App Router
│   │   │   ├── layout.tsx          # Root layout with sidebar nav
│   │   │   ├── page.tsx            # Dashboard / Overview
│   │   │   ├── config/page.tsx     # Configuration page
│   │   │   ├── data/page.tsx       # Data & Components oversight
│   │   │   ├── retrieval/page.tsx  # Retrieval & Query
│   │   │   ├── workflow/page.tsx   # Workflow & HITL
│   │   │   ├── observability/page.tsx  # Observability & Governance
│   │   │   └── cli/page.tsx        # CLI Command Launcher
│   │   ├── components/
│   │   │   ├── layout/             # Sidebar, header, breadcrumbs
│   │   │   ├── health/             # Service health cards
│   │   │   ├── config/             # Config parameter editor
│   │   │   ├── data/               # Data tables and graph viz
│   │   │   ├── retrieval/          # Query form and results table
│   │   │   ├── workflow/           # LangGraph visualization, HITL panel
│   │   │   ├── observability/      # Trace, usage, audit viewers
│   │   │   ├── cli/                # Command palette and output terminal
│   │   │   └── common/             # Shared UI: tooltips, callouts, loaders
│   │   ├── hooks/
│   │   │   ├── useHealthCheck.ts
│   │   │   ├── useWorkflowSocket.ts
│   │   │   └── useApi.ts
│   │   ├── lib/
│   │   │   ├── api.ts              # API client
│   │   │   └── constants.ts
│   │   └── styles/
│   │       └── globals.css
│   └── tests/
```

### Recommended component library

- **shadcn/ui** — accessible, customizable, built on Radix UI primitives
- **Tailwind CSS** — utility-first styling for rapid polish
- **react-flow** (or `@xyflow/react`) — LangGraph workflow visualization with node highlighting
- **tanstack/table** — data tables for vendors, subscriptions, audit events
- **lucide-react** — icon set for navigation and status indicators

### Frontend dependencies

```json
{
  "dependencies": {
    "next": "15.1.0",
    "react": "19.0.0",
    "react-dom": "19.0.0",
    "@xyflow/react": "12.3.0",
    "@tanstack/react-table": "8.20.0",
    "tailwindcss": "3.4.0",
    "lucide-react": "0.460.0"
  }
}
```

## Docker Compose integration

Add a `ui` profile to [`docker-compose.yml`](../docker-compose.yml):

```yaml
services:
  ui-backend:
    build:
      context: ./ui/backend
      dockerfile: Dockerfile
    ports:
      - "3001:3001"
    environment:
      - DATABASE_URL=postgresql://compliance_user:compliance_password@postgres:5432/compliance_analyzer
      - NEO4J_URI=bolt://neo4j:7687
      - MOCK_PRICING_API_URL=http://mock-pricing-api:8000
    depends_on:
      postgres:
        condition: service_healthy
      neo4j:
        condition: service_healthy
    profiles: ["ui"]

  ui-frontend:
    build:
      context: ./ui/frontend
      dockerfile: Dockerfile
    ports:
      - "3000:3000"
    environment:
      - NEXT_PUBLIC_API_URL=http://localhost:3001
    depends_on:
      - ui-backend
    profiles: ["ui"]
```

Start with: `docker compose --profile ui up`

## Implementation todo list

- [ ] Initialize `ui/` directory with `backend/` and `frontend/` subdirectories
- [ ] Create FastAPI backend project with `pyproject.toml` and app factory
- [ ] Implement health check service layer for all 6 connected interfaces
- [ ] Implement config router — read and display all parameters from [`config.py`](../agent-brain/src/agent_brain/config.py)
- [ ] Implement data browsing router — vendors, software, subscriptions, documents, pricing, graph summary
- [ ] Implement retrieval router — vector, graph, and hybrid endpoints wrapping `agent_brain` functions
- [ ] Implement workflow router — start workflow, get state, submit HITL decision
- [ ] Implement WebSocket handler for live workflow node transitions
- [ ] Implement observability router — traces, usage, audit events with provider filtering, comparison, and granular reset
- [ ] Enrich Phoenix trace spans and audit events with `model_provider` and `embedding_provider` metadata in [`observability.py`](../agent-brain/src/agent_brain/governance/observability.py)
- [ ] Implement CLI launcher router — execute CLI commands and capture output
- [ ] Implement reset router — full, PostgreSQL, graph, pricing, audit, workflow-state, and preview endpoints
- [ ] Create Next.js frontend project with Tailwind and shadcn/ui
- [ ] Build root layout with sidebar navigation and header
- [ ] Build Dashboard page — service health cards, config summary, quick actions, recent audit events
- [ ] Build Configuration page — parameter table with descriptions, provider switcher, helper tooltips
- [ ] Build Data & Components page — data tables, graph visualization, component dependency diagram
- [ ] Build Retrieval & Query page — query form, curated presets, results table, evidence viewer, CLI equivalent display
- [ ] Build Workflow & HITL page — react-flow workflow visualization, state inspector, pricing form, recommendation draft viewer, HITL approval panel
- [ ] Build Observability & Governance page — Phoenix traces, Langfuse usage, audit log, safety flags, provider filter dropdown, provider comparison table, granular observability reset buttons
- [ ] Build CLI Command Launcher page — command palette, parameter forms, output terminal, command history
- [ ] Build reset UI — full reset button with two-step confirmation, individual component reset buttons, audit cleanup, workflow state reset, dry-run preview modal
- [ ] Build educational guidance system — Layer 1: onboarding tour with 8 steps, Layer 2: collapsible page intros for all 7 pages, Layer 3: inline tooltips for 17 technical terms and parameters, Layer 4: why-this-matters callouts for 10 decision points, Layer 5: step-by-step workflow stepper with real-time WebSocket updates, Layer 6: CLI equivalent transparency with copy buttons for 10 actions
- [ ] Create centralized guidance content file (`guidance.ts`) with all tooltip, callout, and intro text
- [ ] Build reusable guidance components — Tooltip, Callout, PageIntro, OnboardingTour, WorkflowStepper, CliEquivalent
- [ ] Build guidance preferences system — per-layer toggles, 3 detail levels (Full/Essential/Minimal), per-callout dismiss with localStorage persistence, header quick-toggle button, critical callouts that cannot be dismissed
- [ ] Add accessibility — keyboard-navigable tooltips, ARIA roles for callouts, screen-reader friendly CLI text
- [ ] Add Dockerfiles for backend and frontend
- [ ] Add `ui` profile to [`docker-compose.yml`](../docker-compose.yml)
- [ ] Write backend tests for all routers and services
- [ ] Write frontend component tests
- [ ] Document UI setup in [`docs/06-setup-runbook.md`](../docs/06-setup-runbook.md)
- [ ] Document UI demo path in [`docs/07-demo-runbook.md`](../docs/07-demo-runbook.md)
- [ ] Update [`plans/05-forward-looking-implementation-plan.md`](05-forward-looking-implementation-plan.md) to mark Priority 4 as in-progress
- [ ] Update [`plans/02-implementation-plan-checklist.md`](02-implementation-plan-checklist.md) with UI progress tracking
- [ ] Add ADR for UI architecture decision
- [ ] Update [`CHANGELOG.md`](../CHANGELOG.md) with UI implementation summary
