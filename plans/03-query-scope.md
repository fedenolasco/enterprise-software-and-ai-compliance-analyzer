# Phase 2 Curated Query Scope

## Purpose

This document defines the curated query inputs for the Phase 2 hybrid retrieval demo described in [`plans/01-implementation-plan.md`](01-implementation-plan.md). The goal is to make the notebook or script deterministic, demonstrable, and aligned with the current synthetic data rather than dependent on arbitrary natural-language questions.

Documenting this now is worthwhile because the current context is known: the synthetic subscription data, vendor risk tiers, renewal dates, cost fields, compliance text fixtures, Prisma entities, and planned Neo4j relationships already define clear positive scenarios. Capturing the query scope now prevents future mismatch between demo questions and sample data.

## Source data expected by the queries

### Structured subscription data

The structured fixtures in [`database-layer/data/subscriptions.json`](../database-layer/data/subscriptions.json) currently include:

| Vendor | Vendor code | AI risk tier | Software | Annual cost USD | Renewal date | Status | Positive scenario role |
|---|---|---:|---|---:|---|---|---|
| OpenAI Enterprise | `VND-OPENAI-001` | `HIGH` | ChatGPT Enterprise | `43200` | `2026-10-15` | `ACTIVE` | High-risk AI vendor with material renewal exposure. |
| Microsoft 365 Copilot | `VND-MICROSOFT-001` | `MEDIUM` | Microsoft 365 Copilot | `90000` | `2026-09-01` | `ACTIVE` | High-cost comparison case with document-derived governance risk. |
| Notion AI | `VND-NOTION-001` | `HIGH` | Notion AI | `17280` | `2026-07-01` | `PENDING_RENEWAL` | High-risk AI vendor with pending renewal and underutilization signal. |

### Unstructured compliance corpus

The document fixtures under [`database-layer/data/documents/`](../database-layer/data/documents/) intentionally contain phrases that should trigger positive semantic matches:

| Document | Positive evidence terms | Intended risk categories |
|---|---|---|
| [`database-layer/data/documents/openai-enterprise-sla.txt`](../database-layer/data/documents/openai-enterprise-sla.txt) | cross-border transfers, outside the EU, subprocessors, third-party model infrastructure | `DATA_RESIDENCY`, `SUBPROCESSOR_RISK` |
| [`database-layer/data/documents/openai-gdpr-policy.txt`](../database-layer/data/documents/openai-gdpr-policy.txt) | deletion, erasure, retention, outside the EEA, automated decision making | `DATA_RETENTION`, `DATA_RESIDENCY`, `AUTOMATED_DECISION_MAKING` |
| [`database-layer/data/documents/microsoft-copilot-dpa.txt`](../database-layer/data/documents/microsoft-copilot-dpa.txt) | cross-border transfer, subprocessor categories, security controls | `DATA_RESIDENCY`, `SUBPROCESSOR_RISK`, `SECURITY_CONTROLS` |
| [`database-layer/data/documents/microsoft-copilot-ai-policy.txt`](../database-layer/data/documents/microsoft-copilot-ai-policy.txt) | recommendations, high-impact workflows, profiling, automated decision support | `AUTOMATED_DECISION_MAKING`, `MODEL_TRANSPARENCY` |
| [`database-layer/data/documents/notion-ai-sla.txt`](../database-layer/data/documents/notion-ai-sla.txt) | subprocessors, third-party model providers, outside the EU | `SUBPROCESSOR_RISK`, `DATA_RESIDENCY` |
| [`database-layer/data/documents/notion-ai-gdpr-policy.txt`](../database-layer/data/documents/notion-ai-gdpr-policy.txt) | retention, automated decision making, profiling, international transfer safeguards | `DATA_RETENTION`, `AUTOMATED_DECISION_MAKING`, `DATA_RESIDENCY` |
| [`database-layer/data/documents/vendor-risk-register.txt`](../database-layer/data/documents/vendor-risk-register.txt) | OpenAI cross-border support, Microsoft profiling, Notion non-EU processing | Multi-vendor validation evidence |

## Query design principle

The demo query set should use two coordinated inputs:

1. Structured filters over relational subscription and vendor fields.
2. Semantic query phrases over embedded document chunks.

This ensures the demo proves the project’s central use case: connecting cost, renewal exposure, AI risk posture, and compliance evidence without leaving the local data environment.

## Curated positive demo queries

### Query 1: High-risk AI vendors with renewal cost exposure

**Natural-language prompt:**

```text
Which high-risk AI vendors have active or pending renewal exposure, and what compliance evidence should be reviewed before renewal?
```

**Structured filters:**

```text
Vendor.aiRiskTier = HIGH
Subscription.status IN (ACTIVE, PENDING_RENEWAL)
Subscription.annualCostUsd > 0
Subscription.renewalDate IS NOT NULL
```

**Semantic phrase:**

```text
cross-border processing outside the EU subprocessors automated decision making retention
```

**Expected positive matches:**

| Vendor | Why it should match |
|---|---|
| OpenAI Enterprise | `HIGH` risk tier, annual cost, active renewal, cross-border and subprocessor evidence. |
| Notion AI | `HIGH` risk tier, pending renewal, annual cost, subprocessor and non-EU processing evidence. |

**Expected non-primary comparison:**

| Vendor | Why it may appear only as supporting context |
|---|---|
| Microsoft 365 Copilot | `MEDIUM` risk tier excludes it from the strict structured filter, but document chunks may match governance-risk semantic text. |

### Query 2: Cost-weighted compliance review queue

**Natural-language prompt:**

```text
Prioritize AI software renewals for compliance review based on annual cost, renewal date, and high-severity evidence.
```

**Structured filters:**

```text
Subscription.annualCostUsd DESC
Subscription.status IN (ACTIVE, PENDING_RENEWAL)
```

**Semantic phrase:**

```text
high-impact workflow profiling automated decision support subprocessor cross-border transfer
```

**Expected positive matches:**

| Vendor | Why it should match |
|---|---|
| Microsoft 365 Copilot | Highest annual cost and evidence about profiling or automated decision support. |
| OpenAI Enterprise | High risk, material annual cost, cross-border and subprocessor evidence. |
| Notion AI | Pending renewal with non-EU processing and subprocessor evidence. |

### Query 3: Data residency and international transfer exposure

**Natural-language prompt:**

```text
Which vendors have evidence of cross-border processing, outside-EU processing, or international transfer safeguards?
```

**Structured filters:**

```text
Subscription.status != CANCELLED
```

**Semantic phrase:**

```text
cross-border outside the EU outside the EEA international transfer safeguards
```

**Expected positive matches:**

| Vendor | Evidence source |
|---|---|
| OpenAI Enterprise | [`database-layer/data/documents/openai-enterprise-sla.txt`](../database-layer/data/documents/openai-enterprise-sla.txt), [`database-layer/data/documents/openai-gdpr-policy.txt`](../database-layer/data/documents/openai-gdpr-policy.txt) |
| Microsoft 365 Copilot | [`database-layer/data/documents/microsoft-copilot-dpa.txt`](../database-layer/data/documents/microsoft-copilot-dpa.txt) |
| Notion AI | [`database-layer/data/documents/notion-ai-sla.txt`](../database-layer/data/documents/notion-ai-sla.txt), [`database-layer/data/documents/notion-ai-gdpr-policy.txt`](../database-layer/data/documents/notion-ai-gdpr-policy.txt) |

### Query 4: HITL-required cancellation or renewal recommendation candidates

**Natural-language prompt:**

```text
Which AI subscriptions should require human approval before any cancellation or renewal recommendation is finalized?
```

**Structured filters:**

```text
Vendor.aiRiskTier IN (HIGH, CRITICAL)
OR ComplianceRisk.severity IN (HIGH, CRITICAL)
OR Subscription.annualCostUsd >= 25000
OR Subscription.status = PENDING_RENEWAL
```

**Semantic phrase:**

```text
automated decision making profiling high-impact workflows subprocessors non-EU processing
```

**Expected positive matches:**

| Vendor | HITL rationale |
|---|---|
| OpenAI Enterprise | High AI risk tier, material spend, automated-decision and cross-border evidence. |
| Microsoft 365 Copilot | Highest spend and profiling or automated decision-support governance language. |
| Notion AI | High AI risk tier, pending renewal, non-EU processing, subprocessor evidence, and underutilization signal. |

## Expected result shape

The notebook or script should return rows shaped like this:

| Field | Description |
|---|---|
| `vendor_name` | Vendor matched through structured, graph, or semantic retrieval. |
| `software_name` | Software product linked to the vendor. |
| `subscription_code` | Subscription identifier from relational data. |
| `annual_cost_usd` | Annualized financial exposure. |
| `renewal_date` | Renewal deadline used for prioritization. |
| `subscription_status` | Active, pending renewal, trial, or cancelled state. |
| `risk_tier` | Vendor-level AI risk tier. |
| `risk_category` | Evidence-derived risk category. |
| `risk_severity` | Evidence-derived severity. |
| `evidence_excerpt` | Matching document chunk excerpt. |
| `source_document` | Document path or title. |
| `recommended_review_action` | Renewal review, governance review, data residency review, or HITL-required decision. |

## Suggested deterministic ranking logic

For the first implementation, deterministic ranking is preferable to model-generated ranking.

```text
priority_score =
  ai_risk_weight
  + evidence_severity_weight
  + annual_cost_weight
  + renewal_urgency_weight
  + pending_renewal_bonus
```

Recommended initial weights:

| Signal | Weight rule |
|---|---|
| Vendor AI risk tier | `HIGH = 30`, `CRITICAL = 40`, `MEDIUM = 15`, `LOW = 5` |
| Evidence severity | `CRITICAL = 30`, `HIGH = 20`, `MEDIUM = 10`, `LOW = 3` |
| Annual cost | `annualCostUsd / 5000`, capped at `25` |
| Renewal urgency | More points for nearer renewal dates. |
| Pending renewal status | Add `15` when `status = PENDING_RENEWAL`. |

## Why documenting this now matters

- The synthetic fixtures already contain deliberate positive signals, so the query scope can be captured accurately now.
- The Phase 2 demo can be built against clear expected results instead of reverse-engineering examples later.
- The query scope becomes a contract between data generation, ingestion, vector retrieval, graph traversal, and agent orchestration.
- It helps future tests assert that OpenAI, Notion, and Microsoft each appear for the right reasons.
- It keeps the notebook/script focused on proving the use case rather than exploring arbitrary questions.

## Implementation guidance

The Phase 2 notebook or script should:

- Load curated query definitions from code or a small local fixture.
- Run structured relational filtering against PostgreSQL.
- Run semantic search against `DocumentChunk.embedding`.
- Traverse graph relationships in Neo4j from evidence chunks to vendors, software, and subscriptions.
- Merge results into the expected result shape.
- Assert expected positive matches for each curated query.
- Print both matched records and an explanation of why each record matched.
