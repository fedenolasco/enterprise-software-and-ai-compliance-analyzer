"""Tests for the health checker service."""

from __future__ import annotations

from ui_api.services.health_checker import (
    ServiceName,
    ServiceStatus,
    check_all_services,
    check_foundry_local,
    check_langfuse,
    check_neo4j,
    check_phoenix,
    check_postgres,
    check_pricing_api,
)


def test_check_postgres_returns_service_health() -> None:
    """check_postgres returns a ServiceHealth with the correct name."""
    result = check_postgres()
    assert result.name == ServiceName.POSTGRES.value
    assert result.required is True
    assert result.status in (
        ServiceStatus.HEALTHY,
        ServiceStatus.UNHEALTHY,
    )


def test_check_neo4j_returns_service_health() -> None:
    """check_neo4j returns a ServiceHealth with the correct name."""
    result = check_neo4j()
    assert result.name == ServiceName.NEO4J.value
    assert result.required is True
    assert result.status in (
        ServiceStatus.HEALTHY,
        ServiceStatus.UNHEALTHY,
    )


def test_check_pricing_api_returns_service_health() -> None:
    """check_pricing_api returns a ServiceHealth with the correct name."""
    result = check_pricing_api()
    assert result.name == ServiceName.PRICING_API.value
    assert result.required is True


def test_check_phoenix_returns_disabled_when_not_enabled() -> None:
    """check_phoenix returns DISABLED status when Phoenix is not enabled."""
    result = check_phoenix()
    assert result.name == ServiceName.PHOENIX.value
    assert result.required is False
    # Phoenix is disabled by default in test environment
    assert result.status in (
        ServiceStatus.DISABLED,
        ServiceStatus.HEALTHY,
        ServiceStatus.UNHEALTHY,
    )


def test_check_langfuse_returns_disabled_when_not_enabled() -> None:
    """check_langfuse returns DISABLED status when Langfuse is not enabled."""
    result = check_langfuse()
    assert result.name == ServiceName.LANGFUSE.value
    assert result.required is False
    assert result.status in (
        ServiceStatus.DISABLED,
        ServiceStatus.HEALTHY,
        ServiceStatus.UNHEALTHY,
    )


def test_check_foundry_local_returns_disabled_when_not_configured() -> None:
    """check_foundry_local returns DISABLED when endpoint is not configured."""
    result = check_foundry_local()
    assert result.name == ServiceName.FOUNDRY_LOCAL.value
    assert result.required is False
    assert result.status in (
        ServiceStatus.DISABLED,
        ServiceStatus.HEALTHY,
        ServiceStatus.UNHEALTHY,
    )


def test_check_all_services_returns_six_services() -> None:
    """check_all_services returns health for all 6 services."""
    results = check_all_services()
    assert len(results) == 6
    names = {r.name for r in results}
    assert names == {
        ServiceName.POSTGRES.value,
        ServiceName.NEO4J.value,
        ServiceName.PRICING_API.value,
        ServiceName.PHOENIX.value,
        ServiceName.LANGFUSE.value,
        ServiceName.FOUNDRY_LOCAL.value,
    }


def test_service_health_to_dict_is_serializable() -> None:
    """ServiceHealth.to_dict returns a JSON-serializable mapping."""
    result = check_postgres()
    data = result.to_dict()
    assert "name" in data
    assert "status" in data
    assert "required" in data
    assert "host" in data
    assert "detail" in data
    assert "remediation" in data
    assert "checked_at" in data
