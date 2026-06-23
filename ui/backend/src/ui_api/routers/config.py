"""Configuration router for displaying system parameters."""

from __future__ import annotations

from typing import Any
from urllib.parse import urlparse, urlunparse

from fastapi import APIRouter

from agent_brain.config import get_settings as get_agent_brain_settings

router = APIRouter(prefix="/api/config", tags=["config"])

# Metadata for each config parameter: category, description, and whether it is editable
_CONFIG_METADATA: dict[str, dict[str, str]] = {
    "database_url": {
        "category": "Database",
        "description": "The PostgreSQL connection string. Defaults to a local Docker container.",
        "editable": "false",
        "sensitive": "true",
    },
    "neo4j_uri": {
        "category": "Graph",
        "description": "The Neo4j Bolt URI for graph database connectivity.",
        "editable": "false",
    },
    "neo4j_username": {
        "category": "Graph",
        "description": "The Neo4j username for authentication.",
        "editable": "false",
    },
    "neo4j_password": {
        "category": "Graph",
        "description": "The Neo4j password for authentication.",
        "editable": "false",
        "sensitive": "true",
    },
    "mock_pricing_api_url": {
        "category": "Pricing API",
        "description": "The base URL for the Mock Pricing API service.",
        "editable": "false",
    },
    "embedding_dimension": {
        "category": "Embeddings",
        "description": "The dimensionality of embedding vectors. Changing this requires a schema migration and re-ingestion.",
        "editable": "false",
    },
    "embedding_model": {
        "category": "Embeddings",
        "description": "The name of the embedding model being used.",
        "editable": "false",
    },
    "embedding_provider": {
        "category": "Embeddings",
        "description": "The provider for embedding generation: 'placeholder' (deterministic), 'openai', 'microsoft-foundry-local', or 'openvino'.",
        "editable": "false",
    },
    "vector_top_k": {
        "category": "Retrieval",
        "description": "Maximum number of vector search results to retrieve from PostgreSQL.",
        "editable": "false",
    },
    "graph_result_limit": {
        "category": "Retrieval",
        "description": "Maximum number of graph traversal rows to return from Neo4j.",
        "editable": "false",
    },
    "model_provider": {
        "category": "Model",
        "description": "The LLM provider: 'placeholder' (deterministic), 'microsoft-foundry-local', 'openvino', or 'openai'.",
        "editable": "false",
    },
    "foundry_local_endpoint": {
        "category": "Model",
        "description": "The endpoint URL for Microsoft Foundry Local. None if not configured.",
        "editable": "false",
    },
    "local_model_name": {
        "category": "Model",
        "description": "The name of the local model used for responses.",
        "editable": "false",
    },
    "openvino_endpoint": {
        "category": "OpenVINO",
        "description": "The OpenVINO Model Server endpoint. Defaults to http://localhost:8100 to avoid the mock Pricing API on port 8000.",
        "editable": "false",
    },
    "openvino_model": {
        "category": "OpenVINO",
        "description": "The OpenVINO text-generation model ID for local inference.",
        "editable": "false",
    },
    "openvino_embedding_model": {
        "category": "OpenVINO",
        "description": "The OpenVINO embedding model ID for local semantic embeddings.",
        "editable": "false",
    },
    "openvino_device": {
        "category": "OpenVINO",
        "description": "The OpenVINO target device: NPU, GPU, or CPU.",
        "editable": "false",
    },
    "hf_token": {
        "category": "OpenVINO",
        "description": "Optional Hugging Face token for gated/private models or higher download limits. Public OpenVINO models do not require it.",
        "editable": "false",
        "sensitive": "true",
    },
    "openai_api_key": {
        "category": "Model",
        "description": "The OpenAI API key. None if not configured.",
        "editable": "false",
        "sensitive": "true",
    },
    "openai_model": {
        "category": "Model",
        "description": "The OpenAI model name to use for LLM responses.",
        "editable": "false",
    },
    "openai_base_url": {
        "category": "Model",
        "description": "The OpenAI API base URL.",
        "editable": "false",
    },
    "phoenix_enabled": {
        "category": "Observability",
        "description": "Whether Phoenix observability tracing is enabled.",
        "editable": "false",
    },
    "phoenix_endpoint": {
        "category": "Observability",
        "description": "The Phoenix HTTP endpoint URL.",
        "editable": "false",
    },
    "phoenix_grpc_endpoint": {
        "category": "Observability",
        "description": "The Phoenix gRPC endpoint URL for OTLP export.",
        "editable": "false",
    },
    "langfuse_enabled": {
        "category": "Observability",
        "description": "Whether Langfuse observability is enabled.",
        "editable": "false",
    },
    "langfuse_host": {
        "category": "Observability",
        "description": "The Langfuse host URL.",
        "editable": "false",
    },
    "langfuse_public_key": {
        "category": "Observability",
        "description": "The Langfuse public key. None if not configured.",
        "editable": "false",
        "sensitive": "true",
    },
    "langfuse_secret_key": {
        "category": "Observability",
        "description": "The Langfuse secret key. None if not configured.",
        "editable": "false",
        "sensitive": "true",
    },
}


def _mask_sensitive(value: object) -> str:
    """Mask sensitive values for display.

    Uses a fixed number of asterisks so the masked representation does not grow
    with the value length (which previously caused layout overlap in the UI).
    """
    if value is None:
        return "None"
    value_str = str(value)
    if not value_str:
        return ""
    if len(value_str) <= 4:
        return "*" * len(value_str)
    return value_str[:2] + "****" + value_str[-2:]


def _mask_connection_string(value: object) -> str:
    """Mask credentials in a database/connection URL while keeping host and path visible.

    For example ``postgresql://user:password@host:5432/db?schema=public`` becomes
    ``postgresql://user:****@host:5432/db?schema=public``. Falls back to
    :func:`_mask_sensitive` if the value cannot be parsed as a URL.
    """
    if value is None:
        return "None"
    value_str = str(value)
    if not value_str:
        return ""
    try:
        parsed = urlparse(value_str)
    except ValueError:
        return _mask_sensitive(value_str)
    # Only redact when there is userinfo to redact.
    if parsed.username:
        # Preserve the username but replace the password with a fixed mask.
        userinfo = parsed.username
        if parsed.password is not None:
            userinfo += ":****"
        # Rebuild netloc preserving port.
        host = parsed.hostname or ""
        if parsed.port:
            host = f"{host}:{parsed.port}"
        masked = parsed._replace(netloc=f"{userinfo}@{host}" if host else userinfo)
        return urlunparse(masked)
    return value_str


@router.get("")
async def get_config() -> dict[str, Any]:
    """Get all configuration parameters with metadata."""
    settings = get_agent_brain_settings()
    parameters = []
    for field_name in sorted(_CONFIG_METADATA.keys()):
        metadata = _CONFIG_METADATA[field_name]
        raw_value = getattr(settings, field_name, None)
        is_sensitive = metadata.get("sensitive", "false") == "true"
        if is_sensitive:
            # Connection strings get dedicated masking that keeps host/db visible.
            if field_name == "database_url":
                display_value = _mask_connection_string(raw_value)
            else:
                display_value = _mask_sensitive(raw_value)
        else:
            display_value = str(raw_value)
        parameters.append(
            {
                "name": field_name,
                "value": display_value,
                "category": metadata["category"],
                "description": metadata["description"],
                "editable": metadata.get("editable", "false") == "true",
                "sensitive": is_sensitive,
                "is_none": raw_value is None,
            }
        )

    # Group by category
    categories: dict[str, list[dict[str, Any]]] = {}
    for param in parameters:
        cat = param["category"]
        if cat not in categories:
            categories[cat] = []
        categories[cat].append(param)

    return {
        "parameters": parameters,
        "categories": categories,
        "model_provider": settings.model_provider,
        "embedding_provider": settings.embedding_provider,
        "phoenix_enabled": settings.phoenix_enabled,
        "langfuse_enabled": settings.langfuse_enabled,
        "foundry_local_configured": settings.foundry_local_endpoint is not None,
        "openai_configured": settings.openai_api_key is not None,
    }
