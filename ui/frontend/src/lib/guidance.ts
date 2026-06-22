/**
 * Centralized guidance content for all tooltips, callouts, and page intros.
 * This ensures consistency across the UI.
 */

export const pageIntros: Record<string, string> = {
  dashboard:
    "This is your command center. Monitor service health, review current configuration, launch quick actions, and check recent governance events — all in one place.",
  config:
    "These parameters control how the system operates. The model provider determines whether you use deterministic placeholders (offline), Microsoft Foundry Local (local AI), or OpenAI (cloud API). Switching providers preserves all observability data for comparison.",
  data:
    "Browse the synthetic enterprise software data that powers the compliance analyzer. Vendors, software products, subscriptions, and compliance documents are stored in PostgreSQL. Their relationships are projected into Neo4j for graph traversal.",
  retrieval:
    "Search for compliance evidence using natural language. The system embeds your query, searches document chunks in PostgreSQL using pgvector, and traverses vendor-to-evidence relationships in Neo4j. Results are merged and ranked by a deterministic priority score.",
  workflow:
    "Run the LangGraph agent workflow from retrieval to recommendation. The workflow is deterministic — no LLM decides compliance status. Recommendations involving cancellation or renewal require explicit human approval (HITL) before finalization. This is a governance guarantee, not a UI convenience.",
  observability:
    "Every workflow run emits traces (Phoenix), token usage and cost data (Langfuse), and audit events (PostgreSQL). All data is stored locally. Use the provider filter to compare behavior across placeholder, Foundry Local, and OpenAI providers.",
  cli:
    "Every action in this UI has an equivalent CLI command. This page lets you run those commands directly, with the same arguments. Use this to verify UI behavior or run commands not yet exposed in the UI.",
};

export const tooltips: Record<string, string> = {
  pgvector:
    "A PostgreSQL extension that enables similarity search over vector embeddings. The system stores document chunk embeddings as vectors and finds the most similar chunks to your query.",
  LangGraph:
    "A framework for building stateful, multi-step agent workflows as directed graphs. Each node performs a deterministic function (pricing lookup, recommendation drafting, HITL evaluation).",
  HITL:
    "Human-in-the-Loop. A governance gate that requires a human to approve certain decisions before they are finalized. This prevents automated cancellation or renewal recommendations without oversight.",
  "embedding_provider":
    "The service that converts text into numerical vectors for similarity search. 'placeholder' uses deterministic 8-dimensional vectors for offline validation. 'openai' uses text-embedding-3-small (1536 dimensions) for real semantic search.",
  "model_provider":
    "The service that generates LLM responses. 'placeholder' returns deterministic responses for offline validation. 'microsoft-foundry-local' uses a local Phi-3.5-mini model. 'openai' uses gpt-4o-mini via the OpenAI API.",
  priority_score:
    "A deterministic ranking score combining AI risk tier weight, evidence severity weight, annual cost weight, renewal urgency weight, and pending renewal bonus. Higher scores indicate higher-priority review candidates.",
  vector_distance:
    "The cosine distance between your query embedding and a document chunk embedding. Lower distance means higher semantic similarity.",
  matched_sources:
    "Indicates which retrieval methods contributed to this result: 'vector' (PostgreSQL pgvector search), 'graph' (Neo4j traversal), or both.",
  trace_id:
    "A unique identifier for a single workflow run. Used to correlate Phoenix traces, Langfuse usage events, and audit events across observability systems.",
  safety_flags:
    "Tags attached to workflow state when governance conditions are met (e.g., 'HITL_REQUIRED', 'FINALIZATION_BLOCKED', 'HITL_APPROVED'). These flags are persisted in audit events for compliance traceability.",
  database_url:
    "The PostgreSQL connection string. Defaults to a local Docker container. Changing this requires a service restart.",
  vector_top_k:
    "Maximum number of vector search results to retrieve from PostgreSQL. Higher values return more evidence but may include less relevant matches.",
  graph_result_limit:
    "Maximum number of graph traversal rows to return from Neo4j. Higher values return more vendor-to-evidence paths but increase query time.",
  Phoenix:
    "Arize Phoenix is an open-source LLM observability tool. When enabled, the system emits trace spans for each workflow node, visible in the Phoenix UI at localhost:6006.",
  Langfuse:
    "Langfuse is an open-source LLM engineering platform. When enabled, the system emits token usage and simulated cost events, visible in the Langfuse UI at localhost:3000.",
  "Microsoft Foundry Local":
    "A local model runtime that runs AI models on your machine without cloud APIs. When configured, the system uses Phi-3.5-mini for LLM responses and all-MiniLM-L6-v2 for embeddings.",
};

export const callouts: Record<string, { type: "info" | "warning" | "error"; text: string }> = {
  hitl_pause: {
    type: "warning",
    text: "Human approval required. This recommendation involves a cancellation or renewal decision for a vendor with HIGH AI risk tier and material annual spend. The system cannot finalize this recommendation without explicit human approval. This is a governance guarantee enforced by the LangGraph workflow, not just a UI confirmation.",
  },
  finalization_blocked: {
    type: "error",
    text: "Finalization blocked. The HITL gate has blocked finalization because no approved human decision is present. This is enforced by is_finalization_allowed() in the workflow state — the UI cannot override it.",
  },
  hybrid_results: {
    type: "info",
    text: "Hybrid retrieval. These results combine PostgreSQL vector search (semantic similarity) with Neo4j graph traversal (relationship context). The 'Sources' column shows which method contributed to each result.",
  },
  vector_only_fallback: {
    type: "warning",
    text: "Graph unavailable. Neo4j is not running, so only vector search results are shown. Graph traversal adds vendor-to-evidence relationship context. Start Neo4j to see full hybrid results.",
  },
  provider_switch: {
    type: "info",
    text: "Provider switched. Previous observability data is preserved and tagged with the previous provider. New workflow runs will use the new provider. Visit the Observability page to compare providers side-by-side.",
  },
  embedding_dimension_mismatch: {
    type: "warning",
    text: "Embedding dimension change detected. Switching from 8-dim (placeholder) to 1536-dim (OpenAI) requires a schema migration, data reset, and re-ingestion. Existing vector data is incompatible. Run 'Reset PostgreSQL data' after switching.",
  },
  placeholder_mode: {
    type: "info",
    text: "Running in placeholder mode. The system is using deterministic placeholder responses and 8-dimensional embeddings. This is the default offline mode. Switch to Foundry Local or OpenAI on the Configuration page for real AI responses.",
  },
  provider_comparison: {
    type: "info",
    text: "Provider comparison. This table aggregates data from Phoenix traces, Langfuse usage events, and PostgreSQL audit events. Each column shows metrics for workflow runs tagged with that provider. Use this to compare token usage, cost, and behavior across providers.",
  },
  full_reset: {
    type: "warning",
    text: "Full environment reset. This will delete ALL data (vendors, software, subscriptions, documents, chunks, risks, audit events), reset the Neo4j graph, restore the pricing fixture, and re-ingest from committed fixtures. This cannot be undone. Type RESET to confirm.",
  },
  cli_executed: {
    type: "info",
    text: "CLI command executed. This is the same command available from the terminal. The output below matches what you would see running the command directly. The UI wraps the same Python functions.",
  },
};

export const cliEquivalents: Record<string, string> = {
  "search-vectors": 'agent-brain-search-vectors "cross-border processing" --top-k 5',
  "traverse-graph": "agent-brain-traverse-graph --risk-category DATA_RESIDENCY --limit 10",
  "hybrid-retrieve":
    'agent-brain-hybrid-retrieve "cross-border processing" --top-k 5 --graph-limit 25',
  "run-curated-demo": "agent-brain-run-curated-demo",
  "project-graph": "agent-brain-project-graph",
  validate: "agent-brain-validate",
  "reset-postgresql": "cd database-layer && npm run reset:demo -- --yes",
  "reset-graph": "cd agent-brain && python scripts/reset_graph.py --yes",
  "reset-pricing": "cd mock-pricing-api && python scripts/reset_pricing_fixture.py",
  "reset-full": "./scripts/reset-demo-environment.ps1",
};

export const onboardingSteps = [
  {
    title: "Welcome!",
    text: "This is the Enterprise Software & AI Compliance Analyzer — a local-first tool that connects software subscription costs with AI compliance risk evidence.",
  },
  {
    title: "Dashboard",
    text: "This Dashboard shows the health of all connected services. Green means running, red means unavailable, yellow means optional and disabled.",
  },
  {
    title: "Configuration",
    text: "The Configuration page shows all parameters controlling the system — model provider, embedding provider, observability tools, and database connections.",
  },
  {
    title: "Data & Components",
    text: "The Data & Components page lets you browse vendors, software, subscriptions, and compliance documents stored in PostgreSQL and Neo4j.",
  },
  {
    title: "Retrieval & Query",
    text: "The Retrieval & Query page is where you search for compliance evidence using natural language. The system combines vector search and graph traversal.",
  },
  {
    title: "Workflow & HITL",
    text: "The Workflow & HITL page is where you run the LangGraph agent workflow. Recommendations that involve cancellation or renewal require human approval before finalization.",
  },
  {
    title: "Observability & Governance",
    text: "The Observability & Governance page shows traces, token usage, costs, and audit events — all stored locally.",
  },
  {
    title: "CLI Command Launcher",
    text: "The CLI Command Launcher lets you run any CLI command from the UI, with the same arguments as the terminal.",
  },
];

export const workflowSteps = [
  {
    node: "pricing",
    name: "Pricing node",
    guide:
      "Looking up live pricing from the Mock Pricing API. This adds cost context to the recommendation.",
  },
  {
    node: "draft_recommendation",
    name: "Draft recommendation",
    guide:
      "Analyzing retrieved evidence, compliance risks, and pricing data to draft a recommendation. This is deterministic — no LLM decides the recommendation.",
  },
  {
    node: "route_after_draft",
    name: "Route after draft",
    guide:
      "Evaluating whether this recommendation can be finalized automatically or requires human approval. The decision is based on risk tier, severity, cost, and whether it involves cancellation/renewal.",
  },
  {
    node: "finalize_without_hitl",
    name: "Finalize without HITL",
    guide:
      "Finalizing recommendation. No human approval required because this recommendation does not meet HITL thresholds.",
  },
  {
    node: "build_hitl_pause",
    name: "Build HITL pause",
    guide:
      "Pausing for human approval. This recommendation meets HITL criteria (HIGH risk, material cost, or cancellation/renewal decision). A human must review and approve before finalization.",
  },
  {
    node: "finalize_with_hitl",
    name: "Finalize with HITL",
    guide:
      "Applying human decision. If approved, the final recommendation is produced. If rejected, finalization is blocked.",
  },
];
