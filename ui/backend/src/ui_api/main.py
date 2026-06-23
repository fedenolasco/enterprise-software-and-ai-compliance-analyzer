"""Main entry point for the UI API server."""

from __future__ import annotations

import sys

import uvicorn

from ui_api.config import get_settings

BASELINE_PYTHON_MAJOR = 3
BASELINE_PYTHON_MINOR = 11


def _ensure_baseline_python() -> None:
    """Fail fast unless the UI backend is running on the project Python baseline."""
    if sys.version_info[:2] == (BASELINE_PYTHON_MAJOR, BASELINE_PYTHON_MINOR):
        return

    expected = f"{BASELINE_PYTHON_MAJOR}.{BASELINE_PYTHON_MINOR}"
    actual = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    raise SystemExit(
        "UI backend must run on the project baseline Python "
        f"{expected}. Current interpreter is Python {actual} at {sys.executable}. "
        "Start it with: py -3.11 -m ui_api.main"
    )


def main() -> None:
    """Start the UI API server."""
    _ensure_baseline_python()
    settings = get_settings()
    uvicorn.run(
        "ui_api.app:app",
        host=settings.host,
        port=settings.port,
        reload=False,
    )


if __name__ == "__main__":
    main()
