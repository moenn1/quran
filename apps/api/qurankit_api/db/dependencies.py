from __future__ import annotations

from collections.abc import Iterator

from fastapi import Request
from sqlalchemy.orm import Session, sessionmaker

from qurankit_api.core.errors import ApiError


def get_db_session(request: Request) -> Iterator[Session]:
    session_factory = getattr(request.app.state, "session_factory", None)

    if session_factory is None or not isinstance(session_factory, sessionmaker):
        raise ApiError(
            status_code=503,
            code="database_unavailable",
            message="Database is not configured for this API instance.",
            details={
                "setting": "QURANKIT_DATABASE_URL",
            },
        )

    with session_factory() as session:
        yield session
