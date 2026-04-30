from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from uuid import NAMESPACE_URL, uuid5


UPSTREAM_SOURCE_NAME = "AbdullahGhanem/quran-database"
UPSTREAM_REPOSITORY_URL = "https://github.com/AbdullahGhanem/quran-database"
UPSTREAM_COMMIT_SHA = "f6c4c805f22b0432677d79aafc12139b915e1a0d"
UPSTREAM_COMMIT_DATE = "2026-03-09"
UPSTREAM_ARTIFACT_NAME = "quran.sql.zip"
UPSTREAM_ARTIFACT_SHA256 = "ff9033de414a1a18fe42e241dc81f4528c3b194a1e8304d3ac06c9d5b0d7f155"
UPSTREAM_ARTIFACT_URL = (
    "https://raw.githubusercontent.com/AbdullahGhanem/quran-database/"
    f"{UPSTREAM_COMMIT_SHA}/{UPSTREAM_ARTIFACT_NAME}"
)
EXTRACTED_SQL_ARTIFACT_NAME = "quran.sql"
PROJECT_UUID_NAMESPACE = uuid5(
    NAMESPACE_URL,
    "https://github.com/moenn1/quran/qurankit-data-ids",
)


@dataclass(frozen=True, slots=True)
class SourceArtifactInfo:
    archive_path: str
    archive_sha256: str
    archive_byte_size: int
    sql_artifact_name: str
    sql_sha256: str
    sql_byte_size: int
    raw_url: str
    dump_generated_text: str | None
    dump_server_version: str | None
    dump_export_tool: str | None
    dump_php_version: str | None
    database_name: str | None


def stable_uuid(kind: str, *parts: object) -> str:
    serialized = "::".join([kind, *(str(part) for part in parts)])
    return str(uuid5(PROJECT_UUID_NAMESPACE, serialized))


SOURCE_RELEASE_ID = stable_uuid(
    "source_release",
    UPSTREAM_REPOSITORY_URL,
    UPSTREAM_COMMIT_SHA,
    UPSTREAM_ARTIFACT_SHA256,
)


def build_source_release_seed() -> dict[str, Any]:
    return {
        "id": SOURCE_RELEASE_ID,
        "source_name": UPSTREAM_SOURCE_NAME,
        "repository_url": UPSTREAM_REPOSITORY_URL,
        "upstream_commit_sha": UPSTREAM_COMMIT_SHA,
        "retrieved_artifact_name": UPSTREAM_ARTIFACT_NAME,
        "retrieved_artifact_sha256": UPSTREAM_ARTIFACT_SHA256,
        "dump_generated_text": "Jun 07, 2018 at 10:43 AM",
        "dump_server_version": "5.7.22",
        "dump_export_tool": "phpMyAdmin 4.7.7",
        "notes": (
            "Bootstrapped from the QuranKit upstream evaluation. "
            "Quran text should remain exact to source, while translation and audio reuse "
            "remain review-gated until attribution and rights checks are complete."
        ),
        "metadata_json": {
            "evaluated_commit_date": UPSTREAM_COMMIT_DATE,
            "evaluation_summary_path": "docs/upstream/quran-database-summary.json",
            "evaluation_script": "scripts/analyze_upstream_quran_sql.py",
            "artifact_download_url": UPSTREAM_ARTIFACT_URL,
        },
    }


def build_archive_source_file_seed(
    *,
    byte_size: int | None = None,
    sha256: str = UPSTREAM_ARTIFACT_SHA256,
    source_release_id: str = SOURCE_RELEASE_ID,
) -> dict[str, Any]:
    return {
        "id": stable_uuid("source_file", source_release_id, UPSTREAM_ARTIFACT_NAME),
        "artifact_name": UPSTREAM_ARTIFACT_NAME,
        "artifact_role": "sql_dump_archive",
        "sha256": sha256,
        "media_type": "application/zip",
        "byte_size": byte_size,
        "metadata_json": {
            "contains": EXTRACTED_SQL_ARTIFACT_NAME,
            "artifact_download_url": UPSTREAM_ARTIFACT_URL,
            "upstream_repository_url": UPSTREAM_REPOSITORY_URL,
        },
    }


def build_sql_dump_source_file_seed(
    *,
    sha256: str,
    byte_size: int,
    source_release_id: str = SOURCE_RELEASE_ID,
) -> dict[str, Any]:
    return {
        "id": stable_uuid("source_file", source_release_id, EXTRACTED_SQL_ARTIFACT_NAME),
        "artifact_name": EXTRACTED_SQL_ARTIFACT_NAME,
        "artifact_role": "sql_dump",
        "sha256": sha256,
        "media_type": "application/sql",
        "byte_size": byte_size,
        "metadata_json": {
            "derived_from": UPSTREAM_ARTIFACT_NAME,
            "artifact_download_url": UPSTREAM_ARTIFACT_URL,
            "upstream_repository_url": UPSTREAM_REPOSITORY_URL,
        },
    }


def translation_id_for_upstream_edition(
    upstream_edition_id: int,
    *,
    source_release_id: str = SOURCE_RELEASE_ID,
) -> str:
    return stable_uuid("translation", source_release_id, upstream_edition_id)


def ayah_translation_id_for_source_row(
    source_ayah_edition_id: int,
    *,
    source_release_id: str = SOURCE_RELEASE_ID,
) -> str:
    return stable_uuid("ayah_translation", source_release_id, source_ayah_edition_id)


def edition_attribution_text(upstream_identifier: str) -> str:
    return (
        "Imported into QuranKit from AbdullahGhanem/quran-database "
        f"({UPSTREAM_COMMIT_SHA}) using upstream edition `{upstream_identifier}`."
    )


def edition_rights_notes(edition_type: str) -> str:
    if edition_type == "quran":
        return (
            "The upstream README states that the Quran text is public domain. "
            "QuranKit still preserves source attribution for every imported row."
        )
    return (
        "Imported for normalization from the upstream edition catalog. "
        "Public exposure remains disabled until attribution and reuse rights are reviewed."
    )
