"""Health check router for service status monitoring."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter

from ui_api.services.health_checker import (
    ServiceName,
    check_all_services,
    check_foundry_local,
    check_langfuse,
    check_neo4j,
    check_phoenix,
    check_postgres,
    check_pricing_api,
)

router = APIRouter(prefix="/api/health", tags=["health"])

_SERVICE_CHECKERS = {
    ServiceName.POSTGRES.value: check_postgres,
    ServiceName.NEO4J.value: check_neo4j,
    ServiceName.PRICING_API.value: check_pricing_api,
    ServiceName.PHOENIX.value: check_phoenix,
    ServiceName.LANGFUSE.value: check_langfuse,
    ServiceName.FOUNDRY_LOCAL.value: check_foundry_local,
}


@router.get("")
async def get_health() -> dict[str, Any]:
    """Get aggregate health of all connected services."""
    services = check_all_services()
    return {
        "services": [s.to_dict() for s in services],
        "summary": {
            "total": len(services),
            "healthy": sum(1 for s in services if s.status.value == "healthy"),
            "unhealthy": sum(1 for s in services if s.status.value == "unhealthy"),
            "disabled": sum(1 for s in services if s.status.value == "disabled"),
        },
    }


@router.get("/{service}")
async def get_service_health(service: str) -> dict[str, Any]:
    """Get health of a specific service."""
    checker = _SERVICE_CHECKERS.get(service)
    if checker is None:
        from fastapi import HTTPException

        raise HTTPException(
            status_code=404,
            detail=f"Unknown service: {service}. Valid services: {list(_SERVICE_CHECKERS.keys())}",
        )
    result = checker()
    return result.to_dict()
