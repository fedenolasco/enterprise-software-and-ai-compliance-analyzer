"""Configuration for the local mock pricing API."""

from dataclasses import dataclass
from os import getenv
from pathlib import Path

from dotenv import load_dotenv

DEFAULT_PRICING_FIXTURE_PATH = Path(__file__).parent / "data" / "pricing.json"


@dataclass(frozen=True)
class MockPricingSettings:
    """Environment-backed settings for the mock pricing service."""

    host: str = "127.0.0.1"
    port: int = 8000
    pricing_fixture_path: Path = DEFAULT_PRICING_FIXTURE_PATH


def get_settings() -> MockPricingSettings:
    """Load settings from environment variables and local `.env` values."""

    load_dotenv()
    fixture_path = getenv("PRICING_FIXTURE_PATH")
    return MockPricingSettings(
        host=getenv("MOCK_PRICING_API_HOST", "127.0.0.1"),
        port=_positive_int_from_env("MOCK_PRICING_API_PORT", 8000),
        pricing_fixture_path=Path(fixture_path) if fixture_path else DEFAULT_PRICING_FIXTURE_PATH,
    )


def _positive_int_from_env(name: str, default: int) -> int:
    raw_value = getenv(name)
    if raw_value is None or raw_value.strip() == "":
        return default

    try:
        parsed = int(raw_value)
    except ValueError as exc:
        raise ValueError(f"{name} must be a positive integer.") from exc

    if parsed <= 0:
        raise ValueError(f"{name} must be a positive integer.")
    return parsed
