from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from typing import Any

from sqlalchemy import select
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session

from qurankit_api.db import resolve_database_url, session_scope
from qurankit_api.models import SourceFile, SourceRelease


SOURCE_RELEASE_SEED: dict[str, Any] = {
    "source_name": "AbdullahGhanem/quran-database",
    "repository_url": "https://github.com/AbdullahGhanem/quran-database",
    "upstream_commit_sha": "f6c4c805f22b0432677d79aafc12139b915e1a0d",
    "retrieved_artifact_name": "quran.sql.zip",
    "retrieved_artifact_sha256": "ff9033de414a1a18fe42e241dc81f4528c3b194a1e8304d3ac06c9d5b0d7f155",
    "dump_generated_text": "Jun 07, 2018 at 10:43 AM",
    "dump_server_version": "5.7.22",
    "dump_export_tool": "phpMyAdmin 4.7.7",
    "notes": (
        "Bootstrapped from the QuranKit upstream evaluation. "
        "Quran text should remain exact to source, while translation and audio reuse "
        "remain review-gated until attribution and rights checks are complete."
    ),
    "metadata_json": {
        "evaluated_commit_date": "2026-03-09",
        "evaluation_summary_path": "docs/upstream/quran-database-summary.json",
        "evaluation_script": "scripts/analyze_upstream_quran_sql.py",
    },
}

SOURCE_FILE_SEED: dict[str, Any] = {
    "artifact_name": "quran.sql.zip",
    "artifact_role": "sql_dump_archive",
    "sha256": "ff9033de414a1a18fe42e241dc81f4528c3b194a1e8304d3ac06c9d5b0d7f155",
    "media_type": "application/zip",
    "byte_size": None,
    "metadata_json": {
        "contains": "quran.sql",
        "upstream_repository_url": "https://github.com/AbdullahGhanem/quran-database",
    },
}


@dataclass(slots=True)
class SeedCounts:
    source_releases_created: int = 0
    source_files_created: int = 0


def _apply_source_release_fields(source_release: SourceRelease) -> None:
    source_release.source_name = SOURCE_RELEASE_SEED["source_name"]
    source_release.repository_url = SOURCE_RELEASE_SEED["repository_url"]
    source_release.upstream_commit_sha = SOURCE_RELEASE_SEED["upstream_commit_sha"]
    source_release.retrieved_artifact_name = SOURCE_RELEASE_SEED["retrieved_artifact_name"]
    source_release.retrieved_artifact_sha256 = SOURCE_RELEASE_SEED["retrieved_artifact_sha256"]
    source_release.dump_generated_text = SOURCE_RELEASE_SEED["dump_generated_text"]
    source_release.dump_server_version = SOURCE_RELEASE_SEED["dump_server_version"]
    source_release.dump_export_tool = SOURCE_RELEASE_SEED["dump_export_tool"]
    source_release.notes = SOURCE_RELEASE_SEED["notes"]
    source_release.metadata_json = SOURCE_RELEASE_SEED["metadata_json"]


def _apply_source_file_fields(source_file: SourceFile) -> None:
    source_file.artifact_name = SOURCE_FILE_SEED["artifact_name"]
    source_file.artifact_role = SOURCE_FILE_SEED["artifact_role"]
    source_file.sha256 = SOURCE_FILE_SEED["sha256"]
    source_file.media_type = SOURCE_FILE_SEED["media_type"]
    source_file.byte_size = SOURCE_FILE_SEED["byte_size"]
    source_file.metadata_json = SOURCE_FILE_SEED["metadata_json"]


def seed_source_metadata(session: Session) -> SeedCounts:
    counts = SeedCounts()

    source_release = session.scalar(
        select(SourceRelease).where(
            SourceRelease.repository_url == SOURCE_RELEASE_SEED["repository_url"],
            SourceRelease.upstream_commit_sha == SOURCE_RELEASE_SEED["upstream_commit_sha"],
            SourceRelease.retrieved_artifact_sha256 == SOURCE_RELEASE_SEED["retrieved_artifact_sha256"],
        ),
    )

    if source_release is None:
        source_release = SourceRelease()
        _apply_source_release_fields(source_release)
        session.add(source_release)
        session.flush()
        counts.source_releases_created += 1
    else:
        _apply_source_release_fields(source_release)

    source_file = session.scalar(
        select(SourceFile).where(
            SourceFile.source_release_id == source_release.id,
            SourceFile.artifact_name == SOURCE_FILE_SEED["artifact_name"],
        ),
    )

    if source_file is None:
        source_file = SourceFile(source_release_id=source_release.id)
        _apply_source_file_fields(source_file)
        session.add(source_file)
        counts.source_files_created += 1
    else:
        _apply_source_file_fields(source_file)

    session.commit()
    return counts


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Seed QuranKit source-attribution metadata into the configured database.",
    )
    parser.add_argument(
        "--database-url",
        help="Override QURANKIT_DATABASE_URL for this seed run.",
    )
    parser.add_argument(
        "--echo",
        action="store_true",
        help="Enable SQLAlchemy SQL logging.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    database_url = resolve_database_url(args.database_url)

    try:
        with session_scope(database_url, echo=args.echo) as session:
            counts = seed_source_metadata(session)
    except OperationalError as exc:
        raise SystemExit(
            "Database schema is missing. Run scripts/run-db-migrations.sh before seeding source metadata.",
        ) from exc

    print(
        json.dumps(
            {
                "database_url": database_url,
                **asdict(counts),
            },
            indent=2,
        ),
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
