"""Create the initial QuranKit application schema."""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260430_0001"
down_revision = None
branch_labels = None
depends_on = None


TRANSLATION_REVIEW_STATUS = sa.Enum(
    "pending_review",
    "approved",
    "restricted",
    name="translation_review_status",
    native_enum=False,
)

SEMANTIC_EMBEDDING_STATUS = sa.Enum(
    "pending",
    "indexed",
    "failed",
    name="semantic_embedding_status",
    native_enum=False,
)

READING_PLAN_STATUS = sa.Enum(
    "draft",
    "active",
    "paused",
    "completed",
    "archived",
    name="reading_plan_status",
    native_enum=False,
)


def upgrade() -> None:
    current_timestamp = sa.text("CURRENT_TIMESTAMP")

    op.create_table(
        "source_releases",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("source_name", sa.String(length=128), nullable=False),
        sa.Column("repository_url", sa.String(length=512), nullable=False),
        sa.Column("upstream_commit_sha", sa.String(length=64), nullable=False),
        sa.Column("retrieved_artifact_name", sa.String(length=255), nullable=False),
        sa.Column("retrieved_artifact_sha256", sa.String(length=64), nullable=False),
        sa.Column("dump_generated_text", sa.String(length=128), nullable=True),
        sa.Column("dump_server_version", sa.String(length=64), nullable=True),
        sa.Column("dump_export_tool", sa.String(length=128), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("metadata_json", sa.JSON(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=current_timestamp,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=current_timestamp,
        ),
        sa.CheckConstraint(
            "length(retrieved_artifact_sha256) = 64",
            name="ck_source_releases_artifact_sha256_length",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_source_releases"),
        sa.UniqueConstraint(
            "repository_url",
            "upstream_commit_sha",
            "retrieved_artifact_sha256",
            name="source_identity",
        ),
    )

    op.create_table(
        "source_files",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("source_release_id", sa.String(length=36), nullable=False),
        sa.Column("artifact_name", sa.String(length=255), nullable=False),
        sa.Column("artifact_role", sa.String(length=64), nullable=False),
        sa.Column("sha256", sa.String(length=64), nullable=False),
        sa.Column("media_type", sa.String(length=128), nullable=True),
        sa.Column("byte_size", sa.Integer(), nullable=True),
        sa.Column("metadata_json", sa.JSON(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=current_timestamp,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=current_timestamp,
        ),
        sa.CheckConstraint(
            "length(sha256) = 64",
            name="ck_source_files_sha256_length",
        ),
        sa.CheckConstraint(
            "byte_size IS NULL OR byte_size > 0",
            name="ck_source_files_byte_size_positive",
        ),
        sa.ForeignKeyConstraint(
            ["source_release_id"],
            ["source_releases.id"],
            name="fk_source_files_source_release_id_source_releases",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_source_files"),
        sa.UniqueConstraint(
            "source_release_id",
            "artifact_name",
            name="release_artifact_name",
        ),
    )
    op.create_index(
        "ix_source_files_source_release_id",
        "source_files",
        ["source_release_id"],
        unique=False,
    )

    op.create_table(
        "users",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("external_subject", sa.String(length=255), nullable=True),
        sa.Column("email", sa.String(length=320), nullable=True),
        sa.Column("display_name", sa.String(length=255), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=current_timestamp,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=current_timestamp,
        ),
        sa.PrimaryKeyConstraint("id", name="pk_users"),
        sa.UniqueConstraint("email", name="uq_users_email"),
        sa.UniqueConstraint("external_subject", name="uq_users_external_subject"),
    )

    op.create_table(
        "surahs",
        sa.Column("surah_number", sa.Integer(), nullable=False),
        sa.Column("source_release_id", sa.String(length=36), nullable=False),
        sa.Column("source_surah_id", sa.Integer(), nullable=False),
        sa.Column("arabic_name", sa.String(length=255), nullable=False),
        sa.Column("english_name", sa.String(length=255), nullable=False),
        sa.Column("english_name_translation", sa.String(length=255), nullable=False),
        sa.Column("revelation_type", sa.String(length=32), nullable=True),
        sa.Column("ayah_count", sa.Integer(), nullable=False),
        sa.Column("metadata_json", sa.JSON(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=current_timestamp,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=current_timestamp,
        ),
        sa.CheckConstraint(
            "surah_number BETWEEN 1 AND 114",
            name="ck_surahs_surah_number_range",
        ),
        sa.CheckConstraint(
            "source_surah_id > 0",
            name="ck_surahs_source_surah_id_positive",
        ),
        sa.CheckConstraint(
            "ayah_count > 0",
            name="ck_surahs_ayah_count_positive",
        ),
        sa.ForeignKeyConstraint(
            ["source_release_id"],
            ["source_releases.id"],
            name="fk_surahs_source_release_id_source_releases",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("surah_number", name="pk_surahs"),
        sa.UniqueConstraint("source_surah_id", name="uq_surahs_source_surah_id"),
    )
    op.create_index(
        "ix_surahs_source_release_id",
        "surahs",
        ["source_release_id"],
        unique=False,
    )

    op.create_table(
        "translations",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("source_release_id", sa.String(length=36), nullable=False),
        sa.Column("upstream_edition_id", sa.Integer(), nullable=False),
        sa.Column("upstream_identifier", sa.String(length=255), nullable=False),
        sa.Column("language_code", sa.String(length=32), nullable=False),
        sa.Column("translation_name", sa.String(length=255), nullable=False),
        sa.Column("english_name", sa.String(length=255), nullable=False),
        sa.Column("format", sa.String(length=32), nullable=False),
        sa.Column("edition_type", sa.String(length=32), nullable=False),
        sa.Column("attribution_text", sa.Text(), nullable=True),
        sa.Column("attribution_url", sa.String(length=512), nullable=True),
        sa.Column("license_name", sa.String(length=255), nullable=True),
        sa.Column("license_url", sa.String(length=512), nullable=True),
        sa.Column("license_spdx", sa.String(length=64), nullable=True),
        sa.Column("copyright_notice", sa.Text(), nullable=True),
        sa.Column("rights_notes", sa.Text(), nullable=True),
        sa.Column(
            "review_status",
            TRANSLATION_REVIEW_STATUS,
            nullable=False,
            server_default="pending_review",
        ),
        sa.Column(
            "is_public",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
        sa.Column("metadata_json", sa.JSON(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=current_timestamp,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=current_timestamp,
        ),
        sa.CheckConstraint(
            "upstream_edition_id > 0",
            name="ck_translations_upstream_edition_id_positive",
        ),
        sa.CheckConstraint(
            "language_code <> ''",
            name="ck_translations_language_code_not_blank",
        ),
        sa.CheckConstraint(
            "NOT is_public OR review_status = 'approved'",
            name="ck_translations_public_requires_approved_review",
        ),
        sa.ForeignKeyConstraint(
            ["source_release_id"],
            ["source_releases.id"],
            name="fk_translations_source_release_id_source_releases",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_translations"),
        sa.UniqueConstraint(
            "source_release_id",
            "upstream_edition_id",
            name="source_release_edition_id",
        ),
        sa.UniqueConstraint(
            "source_release_id",
            "upstream_identifier",
            name="source_release_identifier",
        ),
    )
    op.create_index(
        "ix_translations_source_release_id",
        "translations",
        ["source_release_id"],
        unique=False,
    )
    op.create_index(
        "ix_translations_language_code",
        "translations",
        ["language_code"],
        unique=False,
    )

    op.create_table(
        "ayahs",
        sa.Column("global_ayah_number", sa.Integer(), nullable=False),
        sa.Column("surah_number", sa.Integer(), nullable=False),
        sa.Column("source_release_id", sa.String(length=36), nullable=False),
        sa.Column("source_ayah_id", sa.Integer(), nullable=False),
        sa.Column("ayah_number", sa.Integer(), nullable=False),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("text_sha256", sa.String(length=64), nullable=False),
        sa.Column("page_number", sa.Integer(), nullable=False),
        sa.Column("juz_number", sa.Integer(), nullable=False),
        sa.Column("hizb_number", sa.Integer(), nullable=False),
        sa.Column("rub_el_hizb_number", sa.Integer(), nullable=False),
        sa.Column(
            "sajda",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
        sa.Column("metadata_json", sa.JSON(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=current_timestamp,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=current_timestamp,
        ),
        sa.CheckConstraint(
            "global_ayah_number BETWEEN 1 AND 6236",
            name="ck_ayahs_global_ayah_number_range",
        ),
        sa.CheckConstraint(
            "source_ayah_id > 0",
            name="ck_ayahs_source_ayah_id_positive",
        ),
        sa.CheckConstraint(
            "ayah_number > 0",
            name="ck_ayahs_ayah_number_positive",
        ),
        sa.CheckConstraint(
            "page_number BETWEEN 1 AND 604",
            name="ck_ayahs_page_number_range",
        ),
        sa.CheckConstraint(
            "juz_number BETWEEN 1 AND 30",
            name="ck_ayahs_juz_number_range",
        ),
        sa.CheckConstraint(
            "hizb_number BETWEEN 1 AND 60",
            name="ck_ayahs_hizb_number_range",
        ),
        sa.CheckConstraint(
            "rub_el_hizb_number BETWEEN 1 AND 240",
            name="ck_ayahs_rub_el_hizb_number_range",
        ),
        sa.CheckConstraint(
            "length(text_sha256) = 64",
            name="ck_ayahs_text_sha256_length",
        ),
        sa.ForeignKeyConstraint(
            ["source_release_id"],
            ["source_releases.id"],
            name="fk_ayahs_source_release_id_source_releases",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["surah_number"],
            ["surahs.surah_number"],
            name="fk_ayahs_surah_number_surahs",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("global_ayah_number", name="pk_ayahs"),
        sa.UniqueConstraint("source_ayah_id", name="uq_ayahs_source_ayah_id"),
        sa.UniqueConstraint("surah_number", "ayah_number", name="surah_ayah_number"),
    )
    op.create_index("ix_ayahs_surah_number", "ayahs", ["surah_number"], unique=False)
    op.create_index(
        "ix_ayahs_source_release_id",
        "ayahs",
        ["source_release_id"],
        unique=False,
    )
    op.create_index(
        "ix_ayahs_page_number",
        "ayahs",
        ["page_number"],
        unique=False,
    )
    op.create_index("ix_ayahs_juz_number", "ayahs", ["juz_number"], unique=False)
    op.create_index("ix_ayahs_hizb_number", "ayahs", ["hizb_number"], unique=False)
    op.create_index(
        "ix_ayahs_rub_el_hizb_number",
        "ayahs",
        ["rub_el_hizb_number"],
        unique=False,
    )

    op.create_table(
        "ayah_translations",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("translation_id", sa.String(length=36), nullable=False),
        sa.Column("ayah_global_number", sa.Integer(), nullable=False),
        sa.Column("source_release_id", sa.String(length=36), nullable=False),
        sa.Column("source_ayah_edition_id", sa.Integer(), nullable=False),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("text_sha256", sa.String(length=64), nullable=False),
        sa.Column("metadata_json", sa.JSON(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=current_timestamp,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=current_timestamp,
        ),
        sa.CheckConstraint(
            "source_ayah_edition_id > 0",
            name="ck_ayah_translations_source_ayah_edition_id_positive",
        ),
        sa.CheckConstraint(
            "length(text_sha256) = 64",
            name="ck_ayah_translations_text_sha256_length",
        ),
        sa.ForeignKeyConstraint(
            ["ayah_global_number"],
            ["ayahs.global_ayah_number"],
            name="fk_ayah_translations_ayah_global_number_ayahs",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["source_release_id"],
            ["source_releases.id"],
            name="fk_ayah_translations_source_release_id_source_releases",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["translation_id"],
            ["translations.id"],
            name="fk_ayah_translations_translation_id_translations",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_ayah_translations"),
        sa.UniqueConstraint(
            "source_release_id",
            "source_ayah_edition_id",
            name="source_release_ayah_edition_id",
        ),
        sa.UniqueConstraint(
            "translation_id",
            "ayah_global_number",
            name="translation_ayah",
        ),
    )
    op.create_index(
        "ix_ayah_translations_translation_id",
        "ayah_translations",
        ["translation_id"],
        unique=False,
    )
    op.create_index(
        "ix_ayah_translations_ayah_global_number",
        "ayah_translations",
        ["ayah_global_number"],
        unique=False,
    )
    op.create_index(
        "ix_ayah_translations_source_release_id",
        "ayah_translations",
        ["source_release_id"],
        unique=False,
    )

    op.create_table(
        "reading_sessions",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column(
            "is_private",
            sa.Boolean(),
            nullable=False,
            server_default=sa.true(),
        ),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("ended_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("started_ayah_global_number", sa.Integer(), nullable=True),
        sa.Column("ended_ayah_global_number", sa.Integer(), nullable=True),
        sa.Column("metadata_json", sa.JSON(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=current_timestamp,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=current_timestamp,
        ),
        sa.CheckConstraint(
            "ended_at IS NULL OR ended_at >= started_at",
            name="ck_reading_sessions_ended_after_started",
        ),
        sa.ForeignKeyConstraint(
            ["ended_ayah_global_number"],
            ["ayahs.global_ayah_number"],
            name="fk_reading_sessions_ended_ayah_global_number_ayahs",
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["started_ayah_global_number"],
            ["ayahs.global_ayah_number"],
            name="fk_reading_sessions_started_ayah_global_number_ayahs",
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name="fk_reading_sessions_user_id_users",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_reading_sessions"),
    )
    op.create_index(
        "ix_reading_sessions_user_id",
        "reading_sessions",
        ["user_id"],
        unique=False,
    )
    op.create_index(
        "ix_reading_sessions_started_ayah_global_number",
        "reading_sessions",
        ["started_ayah_global_number"],
        unique=False,
    )
    op.create_index(
        "ix_reading_sessions_ended_ayah_global_number",
        "reading_sessions",
        ["ended_ayah_global_number"],
        unique=False,
    )

    op.create_table(
        "reading_progress",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column(
            "is_private",
            sa.Boolean(),
            nullable=False,
            server_default=sa.true(),
        ),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("current_ayah_global_number", sa.Integer(), nullable=False),
        sa.Column("source", sa.String(length=64), nullable=True),
        sa.Column("metadata_json", sa.JSON(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=current_timestamp,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=current_timestamp,
        ),
        sa.ForeignKeyConstraint(
            ["current_ayah_global_number"],
            ["ayahs.global_ayah_number"],
            name="fk_reading_progress_current_ayah_global_number_ayahs",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name="fk_reading_progress_user_id_users",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_reading_progress"),
        sa.UniqueConstraint("user_id", name="user_progress"),
    )
    op.create_index(
        "ix_reading_progress_user_id",
        "reading_progress",
        ["user_id"],
        unique=False,
    )
    op.create_index(
        "ix_reading_progress_current_ayah_global_number",
        "reading_progress",
        ["current_ayah_global_number"],
        unique=False,
    )

    op.create_table(
        "reading_plans",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column(
            "is_private",
            sa.Boolean(),
            nullable=False,
            server_default=sa.true(),
        ),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("start_ayah_global_number", sa.Integer(), nullable=False),
        sa.Column("end_ayah_global_number", sa.Integer(), nullable=False),
        sa.Column("start_date", sa.Date(), nullable=True),
        sa.Column("end_date", sa.Date(), nullable=True),
        sa.Column("target_ayahs_per_day", sa.Integer(), nullable=True),
        sa.Column(
            "status",
            READING_PLAN_STATUS,
            nullable=False,
            server_default="draft",
        ),
        sa.Column("metadata_json", sa.JSON(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=current_timestamp,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=current_timestamp,
        ),
        sa.CheckConstraint(
            "end_ayah_global_number >= start_ayah_global_number",
            name="ck_reading_plans_ayah_range_order",
        ),
        sa.CheckConstraint(
            "target_ayahs_per_day IS NULL OR target_ayahs_per_day > 0",
            name="ck_reading_plans_target_ayahs_per_day_positive",
        ),
        sa.CheckConstraint(
            "end_date IS NULL OR start_date IS NULL OR end_date >= start_date",
            name="ck_reading_plans_date_range_order",
        ),
        sa.ForeignKeyConstraint(
            ["end_ayah_global_number"],
            ["ayahs.global_ayah_number"],
            name="fk_reading_plans_end_ayah_global_number_ayahs",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["start_ayah_global_number"],
            ["ayahs.global_ayah_number"],
            name="fk_reading_plans_start_ayah_global_number_ayahs",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name="fk_reading_plans_user_id_users",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_reading_plans"),
    )
    op.create_index(
        "ix_reading_plans_user_id",
        "reading_plans",
        ["user_id"],
        unique=False,
    )
    op.create_index(
        "ix_reading_plans_start_ayah_global_number",
        "reading_plans",
        ["start_ayah_global_number"],
        unique=False,
    )
    op.create_index(
        "ix_reading_plans_end_ayah_global_number",
        "reading_plans",
        ["end_ayah_global_number"],
        unique=False,
    )

    op.create_table(
        "bookmarks",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column(
            "is_private",
            sa.Boolean(),
            nullable=False,
            server_default=sa.true(),
        ),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("ayah_global_number", sa.Integer(), nullable=False),
        sa.Column("label", sa.String(length=255), nullable=True),
        sa.Column("metadata_json", sa.JSON(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=current_timestamp,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=current_timestamp,
        ),
        sa.ForeignKeyConstraint(
            ["ayah_global_number"],
            ["ayahs.global_ayah_number"],
            name="fk_bookmarks_ayah_global_number_ayahs",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name="fk_bookmarks_user_id_users",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_bookmarks"),
        sa.UniqueConstraint("user_id", "ayah_global_number", name="user_ayah"),
    )
    op.create_index("ix_bookmarks_user_id", "bookmarks", ["user_id"], unique=False)
    op.create_index(
        "ix_bookmarks_ayah_global_number",
        "bookmarks",
        ["ayah_global_number"],
        unique=False,
    )

    op.create_table(
        "notes",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column(
            "is_private",
            sa.Boolean(),
            nullable=False,
            server_default=sa.true(),
        ),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("ayah_global_number", sa.Integer(), nullable=True),
        sa.Column("title", sa.String(length=255), nullable=True),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("metadata_json", sa.JSON(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=current_timestamp,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=current_timestamp,
        ),
        sa.ForeignKeyConstraint(
            ["ayah_global_number"],
            ["ayahs.global_ayah_number"],
            name="fk_notes_ayah_global_number_ayahs",
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name="fk_notes_user_id_users",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_notes"),
    )
    op.create_index("ix_notes_user_id", "notes", ["user_id"], unique=False)
    op.create_index(
        "ix_notes_ayah_global_number",
        "notes",
        ["ayah_global_number"],
        unique=False,
    )

    op.create_table(
        "semantic_embeddings",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("ayah_global_number", sa.Integer(), nullable=True),
        sa.Column("ayah_translation_id", sa.String(length=36), nullable=True),
        sa.Column("provider", sa.String(length=128), nullable=False),
        sa.Column("model_name", sa.String(length=128), nullable=False),
        sa.Column("embedding_version", sa.String(length=64), nullable=False),
        sa.Column(
            "status",
            SEMANTIC_EMBEDDING_STATUS,
            nullable=False,
            server_default="pending",
        ),
        sa.Column("indexed_text_sha256", sa.String(length=64), nullable=False),
        sa.Column("index_namespace", sa.String(length=128), nullable=False),
        sa.Column("index_document_id", sa.String(length=255), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("last_indexed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("metadata_json", sa.JSON(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=current_timestamp,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=current_timestamp,
        ),
        sa.CheckConstraint(
            "("
            "(ayah_global_number IS NOT NULL AND ayah_translation_id IS NULL) OR "
            "(ayah_global_number IS NULL AND ayah_translation_id IS NOT NULL)"
            ")",
            name="ck_semantic_embeddings_embedding_target_xor",
        ),
        sa.CheckConstraint(
            "length(indexed_text_sha256) = 64",
            name="ck_semantic_embeddings_indexed_text_sha256_length",
        ),
        sa.ForeignKeyConstraint(
            ["ayah_global_number"],
            ["ayahs.global_ayah_number"],
            name="fk_semantic_embeddings_ayah_global_number_ayahs",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["ayah_translation_id"],
            ["ayah_translations.id"],
            name="fk_semantic_embeddings_ayah_translation_id_ayah_translations",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_semantic_embeddings"),
        sa.UniqueConstraint("index_namespace", "index_document_id", name="namespace_document"),
    )
    op.create_index(
        "ix_semantic_embeddings_ayah_global_number",
        "semantic_embeddings",
        ["ayah_global_number"],
        unique=False,
    )
    op.create_index(
        "ix_semantic_embeddings_ayah_translation_id",
        "semantic_embeddings",
        ["ayah_translation_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_semantic_embeddings_ayah_translation_id", table_name="semantic_embeddings")
    op.drop_index("ix_semantic_embeddings_ayah_global_number", table_name="semantic_embeddings")
    op.drop_table("semantic_embeddings")

    op.drop_index("ix_notes_ayah_global_number", table_name="notes")
    op.drop_index("ix_notes_user_id", table_name="notes")
    op.drop_table("notes")

    op.drop_index("ix_bookmarks_ayah_global_number", table_name="bookmarks")
    op.drop_index("ix_bookmarks_user_id", table_name="bookmarks")
    op.drop_table("bookmarks")

    op.drop_index("ix_reading_plans_end_ayah_global_number", table_name="reading_plans")
    op.drop_index("ix_reading_plans_start_ayah_global_number", table_name="reading_plans")
    op.drop_index("ix_reading_plans_user_id", table_name="reading_plans")
    op.drop_table("reading_plans")

    op.drop_index("ix_reading_progress_current_ayah_global_number", table_name="reading_progress")
    op.drop_index("ix_reading_progress_user_id", table_name="reading_progress")
    op.drop_table("reading_progress")

    op.drop_index("ix_reading_sessions_ended_ayah_global_number", table_name="reading_sessions")
    op.drop_index("ix_reading_sessions_started_ayah_global_number", table_name="reading_sessions")
    op.drop_index("ix_reading_sessions_user_id", table_name="reading_sessions")
    op.drop_table("reading_sessions")

    op.drop_index("ix_ayah_translations_source_release_id", table_name="ayah_translations")
    op.drop_index("ix_ayah_translations_ayah_global_number", table_name="ayah_translations")
    op.drop_index("ix_ayah_translations_translation_id", table_name="ayah_translations")
    op.drop_table("ayah_translations")

    op.drop_index("ix_ayahs_rub_el_hizb_number", table_name="ayahs")
    op.drop_index("ix_ayahs_hizb_number", table_name="ayahs")
    op.drop_index("ix_ayahs_juz_number", table_name="ayahs")
    op.drop_index("ix_ayahs_page_number", table_name="ayahs")
    op.drop_index("ix_ayahs_source_release_id", table_name="ayahs")
    op.drop_index("ix_ayahs_surah_number", table_name="ayahs")
    op.drop_table("ayahs")

    op.drop_index("ix_translations_language_code", table_name="translations")
    op.drop_index("ix_translations_source_release_id", table_name="translations")
    op.drop_table("translations")

    op.drop_index("ix_surahs_source_release_id", table_name="surahs")
    op.drop_table("surahs")

    op.drop_table("users")

    op.drop_index("ix_source_files_source_release_id", table_name="source_files")
    op.drop_table("source_files")

    op.drop_table("source_releases")
