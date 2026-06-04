# Business Product Requirements: Enterprise Software & AI Compliance Analyzer

## Document control

| Field | Value |
|---|---|
| Product | Enterprise Software & AI Compliance Analyzer |
| Document type | Business Product Requirements Document |
| Current status | Living product document |
| Initial baseline | Phase 0 and Phase 1 scaffold |
| Source roadmap | [`proposal/high-level-plan.md`](../proposal/high-level-plan.md), [`proposal/setup-plan-v3.md`](../proposal/setup-plan-v3.md) |
| Technical plan | [`plans/implementation-plan.md`](../plans/implementation-plan.md) |
| Progress checklist | [`plans/implementation-plan-checklist.md`](../plans/implementation-plan-checklist.md) |

This document is the product-facing source of truth for vision, users, business outcomes, roadmap, and product evolution. Any material change in product direction, target user, capability scope, compliance posture, roadmap sequencing, or demo strategy must update this document.

## Product vision

Build a local-first product that helps enterprise stakeholders understand software subscription spend and AI compliance exposure in one governed workflow.

The product should let users ask business questions such as:

- Which AI-enabled vendors carry high compliance risk and meaningful renewal cost exposure?
- Which subscriptions should be reviewed before renewal or cancellation decisions?
- Which compliance documents provide evidence for data residency, subprocessor, retention, profiling, or automated decision-making risks?
- Which recommendations require human approval before action?

The long-term product vision is a governed AI decision-support system that combines FinOps, procurement, compliance, and AI governance signals without relying on external cloud services during prototype execution.

## Product mission

Provide a repeatable, explainable, and locally governed analyzer that connects:

| Business dimension | Product interpretation |
|---|---|
| Software spend | Subscription cost, seats, renewal timing, owner, and cancellation notice data. |
| AI risk | Vendor AI risk tier, compliance-risk categories, severity, and evidence. |
| Compliance evidence | SLA, GDPR, AI policy, DPA, security addendum, and risk-register text. |
| Retrieval context | Relational records, vector evidence, and graph relationships. |
| Governance | Audit trails, safety flags, HITL approvals, traces, and simulated cost logs. |

## Target users

### Primary users

| User | Need | Product value |
|---|---|---|
| Compliance analyst | Identify AI vendors with evidence-backed compliance risks. | Reduces manual document review and links risks to source evidence. |
| Procurement owner | Prioritize renewals and cancellations using risk and cost context. | Connects spend decisions to governance and compliance impact. |
| FinOps practitioner | Understand software cost exposure and simulated AI operating cost. | Provides cost-weighted review queues and future token economics. |
| AI governance lead | Ensure high-risk AI recommendations receive human oversight. | Enforces HITL before recommendations become final. |

### Secondary users

| User | Need | Product value |
|---|---|---|
| Engineering lead | Validate local, type-safe, observable architecture patterns. | Demonstrates strict schemas, local services, and repeatable reset. |
| Security reviewer | Inspect evidence, audit trails, and local-only data handling. | Supports explainable and auditable compliance workflows. |
| Executive stakeholder | See risk and spend summarized into actionable priorities. | Converts technical evidence into business decision support. |

## Business problem

Enterprise software portfolios increasingly include AI-enabled tools. These tools create overlapping concerns:

- Subscription costs and renewal dates are usually tracked separately from compliance evidence.
- AI risk evidence often lives in unstructured vendor documents.
- Compliance teams need explainable evidence, not black-box recommendations.
- Procurement and FinOps teams need cost-aware prioritization.
- AI governance frameworks require human oversight for high-risk decisions.
- Cloud-based prototypes may be unsuitable for early compliance experimentation.

The product addresses this by creating a local prototype that joins subscription data, document evidence, risk classification, graph relationships, mock live pricing, HITL approvals, and observability.

## Product principles

| Principle | Requirement |
|---|---|
| Local-first | Core prototype services must run locally. |
| Explainability | Every risk recommendation should link to evidence and business context. |
| Type safety | Schema-controlled data access should prevent hallucinated tables or fields. |
| Repeatability | Curated demos must reset and reproduce expected outputs. |
| Human oversight | Cancellation or renewal recommendations must pause for HITL approval. |
| Observability | Reasoning, safety, audit, and simulated cost should be traceable. |
| Evolution tracking | Product direction changes must update this document, changelog, and ADRs when appropriate. |

## Current product scope

### In scope for the current scaffold

- Monorepo structure for database, agent, mock API, docs, plans, and scripts.
- PostgreSQL and pgvector service configuration.
- Neo4j service configuration for future graph retrieval.
- Prisma schema for vendor, software, subscription, document, chunk, risk, and audit records.
- Synthetic subscription and compliance-document fixtures.
- Deterministic placeholder embedding strategy for pgvector write-path validation.
- Data ingestion and concurrency validation scaffolding.
- Product, architecture, schema, query, reset, and technical interaction documentation.
- Public GitHub repository and phase baseline tag.

### Out of scope for the current scaffold

- Runtime-validated Prisma generation and database migration.
- Production semantic embedding model.
- Fully implemented Neo4j graph projection.
- Fully implemented hybrid retrieval notebook or script.
- FastAPI mock pricing service implementation.
- LangGraph agent workflow implementation.
- Actual HITL UI or production approval workflow.
- Production-grade observability integrations.

## Product roadmap

### Phase 0: Product and architecture foundation

**Product goal:** Establish a stable local product concept, monorepo structure, documentation baseline, and change-tracking process.

**Key outcomes:**

- Users can understand the product vision, architecture, and implementation plan.
- Engineering can track progress through plans, checklist, Git, changelog, and ADRs.
- The system has clear workstream boundaries.

**Status:** Mostly complete.

### Phase 1: Local data foundation and repeatable demo baseline

**Product goal:** Build the typed data layer and repeatable synthetic data environment that all later product capabilities depend on.

**Key outcomes:**

- Users can load deterministic software subscription and compliance evidence fixtures.
- PostgreSQL stores structured subscription data and compliance evidence chunks.
- pgvector stores deterministic placeholder embeddings for infrastructure validation.
- Audit events capture ingestion and concurrency validation.
- Demo reset strategy keeps curated demos repeatable.

**Status:** In progress.

### Phase 2: Hybrid retrieval and evidence-to-cost analysis

**Product goal:** Demonstrate that the product can answer evidence-backed business questions by joining cost, risk, renewal, graph, and document context.

**Key outcomes:**

- Users can run curated positive queries from [`plans/query-scope.md`](../plans/query-scope.md).
- Hybrid retrieval returns vendors, subscriptions, costs, risk categories, and evidence excerpts.
- Neo4j graph traversal links vendors, software, subscriptions, documents, chunks, and risks.
- Query outputs are deterministic enough for repeatable demonstrations.

**Status:** Planned.

### Phase 3: Agentic workflow, mock pricing, and HITL governance

**Product goal:** Turn retrieved evidence and cost context into governed recommendation workflows.

**Key outcomes:**

- Users can request a recommendation for renewal or cancellation review.
- The agent can call a local mock pricing API.
- Recommendations are grounded in retrieval context and pricing data.
- High-risk recommendations pause for human approval before finalization.

**Status:** Planned.

### Phase 4: Observability, governance, and FinOps telemetry

**Product goal:** Prove that the local prototype can support enterprise-grade governance, traceability, and cost accountability.

**Key outcomes:**

- Users can inspect traces, safety flags, token usage, and simulated costs.
- Governance-critical events persist locally in audit records.
- The product is ready for a local reasoning engine integration path, including Microsoft Foundry Local or equivalent local model runtime.

**Status:** Planned.

## Product capabilities by maturity

| Capability | Scaffold | Validated prototype | Future product direction |
|---|---|---|---|
| Subscription data modeling | Prisma schema exists | Runtime validation and ingestion complete | Import from enterprise systems. |
| Compliance evidence ingestion | Synthetic text fixtures exist | Chunking, risk inference, embeddings validated | Vendor-document upload and review workflow. |
| Embeddings | Deterministic placeholder vectors | Real local semantic embedding model | Model selection and retrieval quality monitoring. |
| Retrieval | Planned | Hybrid PostgreSQL plus Neo4j query demo | Interactive query experience. |
| Pricing | Planned mock API | Local FastAPI pricing tool | Integration with procurement or pricing systems. |
| HITL governance | Documented requirement | LangGraph pause and approval state | Role-based approval workflow. |
| Observability | Documented architecture | Local trace and cost logging | Full governance dashboard. |

## Success metrics

### Product success metrics

- A user can identify high-risk AI vendors with renewal cost exposure.
- A user can see evidence excerpts behind each compliance risk.
- A user can distinguish strict high-risk matches from broader cost-weighted review candidates.
- A user can reset the demo and reproduce the same curated query outputs.
- A user can see where HITL approval is required before recommendation finalization.

### Technical success metrics

- Prisma schema generation succeeds.
- PostgreSQL schema application succeeds.
- pgvector extension enablement succeeds.
- Synthetic ingestion completes without schema drift.
- Concurrency validation completes without data corruption.
- Hybrid retrieval returns expected positive matches.
- Audit events are persisted for ingestion, validation, HITL, and recommendations.

## Product risks and mitigations

| Risk | Impact | Mitigation |
|---|---|---|
| Placeholder embeddings are mistaken for semantic embeddings. | Retrieval quality could be overestimated. | Documentation clearly labels them deterministic placeholders. |
| Curated demo data is too narrow. | Product appears demo-only. | Use curated data for baseline, then expand scenarios after validation. |
| Graph and relational data drift. | Retrieval returns inconsistent context. | Use reset and projection rules from [`docs/setup-runbook.md`](setup-runbook.md). |
| Agent recommendations overstep governance boundaries. | Compliance risk. | Enforce HITL before final cancellation or renewal recommendation. |
| Product direction changes are undocumented. | Team loses decision history. | Update this document, [`CHANGELOG.md`](../CHANGELOG.md), and ADRs. |

## Evolution and change-control policy

This document must be updated when any of the following occur:

- Product vision or target users change.
- Roadmap phase ordering changes.
- A feature moves into or out of scope.
- The embedding strategy changes from deterministic placeholder vectors to a real local model.
- The system adds or removes a major technology layer.
- The HITL model changes.
- The demo reset strategy changes.
- The product begins using live enterprise or vendor data instead of synthetic fixtures.
- A roadmap phase is validated and tagged in Git.

Material changes should also update:

- [`CHANGELOG.md`](../CHANGELOG.md) for human-readable history.
- [`docs/adr/`](adr/) for architectural decisions.
- [`plans/implementation-plan-checklist.md`](../plans/implementation-plan-checklist.md) for progress tracking.
- Git commits and tags for versioned traceability.

## Current product baseline

The current baseline is tagged as `phase-0-1-baseline` in Git. It represents the transition from proposal and planning into a scaffolded local product architecture.

The baseline is not yet a fully validated runtime prototype. It is a documented and version-controlled foundation for moving toward Phase 1 validation and Phase 2 hybrid retrieval.
