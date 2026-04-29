from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from qurankit_api import models as _models  # noqa: F401
from qurankit_api.app import create_app
from qurankit_api.db import Base, create_engine_from_url, create_session_factory
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


@pytest.fixture
def sqlite_database_url(tmp_path: Path) -> str:
    return f"sqlite+pysqlite:///{tmp_path / 'qurankit.sqlite3'}"


@pytest.fixture
def db_session(sqlite_database_url: str) -> Session:
    engine = create_engine_from_url(sqlite_database_url)
    Base.metadata.create_all(engine)
    session_factory = create_session_factory(engine)

    with session_factory() as session:
        yield session

    engine.dispose()


@pytest.fixture
def migrated_database_url(sqlite_database_url: str) -> str:
    api_dir = Path(__file__).resolve().parents[1]
    config = Config(str(api_dir / "alembic.ini"))
    config.set_main_option("script_location", str(api_dir / "alembic"))
    config.set_main_option("sqlalchemy.url", sqlite_database_url)
    command.upgrade(config, "head")
    return sqlite_database_url
