"""FastAPI application factory for the local mock pricing API."""

from fastapi import FastAPI, HTTPException

from mock_pricing_api.config import MockPricingSettings, get_settings
from mock_pricing_api.models import (
    HealthResponse,
    PricingLookupRequest,
    PricingLookupResponse,
    PricingRecord,
)
from mock_pricing_api.repository import PricingRepository


def create_app(settings: MockPricingSettings | None = None) -> FastAPI:
    """Create the FastAPI app with deterministic local pricing data."""

    active_settings = settings or get_settings()
    repository = PricingRepository(active_settings.pricing_fixture_path)

    app = FastAPI(
        title="Enterprise Software Mock Pricing API",
        version="0.1.0",
        description="Local synthetic pricing API for agent tool-call validation.",
    )

    @app.get("/health", response_model=HealthResponse)
    def health() -> HealthResponse:
        return HealthResponse(status="ok", pricing_records=len(repository.records))

    @app.get("/pricing", response_model=list[PricingRecord])
    def list_pricing() -> tuple[PricingRecord, ...]:
        return repository.records

    @app.get("/pricing/{software_code}", response_model=PricingRecord)
    def get_pricing(software_code: str) -> PricingRecord:
        record = repository.get_by_software_code(software_code)
        if record is None:
            raise HTTPException(status_code=404, detail="Pricing record not found.")
        return record

    @app.post("/pricing:lookup", response_model=PricingLookupResponse)
    def lookup_pricing(request: PricingLookupRequest) -> PricingLookupResponse:
        response = repository.lookup(request.software_code, request.requested_seats)
        if response is None:
            raise HTTPException(status_code=404, detail="Pricing record not found.")
        return response

    return app


app = create_app()
