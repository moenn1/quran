from pathlib import Path

from qurankit.backends import LocalSQLiteBackend, RemoteBackend, select_backend
from qurankit.config import BackendMode, Settings


def test_select_backend_uses_remote_mode() -> None:
    settings = Settings(
        mode=BackendMode.REMOTE,
        api_url="https://example.com/api",
        db_path="/tmp/qurankit.sqlite3",
        translation="en.sahih",
    )

    backend = select_backend(settings)

    assert isinstance(backend, RemoteBackend)
    assert backend.summary == "Remote API at https://example.com/api"


def test_select_backend_uses_local_sqlite_mode(tmp_path: Path) -> None:
    db_path = tmp_path / "qurankit.sqlite3"
    settings = Settings(
        mode=BackendMode.LOCAL,
        api_url="https://example.com/api",
        db_path=str(db_path),
        translation="en.sahih",
    )

    backend = select_backend(settings)

    assert isinstance(backend, LocalSQLiteBackend)
    assert backend.summary.endswith("(file not found yet)")
