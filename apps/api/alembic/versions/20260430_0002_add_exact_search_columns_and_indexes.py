"""Add normalized exact-search columns and indexes."""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260430_0002"
down_revision = "20260430_0001"
branch_labels = None
depends_on = None


def _normalized_search_sql(column_name: str, dialect_name: str) -> str:
    bom_function = "char(65279)" if dialect_name == "sqlite" else "chr(65279)"
    return f"lower(trim(replace({column_name}, {bom_function}, '')))"


def upgrade() -> None:
    bind = op.get_bind()
    dialect_name = bind.dialect.name

    with op.batch_alter_table("ayahs") as batch_op:
        batch_op.add_column(
            sa.Column("search_text", sa.Text(), nullable=False, server_default=""),
        )

    with op.batch_alter_table("ayah_translations") as batch_op:
        batch_op.add_column(
            sa.Column("search_text", sa.Text(), nullable=False, server_default=""),
        )

    op.execute(
        f"UPDATE ayahs SET search_text = {_normalized_search_sql('text', dialect_name)}",
    )
    op.execute(
        "UPDATE ayah_translations "
        f"SET search_text = {_normalized_search_sql('text', dialect_name)}",
    )

    op.create_index("ix_ayahs_search_text", "ayahs", ["search_text"], unique=False)
    op.create_index(
        "ix_ayah_translations_search_text",
        "ayah_translations",
        ["search_text"],
        unique=False,
    )

    if dialect_name == "postgresql":
        op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")
        op.execute(
            "CREATE INDEX ix_ayahs_search_text_trgm "
            "ON ayahs USING gin (search_text gin_trgm_ops)",
        )
        op.execute(
            "CREATE INDEX ix_ayah_translations_search_text_trgm "
            "ON ayah_translations USING gin (search_text gin_trgm_ops)",
        )


def downgrade() -> None:
    bind = op.get_bind()
    dialect_name = bind.dialect.name

    if dialect_name == "postgresql":
        op.execute("DROP INDEX IF EXISTS ix_ayah_translations_search_text_trgm")
        op.execute("DROP INDEX IF EXISTS ix_ayahs_search_text_trgm")

    op.drop_index("ix_ayah_translations_search_text", table_name="ayah_translations")
    op.drop_index("ix_ayahs_search_text", table_name="ayahs")

    with op.batch_alter_table("ayah_translations") as batch_op:
        batch_op.drop_column("search_text")

    with op.batch_alter_table("ayahs") as batch_op:
        batch_op.drop_column("search_text")
