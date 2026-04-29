from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from qurankit.app import app

runner = CliRunner()


def test_config_show_json_uses_xdg_defaults(tmp_path: Path) -> None:
    result = runner.invoke(
        app,
        ["config", "show", "--format", "json"],
        env={
            "QURANKIT_CONFIG_HOME": str(tmp_path / "config"),
            "QURANKIT_DATA_HOME": str(tmp_path / "data"),
        },
    )

    assert result.exit_code == 0

    payload = json.loads(result.stdout)
    assert payload["mode"] == "remote"
    assert payload["api_url"] == "http://localhost:8000"
    assert payload["translation"] == "en.sahih"
    assert payload["db_path"] == str(tmp_path / "data" / "qurankit.sqlite3")
    assert payload["backend_kind"] == "remote"


def test_config_set_persists_values(tmp_path: Path) -> None:
    env = {
        "QURANKIT_CONFIG_HOME": str(tmp_path / "config"),
        "QURANKIT_DATA_HOME": str(tmp_path / "data"),
    }

    mode_result = runner.invoke(app, ["config", "set", "mode", "local"], env=env)
    db_result = runner.invoke(
        app,
        ["config", "set", "db-path", str(tmp_path / "library.sqlite3")],
        env=env,
    )
    translation_result = runner.invoke(
        app,
        ["config", "set", "translation", "en.asad"],
        env=env,
    )
    show_result = runner.invoke(app, ["config", "show", "--format", "json"], env=env)

    assert mode_result.exit_code == 0
    assert db_result.exit_code == 0
    assert translation_result.exit_code == 0
    assert show_result.exit_code == 0

    payload = json.loads(show_result.stdout)
    assert payload["mode"] == "local"
    assert payload["db_path"] == str(tmp_path / "library.sqlite3")
    assert payload["translation"] == "en.asad"
    assert payload["backend_kind"] == "local"


def test_config_set_rejects_invalid_api_url(tmp_path: Path) -> None:
    result = runner.invoke(
        app,
        ["config", "set", "api-url", "localhost:8000"],
        env={"QURANKIT_CONFIG_HOME": str(tmp_path / "config")},
    )

    assert result.exit_code != 0
    assert "api-url must be an absolute http or https URL" in result.output
