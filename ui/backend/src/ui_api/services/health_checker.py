"""Service health checking for all connected interfaces."""

from __future__ import annotations

import asyncio
import socket
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

import httpx

from agent_brain.config import get_settings as get_agent_brain_settings


class ServiceName(StrEnum):
    """Names of all services the UI monitors."""

    POSTGRES = "postgres"
    NEO4J = "neo4j"
    PRICING_API = "pricing-api"
    PHOENIX = "phoenix"
    LANGFUSE = "langfuse"
    FOUNDRY_LOCAL = "foundry-local"


class ServiceStatus(StrEnum):
    """Health status values for a service."""

    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"
    DISABLED = "disabled"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class ServiceHealth:
    """Health check result for a single service."""

    name: str
    status: ServiceStatus
    required: bool
    host: str
    port: int | None
    detail: str
    remediation: str
    checked_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-serializable mapping."""
        return {
            "name": self.name,
            "status": self.status.value,
            "required": self.required,
            "host": self.host,
            "port": self.port,
            "detail": self.detail,
            "remediation": self.remediation,
            "checked_at": self.checked_at,
        }


def _check_tcp(host: str, port: int, timeout: float = 3.0) -> bool:
    """Check if a TCP port is reachable."""
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except (OSError, socket.timeout):
        return False


def _check_http(url: str, timeout: float = 3.0) -> tuple[bool, str]:
    """Check if an HTTP endpoint is reachable. Returns (success, detail)."""
    try:
        response = httpx.get(url, timeout=timeout)
        if response.status_code < 400:
            return True, f"HTTP {response.status_code}"
        return False, f"HTTP {response.status_code}"
    except httpx.RequestError as exc:
        return False, str(exc)


def check_postgres() -> ServiceHealth:
    """Check PostgreSQL connectivity."""
    settings = get_agent_brain_settings()
    # Parse host and port from database_url
    db_url = settings.database_url
    host = "localhost"
    port = 5432
    if "@" in db_url:
        parts = db_url.split("@", 1)[1]
        if ":" in parts:
            host_port = parts.split("/", 1)[0]
            if ":" in host_port:
                host, port_str = host_port.rsplit(":", 1)
                try:
                    port = int(port_str)
                except ValueError:
                    pass

    if _check_tcp(host, port):
        return ServiceHealth(
            name=ServiceName.POSTGRES.value,
            status=ServiceStatus.HEALTHY,
            required=True,
            host=host,
            port=port,
            detail="Running and accepting connections on port " + str(port),
            remediation="",
        )
    return ServiceHealth(
        name=ServiceName.POSTGRES.value,
        status=ServiceStatus.UNHEALTHY,
        required=True,
        host=host,
        port=port,
        detail="Connection refused",
        remediation="Start PostgreSQL: docker compose up postgres",
    )


def check_neo4j() -> ServiceHealth:
    """Check Neo4j connectivity."""
    settings = get_agent_brain_settings()
    # Parse host and port from neo4j_uri
    uri = settings.neo4j_uri
    host = "localhost"
    port = 7687
    if "://" in uri:
        parts = uri.split("://", 1)[1]
        if ":" in parts:
            host, port_str = parts.split(":", 1)
            try:
                port = int(port_str)
            except ValueError:
                pass
        else:
            host = parts

    if _check_tcp(host, port):
        return ServiceHealth(
            name=ServiceName.NEO4J.value,
            status=ServiceStatus.HEALTHY,
            required=True,
            host=host,
            port=port,
            detail="Running and accepting connections on port " + str(port),
            remediation="",
        )
    return ServiceHealth(
        name=ServiceName.NEO4J.value,
        status=ServiceStatus.UNHEALTHY,
        required=True,
        host=host,
        port=port,
        detail="Connection refused",
        remediation="Start Neo4j: docker compose up neo4j",
    )


def check_pricing_api() -> ServiceHealth:
    """Check Mock Pricing API connectivity."""
    settings = get_agent_brain_settings()
    base_url = settings.mock_pricing_api_url
    health_url = f"{base_url}/health"

    success, detail = _check_http(health_url)
    if success:
        return ServiceHealth(
            name=ServiceName.PRICING_API.value,
            status=ServiceStatus.HEALTHY,
            required=True,
            host=base_url,
            port=None,
            detail="Running and responding to health checks at " + base_url,
            remediation="",
        )
    return ServiceHealth(
        name=ServiceName.PRICING_API.value,
        status=ServiceStatus.UNHEALTHY,
        required=True,
        host=base_url,
        port=None,
        detail=detail,
        remediation="Start pricing API: cd mock-pricing-api && python -m mock_pricing_api.main",
    )


def check_phoenix() -> ServiceHealth:
    """Check Phoenix observability connectivity."""
    settings = get_agent_brain_settings()
    if not settings.phoenix_enabled:
        return ServiceHealth(
            name=ServiceName.PHOENIX.value,
            status=ServiceStatus.DISABLED,
            required=False,
            host=settings.phoenix_endpoint,
            port=None,
            detail="Phoenix is not enabled (PHOENIX_ENABLED=false)",
            remediation=(
                "To enable Phoenix: set PHOENIX_ENABLED=true and run "
                "docker compose --profile observability up"
            ),
        )

    success, detail = _check_http(settings.phoenix_endpoint)
    if success:
        return ServiceHealth(
            name=ServiceName.PHOENIX.value,
            status=ServiceStatus.HEALTHY,
            required=False,
            host=settings.phoenix_endpoint,
            port=None,
            detail="Running and accessible at " + settings.phoenix_endpoint,
            remediation="",
        )
    return ServiceHealth(
        name=ServiceName.PHOENIX.value,
        status=ServiceStatus.UNHEALTHY,
        required=False,
        host=settings.phoenix_endpoint,
        port=None,
        detail=detail,
        remediation=(
            "Phoenix is enabled but unreachable. Start it with: "
            "docker compose --profile observability up"
        ),
    )


def check_langfuse() -> ServiceHealth:
    """Check Langfuse observability connectivity."""
    settings = get_agent_brain_settings()
    if not settings.langfuse_enabled:
        return ServiceHealth(
            name=ServiceName.LANGFUSE.value,
            status=ServiceStatus.DISABLED,
            required=False,
            host=settings.langfuse_host,
            port=None,
            detail="Langfuse is not enabled (LANGFUSE_ENABLED=false)",
            remediation=(
                "To enable Langfuse: set LANGFUSE_ENABLED=true and run "
                "docker compose --profile observability up"
            ),
        )

    success, detail = _check_http(settings.langfuse_host)
    if success:
        return ServiceHealth(
            name=ServiceName.LANGFUSE.value,
            status=ServiceStatus.HEALTHY,
            required=False,
            host=settings.langfuse_host,
            port=None,
            detail="Running and accessible at " + settings.langfuse_host,
            remediation="",
        )
    return ServiceHealth(
        name=ServiceName.LANGFUSE.value,
        status=ServiceStatus.UNHEALTHY,
        required=False,
        host=settings.langfuse_host,
        port=None,
        detail=detail,
        remediation=(
            "Langfuse is enabled but unreachable. Start it with: "
            "docker compose --profile observability up"
        ),
    )


def check_foundry_local() -> ServiceHealth:
    """Check Microsoft Foundry Local connectivity."""
    settings = get_agent_brain_settings()
    endpoint = settings.foundry_local_endpoint

    # Foundry Local is only relevant when MODEL_PROVIDER is set to microsoft-foundry-local
    if settings.model_provider != "microsoft-foundry-local":
        return ServiceHealth(
            name=ServiceName.FOUNDRY_LOCAL.value,
            status=ServiceStatus.DISABLED,
            required=False,
            host="not in use",
            port=None,
            detail=(
                f"Foundry Local is not in use (MODEL_PROVIDER={settings.model_provider}). "
                f"Switch to 'microsoft-foundry-local' on the Configuration page to use it."
            ),
            remediation=(
                "To use Foundry Local: set MODEL_PROVIDER=microsoft-foundry-local "
                "and ensure Foundry Local is installed and running."
            ),
        )

    if not endpoint:
        return ServiceHealth(
            name=ServiceName.FOUNDRY_LOCAL.value,
            status=ServiceStatus.DISABLED,
            required=False,
            host="not configured",
            port=None,
            detail="Foundry Local endpoint is not configured (FOUNDRY_LOCAL_ENDPOINT not set)",
            remediation=(
                "Set FOUNDRY_LOCAL_ENDPOINT=http://localhost:5272/v1 in the .env file."
            ),
        )

    success, detail = _check_http(endpoint)
    if success:
        return ServiceHealth(
            name=ServiceName.FOUNDRY_LOCAL.value,
            status=ServiceStatus.HEALTHY,
            required=False,
            host=endpoint,
            port=None,
            detail="Running and responding at " + endpoint,
            remediation="",
        )
    return ServiceHealth(
        name=ServiceName.FOUNDRY_LOCAL.value,
        status=ServiceStatus.UNHEALTHY,
        required=False,
        host=endpoint,
        port=None,
        detail=detail,
        remediation=(
            "Foundry Local endpoint is configured but unreachable. "
            "Ensure Foundry Local is running."
        ),
    )


def check_all_services() -> list[ServiceHealth]:
    """Check all services and return their health status."""
    return [
        check_postgres(),
        check_neo4j(),
        check_pricing_api(),
        check_phoenix(),
        check_langfuse(),
        check_foundry_local(),
    ]


async def check_all_services_async() -> list[ServiceHealth]:
    """Check all services concurrently."""
    loop = asyncio.get_event_loop()
    tasks = [
        loop.run_in_executor(None, check_postgres),
        loop.run_in_executor(None, check_neo4j),
        loop.run_in_executor(None, check_pricing_api),
        loop.run_in_executor(None, check_phoenix),
        loop.run_in_executor(None, check_langfuse),
        loop.run_in_executor(None, check_foundry_local),
    ]
    return await asyncio.gather(*tasks)
