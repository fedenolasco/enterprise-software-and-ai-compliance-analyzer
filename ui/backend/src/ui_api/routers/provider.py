"""Provider switching router for changing model and embedding providers."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from agent_brain.config import get_settings as get_agent_brain_settings
from ui_api.config import get_settings as get_ui_settings

router = APIRouter(prefix="/api/provider", tags=["provider"])

VALID_MODEL_PROVIDERS = ["placeholder", "microsoft-foundry-local", "openai"]
VALID_EMBEDDING_PROVIDERS = ["placeholder", "microsoft-foundry-local", "openai"]


class SwitchProviderRequest(BaseModel):
    """Request to switch the model or embedding provider."""

    model_provider: str | None = Field(
        default=None, description="New model provider: placeholder, microsoft-foundry-local, or openai."
    )
    embedding_provider: str | None = Field(
        default=None, description="New embedding provider: placeholder, microsoft-foundry-local, or openai."
    )
    openai_api_key: str | None = Field(
        default=None, description="OpenAI API key (required when switching to openai)."
    )


def _update_env_file(updates: dict[str, str]) -> None:
    """Update the .env file with new values."""
    settings = get_ui_settings()
    env_file = settings.repo_root / ".env"

    if not env_file.exists():
        raise HTTPException(
            status_code=500,
            detail=".env file not found. The backend should have created it on startup.",
        )

    # Read current .env content
    lines = env_file.read_text(encoding="utf-8").splitlines()
    env_keys = {line.split("=", 1)[0].strip() for line in lines if "=" in line and not line.startswith("#")}

    # Update existing keys
    updated_lines = []
    for line in lines:
        if "=" in line and not line.startswith("#"):
            key = line.split("=", 1)[0].strip()
            if key in updates:
                updated_lines.append(f"{key}={updates[key]}")
            else:
                updated_lines.append(line)
        else:
            updated_lines.append(line)

    # Add new keys that don't exist yet
    for key, value in updates.items():
        if key not in env_keys:
            updated_lines.append(f"{key}={value}")

    env_file.write_text("\n".join(updated_lines) + "\n", encoding="utf-8")

    # Also update the current process environment so the change takes effect immediately
    for key, value in updates.items():
        os.environ[key] = value


@router.get("")
async def get_provider_info() -> dict[str, Any]:
    """Get current provider configuration and available options."""
    settings = get_agent_brain_settings()
    return {
        "current": {
            "model_provider": settings.model_provider,
            "embedding_provider": settings.embedding_provider,
            "foundry_local_endpoint": settings.foundry_local_endpoint,
            "openai_configured": settings.openai_api_key is not None,
            "openai_model": settings.openai_model,
        },
        "available_model_providers": [
            {
                "value": "placeholder",
                "label": "Placeholder (deterministic, offline)",
                "description": "Uses deterministic placeholder responses. No API key or local model needed. Default for offline validation.",
                "requires_api_key": False,
                "requires_local_runtime": False,
            },
            {
                "value": "microsoft-foundry-local",
                "label": "Microsoft Foundry Local (local AI)",
                "description": "Uses a local Phi-3.5-mini model via Foundry Local. No cloud API needed. Requires Foundry Local installed.",
                "requires_api_key": False,
                "requires_local_runtime": True,
            },
            {
                "value": "openai",
                "label": "OpenAI (cloud API)",
                "description": "Uses gpt-4o-mini via the OpenAI API. Requires an API key. Cloud-dependent.",
                "requires_api_key": True,
                "requires_local_runtime": False,
            },
        ],
        "available_embedding_providers": [
            {
                "value": "placeholder",
                "label": "Placeholder (8-dim deterministic)",
                "description": "Uses deterministic 8-dimensional vectors. No API key needed. Default for offline validation.",
                "requires_api_key": False,
            },
            {
                "value": "microsoft-foundry-local",
                "label": "Foundry Local (384-dim)",
                "description": "Uses all-MiniLM-L6-v2 via Foundry Local. Requires Foundry Local installed.",
                "requires_api_key": False,
            },
            {
                "value": "openai",
                "label": "OpenAI (1536-dim)",
                "description": "Uses text-embedding-3-small via OpenAI API. Requires API key. Note: changing embedding dimension requires schema migration and re-ingestion.",
                "requires_api_key": True,
            },
        ],
    }


@router.post("/switch")
async def switch_provider(request: SwitchProviderRequest) -> dict[str, Any]:
    """Switch the model or embedding provider by updating the .env file."""
    updates: dict[str, str] = {}

    if request.model_provider is not None:
        if request.model_provider not in VALID_MODEL_PROVIDERS:
            raise HTTPException(
                status_code=422,
                detail=f"Invalid model provider: {request.model_provider}. Valid options: {VALID_MODEL_PROVIDERS}",
            )

        # Validate OpenAI provider requires API key
        if request.model_provider == "openai":
            settings = get_agent_brain_settings()
            if not settings.openai_api_key and not request.openai_api_key:
                raise HTTPException(
                    status_code=422,
                    detail="OpenAI API key is required when switching to the openai provider. Provide openai_api_key in the request.",
                )
            if request.openai_api_key:
                updates["OPENAI_API_KEY"] = request.openai_api_key

        updates["MODEL_PROVIDER"] = request.model_provider

    if request.embedding_provider is not None:
        if request.embedding_provider not in VALID_EMBEDDING_PROVIDERS:
            raise HTTPException(
                status_code=422,
                detail=f"Invalid embedding provider: {request.embedding_provider}. Valid options: {VALID_EMBEDDING_PROVIDERS}",
            )

        if request.embedding_provider == "openai":
            settings = get_agent_brain_settings()
            if not settings.openai_api_key and not request.openai_api_key:
                raise HTTPException(
                    status_code=422,
                    detail="OpenAI API key is required when switching to the openai embedding provider.",
                )
            if request.openai_api_key and "OPENAI_API_KEY" not in updates:
                updates["OPENAI_API_KEY"] = request.openai_api_key

        updates["EMBEDDING_PROVIDER"] = request.embedding_provider

    if not updates:
        raise HTTPException(
            status_code=422,
            detail="No provider changes requested. Provide model_provider or embedding_provider.",
        )

    # Update the .env file
    _update_env_file(updates)

    # Read back the updated settings
    # Force reload by clearing any cached settings
    import importlib
    import agent_brain.config as config_module
    importlib.reload(config_module)
    new_settings = config_module.get_settings()

    # Check for embedding dimension mismatch warning
    warnings: list[str] = []
    if request.embedding_provider == "openai" and new_settings.embedding_dimension != 1536:
        warnings.append(
            "Embedding dimension change detected. Switching to OpenAI embeddings (1536-dim) requires "
            "a schema migration, data reset, and re-ingestion. Current dimension is "
            f"{new_settings.embedding_dimension}. Run 'Reset PostgreSQL data' after switching."
        )
    if request.embedding_provider == "microsoft-foundry-local" and new_settings.embedding_dimension != 384:
        warnings.append(
            "Embedding dimension change detected. Foundry Local embeddings use 384-dim. "
            f"Current dimension is {new_settings.embedding_dimension}. A schema migration and re-ingestion may be needed."
        )

    return {
        "success": True,
        "message": "Provider updated successfully. The change takes effect immediately for new workflow runs.",
        "updates": updates,
        "new_settings": {
            "model_provider": new_settings.model_provider,
            "embedding_provider": new_settings.embedding_provider,
        },
        "warnings": warnings,
        "note": "Previous observability data is preserved and tagged with the previous provider. Visit the Observability page to compare providers.",
    }
