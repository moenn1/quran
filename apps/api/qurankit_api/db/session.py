from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager

from sqlalchemy import Engine, create_engine, event
from sqlalchemy.orm import Session, sessionmaker

from qurankit_api.core.config import get_settings


def resolve_database_url(database_url: str | None = None) -> str:
    resolved = database_url or get_settings().database_url
    if not resolved:
        raise RuntimeError(
            "QURANKIT_DATABASE_URL is not configured. "
            "Set it explicitly or use the repository migration and seed scripts.",
        )
    return resolved


def create_engine_from_url(
    database_url: str | None = None,
    *,
    echo: bool = False,
) -> Engine:
    resolved_url = resolve_database_url(database_url)
    connect_args = {"check_same_thread": False} if resolved_url.startswith("sqlite") else {}
    engine = create_engine(
        resolved_url,
        echo=echo,
        future=True,
        connect_args=connect_args,
    )

    if resolved_url.startswith("sqlite"):
        @event.listens_for(engine, "connect")
        def _set_sqlite_pragma(dbapi_connection, _connection_record) -> None:
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()

    return engine


def create_session_factory(engine: Engine) -> sessionmaker[Session]:
    return sessionmaker(
        bind=engine,
        autoflush=False,
        expire_on_commit=False,
        future=True,
    )


@contextmanager
def session_scope(
    database_url: str | None = None,
    *,
    echo: bool = False,
) -> Iterator[Session]:
    engine = create_engine_from_url(database_url, echo=echo)
    session_factory = create_session_factory(engine)
    with session_factory() as session:
        try:
            yield session
        finally:
            engine.dispose()
