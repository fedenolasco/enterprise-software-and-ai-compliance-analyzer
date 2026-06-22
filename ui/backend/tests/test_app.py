"""Tests for the FastAPI application."""

from __future__ import annotations

from fastapi.testclient import TestClient

from ui_api.app import create_app


def test_app_creates_successfully() -> None:
    """create_app returns a FastAPI instance."""
    app = create_app()
    assert app is not None


def test_root_endpoint_returns_api_info() -> None:
    """The root endpoint returns API information."""
    app = create_app()
    client = TestClient(app)
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "name" in data
    assert "version" in data
    assert "docs" in data
    assert "health" in data


def test_health_endpoint_returns_service_list() -> None:
    """The /api/health endpoint returns a list of services."""
    app = create_app()
    client = TestClient(app)
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert "services" in data
    assert "summary" in data
    assert data["summary"]["total"] == 6


def test_config_endpoint_returns_parameters() -> None:
    """The /api/config endpoint returns configuration parameters."""
    app = create_app()
    client = TestClient(app)
    response = client.get("/api/config")
    assert response.status_code == 200
    data = response.json()
    assert "parameters" in data
    assert "categories" in data
    assert "model_provider" in data
    assert "embedding_provider" in data


def test_cli_endpoint_returns_command_list() -> None:
    """The /api/cli endpoint returns available CLI commands."""
    app = create_app()
    client = TestClient(app)
    response = client.get("/api/cli")
    assert response.status_code == 200
    data = response.json()
    assert "commands" in data
    assert len(data["commands"]) == 6


def test_reset_preview_endpoint_returns_options() -> None:
    """The /api/reset/preview endpoint returns reset options."""
    app = create_app()
    client = TestClient(app)
    response = client.get("/api/reset/preview")
    assert response.status_code == 200
    data = response.json()
    assert "current_counts" in data
    assert "reset_options" in data
    assert "full" in data["reset_options"]
    assert "postgresql" in data["reset_options"]
    assert "graph" in data["reset_options"]
    assert "pricing" in data["reset_options"]
    assert "audit" in data["reset_options"]
    assert "workflow-state" in data["reset_options"]
