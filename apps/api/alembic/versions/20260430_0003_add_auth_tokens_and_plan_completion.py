"""Add auth token persistence and reading-plan completion tracking."""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260430_0003"
down_revision = "20260430_0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    current_timestamp = sa.text("CURRENT_TIMESTAMP")

    with op.batch_alter_table("users") as batch_op:
        batch_op.add_column(sa.Column("password_hash", sa.String(length=255), nullable=True))
        batch_op.add_column(sa.Column("password_salt", sa.String(length=255), nullable=True))
        batch_op.add_column(
            sa.Column("password_hash_iterations", sa.Integer(), nullable=True),
        )

    op.create_table(
        "auth_tokens",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("token_hash", sa.String(length=64), nullable=False),
        sa.Column("token_prefix", sa.String(length=32), nullable=False),
        sa.Column("last_used_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
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
        sa.CheckConstraint("length(token_hash) = 64", name="ck_auth_tokens_token_hash_length"),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name="fk_auth_tokens_user_id_users",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_auth_tokens"),
        sa.UniqueConstraint("token_hash", name="token_hash"),
    )
    op.create_index("ix_auth_tokens_user_id", "auth_tokens", ["user_id"], unique=False)
    op.create_index("ix_auth_tokens_token_hash", "auth_tokens", ["token_hash"], unique=True)

    with op.batch_alter_table("reading_plans") as batch_op:
        batch_op.add_column(
            sa.Column("completed_through_ayah_global_number", sa.Integer(), nullable=True),
        )
        batch_op.create_foreign_key(
            "fk_reading_plans_completed_through_ayah_global_number_ayahs",
            "ayahs",
            ["completed_through_ayah_global_number"],
            ["global_ayah_number"],
            ondelete="SET NULL",
        )
        batch_op.create_index(
            "ix_reading_plans_completed_through_ayah_global_number",
            ["completed_through_ayah_global_number"],
            unique=False,
        )


def downgrade() -> None:
    with op.batch_alter_table("reading_plans") as batch_op:
        batch_op.drop_index("ix_reading_plans_completed_through_ayah_global_number")
        batch_op.drop_constraint(
            "fk_reading_plans_completed_through_ayah_global_number_ayahs",
            type_="foreignkey",
        )
        batch_op.drop_column("completed_through_ayah_global_number")

    op.drop_index("ix_auth_tokens_token_hash", table_name="auth_tokens")
    op.drop_index("ix_auth_tokens_user_id", table_name="auth_tokens")
    op.drop_table("auth_tokens")

    with op.batch_alter_table("users") as batch_op:
        batch_op.drop_column("password_hash_iterations")
        batch_op.drop_column("password_salt")
        batch_op.drop_column("password_hash")
