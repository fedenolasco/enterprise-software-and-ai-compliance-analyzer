from mock_pricing_api.config import DEFAULT_PRICING_FIXTURE_PATH
from mock_pricing_api.repository import PricingRepository


def test_repository_loads_fixture_records() -> None:
    repository = PricingRepository(DEFAULT_PRICING_FIXTURE_PATH)

    assert len(repository.records) == 3
    assert repository.get_by_software_code("SW-MS-COPILOT-M365") is not None


def test_lookup_uses_minimum_seats_when_requested_seats_are_omitted() -> None:
    repository = PricingRepository(DEFAULT_PRICING_FIXTURE_PATH)
    response = repository.lookup("SW-NOTION-AI")

    assert response is not None
    assert response.requested_seats is None
    assert response.estimated_annual_total_usd == 2160.0
