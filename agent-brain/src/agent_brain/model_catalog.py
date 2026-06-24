"""Shared model catalog helpers.

The canonical provider/model alias list lives in ``config/model-catalog.json``
at the repository root. Runtime packages use these helpers for defaults so
aliases do not drift across frontend, backend, and agent code.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def _repo_root() -> Path:
    """Return the repository root from the installed source layout."""

    return Path(__file__).resolve().parents[4]


def load_model_catalog() -> dict[str, Any]:
    """Load the centralized provider model catalog."""

    catalog_path = _repo_root() / "config" / "model-catalog.json"
    if not catalog_path.exists():
        return {"models": []}
    return json.loads(catalog_path.read_text(encoding="utf-8"))


def catalog_default_alias(provider: str, role: str, fallback: str) -> str:
    """Return the default model alias for provider/role from the catalog."""

    models = [
        model
        for model in load_model_catalog().get("models", [])
        if model.get("provider") == provider and model.get("role") == role
    ]
    default = next((model for model in models if model.get("default") is True), None)
    selected = default or (models[0] if models else None)
    return str(selected.get("alias")) if selected else fallback
