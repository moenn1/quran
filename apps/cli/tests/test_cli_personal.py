from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from qurankit.app import app
from qurankit.config import BackendMode, ConfigStore, Settings, StateMode

runner = CliRunner()


def test_progress_mark_and_progress_show_json_round_trip(
    sample_sqlite_db: Path, tmp_path: Path
) -> None:
    env = _write_settings(tmp_path, mode=BackendMode.LOCAL, db_path=sample_sqlite_db)

    mark_result = runner.invoke(app, ["progress", "mark", "1:1-3", "--json"], env=env)
    show_result = runner.invoke(app, ["progress", "--json"], env=env)

    assert mark_result.exit_code == 0
    assert show_result.exit_code == 0

    mark_payload = json.loads(mark_result.stdout)
    show_payload = json.loads(show_result.stdout)
    assert mark_payload["progress"]["range"]["label"] == "1:1-3"
    assert mark_payload["storage"]["private_by_default"] is True
    assert show_payload["progress"]["range"]["label"] == "1:1-3"
    assert show_payload["bookmark_count"] == 0
    assert Path(env["QURANKIT_DATA_HOME"], "study-state.json").exists()


def test_plan_create_and_today_follow_progress_checkpoint(
    sample_sqlite_db: Path, tmp_path: Path
) -> None:
    env = _write_settings(tmp_path, mode=BackendMode.LOCAL, db_path=sample_sqlite_db)

    create_result = runner.invoke(
        app,
        ["plan", "create", "Morning", "1:1-2:2", "--daily", "2", "--json"],
        env=env,
    )
    mark_result = runner.invoke(app, ["progress", "mark", "1:1-2", "--json"], env=env)
    today_result = runner.invoke(
        app,
        ["plan", "today", "--plan", "Morning", "--json"],
        env=env,
    )

    assert create_result.exit_code == 0
    assert mark_result.exit_code == 0
    assert today_result.exit_code == 0

    today_payload = json.loads(today_result.stdout)
    assert today_payload["today_range"]["start_reference"] == "1:3"
    assert today_payload["today_range"]["end_reference"] == "1:4"
    assert today_payload["today_range"]["ayah_count"] == 2
    assert today_payload["completed_ayahs"] == 2


def test_bookmark_note_and_export_commands(
    sample_sqlite_db: Path, tmp_path: Path
) -> None:
    env = _write_settings(tmp_path, mode=BackendMode.LOCAL, db_path=sample_sqlite_db)

    bookmark_result = runner.invoke(
        app,
        ["bookmark", "add", "1:6", "--label", "Guidance", "--json"],
        env=env,
    )
    note_result = runner.invoke(
        app,
        ["note", "add", "1:6", "Reflect", "on", "guidance", "--json"],
        env=env,
    )
    note_list_result = runner.invoke(app, ["note", "--json"], env=env)
    export_result = runner.invoke(app, ["export", "bookmarks"], env=env)

    assert bookmark_result.exit_code == 0
    assert note_result.exit_code == 0
    assert note_list_result.exit_code == 0
    assert export_result.exit_code == 0

    bookmark_payload = json.loads(bookmark_result.stdout)
    note_list_payload = json.loads(note_list_result.stdout)
    export_payload = json.loads(export_result.stdout)
    assert bookmark_payload["bookmark"]["label"] == "Guidance"
    assert note_list_payload["count"] == 1
    assert note_list_payload["notes"][0]["body"] == "Reflect on guidance"
    assert export_payload["count"] == 1
    assert export_payload["bookmarks"][0]["range"]["label"] == "1:6"


def test_export_surah_writes_json_file(
    sample_sqlite_db: Path, tmp_path: Path
) -> None:
    env = _write_settings(tmp_path, mode=BackendMode.LOCAL, db_path=sample_sqlite_db)
    output = tmp_path / "exports" / "surah-1.json"

    result = runner.invoke(
        app,
        ["export", "surah", "1", "--output", str(output)],
        env=env,
    )

    assert result.exit_code == 0
    payload = json.loads(output.read_text(encoding="utf-8"))
    assert payload["surah_number"] == 1
    assert payload["ayah_count"] == 6
    assert payload["arabic_source"]["repository"] == "AbdullahGhanem/quran-database"


def _write_settings(
    tmp_path: Path,
    *,
    mode: BackendMode,
    translation: str = "en.sahih",
    db_path: Path | None = None,
    api_url: str = "https://api.example.test",
) -> dict[str, str]:
    config_home = tmp_path / "config"
    data_home = tmp_path / "data"
    store = ConfigStore(config_home / "config.json")
    store.save(
        Settings(
            mode=mode,
            state_mode=StateMode.LOCAL,
            api_url=api_url,
            db_path=str(db_path or (data_home / "qurankit.sqlite3")),
            state_path=str(data_home / "study-state.json"),
            translation=translation,
        )
    )

    return {
        "QURANKIT_CONFIG_HOME": str(config_home),
        "QURANKIT_DATA_HOME": str(data_home),
    }
