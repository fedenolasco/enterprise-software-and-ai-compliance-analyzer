"""Configuration for the UI API backend."""

from __future__ import annotations

import sys
from dataclasses import dataclass
from os import getenv
from pathlib import Path

from dotenv import load_dotenv

# Ensure agent_brain source is importable
_AGENT_BRAIN_SRC = Path(__file__).resolve().parents[4] / "agent-brain" / "src"
if str(_AGENT_BRAIN_SRC) not in sys.path:
    sys.path.insert(0, str(_AGENT_BRAIN_SRC))

# Ensure mock_pricing_api source is importable
_MOCK_PRICING_SRC = Path(__file__).resolve().parents[4] / "mock-pricing-api" / "src"
if str(_MOCK_PRICING_SRC) not in sys.path:
    sys.path.insert(0, str(_MOCK_PRICING_SRC))


def _bool_from_env(name: str, default: bool) -> bool:
    """Read a boolean from the environment."""

    raw_value = getenv(name)
    if raw_value is None or raw_value.strip() == "":
        return default
    normalized = raw_value.strip().lower()
    if normalized in {"1", "true", "yes", "on"}:
        return True
    if normalized in {"0", "false", "no", "off"}:
        return False
    raise ValueError(f"{name} must be a boolean value.")


def _positive_int_from_env(name: str, default: int) -> int:
    """Read a positive integer from the environment."""

    raw_value = getenv(name)
    if raw_value is None or raw_value.strip() == "":
        return default
    try:
        parsed_value = int(raw_value)
    except ValueError as exc:
        raise ValueError(f"{name} must be a positive integer.") from exc
    if parsed_value <= 0:
        raise ValueError(f"{name} must be a positive integer.")
    return parsed_value


@dataclass(frozen=True)
class UiApiSettings:
    """Environment-backed settings for the UI API server."""

    host: str = "127.0.0.1"
    port: int = 3001
    cors_origins: tuple[str, ...] = ("http://localhost:3000",)
    # Paths to sibling project roots for subprocess-based CLI execution
    agent_brain_dir: Path = Path(__file__).resolve().parents[4] / "agent-brain"
    database_layer_dir: Path = Path(__file__).resolve().parents[4] / "database-layer"
    mock_pricing_dir: Path = Path(__file__).resolve().parents[4] / "mock-pricing-api"
    scripts_dir: Path = Path(__file__).resolve().parents[4] / "scripts"
    repo_root: Path = Path(__file__).resolve().parents[4]


def get_settings() -> UiApiSettings:
    """Return settings using environment variables and local `.env` values."""

    load_dotenv()
    cors_raw = getenv("CORS_ORIGINS", "http://localhost:3000")
    cors_origins = tuple(
        origin.strip() for origin in cors_raw.split(",") if origin.strip()
    )
    return UiApiSettings(
        host=getenv("UI_API_HOST", "127.0.0.1"),
        port=_positive_int_from_env("UI_API_PORT", 3001),
        cors_origins=cors_origins,
    )
