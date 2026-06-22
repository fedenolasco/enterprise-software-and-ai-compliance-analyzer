"""Main entry point for the UI API server."""

from __future__ import annotations

import uvicorn

from ui_api.config import get_settings


def main() -> None:
    """Start the UI API server."""
    settings = get_settings()
    uvicorn.run(
        "ui_api.app:app",
        host=settings.host,
        port=settings.port,
        reload=False,
    )


if __name__ == "__main__":
    main()
