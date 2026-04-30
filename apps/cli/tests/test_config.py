from __future__ import annotations

from pathlib import Path

from qurankit.config import (
    BackendMode,
    ConfigField,
    ConfigStore,
    Settings,
    StateMode,
    apply_environment_overrides,
    default_settings,
)


def test_default_settings_use_local_data_directory(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("QURANKIT_DATA_HOME", str(tmp_path / "data-home"))

    settings = default_settings()

    assert settings.mode is BackendMode.REMOTE
    assert settings.state_mode is StateMode.LOCAL
    assert settings.db_path == str(tmp_path / "data-home" / "qurankit.sqlite3")
    assert settings.state_path == str(tmp_path / "data-home" / "study-state.json")


def test_config_store_saves_and_loads_settings(tmp_path: Path) -> None:
    store = ConfigStore(tmp_path / "config.json")
    expected = Settings(
        mode=BackendMode.LOCAL,
        state_mode=StateMode.REMOTE,
        api_url="https://api.example.test",
        db_path=str(tmp_path / "library.sqlite3"),
        state_path=str(tmp_path / "study-state.json"),
        translation="en.pickthall",
        api_token="test-token",
    )

    store.save(expected)
    loaded = store.load(env={})

    assert loaded == expected


def test_config_store_updates_selected_field(tmp_path: Path) -> None:
    store = ConfigStore(tmp_path / "config.json")

    store.update(ConfigField.TRANSLATION, "en.asad")
    updated = store.update(ConfigField.MODE, "local")
    updated = store.update(ConfigField.STATE_MODE, "remote")

    assert updated.translation == "en.asad"
    assert updated.mode is BackendMode.LOCAL
    assert updated.state_mode is StateMode.REMOTE


def test_environment_overrides_take_priority() -> None:
    settings = Settings(
        mode=BackendMode.REMOTE,
        state_mode=StateMode.LOCAL,
        api_url="https://api.example.test",
        db_path="/tmp/library.sqlite3",
        state_path="/tmp/study-state.json",
        translation="en.sahih",
    )

    overridden = apply_environment_overrides(
        settings,
        env={
            "QURANKIT_MODE": "local",
            "QURANKIT_STATE_MODE": "remote",
            "QURANKIT_DB_PATH": "/tmp/override.sqlite3",
            "QURANKIT_STATE_PATH": "/tmp/override-state.json",
            "QURANKIT_API_TOKEN": "env-token",
        },
    )

    assert overridden.mode is BackendMode.LOCAL
    assert overridden.state_mode is StateMode.REMOTE
    assert overridden.db_path == "/tmp/override.sqlite3"
    assert overridden.state_path == "/tmp/override-state.json"
    assert overridden.api_token == "env-token"
