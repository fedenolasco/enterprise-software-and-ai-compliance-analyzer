"""Pricing fixture loading and lookup helpers."""

import json
from pathlib import Path

from mock_pricing_api.models import PricingLookupResponse, PricingRecord


class PricingRepository:
    """In-memory repository backed by deterministic local JSON pricing data."""

    def __init__(self, fixture_path: Path) -> None:
        self._records = tuple(_load_pricing_records(fixture_path))
        self._by_software_code = {record.software_code: record for record in self._records}

    @property
    def records(self) -> tuple[PricingRecord, ...]:
        """Return all pricing records."""

        return self._records

    def get_by_software_code(self, software_code: str) -> PricingRecord | None:
        """Return one pricing record by software code."""

        return self._by_software_code.get(software_code)

    def lookup(
        self,
        software_code: str,
        requested_seats: int | None = None,
    ) -> PricingLookupResponse | None:
        """Return a pricing lookup response with deterministic volume discount calculation."""

        record = self.get_by_software_code(software_code)
        if record is None:
            return None

        discount_percent = _discount_for_requested_seats(record, requested_seats)
        seats = requested_seats or record.minimum_seats
        annual_total = record.annual_unit_price_usd * seats * (1 - discount_percent / 100)
        return PricingLookupResponse(
            pricing=record,
            requested_seats=requested_seats,
            applied_discount_percent=discount_percent,
            estimated_annual_total_usd=round(annual_total, 2),
        )


def _load_pricing_records(fixture_path: Path) -> list[PricingRecord]:
    payload = json.loads(fixture_path.read_text(encoding="utf-8"))
    records = payload.get("pricing", [])
    return [PricingRecord.model_validate(record) for record in records]


def _discount_for_requested_seats(record: PricingRecord, requested_seats: int | None) -> float:
    if requested_seats is None:
        return 0.0

    eligible_discounts = [
        discount.discount_percent
        for discount in record.volume_discounts
        if requested_seats >= discount.minimum_seats
    ]
    return max(eligible_discounts, default=0.0)
