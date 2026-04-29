from __future__ import annotations

from pathlib import Path

from qurankit.config import (
    BackendMode,
    ConfigField,
    ConfigStore,
    Settings,
    apply_environment_overrides,
    default_settings,
)


def test_default_settings_use_local_data_directory(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("QURANKIT_DATA_HOME", str(tmp_path / "data-home"))

    settings = default_settings()

    assert settings.mode is BackendMode.REMOTE
    assert settings.db_path == str(tmp_path / "data-home" / "qurankit.sqlite3")


def test_config_store_saves_and_loads_settings(tmp_path: Path) -> None:
    store = ConfigStore(tmp_path / "config.json")
    expected = Settings(
        mode=BackendMode.LOCAL,
        api_url="https://api.example.test",
        db_path=str(tmp_path / "library.sqlite3"),
        translation="en.pickthall",
    )

    store.save(expected)
    loaded = store.load(env={})

    assert loaded == expected


def test_config_store_updates_selected_field(tmp_path: Path) -> None:
    store = ConfigStore(tmp_path / "config.json")

    store.update(ConfigField.TRANSLATION, "en.asad")
    updated = store.update(ConfigField.MODE, "local")

    assert updated.translation == "en.asad"
    assert updated.mode is BackendMode.LOCAL


def test_environment_overrides_take_priority() -> None:
    settings = Settings(
        mode=BackendMode.REMOTE,
        api_url="https://api.example.test",
        db_path="/tmp/library.sqlite3",
        translation="en.sahih",
    )

    overridden = apply_environment_overrides(
        settings,
        env={
            "QURANKIT_MODE": "local",
            "QURANKIT_DB_PATH": "/tmp/override.sqlite3",
        },
    )

    assert overridden.mode is BackendMode.LOCAL
    assert overridden.db_path == "/tmp/override.sqlite3"
