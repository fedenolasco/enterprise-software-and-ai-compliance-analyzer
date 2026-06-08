"""Run the local mock pricing API with Uvicorn."""

import uvicorn

from mock_pricing_api.config import get_settings


def main() -> None:
    """Start the local mock pricing API."""

    settings = get_settings()
    uvicorn.run(
        "mock_pricing_api.app:app",
        host=settings.host,
        port=settings.port,
        reload=False,
    )


if __name__ == "__main__":
    main()
