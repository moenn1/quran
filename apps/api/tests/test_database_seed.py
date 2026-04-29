from sqlalchemy import select
from sqlalchemy.orm import Session

from qurankit_api.db import create_engine_from_url, create_session_factory
from qurankit_api.db.seed import seed_source_metadata
from qurankit_api.models import SourceFile, SourceRelease


def test_seed_source_metadata_is_idempotent(migrated_database_url: str) -> None:
    engine = create_engine_from_url(migrated_database_url)
    session_factory = create_session_factory(engine)

    with session_factory() as session:
        first_run = seed_source_metadata(session)

    with session_factory() as session:
        second_run = seed_source_metadata(session)
        source_release = session.scalar(select(SourceRelease))
        source_file = session.scalar(select(SourceFile))

    assert first_run.source_releases_created == 1
    assert first_run.source_files_created == 1
    assert second_run.source_releases_created == 0
    assert second_run.source_files_created == 0
    assert source_release is not None
    assert source_release.source_name == "AbdullahGhanem/quran-database"
    assert source_release.upstream_commit_sha == "f6c4c805f22b0432677d79aafc12139b915e1a0d"
    assert source_file is not None
    assert source_file.artifact_role == "sql_dump_archive"

    engine.dispose()
