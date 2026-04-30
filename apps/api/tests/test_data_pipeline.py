from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

from sqlalchemy import func, select

from qurankit_api.data.pipeline import (
    ValidationExpectations,
    build_data_artifacts,
    load_normalized_dataset,
    validate_upstream_artifact,
)
from qurankit_api.db import create_engine_from_url, create_session_factory
from qurankit_api.models import Ayah, SourceFile, Surah, Translation


SAMPLE_SQL = """-- phpMyAdmin SQL Dump
-- version 4.7.7
-- Generation Time: Apr 29, 2026 at 10:00 PM
-- Server version: 5.7.22
-- PHP Version: 7.1.18

-- Database: `quran`
--

CREATE TABLE `ayahs` (
  `id` int(10) UNSIGNED NOT NULL,
  `number` int(11) NOT NULL,
  `text` text COLLATE utf8mb4_unicode_ci NOT NULL,
  `number_in_surah` int(11) NOT NULL,
  `page` int(11) NOT NULL,
  `surah_id` int(11) NOT NULL,
  `hizb_id` int(11) NOT NULL,
  `juz_id` int(11) NOT NULL,
  `sajda` tinyint(1) NOT NULL,
  `created_at` timestamp NULL DEFAULT NULL,
  `updated_at` timestamp NULL DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `ayah_edition` (
  `id` int(10) UNSIGNED NOT NULL,
  `ayah_id` int(10) UNSIGNED NOT NULL,
  `edition_id` int(10) UNSIGNED NOT NULL,
  `data` text COLLATE utf8mb4_unicode_ci NOT NULL,
  `is_audio` tinyint(1) NOT NULL,
  `created_at` timestamp NULL DEFAULT NULL,
  `updated_at` timestamp NULL DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `editions` (
  `id` int(10) UNSIGNED NOT NULL,
  `identifier` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `language` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `name` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `englishName` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `format` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `type` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `created_at` timestamp NULL DEFAULT NULL,
  `updated_at` timestamp NULL DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `surahs` (
  `id` int(10) UNSIGNED NOT NULL,
  `number` int(11) NOT NULL,
  `name_ar` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `name_en` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `name_en_translation` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `type` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `created_at` timestamp NULL DEFAULT NULL,
  `updated_at` timestamp NULL DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

INSERT INTO `surahs` (`id`, `number`, `name_ar`, `name_en`, `name_en_translation`, `type`, `created_at`, `updated_at`) VALUES
(1, 1, 'سورة الفاتحة', 'Al-Faatiha', 'The Opening', 'Meccan', NULL, NULL),
(2, 2, 'سورة البقرة', 'Al-Baqara', 'The Cow', 'Medinan', NULL, NULL);

INSERT INTO `ayahs` (`id`, `number`, `text`, `number_in_surah`, `page`, `surah_id`, `hizb_id`, `juz_id`, `sajda`, `created_at`, `updated_at`) VALUES
(1, 1, '﻿بِسْمِ ٱللَّهِ', 1, 1, 1, 1, 1, 0, NULL, NULL),
(2, 2, 'بِسْمِ ٱللَّهِ الٓمٓ', 1, 2, 2, 4, 1, 0, NULL, NULL),
(3, 3, 'ذَٰلِكَ ٱلْكِتَٰبُ', 2, 2, 2, 4, 1, 1, NULL, NULL);

INSERT INTO `editions` (`id`, `identifier`, `language`, `name`, `englishName`, `format`, `type`, `created_at`, `updated_at`) VALUES
(1, 'en.sahih', 'en', 'Sahih', 'Saheeh International', 'text', 'translation', NULL, NULL),
(2, 'quran-simple', 'ar', 'Simple', 'Simple', 'text', 'quran', NULL, NULL);

INSERT INTO `ayah_edition` (`id`, `ayah_id`, `edition_id`, `data`, `is_audio`, `created_at`, `updated_at`) VALUES
(1, 1, 1, 'In the name of Allah', 0, NULL, NULL),
(2, 2, 1, 'Alif Lam Mim', 0, NULL, NULL),
(3, 3, 1, 'That is the Book', 0, NULL, NULL),
(4, 1, 2, 'بِسْمِ ٱللَّهِ', 0, NULL, NULL),
(5, 2, 2, 'بِسْمِ ٱللَّهِ الٓمٓ', 0, NULL, NULL),
(6, 3, 2, 'ذَٰلِكَ ٱلْكِتَٰبُ', 0, NULL, NULL);
"""

SAMPLE_EXPECTATIONS = ValidationExpectations(
    surah_count=2,
    ayah_count=3,
    page_range=(1, 2),
    juz_range=(1, 1),
    hizb_range=(1, 1),
    rub_el_hizb_range=(1, 4),
)


def _write_sample_zip(path: Path) -> Path:
    with ZipFile(path, "w", compression=ZIP_DEFLATED) as archive:
        archive.writestr("quran.sql", SAMPLE_SQL)
    return path


def test_validate_upstream_artifact_supports_fixture_expectations(tmp_path: Path) -> None:
    artifact_path = _write_sample_zip(tmp_path / "sample-quran.sql.zip")

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
    artifact_path = _write_sample_zip(tmp_path / "sample-quran.sql.zip")

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
    artifact_path = _write_sample_zip(tmp_path / "sample-quran.sql.zip")
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
