from __future__ import annotations

import argparse
import hashlib
import json
import os
from collections import Counter
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any
from urllib.request import urlopen
from zipfile import ZipFile

from alembic import command
from alembic.config import Config
from sqlalchemy import func, insert, select
from sqlalchemy.exc import OperationalError

from qurankit_api.data.source_metadata import (
    EXTRACTED_SQL_ARTIFACT_NAME,
    SOURCE_RELEASE_ID,
    UPSTREAM_ARTIFACT_NAME,
    UPSTREAM_ARTIFACT_SHA256,
    UPSTREAM_ARTIFACT_URL,
    UPSTREAM_COMMIT_SHA,
    UPSTREAM_REPOSITORY_URL,
    SourceArtifactInfo,
    ayah_translation_id_for_source_row,
    build_archive_source_file_seed,
    build_source_release_seed,
    build_sql_dump_source_file_seed,
    edition_attribution_text,
    edition_rights_notes,
    translation_id_for_upstream_edition,
)
from qurankit_api.data.upstream_sql import iter_zip_sql_table_rows, read_dump_metadata
from qurankit_api.db import resolve_database_url, session_scope
from qurankit_api.db.seed import seed_source_metadata
from qurankit_api.models import (
    Ayah,
    AyahTranslation,
    Surah,
    Translation,
    TranslationReviewStatus,
)


ISSUE_SAMPLE_LIMIT = 12
SQL_BATCH_SIZE = 1_000
SOURCE_TABLES = {"surahs", "ayahs", "editions", "ayah_edition"}

SOURCE_RELEASE_COLUMNS = [
    "id",
    "source_name",
    "repository_url",
    "upstream_commit_sha",
    "retrieved_artifact_name",
    "retrieved_artifact_sha256",
    "dump_generated_text",
    "dump_server_version",
    "dump_export_tool",
    "notes",
    "metadata_json",
]
SOURCE_FILE_COLUMNS = [
    "id",
    "source_release_id",
    "artifact_name",
    "artifact_role",
    "sha256",
    "media_type",
    "byte_size",
    "metadata_json",
]
SURAH_COLUMNS = [
    "surah_number",
    "source_release_id",
    "source_surah_id",
    "arabic_name",
    "english_name",
    "english_name_translation",
    "revelation_type",
    "ayah_count",
    "metadata_json",
]
AYAH_COLUMNS = [
    "global_ayah_number",
    "surah_number",
    "source_release_id",
    "source_ayah_id",
    "ayah_number",
    "text",
    "text_sha256",
    "page_number",
    "juz_number",
    "hizb_number",
    "rub_el_hizb_number",
    "sajda",
    "metadata_json",
]
TRANSLATION_COLUMNS = [
    "id",
    "source_release_id",
    "upstream_edition_id",
    "upstream_identifier",
    "language_code",
    "translation_name",
    "english_name",
    "format",
    "edition_type",
    "attribution_text",
    "attribution_url",
    "license_name",
    "license_url",
    "license_spdx",
    "copyright_notice",
    "rights_notes",
    "review_status",
    "is_public",
    "metadata_json",
]
AYAH_TRANSLATION_COLUMNS = [
    "id",
    "translation_id",
    "ayah_global_number",
    "source_release_id",
    "source_ayah_edition_id",
    "text",
    "text_sha256",
    "metadata_json",
]


@dataclass(frozen=True, slots=True)
class ValidationExpectations:
    surah_count: int = 114
    ayah_count: int = 6236
    page_range: tuple[int, int] = (1, 604)
    juz_range: tuple[int, int] = (1, 30)
    hizb_range: tuple[int, int] = (1, 60)
    rub_el_hizb_range: tuple[int, int] = (1, 240)


@dataclass(frozen=True, slots=True)
class ValidationIssue:
    code: str
    message: str
    context: dict[str, Any] | None = None

    def asdict(self) -> dict[str, Any]:
        payload = {"code": self.code, "message": self.message}
        if self.context:
            payload["context"] = self.context
        return payload


@dataclass(slots=True)
class ValidationReport:
    artifact: SourceArtifactInfo
    counts: dict[str, int]
    ranges: dict[str, Any]
    edition_coverage: dict[str, Any]
    warnings: list[ValidationIssue]
    errors: list[ValidationIssue]

    @property
    def is_valid(self) -> bool:
        return not self.errors

    def asdict(self) -> dict[str, Any]:
        return {
            "ok": self.is_valid,
            "artifact": asdict(self.artifact),
            "counts": self.counts,
            "ranges": self.ranges,
            "edition_coverage": self.edition_coverage,
            "warnings": [issue.asdict() for issue in self.warnings],
            "errors": [issue.asdict() for issue in self.errors],
        }

    def to_text(self) -> str:
        status = "PASS" if self.is_valid else "FAIL"
        lines = [
            f"QuranKit upstream validation: {status}",
            f"Archive: {self.artifact.archive_path}",
            (
                "Dump metadata: "
                f"generated={self.artifact.dump_generated_text or 'unknown'}, "
                f"server={self.artifact.dump_server_version or 'unknown'}, "
                f"tool={self.artifact.dump_export_tool or 'unknown'}"
            ),
            (
                "Counts: "
                f"surahs={self.counts['surahs']} "
                f"ayahs={self.counts['ayahs']} "
                f"editions={self.counts['editions']} "
                f"ayah_edition={self.counts['ayah_edition']}"
            ),
            (
                "Ranges: "
                f"page={_format_range(self.ranges['page'])} "
                f"juz={_format_range(self.ranges['juz'])} "
                f"hizb={_format_range(self.ranges['hizb'])} "
                f"rub_el_hizb={_format_range(self.ranges['rub_el_hizb'])} "
                f"sajda={self.ranges['sajda_count']}"
            ),
            (
                "Edition coverage: "
                f"{self.edition_coverage['complete_editions']}/"
                f"{self.counts['editions']} complete"
            ),
        ]

        if self.warnings:
            lines.append("Warnings:")
            lines.extend(f"- {issue.message}" for issue in self.warnings)

        if self.errors:
            lines.append("Errors:")
            lines.extend(f"- {issue.message}" for issue in self.errors)

        return "\n".join(lines)


@dataclass(slots=True)
class LoadCounts:
    source_release_id: str
    source_releases_created: int
    source_files_created: int
    surahs_loaded: int
    ayahs_loaded: int
    translations_loaded: int
    ayah_translations_loaded: int


def _api_dir() -> Path:
    return Path(__file__).resolve().parents[2]


def default_data_dir() -> Path:
    return _api_dir() / ".data"


def default_artifact_path() -> Path:
    raw = os.environ.get("QURANKIT_UPSTREAM_ARTIFACT_PATH")
    if raw:
        return Path(raw).expanduser()
    return default_data_dir() / "upstream" / UPSTREAM_ARTIFACT_NAME


def default_build_output_dir() -> Path:
    return default_data_dir() / "exports"


def _sha256_file(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1_048_576), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def _sha256_zip_entry(archive_path: Path, *, sql_entry_name: str) -> str:
    hasher = hashlib.sha256()
    with ZipFile(archive_path) as archive:
        with archive.open(sql_entry_name) as handle:
            for chunk in iter(lambda: handle.read(1_048_576), b""):
                hasher.update(chunk)
    return hasher.hexdigest()


def ensure_upstream_artifact(
    artifact_path: Path | None = None,
    *,
    force_download: bool = False,
    verify_checksum: bool = True,
) -> Path:
    path = (artifact_path or default_artifact_path()).expanduser()
    path.parent.mkdir(parents=True, exist_ok=True)

    if path.exists():
        if not verify_checksum:
            return path
        existing_sha = _sha256_file(path)
        if existing_sha == UPSTREAM_ARTIFACT_SHA256:
            return path
        if not force_download:
            raise RuntimeError(
                f"Existing artifact at {path} has SHA-256 {existing_sha}, "
                f"expected {UPSTREAM_ARTIFACT_SHA256}. "
                "Remove it or rerun with --force-download.",
            )

    if artifact_path is not None and not verify_checksum:
        raise RuntimeError(f"Artifact path {path} does not exist.")

    partial_path = path.with_suffix(f"{path.suffix}.partial")
    hasher = hashlib.sha256()

    with urlopen(UPSTREAM_ARTIFACT_URL) as response, partial_path.open("wb") as handle:
        for chunk in iter(lambda: response.read(1_048_576), b""):
            handle.write(chunk)
            hasher.update(chunk)

    downloaded_sha = hasher.hexdigest()
    if downloaded_sha != UPSTREAM_ARTIFACT_SHA256:
        partial_path.unlink(missing_ok=True)
        raise RuntimeError(
            "Downloaded upstream artifact failed checksum verification. "
            f"Expected {UPSTREAM_ARTIFACT_SHA256}, got {downloaded_sha}.",
        )

    partial_path.replace(path)
    return path


def inspect_source_artifact(archive_path: Path) -> SourceArtifactInfo:
    metadata = read_dump_metadata(archive_path, sql_entry_name=EXTRACTED_SQL_ARTIFACT_NAME)

    with ZipFile(archive_path) as archive:
        try:
            sql_info = archive.getinfo(EXTRACTED_SQL_ARTIFACT_NAME)
        except KeyError as exc:
            raise RuntimeError(
                f"{archive_path} does not contain {EXTRACTED_SQL_ARTIFACT_NAME}.",
            ) from exc

    return SourceArtifactInfo(
        archive_path=str(archive_path),
        archive_sha256=_sha256_file(archive_path),
        archive_byte_size=archive_path.stat().st_size,
        sql_artifact_name=EXTRACTED_SQL_ARTIFACT_NAME,
        sql_sha256=_sha256_zip_entry(
            archive_path,
            sql_entry_name=EXTRACTED_SQL_ARTIFACT_NAME,
        ),
        sql_byte_size=sql_info.file_size,
        raw_url=UPSTREAM_ARTIFACT_URL,
        dump_generated_text=metadata.get("generation_time"),
        dump_server_version=metadata.get("server_version"),
        dump_export_tool=metadata.get("dump_export_tool"),
        dump_php_version=metadata.get("php_version"),
        database_name=metadata.get("database_name"),
    )


def validate_upstream_artifact(
    artifact_path: Path,
    *,
    expectations: ValidationExpectations = ValidationExpectations(),
    verify_locked_source: bool = True,
) -> ValidationReport:
    artifact = inspect_source_artifact(artifact_path)
    warnings: list[ValidationIssue] = []
    errors: list[ValidationIssue] = []

    surah_numbers_seen: set[int] = set()
    source_surah_ids_seen: set[int] = set()
    surah_ayah_counts: Counter[int] = Counter()
    first_ayah_text_by_surah: dict[int, str] = {}

    edition_rows: dict[int, dict[str, Any]] = {}
    edition_identifiers_seen: set[str] = set()
    edition_ayah_counts: Counter[int] = Counter()
    seen_ayahs_by_edition: dict[int, bytearray] = {}
    surah_count = 0
    ayah_count = 0
    edition_count = 0
    ayah_edition_count = 0
    sajda_count = 0

    last_source_ayah_id = 0
    last_global_ayah_number = 0
    last_number_in_surah: dict[int, int] = {}
    page_min: int | None = None
    page_max: int | None = None
    juz_min: int | None = None
    juz_max: int | None = None
    rub_min: int | None = None
    rub_max: int | None = None
    hizb_min: int | None = None
    hizb_max: int | None = None

    for table_name, row in iter_zip_sql_table_rows(
        artifact_path,
        sql_entry_name=EXTRACTED_SQL_ARTIFACT_NAME,
        tables=SOURCE_TABLES,
    ):
        if table_name == "surahs":
            surah_count += 1
            source_surah_id = int(row["id"])
            surah_number = int(row["number"])

            if source_surah_id in source_surah_ids_seen:
                _record_issue(
                    errors,
                    "duplicate_source_surah_id",
                    f"Duplicate source surah id {source_surah_id} detected.",
                    {"source_surah_id": source_surah_id},
                )
            if surah_number in surah_numbers_seen:
                _record_issue(
                    errors,
                    "duplicate_surah_number",
                    f"Duplicate surah number {surah_number} detected.",
                    {"surah_number": surah_number},
                )

            source_surah_ids_seen.add(source_surah_id)
            surah_numbers_seen.add(surah_number)
            continue

        if table_name == "ayahs":
            ayah_count += 1
            source_ayah_id = int(row["id"])
            global_ayah_number = int(row["number"])
            surah_id = int(row["surah_id"])
            ayah_number = int(row["number_in_surah"])
            page_number = int(row["page"])
            juz_number = int(row["juz_id"])
            rub_el_hizb_number = int(row["hizb_id"])
            hizb_number = _hizb_number_from_slot(rub_el_hizb_number)

            if source_ayah_id != last_source_ayah_id + 1:
                _record_issue(
                    errors,
                    "source_ayah_id_gap",
                    (
                        f"Expected source ayah id {last_source_ayah_id + 1}, "
                        f"got {source_ayah_id}."
                    ),
                    {"expected": last_source_ayah_id + 1, "actual": source_ayah_id},
                )

            if global_ayah_number != last_global_ayah_number + 1:
                _record_issue(
                    errors,
                    "global_ayah_number_gap",
                    (
                        f"Expected global ayah number {last_global_ayah_number + 1}, "
                        f"got {global_ayah_number}."
                    ),
                    {
                        "expected": last_global_ayah_number + 1,
                        "actual": global_ayah_number,
                    },
                )

            if source_ayah_id != global_ayah_number:
                _record_issue(
                    errors,
                    "source_ayah_global_number_mismatch",
                    (
                        f"Source ayah id {source_ayah_id} does not match "
                        f"global ayah number {global_ayah_number}."
                    ),
                    {
                        "source_ayah_id": source_ayah_id,
                        "global_ayah_number": global_ayah_number,
                    },
                )

            expected_number_in_surah = last_number_in_surah.get(surah_id, 0) + 1
            if ayah_number != expected_number_in_surah:
                _record_issue(
                    errors,
                    "ayah_number_in_surah_gap",
                    (
                        f"Expected ayah number {expected_number_in_surah} in surah {surah_id}, "
                        f"got {ayah_number}."
                    ),
                    {
                        "surah_id": surah_id,
                        "expected": expected_number_in_surah,
                        "actual": ayah_number,
                    },
                )

            last_source_ayah_id = source_ayah_id
            last_global_ayah_number = global_ayah_number
            last_number_in_surah[surah_id] = ayah_number
            surah_ayah_counts[surah_id] += 1
            first_ayah_text_by_surah.setdefault(surah_id, str(row["text"]))

            page_min = page_number if page_min is None else min(page_min, page_number)
            page_max = page_number if page_max is None else max(page_max, page_number)
            juz_min = juz_number if juz_min is None else min(juz_min, juz_number)
            juz_max = juz_number if juz_max is None else max(juz_max, juz_number)
            rub_min = (
                rub_el_hizb_number
                if rub_min is None
                else min(rub_min, rub_el_hizb_number)
            )
            rub_max = (
                rub_el_hizb_number
                if rub_max is None
                else max(rub_max, rub_el_hizb_number)
            )
            hizb_min = hizb_number if hizb_min is None else min(hizb_min, hizb_number)
            hizb_max = hizb_number if hizb_max is None else max(hizb_max, hizb_number)
            if bool(int(row["sajda"])):
                sajda_count += 1
            continue

        if table_name == "editions":
            edition_count += 1
            edition_id = int(row["id"])
            identifier = str(row["identifier"])

            if edition_id in edition_rows:
                _record_issue(
                    errors,
                    "duplicate_edition_id",
                    f"Duplicate edition id {edition_id} detected.",
                    {"edition_id": edition_id},
                )
            if identifier in edition_identifiers_seen:
                _record_issue(
                    errors,
                    "duplicate_edition_identifier",
                    f"Duplicate edition identifier {identifier} detected.",
                    {"identifier": identifier},
                )

            edition_rows[edition_id] = row
            edition_identifiers_seen.add(identifier)
            continue

        if table_name == "ayah_edition":
            ayah_edition_count += 1
            edition_id = int(row["edition_id"])
            ayah_id = int(row["ayah_id"])
            edition_ayah_counts[edition_id] += 1

            if ayah_id < 1 or ayah_id > max(expectations.ayah_count, last_global_ayah_number):
                _record_issue(
                    errors,
                    "ayah_edition_out_of_range_ayah_id",
                    (
                        f"Edition row {row['id']} points to ayah id {ayah_id}, "
                        "which is outside the validated ayah range."
                    ),
                    {
                        "source_ayah_edition_id": int(row["id"]),
                        "ayah_id": ayah_id,
                    },
                )
            seen = seen_ayahs_by_edition.setdefault(
                edition_id,
                bytearray(max(expectations.ayah_count, last_global_ayah_number) + 1),
            )
            if ayah_id >= len(seen):
                seen.extend(b"\x00" * (ayah_id - len(seen) + 1))
            if seen[ayah_id]:
                _record_issue(
                    errors,
                    "duplicate_edition_ayah_pair",
                    (
                        f"Duplicate ayah_edition pair detected for edition {edition_id} "
                        f"and ayah {ayah_id}."
                    ),
                    {"edition_id": edition_id, "ayah_id": ayah_id},
                )
            else:
                seen[ayah_id] = 1
    expected_surah_numbers = set(range(1, expectations.surah_count + 1))
    if verify_locked_source and artifact.archive_sha256 != UPSTREAM_ARTIFACT_SHA256:
        _record_issue(
            errors,
            "artifact_sha_mismatch",
            (
                f"Archive SHA-256 {artifact.archive_sha256} does not match the locked "
                f"source checksum {UPSTREAM_ARTIFACT_SHA256}."
            ),
        )

    if surah_count != expectations.surah_count:
        _record_issue(
            errors,
            "surah_count_mismatch",
            (
                f"Expected {expectations.surah_count} surahs, found {surah_count}."
            ),
            {"expected": expectations.surah_count, "actual": surah_count},
        )

    if ayah_count != expectations.ayah_count:
        _record_issue(
            errors,
            "ayah_count_mismatch",
            f"Expected {expectations.ayah_count} ayahs, found {ayah_count}.",
            {"expected": expectations.ayah_count, "actual": ayah_count},
        )

    if surah_numbers_seen != expected_surah_numbers:
        _record_issue(
            errors,
            "surah_number_set_mismatch",
            (
                "Surah numbers are not the exact expected range "
                f"1..{expectations.surah_count}."
            ),
            {
                "missing": sorted(expected_surah_numbers - surah_numbers_seen)[: ISSUE_SAMPLE_LIMIT],
                "extra": sorted(surah_numbers_seen - expected_surah_numbers)[: ISSUE_SAMPLE_LIMIT],
            },
        )

    if set(surah_ayah_counts) - source_surah_ids_seen:
        _record_issue(
            errors,
            "ayah_surah_reference_missing",
            "One or more ayah rows reference a missing surah id.",
            {
                "missing_source_surah_ids": sorted(
                    set(surah_ayah_counts) - source_surah_ids_seen,
                )[: ISSUE_SAMPLE_LIMIT],
            },
        )

    if (page_min, page_max) != expectations.page_range:
        _record_issue(
            errors,
            "page_range_mismatch",
            (
                f"Expected page range {_format_range(expectations.page_range)}, "
                f"found {_format_range((page_min, page_max))}."
            ),
        )

    if (juz_min, juz_max) != expectations.juz_range:
        _record_issue(
            errors,
            "juz_range_mismatch",
            (
                f"Expected juz range {_format_range(expectations.juz_range)}, "
                f"found {_format_range((juz_min, juz_max))}."
            ),
        )

    if (hizb_min, hizb_max) != expectations.hizb_range:
        _record_issue(
            errors,
            "hizb_range_mismatch",
            (
                f"Expected hizb range {_format_range(expectations.hizb_range)}, "
                f"found {_format_range((hizb_min, hizb_max))}."
            ),
        )

    if (rub_min, rub_max) != expectations.rub_el_hizb_range:
        _record_issue(
            errors,
            "rub_el_hizb_range_mismatch",
            (
                f"Expected rub el hizb range {_format_range(expectations.rub_el_hizb_range)}, "
                f"found {_format_range((rub_min, rub_max))}."
            ),
        )

    unknown_edition_ids = set(edition_ayah_counts) - set(edition_rows)
    if unknown_edition_ids:
        _record_issue(
            errors,
            "ayah_edition_missing_edition",
            "One or more ayah_edition rows reference an edition that is missing from editions.",
            {"edition_ids": sorted(unknown_edition_ids)[: ISSUE_SAMPLE_LIMIT]},
        )

    incomplete_editions: list[dict[str, Any]] = []
    complete_edition_count = 0
    for edition_id, edition_row in sorted(edition_rows.items()):
        seen = seen_ayahs_by_edition.get(edition_id, bytearray(expectations.ayah_count + 1))
        distinct_ayahs = sum(seen[: expectations.ayah_count + 1])
        loaded_rows = edition_ayah_counts.get(edition_id, 0)
        if loaded_rows == expectations.ayah_count and distinct_ayahs == expectations.ayah_count:
            complete_edition_count += 1
            continue

        missing_count = max(expectations.ayah_count - distinct_ayahs, 0)
        incomplete = {
            "edition_id": edition_id,
            "identifier": str(edition_row["identifier"]),
            "loaded_rows": loaded_rows,
            "distinct_ayah_rows": distinct_ayahs,
            "missing_ayah_rows": missing_count,
        }
        incomplete_editions.append(incomplete)
        _record_issue(
            errors,
            "edition_coverage_incomplete",
            (
                f"Edition {edition_row['identifier']} should have {expectations.ayah_count} "
                f"ayah rows but has {loaded_rows} rows and {distinct_ayahs} distinct ayahs."
            ),
            incomplete,
        )

    if first_ayah_text_by_surah.get(1, "").startswith("\ufeff"):
        _record_issue(
            warnings,
            "utf8_bom_on_first_ayah",
            (
                "Surah 1 ayah 1 starts with a UTF-8 BOM in the source dump. "
                "QuranKit preserves the sourced text and records the artifact metadata explicitly."
            ),
        )

    basmala_prefixed_surahs = [
        surah_id
        for surah_id, text in sorted(first_ayah_text_by_surah.items())
        if surah_id not in {1, 9} and _normalized_text(text).startswith("بِسْمِ")
    ]
    if basmala_prefixed_surahs:
        _record_issue(
            warnings,
            "basmala_prefixed_first_ayahs",
            (
                f"{len(basmala_prefixed_surahs)} surah-first ayahs outside surahs 1 and 9 "
                "are basmala-prefixed in the upstream dump."
            ),
            {"sample_surah_ids": basmala_prefixed_surahs[: ISSUE_SAMPLE_LIMIT]},
        )

    _record_issue(
        warnings,
        "edition_rights_review_pending",
        (
            "Translation, tafsir, transliteration, and audio editions remain review-gated "
            "until attribution and reuse rights are confirmed."
        ),
    )

    return ValidationReport(
        artifact=artifact,
        counts={
            "surahs": surah_count,
            "ayahs": ayah_count,
            "editions": edition_count,
            "ayah_edition": ayah_edition_count,
        },
        ranges={
            "page": [page_min, page_max],
            "juz": [juz_min, juz_max],
            "hizb": [hizb_min, hizb_max],
            "rub_el_hizb": [rub_min, rub_max],
            "sajda_count": sajda_count,
        },
        edition_coverage={
            "complete_editions": complete_edition_count,
            "incomplete_editions": incomplete_editions[: ISSUE_SAMPLE_LIMIT],
        },
        warnings=warnings,
        errors=errors,
    )


def _record_issue(
    collection: list[ValidationIssue],
    code: str,
    message: str,
    context: dict[str, Any] | None = None,
) -> None:
    if len(collection) >= ISSUE_SAMPLE_LIMIT:
        return
    collection.append(ValidationIssue(code=code, message=message, context=context))


def _format_range(value: tuple[int | None, int | None] | list[int | None]) -> str:
    start, end = value
    return f"{start}..{end}"


def _normalized_text(value: str | None) -> str:
    if not value:
        return ""
    return value.lstrip("\ufeff").strip()


def _text_sha256(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _hizb_number_from_slot(rub_el_hizb_number: int) -> int:
    return ((rub_el_hizb_number - 1) // 4) + 1


def _row_metadata(
    row: dict[str, Any],
    *,
    extra: dict[str, Any] | None = None,
) -> dict[str, Any] | None:
    metadata: dict[str, Any] = {}
    if row.get("created_at") is not None:
        metadata["source_created_at"] = row["created_at"]
    if row.get("updated_at") is not None:
        metadata["source_updated_at"] = row["updated_at"]
    if extra:
        metadata.update(extra)
    return metadata or None


def _collect_table_rows(artifact_path: Path, table_name: str) -> list[dict[str, Any]]:
    return [
        row
        for _, row in iter_zip_sql_table_rows(
            artifact_path,
            sql_entry_name=EXTRACTED_SQL_ARTIFACT_NAME,
            tables={table_name},
        )
    ]


def normalized_source_release_row() -> dict[str, Any]:
    return build_source_release_seed()


def normalized_source_file_rows(
    artifact: SourceArtifactInfo,
    *,
    source_release_id: str = SOURCE_RELEASE_ID,
) -> list[dict[str, Any]]:
    archive_row = build_archive_source_file_seed(
        byte_size=artifact.archive_byte_size,
        sha256=artifact.archive_sha256,
        source_release_id=source_release_id,
    )
    sql_row = build_sql_dump_source_file_seed(
        sha256=artifact.sql_sha256,
        byte_size=artifact.sql_byte_size,
        source_release_id=source_release_id,
    )
    return [
        {"source_release_id": source_release_id, **archive_row},
        {"source_release_id": source_release_id, **sql_row},
    ]


def normalized_surah_rows(
    artifact_path: Path,
    *,
    source_release_id: str = SOURCE_RELEASE_ID,
) -> list[dict[str, Any]]:
    ayah_rows = _collect_table_rows(artifact_path, "ayahs")
    ayah_count_by_surah = Counter(int(row["surah_id"]) for row in ayah_rows)
    rows: list[dict[str, Any]] = []

    for row in _collect_table_rows(artifact_path, "surahs"):
        source_surah_id = int(row["id"])
        rows.append(
            {
                "surah_number": int(row["number"]),
                "source_release_id": source_release_id,
                "source_surah_id": source_surah_id,
                "arabic_name": str(row["name_ar"]),
                "english_name": str(row["name_en"]),
                "english_name_translation": str(row["name_en_translation"]),
                "revelation_type": str(row["type"]).lower(),
                "ayah_count": ayah_count_by_surah[source_surah_id],
                "metadata_json": _row_metadata(row),
            },
        )

    return rows


def normalized_ayah_rows(
    artifact_path: Path,
    *,
    source_release_id: str = SOURCE_RELEASE_ID,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in _collect_table_rows(artifact_path, "ayahs"):
        text = str(row["text"])
        rub_el_hizb_number = int(row["hizb_id"])
        rows.append(
            {
                "global_ayah_number": int(row["number"]),
                "surah_number": int(row["surah_id"]),
                "source_release_id": source_release_id,
                "source_ayah_id": int(row["id"]),
                "ayah_number": int(row["number_in_surah"]),
                "text": text,
                "text_sha256": _text_sha256(text),
                "page_number": int(row["page"]),
                "juz_number": int(row["juz_id"]),
                "hizb_number": _hizb_number_from_slot(rub_el_hizb_number),
                "rub_el_hizb_number": rub_el_hizb_number,
                "sajda": bool(int(row["sajda"])),
                "metadata_json": _row_metadata(
                    row,
                    extra={"has_leading_bom": text.startswith("\ufeff")},
                ),
            },
        )

    return rows


def normalized_translation_rows(
    artifact_path: Path,
    *,
    source_release_id: str = SOURCE_RELEASE_ID,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in _collect_table_rows(artifact_path, "editions"):
        upstream_edition_id = int(row["id"])
        upstream_identifier = str(row["identifier"])
        edition_type = str(row["type"]).lower()
        rows.append(
            {
                "id": translation_id_for_upstream_edition(
                    upstream_edition_id,
                    source_release_id=source_release_id,
                ),
                "source_release_id": source_release_id,
                "upstream_edition_id": upstream_edition_id,
                "upstream_identifier": upstream_identifier,
                "language_code": str(row["language"]).lower(),
                "translation_name": str(row["name"]),
                "english_name": str(row["englishName"]),
                "format": str(row["format"]).lower(),
                "edition_type": edition_type,
                "attribution_text": edition_attribution_text(upstream_identifier),
                "attribution_url": UPSTREAM_REPOSITORY_URL,
                "license_name": None,
                "license_url": None,
                "license_spdx": None,
                "copyright_notice": None,
                "rights_notes": edition_rights_notes(edition_type),
                "review_status": TranslationReviewStatus.pending_review.value,
                "is_public": False,
                "metadata_json": _row_metadata(row),
            },
        )

    return rows


def iter_normalized_ayah_translation_rows(
    artifact_path: Path,
    *,
    source_release_id: str = SOURCE_RELEASE_ID,
):
    for _, row in iter_zip_sql_table_rows(
        artifact_path,
        sql_entry_name=EXTRACTED_SQL_ARTIFACT_NAME,
        tables={"ayah_edition"},
    ):
        text = str(row["data"])
        upstream_edition_id = int(row["edition_id"])
        source_ayah_edition_id = int(row["id"])
        yield {
            "id": ayah_translation_id_for_source_row(
                source_ayah_edition_id,
                source_release_id=source_release_id,
            ),
            "translation_id": translation_id_for_upstream_edition(
                upstream_edition_id,
                source_release_id=source_release_id,
            ),
            "ayah_global_number": int(row["ayah_id"]),
            "source_release_id": source_release_id,
            "source_ayah_edition_id": source_ayah_edition_id,
            "text": text,
            "text_sha256": _text_sha256(text),
            "metadata_json": _row_metadata(
                row,
                extra={"is_audio": bool(int(row["is_audio"]))},
            ),
        }


def _batched(rows: list[dict[str, Any]] | Any, size: int):
    batch: list[dict[str, Any]] = []
    for row in rows:
        batch.append(row)
        if len(batch) >= size:
            yield batch
            batch = []
    if batch:
        yield batch


def _canonical_table_counts(session) -> dict[str, int]:
    return {
        "surahs": int(session.scalar(select(func.count()).select_from(Surah)) or 0),
        "ayahs": int(session.scalar(select(func.count()).select_from(Ayah)) or 0),
        "translations": int(
            session.scalar(select(func.count()).select_from(Translation)) or 0,
        ),
        "ayah_translations": int(
            session.scalar(select(func.count()).select_from(AyahTranslation)) or 0,
        ),
    }


def load_normalized_dataset(
    database_url: str,
    *,
    artifact_path: Path | None = None,
    expectations: ValidationExpectations = ValidationExpectations(),
    force_download: bool = False,
    validation_report: ValidationReport | None = None,
    verify_locked_source: bool = True,
) -> LoadCounts:
    archive_path = ensure_upstream_artifact(
        artifact_path,
        force_download=force_download,
        verify_checksum=verify_locked_source,
    )
    report = validation_report or validate_upstream_artifact(
        archive_path,
        expectations=expectations,
        verify_locked_source=verify_locked_source,
    )
    if not report.is_valid:
        raise RuntimeError(report.to_text())

    surah_rows = normalized_surah_rows(archive_path)
    ayah_rows = normalized_ayah_rows(archive_path)
    translation_rows = normalized_translation_rows(archive_path)

    try:
        with session_scope(resolve_database_url(database_url)) as session:
            try:
                existing_counts = _canonical_table_counts(session)
                if any(existing_counts.values()):
                    raise RuntimeError(
                        "Canonical Quran tables already contain rows. "
                        "Use a fresh database URL before loading QuranKit data.",
                    )

                seed_counts = seed_source_metadata(
                    session,
                    artifact_byte_size=report.artifact.archive_byte_size,
                    sql_sha256=report.artifact.sql_sha256,
                    sql_byte_size=report.artifact.sql_byte_size,
                    commit=False,
                )
                source_release_id = seed_counts.source_release_id or SOURCE_RELEASE_ID

                session.execute(
                    insert(Surah),
                    [
                        {
                            **row,
                            "source_release_id": source_release_id,
                        }
                        for row in surah_rows
                    ],
                )

                for batch in _batched(
                    [
                        {
                            **row,
                            "source_release_id": source_release_id,
                        }
                        for row in ayah_rows
                    ],
                    SQL_BATCH_SIZE,
                ):
                    session.execute(insert(Ayah), batch)

                session.execute(
                    insert(Translation),
                    [
                        {
                            **row,
                            "id": translation_id_for_upstream_edition(
                                row["upstream_edition_id"],
                                source_release_id=source_release_id,
                            ),
                            "source_release_id": source_release_id,
                        }
                        for row in translation_rows
                    ],
                )

                ayah_translation_count = 0
                for batch in _batched(
                    iter_normalized_ayah_translation_rows(
                        archive_path,
                        source_release_id=source_release_id,
                    ),
                    SQL_BATCH_SIZE,
                ):
                    session.execute(insert(AyahTranslation), batch)
                    ayah_translation_count += len(batch)

                session.commit()
            except Exception:
                session.rollback()
                raise
    except OperationalError as exc:
        raise RuntimeError(
            "Database schema is missing. Run scripts/run-db-migrations.sh before loading QuranKit data.",
        ) from exc

    return LoadCounts(
        source_release_id=seed_counts.source_release_id or SOURCE_RELEASE_ID,
        source_releases_created=seed_counts.source_releases_created,
        source_files_created=seed_counts.source_files_created,
        surahs_loaded=len(surah_rows),
        ayahs_loaded=len(ayah_rows),
        translations_loaded=len(translation_rows),
        ayah_translations_loaded=ayah_translation_count,
    )


def export_json_artifacts(
    output_dir: Path,
    *,
    artifact_path: Path,
    validation_report: ValidationReport | None = None,
    verify_locked_source: bool = True,
) -> dict[str, Any]:
    report = validation_report or validate_upstream_artifact(
        artifact_path,
        verify_locked_source=verify_locked_source,
    )
    if not report.is_valid:
        raise RuntimeError(report.to_text())

    output_dir.mkdir(parents=True, exist_ok=True)
    source_release_row = normalized_source_release_row()
    source_file_rows = normalized_source_file_rows(report.artifact)
    surah_rows = normalized_surah_rows(artifact_path)
    ayah_rows = normalized_ayah_rows(artifact_path)
    translation_rows = normalized_translation_rows(artifact_path)

    source_release_path = output_dir / "source-release.json"
    source_files_path = output_dir / "source-files.json"
    surahs_path = output_dir / "surahs.json"
    ayahs_path = output_dir / "ayahs.jsonl"
    translations_path = output_dir / "translations.json"
    ayah_translations_path = output_dir / "ayah-translations.jsonl"
    manifest_path = output_dir / "manifest.json"

    _write_json(source_release_path, source_release_row)
    _write_json(source_files_path, source_file_rows)
    _write_json(surahs_path, surah_rows)
    _write_json(translations_path, translation_rows)
    _write_jsonl(ayahs_path, ayah_rows)
    _write_jsonl(
        ayah_translations_path,
        iter_normalized_ayah_translation_rows(artifact_path),
    )

    manifest = {
        "source_release": {
            "id": source_release_row["id"],
            "repository_url": source_release_row["repository_url"],
            "upstream_commit_sha": source_release_row["upstream_commit_sha"],
            "retrieved_artifact_sha256": source_release_row["retrieved_artifact_sha256"],
        },
        "counts": report.counts,
        "files": {
            "source_release": {"path": source_release_path.name, "format": "json", "count": 1},
            "source_files": {
                "path": source_files_path.name,
                "format": "json",
                "count": len(source_file_rows),
            },
            "surahs": {"path": surahs_path.name, "format": "json", "count": len(surah_rows)},
            "ayahs": {"path": ayahs_path.name, "format": "jsonl", "count": len(ayah_rows)},
            "translations": {
                "path": translations_path.name,
                "format": "json",
                "count": len(translation_rows),
            },
            "ayah_translations": {
                "path": ayah_translations_path.name,
                "format": "jsonl",
                "count": report.counts["ayah_edition"],
            },
        },
    }
    _write_json(manifest_path, manifest)
    return {"manifest_path": str(manifest_path), "counts": manifest["files"]}


def export_postgres_artifact(
    output_path: Path,
    *,
    artifact_path: Path,
    validation_report: ValidationReport | None = None,
    verify_locked_source: bool = True,
) -> Path:
    report = validation_report or validate_upstream_artifact(
        artifact_path,
        verify_locked_source=verify_locked_source,
    )
    if not report.is_valid:
        raise RuntimeError(report.to_text())

    output_path.parent.mkdir(parents=True, exist_ok=True)
    source_release_row = normalized_source_release_row()
    source_file_rows = normalized_source_file_rows(report.artifact)
    surah_rows = normalized_surah_rows(artifact_path)
    ayah_rows = normalized_ayah_rows(artifact_path)
    translation_rows = normalized_translation_rows(artifact_path)

    with output_path.open("w", encoding="utf-8") as handle:
        handle.write("-- QuranKit normalized PostgreSQL seed export\n")
        handle.write("-- Apply Alembic migrations before importing this file.\n")
        handle.write(f"-- Source repository: {UPSTREAM_REPOSITORY_URL}\n")
        handle.write(f"-- Source commit: {UPSTREAM_COMMIT_SHA}\n\n")
        handle.write("BEGIN;\n\n")

        _write_postgres_insert_block(
            handle,
            "source_releases",
            SOURCE_RELEASE_COLUMNS,
            [source_release_row],
        )
        _write_postgres_insert_block(
            handle,
            "source_files",
            SOURCE_FILE_COLUMNS,
            source_file_rows,
        )
        _write_postgres_insert_block(handle, "surahs", SURAH_COLUMNS, surah_rows)
        _write_postgres_insert_block(handle, "ayahs", AYAH_COLUMNS, ayah_rows)
        _write_postgres_insert_block(
            handle,
            "translations",
            TRANSLATION_COLUMNS,
            translation_rows,
        )
        _write_postgres_insert_block(
            handle,
            "ayah_translations",
            AYAH_TRANSLATION_COLUMNS,
            iter_normalized_ayah_translation_rows(artifact_path),
        )
        handle.write("COMMIT;\n")

    return output_path


def build_data_artifacts(
    output_dir: Path,
    *,
    artifact_path: Path | None = None,
    expectations: ValidationExpectations = ValidationExpectations(),
    force_download: bool = False,
    verify_locked_source: bool = True,
) -> dict[str, Any]:
    archive_path = ensure_upstream_artifact(
        artifact_path,
        force_download=force_download,
        verify_checksum=verify_locked_source,
    )
    report = validate_upstream_artifact(
        archive_path,
        expectations=expectations,
        verify_locked_source=verify_locked_source,
    )
    if not report.is_valid:
        raise RuntimeError(report.to_text())

    output_dir.mkdir(parents=True, exist_ok=True)
    validation_text_path = output_dir / "validation-report.txt"
    validation_json_path = output_dir / "validation-report.json"
    sqlite_path = output_dir / "qurankit.sqlite3"
    postgres_path = output_dir / "qurankit.postgres.sql"
    json_output_dir = output_dir / "json"
    build_manifest_path = output_dir / "build-manifest.json"

    sqlite_path.unlink(missing_ok=True)

    _write_text(validation_text_path, f"{report.to_text()}\n")
    _write_json(validation_json_path, report.asdict())
    _apply_migrations(_sqlite_database_url(sqlite_path))
    load_counts = load_normalized_dataset(
        _sqlite_database_url(sqlite_path),
        artifact_path=archive_path,
        expectations=expectations,
        validation_report=report,
        verify_locked_source=verify_locked_source,
    )
    json_manifest = export_json_artifacts(
        json_output_dir,
        artifact_path=archive_path,
        validation_report=report,
        verify_locked_source=verify_locked_source,
    )
    export_postgres_artifact(
        postgres_path,
        artifact_path=archive_path,
        validation_report=report,
        verify_locked_source=verify_locked_source,
    )

    build_manifest = {
        "artifact_path": str(archive_path),
        "validation_report_text": str(validation_text_path),
        "validation_report_json": str(validation_json_path),
        "sqlite_database": str(sqlite_path),
        "postgres_sql": str(postgres_path),
        "json_manifest": json_manifest["manifest_path"],
        "counts": asdict(load_counts),
    }
    _write_json(build_manifest_path, build_manifest)
    return build_manifest


def _sqlite_database_url(sqlite_path: Path) -> str:
    return f"sqlite+pysqlite:///{sqlite_path}"


def _apply_migrations(database_url: str) -> None:
    api_dir = _api_dir()
    config = Config(str(api_dir / "alembic.ini"))
    config.set_main_option("script_location", str(api_dir / "alembic"))
    config.set_main_option("sqlalchemy.url", database_url)
    command.upgrade(config, "head")


def _write_json(path: Path, payload: Any) -> None:
    path.write_text(
        f"{json.dumps(payload, ensure_ascii=False, indent=2)}\n",
        encoding="utf-8",
    )


def _write_text(path: Path, payload: str) -> None:
    path.write_text(payload, encoding="utf-8")


def _write_jsonl(path: Path, rows) -> None:
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False))
            handle.write("\n")


def _pg_literal(value: Any) -> str:
    if value is None:
        return "NULL"
    if isinstance(value, bool):
        return "TRUE" if value else "FALSE"
    if isinstance(value, (int, float)):
        return str(value)
    if isinstance(value, dict):
        payload = json.dumps(value, ensure_ascii=False, sort_keys=True)
        escaped_payload = payload.replace("'", "''")
        return f"'{escaped_payload}'::jsonb"
    escaped_value = str(value).replace("'", "''")
    return f"'{escaped_value}'"


def _write_postgres_insert_block(handle, table_name: str, columns: list[str], rows) -> None:
    batch: list[str] = []
    for row in rows:
        batch.append(
            "(" + ", ".join(_pg_literal(row.get(column)) for column in columns) + ")",
        )
        if len(batch) >= SQL_BATCH_SIZE:
            _flush_postgres_insert_block(handle, table_name, columns, batch)
            batch = []
    if batch:
        _flush_postgres_insert_block(handle, table_name, columns, batch)


def _flush_postgres_insert_block(
    handle,
    table_name: str,
    columns: list[str],
    batch: list[str],
) -> None:
    handle.write(f"INSERT INTO {table_name} ({', '.join(columns)}) VALUES\n")
    handle.write(",\n".join(batch))
    handle.write(";\n\n")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate, normalize, load, and export QuranKit source data.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    validate_parser = subparsers.add_parser("validate", help="Validate the locked upstream dump.")
    validate_parser.add_argument("--artifact-path", type=Path)
    validate_parser.add_argument(
        "--format",
        choices=("text", "json"),
        default="text",
    )
    validate_parser.add_argument("--output", type=Path)
    validate_parser.add_argument("--force-download", action="store_true")

    load_parser = subparsers.add_parser("load", help="Load normalized Quran data into a database.")
    load_parser.add_argument("--artifact-path", type=Path)
    load_parser.add_argument("--database-url")
    load_parser.add_argument("--force-download", action="store_true")

    build_parser = subparsers.add_parser(
        "build",
        help="Build SQLite, JSON, and PostgreSQL artifacts from the locked upstream dump.",
    )
    build_parser.add_argument("--artifact-path", type=Path)
    build_parser.add_argument("--output-dir", type=Path, default=default_build_output_dir())
    build_parser.add_argument("--force-download", action="store_true")

    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)

    if args.command == "validate":
        archive_path = ensure_upstream_artifact(
            args.artifact_path,
            force_download=args.force_download,
            verify_checksum=True,
        )
        report = validate_upstream_artifact(archive_path, verify_locked_source=True)
        payload = (
            report.to_text()
            if args.format == "text"
            else json.dumps(report.asdict(), ensure_ascii=False, indent=2)
        )
        if args.output:
            if args.format == "text":
                _write_text(args.output, f"{payload}\n")
            else:
                _write_json(args.output, report.asdict())
        print(payload)
        return 0 if report.is_valid else 1

    if args.command == "load":
        counts = load_normalized_dataset(
            args.database_url,
            artifact_path=args.artifact_path,
            force_download=args.force_download,
            verify_locked_source=True,
        )
        print(json.dumps(asdict(counts), ensure_ascii=False, indent=2))
        return 0

    if args.command == "build":
        manifest = build_data_artifacts(
            args.output_dir,
            artifact_path=args.artifact_path,
            force_download=args.force_download,
            verify_locked_source=True,
        )
        print(json.dumps(manifest, ensure_ascii=False, indent=2))
        return 0

    raise RuntimeError(f"Unsupported command {args.command!r}")


if __name__ == "__main__":
    raise SystemExit(main())
