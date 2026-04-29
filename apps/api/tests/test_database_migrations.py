from sqlalchemy import create_engine, inspect


EXPECTED_TABLES = {
    "ayah_translations",
    "ayahs",
    "bookmarks",
    "notes",
    "reading_plans",
    "reading_progress",
    "reading_sessions",
    "semantic_embeddings",
    "source_files",
    "source_releases",
    "surahs",
    "translations",
    "users",
}


def test_alembic_upgrade_creates_expected_tables_and_columns(
    migrated_database_url: str,
) -> None:
    engine = create_engine(migrated_database_url)
    inspector = inspect(engine)

    assert EXPECTED_TABLES.issubset(set(inspector.get_table_names()))

    ayah_columns = {column["name"] for column in inspector.get_columns("ayahs")}
    translation_columns = {column["name"] for column in inspector.get_columns("translations")}
    bookmark_columns = {column["name"] for column in inspector.get_columns("bookmarks")}

    assert {"global_ayah_number", "text_sha256", "rub_el_hizb_number"} <= ayah_columns
    assert {"review_status", "is_public", "license_name"} <= translation_columns
    assert {"ayah_global_number", "is_private"} <= bookmark_columns

    engine.dispose()
