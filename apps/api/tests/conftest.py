import pytest
from fastapi.testclient import TestClient

from qurankit_api.app import create_app
from qurankit_api.core.config import Settings


@pytest.fixture
def settings() -> Settings:
    return Settings(
        app_name="QuranKit API Test",
        app_version="0.1.0-test",
        environment="test",
        redoc_url=None,
    )


@pytest.fixture
def client(settings: Settings) -> TestClient:
    with TestClient(create_app(settings)) as test_client:
        yield test_client


@pytest.fixture
def no_raise_client(settings: Settings) -> TestClient:
    app = create_app(settings)

    @app.get("/api/v1/_boom", include_in_schema=False)
    async def boom() -> None:
        raise RuntimeError("boom")

    with TestClient(app, raise_server_exceptions=False) as test_client:
        yield test_client
