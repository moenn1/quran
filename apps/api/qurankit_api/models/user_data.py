from __future__ import annotations

from datetime import date, datetime
from enum import StrEnum
from typing import Any

from sqlalchemy import JSON, CheckConstraint, Date, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from qurankit_api.db.base import (
    Base,
    PrivateByDefaultMixin,
    TimestampMixin,
    UUIDPrimaryKeyMixin,
    build_enum,
)


class ReadingPlanStatus(StrEnum):
    draft = "draft"
    active = "active"
    paused = "paused"
    completed = "completed"
    archived = "archived"


class User(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "users"

    external_subject: Mapped[str | None] = mapped_column(String(255), unique=True)
    email: Mapped[str | None] = mapped_column(String(320), unique=True)
    display_name: Mapped[str | None] = mapped_column(String(255))
    password_hash: Mapped[str | None] = mapped_column(String(255))
    password_salt: Mapped[str | None] = mapped_column(String(255))
    password_hash_iterations: Mapped[int | None] = mapped_column(Integer)

    auth_tokens: Mapped[list["AuthToken"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )
    reading_sessions: Mapped[list["ReadingSession"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )
    reading_progress: Mapped["ReadingProgress | None"] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
        uselist=False,
    )
    reading_plans: Mapped[list["ReadingPlan"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )
    bookmarks: Mapped[list["Bookmark"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )
    notes: Mapped[list["Note"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )


class AuthToken(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "auth_tokens"
    __table_args__ = (
        UniqueConstraint("token_hash", name="token_hash"),
        CheckConstraint("length(token_hash) = 64", name="token_hash_length"),
    )

    user_id: Mapped[str] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    token_hash: Mapped[str] = mapped_column(String(64), nullable=False, unique=True, index=True)
    token_prefix: Mapped[str] = mapped_column(String(32), nullable=False)
    last_used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    metadata_json: Mapped[dict[str, Any] | None] = mapped_column(JSON)

    user: Mapped["User"] = relationship(back_populates="auth_tokens")


class ReadingSession(UUIDPrimaryKeyMixin, PrivateByDefaultMixin, TimestampMixin, Base):
    __tablename__ = "reading_sessions"
    __table_args__ = (
        CheckConstraint(
            "ended_at IS NULL OR ended_at >= started_at",
            name="ended_after_started",
        ),
    )

    user_id: Mapped[str] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    started_ayah_global_number: Mapped[int | None] = mapped_column(
        ForeignKey("ayahs.global_ayah_number", ondelete="SET NULL"),
        index=True,
    )
    ended_ayah_global_number: Mapped[int | None] = mapped_column(
        ForeignKey("ayahs.global_ayah_number", ondelete="SET NULL"),
        index=True,
    )
    metadata_json: Mapped[dict[str, Any] | None] = mapped_column(JSON)

    user: Mapped["User"] = relationship(back_populates="reading_sessions")
    started_ayah: Mapped["Ayah | None"] = relationship(
        back_populates="reading_sessions_started",
        foreign_keys=[started_ayah_global_number],
    )
    ended_ayah: Mapped["Ayah | None"] = relationship(
        back_populates="reading_sessions_ended",
        foreign_keys=[ended_ayah_global_number],
    )


class ReadingProgress(UUIDPrimaryKeyMixin, PrivateByDefaultMixin, TimestampMixin, Base):
    __tablename__ = "reading_progress"
    __table_args__ = (
        UniqueConstraint("user_id", name="user_progress"),
    )

    user_id: Mapped[str] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    current_ayah_global_number: Mapped[int] = mapped_column(
        ForeignKey("ayahs.global_ayah_number", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    source: Mapped[str | None] = mapped_column(String(64))
    metadata_json: Mapped[dict[str, Any] | None] = mapped_column(JSON)

    user: Mapped["User"] = relationship(back_populates="reading_progress")
    current_ayah: Mapped["Ayah"] = relationship(back_populates="reading_progress_entries")


class ReadingPlan(UUIDPrimaryKeyMixin, PrivateByDefaultMixin, TimestampMixin, Base):
    __tablename__ = "reading_plans"
    __table_args__ = (
        CheckConstraint(
            "end_ayah_global_number >= start_ayah_global_number",
            name="ayah_range_order",
        ),
        CheckConstraint(
            "target_ayahs_per_day IS NULL OR target_ayahs_per_day > 0",
            name="target_ayahs_per_day_positive",
        ),
        CheckConstraint(
            "end_date IS NULL OR start_date IS NULL OR end_date >= start_date",
            name="date_range_order",
        ),
    )

    user_id: Mapped[str] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    start_ayah_global_number: Mapped[int] = mapped_column(
        ForeignKey("ayahs.global_ayah_number", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    end_ayah_global_number: Mapped[int] = mapped_column(
        ForeignKey("ayahs.global_ayah_number", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    completed_through_ayah_global_number: Mapped[int | None] = mapped_column(
        ForeignKey("ayahs.global_ayah_number", ondelete="SET NULL"),
        index=True,
    )
    start_date: Mapped[date | None] = mapped_column(Date)
    end_date: Mapped[date | None] = mapped_column(Date)
    target_ayahs_per_day: Mapped[int | None] = mapped_column(Integer)
    status: Mapped[ReadingPlanStatus] = mapped_column(
        build_enum(ReadingPlanStatus, "reading_plan_status"),
        nullable=False,
        default=ReadingPlanStatus.draft,
    )
    metadata_json: Mapped[dict[str, Any] | None] = mapped_column(JSON)

    user: Mapped["User"] = relationship(back_populates="reading_plans")
    start_ayah: Mapped["Ayah"] = relationship(
        back_populates="reading_plans_starting_here",
        foreign_keys=[start_ayah_global_number],
    )
    end_ayah: Mapped["Ayah"] = relationship(
        back_populates="reading_plans_ending_here",
        foreign_keys=[end_ayah_global_number],
    )
    completed_through_ayah: Mapped["Ayah | None"] = relationship(
        foreign_keys=[completed_through_ayah_global_number],
    )


class Bookmark(UUIDPrimaryKeyMixin, PrivateByDefaultMixin, TimestampMixin, Base):
    __tablename__ = "bookmarks"
    __table_args__ = (
        UniqueConstraint("user_id", "ayah_global_number", name="user_ayah"),
    )

    user_id: Mapped[str] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    ayah_global_number: Mapped[int] = mapped_column(
        ForeignKey("ayahs.global_ayah_number", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    label: Mapped[str | None] = mapped_column(String(255))
    metadata_json: Mapped[dict[str, Any] | None] = mapped_column(JSON)

    user: Mapped["User"] = relationship(back_populates="bookmarks")
    ayah: Mapped["Ayah"] = relationship(back_populates="bookmarks")


class Note(UUIDPrimaryKeyMixin, PrivateByDefaultMixin, TimestampMixin, Base):
    __tablename__ = "notes"

    user_id: Mapped[str] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    ayah_global_number: Mapped[int | None] = mapped_column(
        ForeignKey("ayahs.global_ayah_number", ondelete="SET NULL"),
        index=True,
    )
    title: Mapped[str | None] = mapped_column(String(255))
    body: Mapped[str] = mapped_column(Text, nullable=False)
    metadata_json: Mapped[dict[str, Any] | None] = mapped_column(JSON)

    user: Mapped["User"] = relationship(back_populates="notes")
    ayah: Mapped["Ayah | None"] = relationship(back_populates="notes")
