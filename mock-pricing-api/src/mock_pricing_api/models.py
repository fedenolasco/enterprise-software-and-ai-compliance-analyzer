"""Typed API models for synthetic software pricing."""

from typing import Literal

from pydantic import BaseModel, Field

BillingCycle = Literal["MONTHLY", "ANNUAL"]


class VolumeDiscount(BaseModel):
    """Simple deterministic discount band for requested seat counts."""

    minimum_seats: int = Field(ge=0)
    discount_percent: float = Field(ge=0.0, le=100.0)


class PricingRecord(BaseModel):
    """Synthetic pricing data for one software product."""

    vendor_code: str
    vendor_name: str
    software_code: str
    software_name: str
    currency: str = "USD"
    billing_cycle: BillingCycle
    list_unit_price_usd: float = Field(ge=0.0)
    annual_unit_price_usd: float = Field(ge=0.0)
    minimum_seats: int = Field(ge=0)
    included_support_tier: str
    data_residency_available: bool
    enterprise_controls_available: bool
    volume_discounts: tuple[VolumeDiscount, ...] = ()
    notes: str


class PricingLookupRequest(BaseModel):
    """Typed lookup request for agent tool calls."""

    software_code: str
    requested_seats: int | None = Field(default=None, ge=0)


class PricingLookupResponse(BaseModel):
    """Typed lookup response returned by the mock pricing tool."""

    pricing: PricingRecord
    requested_seats: int | None = Field(default=None, ge=0)
    applied_discount_percent: float = Field(ge=0.0, le=100.0)
    estimated_annual_total_usd: float = Field(ge=0.0)
    source: str = "mock-pricing-api"


class HealthResponse(BaseModel):
    """Health response for local validation."""

    status: Literal["ok"]
    pricing_records: int
