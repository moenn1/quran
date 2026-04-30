from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from sqlalchemy import func, select

from qurankit_api.data.pipeline import (
    build_data_artifacts,
    load_normalized_dataset,
    validate_upstream_artifact,
)
from qurankit_api.db import create_engine_from_url, create_session_factory
from qurankit_api.models import Ayah, SourceFile, Surah, Translation

from tests.support.sample_dataset import SAMPLE_EXPECTATIONS, write_sample_zip


def test_validate_upstream_artifact_supports_fixture_expectations(tmp_path: Path) -> None:
    artifact_path = write_sample_zip(tmp_path / "sample-quran.sql.zip")

    report = validate_upstream_artifact(
        artifact_path,
        expectations=SAMPLE_EXPECTATIONS,
        verify_locked_source=False,
    )

    assert report.is_valid is True
    assert report.counts == {
        "surahs": 2,
        "ayahs": 3,
        "editions": 2,
        "ayah_edition": 6,
    }
    assert report.ranges == {
        "page": [1, 2],
        "juz": [1, 1],
        "hizb": [1, 1],
        "rub_el_hizb": [1, 4],
        "sajda_count": 1,
    }
    assert report.edition_coverage["complete_editions"] == 2
    assert any(issue.code == "utf8_bom_on_first_ayah" for issue in report.warnings)


def test_load_normalized_dataset_inserts_rows_and_source_files(
    migrated_database_url: str,
    tmp_path: Path,
) -> None:
    artifact_path = write_sample_zip(tmp_path / "sample-quran.sql.zip")

    counts = load_normalized_dataset(
        migrated_database_url,
        artifact_path=artifact_path,
        expectations=SAMPLE_EXPECTATIONS,
        verify_locked_source=False,
    )

    engine = create_engine_from_url(migrated_database_url)
    session_factory = create_session_factory(engine)
    with session_factory() as session:
        assert session.scalar(select(func.count()).select_from(Surah)) == 2
        assert session.scalar(select(func.count()).select_from(Ayah)) == 3
        assert session.scalar(select(func.count()).select_from(Translation)) == 2
        assert session.scalar(select(func.count()).select_from(SourceFile)) == 2

        ayah = session.get(Ayah, 1)
        assert ayah is not None
        assert ayah.text.startswith("\ufeff")
        assert ayah.hizb_number == 1

        translation = session.scalar(
            select(Translation).where(Translation.upstream_identifier == "en.sahih"),
        )
        assert translation is not None
        assert translation.attribution_url == "https://github.com/AbdullahGhanem/quran-database"

        source_files = session.scalars(select(SourceFile).order_by(SourceFile.artifact_name)).all()
        assert [source_file.artifact_name for source_file in source_files] == [
            "quran.sql",
            "quran.sql.zip",
        ]

    assert counts.surahs_loaded == 2
    assert counts.ayahs_loaded == 3
    assert counts.translations_loaded == 2
    assert counts.ayah_translations_loaded == 6

    engine.dispose()


def test_build_data_artifacts_writes_sqlite_json_and_postgres_outputs(tmp_path: Path) -> None:
    artifact_path = write_sample_zip(tmp_path / "sample-quran.sql.zip")
    output_dir = tmp_path / "exports"

    manifest = build_data_artifacts(
        output_dir,
        artifact_path=artifact_path,
        expectations=SAMPLE_EXPECTATIONS,
        verify_locked_source=False,
    )

    sqlite_path = output_dir / "qurankit.sqlite3"
    postgres_path = output_dir / "qurankit.postgres.sql"
    validation_json_path = output_dir / "validation-report.json"
    json_manifest_path = output_dir / "json" / "manifest.json"

    assert sqlite_path.exists()
    assert postgres_path.exists()
    assert validation_json_path.exists()
    assert json_manifest_path.exists()
    assert manifest["sqlite_database"] == str(sqlite_path)

    validation_payload = json.loads(validation_json_path.read_text(encoding="utf-8"))
    assert validation_payload["ok"] is True
    assert validation_payload["counts"]["ayah_edition"] == 6

    json_manifest = json.loads(json_manifest_path.read_text(encoding="utf-8"))
    assert json_manifest["files"]["ayah_translations"]["count"] == 6

    postgres_sql = postgres_path.read_text(encoding="utf-8")
    assert "INSERT INTO source_releases" in postgres_sql
    assert "INSERT INTO ayah_translations" in postgres_sql

    with sqlite3.connect(sqlite_path) as connection:
        cursor = connection.execute("SELECT COUNT(*) FROM ayahs")
        assert cursor.fetchone() == (3,)
