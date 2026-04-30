from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass
from enum import StrEnum
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

APP_NAME = "qurankit"
DEFAULT_API_URL = "http://localhost:8000"
DEFAULT_TRANSLATION = "en.sahih"
DEFAULT_DB_FILENAME = "qurankit.sqlite3"
DEFAULT_STATE_FILENAME = "study-state.json"


class BackendMode(StrEnum):
    REMOTE = "remote"
    LOCAL = "local"


class StateMode(StrEnum):
    LOCAL = "local"
    REMOTE = "remote"


class ConfigField(StrEnum):
    MODE = "mode"
    STATE_MODE = "state-mode"
    API_URL = "api-url"
    DB_PATH = "db-path"
    STATE_PATH = "state-path"
    TRANSLATION = "translation"
    API_TOKEN = "api-token"


@dataclass(frozen=True)
class Settings:
    mode: BackendMode
    state_mode: StateMode
    api_url: str
    db_path: str
    state_path: str
    translation: str
    api_token: str | None = None

    def to_dict(self) -> dict[str, str | None]:
        payload = asdict(self)
        payload["mode"] = self.mode.value
        payload["state_mode"] = self.state_mode.value
        return payload


def config_dir() -> Path:
    if override := os.environ.get("QURANKIT_CONFIG_HOME"):
        return Path(override).expanduser()

    if xdg_home := os.environ.get("XDG_CONFIG_HOME"):
        return Path(xdg_home).expanduser() / APP_NAME

    return Path.home() / ".config" / APP_NAME


def data_dir() -> Path:
    if override := os.environ.get("QURANKIT_DATA_HOME"):
        return Path(override).expanduser()

    if xdg_home := os.environ.get("XDG_DATA_HOME"):
        return Path(xdg_home).expanduser() / APP_NAME

    return Path.home() / ".local" / "share" / APP_NAME


def config_file() -> Path:
    if override := os.environ.get("QURANKIT_CONFIG_FILE"):
        return Path(override).expanduser()

    return config_dir() / "config.json"


def default_db_path() -> Path:
    return data_dir() / DEFAULT_DB_FILENAME


def default_state_path() -> Path:
    return data_dir() / DEFAULT_STATE_FILENAME


def default_settings() -> Settings:
    return Settings(
        mode=BackendMode.REMOTE,
        state_mode=StateMode.LOCAL,
        api_url=DEFAULT_API_URL,
        db_path=str(default_db_path()),
        state_path=str(default_state_path()),
        translation=DEFAULT_TRANSLATION,
    )


def _validate_url(value: str) -> str:
    parsed = urlparse(value)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ValueError("api-url must be an absolute http or https URL")

    return value.rstrip("/")


def _validate_translation(value: str) -> str:
    normalized = value.strip()
    if not normalized:
        raise ValueError("translation cannot be empty")

    return normalized


def _validate_path(value: str, *, field_name: str) -> str:
    normalized = value.strip()
    if not normalized:
        raise ValueError(f"{field_name} cannot be empty")

    return str(Path(normalized).expanduser())


def _validate_api_token(value: Any) -> str | None:
    if value is None:
        return None

    normalized = str(value).strip()
    if not normalized:
        return None

    return normalized


def _normalize_backend_mode(value: str) -> BackendMode:
    try:
        return BackendMode(value.strip().lower())
    except ValueError as exc:
        valid = ", ".join(mode.value for mode in BackendMode)
        raise ValueError(f"mode must be one of: {valid}") from exc


def _normalize_state_mode(value: str) -> StateMode:
    try:
        return StateMode(value.strip().lower())
    except ValueError as exc:
        valid = ", ".join(mode.value for mode in StateMode)
        raise ValueError(f"state-mode must be one of: {valid}") from exc


def normalize_settings(payload: dict[str, Any]) -> Settings:
    defaults = default_settings()

    return Settings(
        mode=_normalize_backend_mode(str(payload.get("mode", defaults.mode.value))),
        state_mode=_normalize_state_mode(
            str(payload.get("state_mode", defaults.state_mode.value))
        ),
        api_url=_validate_url(str(payload.get("api_url", defaults.api_url))),
        db_path=_validate_path(
            str(payload.get("db_path", defaults.db_path)),
            field_name="db-path",
        ),
        state_path=_validate_path(
            str(payload.get("state_path", defaults.state_path)),
            field_name="state-path",
        ),
        translation=_validate_translation(
            str(payload.get("translation", defaults.translation))
        ),
        api_token=_validate_api_token(payload.get("api_token", defaults.api_token)),
    )


def apply_environment_overrides(
    settings: Settings, env: dict[str, str] | None = None
) -> Settings:
    source = os.environ if env is None else env
    payload = settings.to_dict()

    if "QURANKIT_MODE" in source:
        payload["mode"] = source["QURANKIT_MODE"]
    if "QURANKIT_STATE_MODE" in source:
        payload["state_mode"] = source["QURANKIT_STATE_MODE"]
    if "QURANKIT_API_URL" in source:
        payload["api_url"] = source["QURANKIT_API_URL"]
    if "QURANKIT_DB_PATH" in source:
        payload["db_path"] = source["QURANKIT_DB_PATH"]
    if "QURANKIT_STATE_PATH" in source:
        payload["state_path"] = source["QURANKIT_STATE_PATH"]
    if "QURANKIT_TRANSLATION" in source:
        payload["translation"] = source["QURANKIT_TRANSLATION"]
    if "QURANKIT_API_TOKEN" in source:
        payload["api_token"] = source["QURANKIT_API_TOKEN"]

    return normalize_settings(payload)


class ConfigStore:
    def __init__(self, path: Path | None = None) -> None:
        self.path = path or config_file()

    def load(self, env: dict[str, str] | None = None) -> Settings:
        if not self.path.exists():
            return apply_environment_overrides(default_settings(), env=env)

        payload = json.loads(self.path.read_text(encoding="utf-8"))
        settings = normalize_settings(payload)
        return apply_environment_overrides(settings, env=env)

    def save(self, settings: Settings) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(
            json.dumps(settings.to_dict(), indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )

    def update(self, field: ConfigField, value: str) -> Settings:
        payload = self.load(env={}).to_dict()

        match field:
            case ConfigField.MODE:
                payload["mode"] = value
            case ConfigField.STATE_MODE:
                payload["state_mode"] = value
            case ConfigField.API_URL:
                payload["api_url"] = value
            case ConfigField.DB_PATH:
                payload["db_path"] = value
            case ConfigField.STATE_PATH:
                payload["state_path"] = value
            case ConfigField.TRANSLATION:
                payload["translation"] = value
            case ConfigField.API_TOKEN:
                payload["api_token"] = value

        settings = normalize_settings(payload)
        self.save(settings)
        return settings
