from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .config import BackendMode, Settings


@dataclass(frozen=True)
class RemoteBackend:
    api_url: str

    @property
    def kind(self) -> str:
        return "remote"

    @property
    def summary(self) -> str:
        return f"Remote API at {self.api_url}"


@dataclass(frozen=True)
class LocalSQLiteBackend:
    db_path: Path

    @property
    def kind(self) -> str:
        return "local"

    @property
    def summary(self) -> str:
        if self.db_path.exists():
            return f"Local SQLite database at {self.db_path}"

        return f"Local SQLite database at {self.db_path} (file not found yet)"


Backend = RemoteBackend | LocalSQLiteBackend


def select_backend(settings: Settings) -> Backend:
    if settings.mode is BackendMode.LOCAL:
        return LocalSQLiteBackend(Path(settings.db_path))

    return RemoteBackend(settings.api_url)
