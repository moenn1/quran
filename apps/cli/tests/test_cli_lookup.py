from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from qurankit.app import app
from qurankit.backends import (
    AyahRecord,
    ExactSearchHit,
    ExactSearchResult,
    SemanticSearchHit,
    SemanticSearchResult,
    TranslationAttribution,
)
from qurankit.config import BackendMode, ConfigStore, Settings, StateMode

runner = CliRunner()


class StubResponse:
    def __init__(self, payload: dict[str, object]) -> None:
        self.payload = payload

    def __enter__(self) -> StubResponse:
        return self

    def __exit__(self, exc_type, exc, tb) -> bool:
        return False

    def read(self) -> bytes:
        return json.dumps(self.payload, ensure_ascii=False).encode("utf-8")


def test_surah_command_renders_local_text_output(
    sample_sqlite_db: Path, tmp_path: Path
) -> None:
    env = _write_settings(tmp_path, mode=BackendMode.LOCAL, db_path=sample_sqlite_db)

    result = runner.invoke(app, ["surah", "1"], env=env)

    assert result.exit_code == 0
    assert "Surah 1: Al-Fatihah" in result.stdout
    assert "1:1" in result.stdout
    assert "Arabic source: AbdullahGhanem/quran-database" in result.stdout
    assert "Translation: Saheeh International (en.sahih)" in result.stdout


def test_ayah_command_json_output_contains_attribution(
    sample_sqlite_db: Path, tmp_path: Path
) -> None:
    env = _write_settings(tmp_path, mode=BackendMode.LOCAL, db_path=sample_sqlite_db)

    result = runner.invoke(app, ["ayah", "1:6", "--json"], env=env)

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["selection_kind"] == "ayah"
    assert payload["ayah"]["reference"] == "1:6"
    assert payload["translation_attribution"]["identifier"] == "en.sahih"
    assert payload["arabic_source"]["repository"] == "AbdullahGhanem/quran-database"


def test_juz_command_json_output_contains_range(
    sample_sqlite_db: Path, tmp_path: Path
) -> None:
    env = _write_settings(tmp_path, mode=BackendMode.LOCAL, db_path=sample_sqlite_db)

    result = runner.invoke(app, ["juz", "30", "--json"], env=env)

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["juz_number"] == 30
    assert payload["start_reference"] == "112:1"
    assert payload["end_reference"] == "112:2"
    assert payload["ayah_count"] == 2


def test_search_command_text_output_stays_exact_and_explainable(
    sample_sqlite_db: Path, tmp_path: Path
) -> None:
    env = _write_settings(tmp_path, mode=BackendMode.LOCAL, db_path=sample_sqlite_db)

    result = runner.invoke(app, ["search", "Merciful"], env=env)

    assert result.exit_code == 0
    assert 'Exact matches for "Merciful"' in result.stdout
    assert "Matched in: Selected translation" in result.stdout
    assert "Related passages by textual similarity" not in result.stdout


def test_semantic_command_text_output_uses_similarity_guardrail(
    sample_sqlite_db: Path, tmp_path: Path
) -> None:
    env = _write_settings(tmp_path, mode=BackendMode.LOCAL, db_path=sample_sqlite_db)

    result = runner.invoke(app, ["semantic", "guide", "path"], env=env)

    assert result.exit_code == 0
    assert 'Related passages by textual similarity for "guide path"' in result.stdout
    assert "not tafsir, fatwa, or religious rulings" in result.stdout
    assert "Why it was included:" in result.stdout


def test_random_command_json_supports_no_translation(
    sample_sqlite_db: Path, tmp_path: Path
) -> None:
    env = _write_settings(tmp_path, mode=BackendMode.LOCAL, db_path=sample_sqlite_db)

    result = runner.invoke(app, ["random", "--no-translation", "--json"], env=env)

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["selection_kind"] == "random"
    assert payload["translation_attribution"] is None
    assert payload["ayah"]["reference"] in {
        "1:1",
        "1:2",
        "1:3",
        "1:4",
        "1:5",
        "1:6",
        "2:1",
        "2:2",
        "112:1",
        "112:2",
    }


def test_local_mode_reports_missing_database(tmp_path: Path) -> None:
    env = _write_settings(
        tmp_path,
        mode=BackendMode.LOCAL,
        db_path=tmp_path / "missing.sqlite3",
    )

    result = runner.invoke(app, ["ayah", "1:1"], env=env)

    assert result.exit_code == 1
    assert "Local SQLite database not found" in result.stderr


def test_search_command_uses_remote_mode(
    monkeypatch, tmp_path: Path
) -> None:
    env = _write_settings(
        tmp_path,
        mode=BackendMode.REMOTE,
        api_url="https://api.example.test",
    )
    requested_urls: list[str] = []
    translation = TranslationAttribution(
        identifier="en.sahih",
        language="en",
        name="Saheeh International",
        english_name="Saheeh International",
        edition_type="translation",
        format="text",
    )
    sample_ayah = AyahRecord(
        surah_number=1,
        ayah_number=6,
        surah_name_arabic="ٱلْفَاتِحَةِ",
        surah_name_english="Al-Fatihah",
        surah_name_translation="The Opening",
        revelation_type="Meccan",
        arabic_text="ٱهْدِنَا ٱلصِّرَٰطَ ٱلْمُسْتَقِيمَ",
        translation_text="Guide us to the straight path.",
        page_number=1,
        juz_number=1,
        hizb_number=1,
        sajda=False,
    )
    payload = ExactSearchResult(
        query="guide",
        results=(ExactSearchHit(ayah=sample_ayah, match_sources=("translation",)),),
        searched_fields=("arabic_text", "translation"),
        translation_attribution=translation,
    ).to_dict()

    def opener(request, timeout):
        requested_urls.append(request.full_url)
        return StubResponse(payload)

    monkeypatch.setattr("qurankit.backends.urlopen", opener)

    result = runner.invoke(app, ["search", "guide", "--json"], env=env)

    assert result.exit_code == 0
    response_payload = json.loads(result.stdout)
    assert response_payload["count"] == 1
    assert response_payload["results"][0]["ayah"]["reference"] == "1:6"
    assert requested_urls == [
        "https://api.example.test/api/v1/search/exact?q=guide&translation=en.sahih&limit=5"
    ]


def test_semantic_command_uses_remote_mode(
    monkeypatch, tmp_path: Path
) -> None:
    env = _write_settings(
        tmp_path,
        mode=BackendMode.REMOTE,
        api_url="https://api.example.test",
    )
    requested_urls: list[str] = []
    translation = TranslationAttribution(
        identifier="en.sahih",
        language="en",
        name="Saheeh International",
        english_name="Saheeh International",
        edition_type="translation",
        format="text",
    )
    sample_ayah = AyahRecord(
        surah_number=113,
        ayah_number=1,
        surah_name_arabic="ٱلْفَلَقِ",
        surah_name_english="Al-Falaq",
        surah_name_translation="The Daybreak",
        revelation_type="Meccan",
        arabic_text="قُلْ أَعُوذُ بِرَبِّ ٱلْفَلَقِ",
        translation_text="Say, I seek refuge in the Lord of daybreak.",
        page_number=604,
        juz_number=30,
        hizb_number=60,
        sajda=False,
    )
    payload = SemanticSearchResult(
        query="seek refuge",
        results=(
            SemanticSearchHit(
                ayah=sample_ayah,
                similarity_score=0.82,
                reason="Shared language about seeking refuge.",
            ),
        ),
        translation_attribution=translation,
    ).to_dict()

    def opener(request, timeout):
        requested_urls.append(request.full_url)
        return StubResponse(payload)

    monkeypatch.setattr("qurankit.backends.urlopen", opener)

    result = runner.invoke(app, ["semantic", "seek", "refuge", "--json"], env=env)

    assert result.exit_code == 0
    response_payload = json.loads(result.stdout)
    assert response_payload["count"] == 1
    assert response_payload["disclaimer"].startswith(
        "Related passages are ranked by textual similarity only."
    )
    assert response_payload["results"][0]["ayah"]["reference"] == "113:1"
    assert requested_urls == [
        "https://api.example.test/api/v1/search/semantic?q=seek+refuge&translation=en.sahih&limit=5"
    ]


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
