"""FastAPI application factory for the UI API."""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from ui_api.config import get_settings
from ui_api.routers import cli, config, data, health, observability, provider, reset, retrieval, services, workflow
from ui_api.websocket.workflow_ws import router as websocket_router


def _ensure_env_file() -> None:
    """Ensure .env file exists before the server starts."""
    import shutil
    from pathlib import Path

    settings = get_settings()
    env_file = settings.repo_root / ".env"
    env_example = settings.repo_root / ".env.example"
    if not env_file.exists() and env_example.exists():
        shutil.copy2(env_example, env_file)
        print(f"Created .env from .env.example at {env_file}")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""

    # Ensure .env file exists before anything else
    _ensure_env_file()

    settings = get_settings()

    app = FastAPI(
        title="Enterprise Software & AI Compliance Analyzer — UI API",
        version="0.1.0",
        description=(
            "FastAPI backend wrapping the agent_brain Python package as REST and "
            "WebSocket endpoints for the compliance analyzer UI."
        ),
    )

    # CORS configuration
    app.add_middleware(
        CORSMiddleware,
        allow_origins=list(settings.cors_origins),
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Register routers
    app.include_router(health.router)
    app.include_router(config.router)
    app.include_router(data.router)
    app.include_router(retrieval.router)
    app.include_router(workflow.router)
    app.include_router(observability.router)
    app.include_router(cli.router)
    app.include_router(reset.router)
    app.include_router(services.router)
    app.include_router(provider.router)
    app.include_router(websocket_router)

    @app.get("/")
    async def root() -> dict[str, str]:
        """Root endpoint with API information."""
        return {
            "name": "Enterprise Software & AI Compliance Analyzer — UI API",
            "version": "0.1.0",
            "docs": "/docs",
            "health": "/api/health",
        }

    return app


# Module-level app instance for uvicorn
app = create_app()
