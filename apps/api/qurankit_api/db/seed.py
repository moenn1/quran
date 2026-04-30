from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from typing import Any

from sqlalchemy import select
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session

from qurankit_api.db import resolve_database_url, session_scope
from qurankit_api.data.source_metadata import (
    SOURCE_RELEASE_ID,
    UPSTREAM_COMMIT_SHA,
    UPSTREAM_REPOSITORY_URL,
    UPSTREAM_SOURCE_NAME,
    build_archive_source_file_seed,
    build_source_release_seed,
    build_sql_dump_source_file_seed,
)
from qurankit_api.models import SourceFile, SourceRelease


@dataclass(slots=True)
class SeedCounts:
    source_release_id: str | None = None
    source_releases_created: int = 0
    source_files_created: int = 0


def _apply_source_release_fields(
    source_release: SourceRelease,
    seed: dict[str, Any],
    *,
    set_id: bool,
) -> None:
    if set_id:
        source_release.id = seed["id"]
    source_release.source_name = seed["source_name"]
    source_release.repository_url = seed["repository_url"]
    source_release.upstream_commit_sha = seed["upstream_commit_sha"]
    source_release.retrieved_artifact_name = seed["retrieved_artifact_name"]
    source_release.retrieved_artifact_sha256 = seed["retrieved_artifact_sha256"]
    source_release.dump_generated_text = seed["dump_generated_text"]
    source_release.dump_server_version = seed["dump_server_version"]
    source_release.dump_export_tool = seed["dump_export_tool"]
    source_release.notes = seed["notes"]
    source_release.metadata_json = seed["metadata_json"]


def _apply_source_file_fields(
    source_file: SourceFile,
    seed: dict[str, Any],
    *,
    set_id: bool,
) -> None:
    if set_id:
        source_file.id = seed["id"]
    source_file.artifact_name = seed["artifact_name"]
    source_file.artifact_role = seed["artifact_role"]
    source_file.sha256 = seed["sha256"]
    source_file.media_type = seed["media_type"]
    source_file.byte_size = seed["byte_size"]
    source_file.metadata_json = seed["metadata_json"]


def _upsert_source_file(
    session: Session,
    *,
    source_release_id: str,
    seed: dict[str, Any],
    counts: SeedCounts,
) -> None:
    source_file = session.scalar(
        select(SourceFile).where(
            SourceFile.source_release_id == source_release_id,
            SourceFile.artifact_name == seed["artifact_name"],
        ),
    )

    if source_file is None:
        source_file = SourceFile(source_release_id=source_release_id)
        _apply_source_file_fields(source_file, seed, set_id=True)
        session.add(source_file)
        counts.source_files_created += 1
        return

    _apply_source_file_fields(source_file, seed, set_id=False)


def seed_source_metadata(
    session: Session,
    *,
    artifact_byte_size: int | None = None,
    sql_sha256: str | None = None,
    sql_byte_size: int | None = None,
    commit: bool = True,
) -> SeedCounts:
    counts = SeedCounts()
    source_release_seed = build_source_release_seed()
    source_release = session.scalar(
        select(SourceRelease).where(
            SourceRelease.repository_url == UPSTREAM_REPOSITORY_URL,
            SourceRelease.upstream_commit_sha == UPSTREAM_COMMIT_SHA,
            SourceRelease.retrieved_artifact_sha256
            == source_release_seed["retrieved_artifact_sha256"],
        ),
    )

    if source_release is None:
        source_release = SourceRelease(id=SOURCE_RELEASE_ID)
        _apply_source_release_fields(source_release, source_release_seed, set_id=True)
        session.add(source_release)
        session.flush()
        counts.source_releases_created += 1
    else:
        _apply_source_release_fields(source_release, source_release_seed, set_id=False)

    counts.source_release_id = source_release.id

    _upsert_source_file(
        session,
        source_release_id=source_release.id,
        seed=build_archive_source_file_seed(
            byte_size=artifact_byte_size,
            source_release_id=source_release.id,
        ),
        counts=counts,
    )

    if sql_sha256 and sql_byte_size is not None:
        _upsert_source_file(
            session,
            source_release_id=source_release.id,
            seed=build_sql_dump_source_file_seed(
                sha256=sql_sha256,
                byte_size=sql_byte_size,
                source_release_id=source_release.id,
            ),
            counts=counts,
        )

    if commit:
        session.commit()
    else:
        session.flush()
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
