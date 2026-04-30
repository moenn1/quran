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
    ayah_translation_columns = {
        column["name"] for column in inspector.get_columns("ayah_translations")
    }
    translation_columns = {column["name"] for column in inspector.get_columns("translations")}
    bookmark_columns = {column["name"] for column in inspector.get_columns("bookmarks")}
    ayah_indexes = {index["name"] for index in inspector.get_indexes("ayahs")}
    ayah_translation_indexes = {
        index["name"] for index in inspector.get_indexes("ayah_translations")
    }

    assert {
        "global_ayah_number",
        "search_text",
        "text_sha256",
        "rub_el_hizb_number",
    } <= ayah_columns
    assert {"search_text", "text_sha256"} <= ayah_translation_columns
    assert {"review_status", "is_public", "license_name"} <= translation_columns
    assert {"ayah_global_number", "is_private"} <= bookmark_columns
    assert "ix_ayahs_search_text" in ayah_indexes
    assert "ix_ayah_translations_search_text" in ayah_translation_indexes

    engine.dispose()
