# Mock Pricing API Contract

## Purpose

This document defines the Phase 3 mock pricing API contract for local agent tool-use validation. The implementation is REST-first with FastAPI, but the resource model is intentionally GraphQL-style: strongly typed objects, explicit lookup inputs, predictable response shapes, and no ambiguous free-form pricing fields.

The API is local-only and serves synthetic data from [`mock-pricing-api/src/mock_pricing_api/data/pricing.json`](../mock-pricing-api/src/mock_pricing_api/data/pricing.json). It must not call external vendor pricing systems.

## Runtime

- Service folder: [`mock-pricing-api/`](../mock-pricing-api/)
- Default base URL: `http://127.0.0.1:8000`
- Local runner: [`mock_pricing_api.main`](../mock-pricing-api/src/mock_pricing_api/main.py)
- FastAPI app factory: [`create_app()`](../mock-pricing-api/src/mock_pricing_api/app.py)

## REST endpoints

| Method | Path | Purpose |
|---|---|---|
| `GET` | `/health` | Confirm service health and loaded fixture count. |
| `GET` | `/pricing` | Return all synthetic pricing records. |
| `GET` | `/pricing/{software_code}` | Return one pricing record by software code. |
| `POST` | `/pricing:lookup` | Return one pricing record with deterministic requested-seat estimate. |

## GraphQL-style type model

The first implementation does not expose a GraphQL endpoint. These type definitions document the intended strongly typed contract that future tool wrappers and agent state should treat as stable.

```graphql
enum BillingCycle {
  MONTHLY
  ANNUAL
}

type VolumeDiscount {
  minimumSeats: Int!
  discountPercent: Float!
}

type PricingRecord {
  vendorCode: String!
  vendorName: String!
  softwareCode: String!
  softwareName: String!
  currency: String!
  billingCycle: BillingCycle!
  listUnitPriceUsd: Float!
  annualUnitPriceUsd: Float!
  minimumSeats: Int!
  includedSupportTier: String!
  dataResidencyAvailable: Boolean!
  enterpriseControlsAvailable: Boolean!
  volumeDiscounts: [VolumeDiscount!]!
  notes: String!
}

input PricingLookupInput {
  softwareCode: String!
  requestedSeats: Int
}

type PricingLookupResult {
  pricing: PricingRecord!
  requestedSeats: Int
  appliedDiscountPercent: Float!
  estimatedAnnualTotalUsd: Float!
  source: String!
}

type Query {
  pricing: [PricingRecord!]!
  pricingBySoftwareCode(softwareCode: String!): PricingRecord
  lookupPricing(input: PricingLookupInput!): PricingLookupResult
}
```

## Deterministic lookup rules

[`PricingRepository.lookup()`](../mock-pricing-api/src/mock_pricing_api/repository.py) applies deterministic pricing rules:

1. Match the `software_code` exactly.
2. If `requested_seats` is omitted, estimate using `minimum_seats` and no discount.
3. If `requested_seats` is present, apply the highest eligible volume discount where `requested_seats >= minimum_seats`.
4. Calculate `estimated_annual_total_usd` as `annual_unit_price_usd * seats * (1 - discount / 100)`.
5. Round the estimate to two decimal places.

## Current synthetic records

The fixture contains pricing for the same software products used in the Phase 2 retrieval demo:

| Software code | Vendor | Product |
|---|---|---|
| `SW-OPENAI-CHATGPT-ENT` | OpenAI Enterprise | ChatGPT Enterprise |
| `SW-MS-COPILOT-M365` | Microsoft 365 Copilot | Microsoft 365 Copilot |
| `SW-NOTION-AI` | Notion AI | Notion AI |

## Validation commands

Run these from [`mock-pricing-api/`](../mock-pricing-api/):

```powershell
python -m pytest
python -m ruff check src tests
python -m mypy src
```

## Tool-use guidance

Future agent tool wrappers should call `POST /pricing:lookup` rather than scraping all pricing records. The wrapper should pass the `software_code` from retrieval context and, when available, use subscription seats as `requested_seats`.

The response must be treated as synthetic local data for demonstration only. It is suitable for validating tool calls, recommendation drafting, and HITL gating, but it is not a live vendor quote.
