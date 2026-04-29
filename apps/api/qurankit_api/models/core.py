from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any

from sqlalchemy import (
    JSON,
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from qurankit_api.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin, build_enum


class TranslationReviewStatus(StrEnum):
    pending_review = "pending_review"
    approved = "approved"
    restricted = "restricted"


class SemanticEmbeddingStatus(StrEnum):
    pending = "pending"
    indexed = "indexed"
    failed = "failed"


class SourceRelease(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "source_releases"
    __table_args__ = (
        UniqueConstraint(
            "repository_url",
            "upstream_commit_sha",
            "retrieved_artifact_sha256",
            name="source_identity",
        ),
        CheckConstraint(
            "length(retrieved_artifact_sha256) = 64",
            name="artifact_sha256_length",
        ),
    )

    source_name: Mapped[str] = mapped_column(String(128), nullable=False)
    repository_url: Mapped[str] = mapped_column(String(512), nullable=False)
    upstream_commit_sha: Mapped[str] = mapped_column(String(64), nullable=False)
    retrieved_artifact_name: Mapped[str] = mapped_column(String(255), nullable=False)
    retrieved_artifact_sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    dump_generated_text: Mapped[str | None] = mapped_column(String(128))
    dump_server_version: Mapped[str | None] = mapped_column(String(64))
    dump_export_tool: Mapped[str | None] = mapped_column(String(128))
    notes: Mapped[str | None] = mapped_column(Text)
    metadata_json: Mapped[dict[str, Any] | None] = mapped_column(JSON)

    source_files: Mapped[list["SourceFile"]] = relationship(
        back_populates="source_release",
        cascade="all, delete-orphan",
    )
    surahs: Mapped[list["Surah"]] = relationship(back_populates="source_release")
    ayahs: Mapped[list["Ayah"]] = relationship(back_populates="source_release")
    translations: Mapped[list["Translation"]] = relationship(back_populates="source_release")
    ayah_translations: Mapped[list["AyahTranslation"]] = relationship(
        back_populates="source_release",
    )


class SourceFile(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "source_files"
    __table_args__ = (
        UniqueConstraint(
            "source_release_id",
            "artifact_name",
            name="release_artifact_name",
        ),
        CheckConstraint("length(sha256) = 64", name="sha256_length"),
        CheckConstraint(
            "byte_size IS NULL OR byte_size > 0",
            name="byte_size_positive",
        ),
    )

    source_release_id: Mapped[str] = mapped_column(
        ForeignKey("source_releases.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    artifact_name: Mapped[str] = mapped_column(String(255), nullable=False)
    artifact_role: Mapped[str] = mapped_column(String(64), nullable=False)
    sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    media_type: Mapped[str | None] = mapped_column(String(128))
    byte_size: Mapped[int | None] = mapped_column(Integer)
    metadata_json: Mapped[dict[str, Any] | None] = mapped_column(JSON)

    source_release: Mapped["SourceRelease"] = relationship(back_populates="source_files")


class Surah(TimestampMixin, Base):
    __tablename__ = "surahs"
    __table_args__ = (
        CheckConstraint("surah_number BETWEEN 1 AND 114", name="surah_number_range"),
        CheckConstraint("source_surah_id > 0", name="source_surah_id_positive"),
        CheckConstraint("ayah_count > 0", name="ayah_count_positive"),
    )

    surah_number: Mapped[int] = mapped_column(Integer, primary_key=True)
    source_release_id: Mapped[str] = mapped_column(
        ForeignKey("source_releases.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    source_surah_id: Mapped[int] = mapped_column(Integer, nullable=False, unique=True)
    arabic_name: Mapped[str] = mapped_column(String(255), nullable=False)
    english_name: Mapped[str] = mapped_column(String(255), nullable=False)
    english_name_translation: Mapped[str] = mapped_column(String(255), nullable=False)
    revelation_type: Mapped[str | None] = mapped_column(String(32))
    ayah_count: Mapped[int] = mapped_column(Integer, nullable=False)
    metadata_json: Mapped[dict[str, Any] | None] = mapped_column(JSON)

    source_release: Mapped["SourceRelease"] = relationship(back_populates="surahs")
    ayahs: Mapped[list["Ayah"]] = relationship(back_populates="surah")


class Ayah(TimestampMixin, Base):
    __tablename__ = "ayahs"
    __table_args__ = (
        UniqueConstraint("surah_number", "ayah_number", name="surah_ayah_number"),
        CheckConstraint(
            "global_ayah_number BETWEEN 1 AND 6236",
            name="global_ayah_number_range",
        ),
        CheckConstraint("source_ayah_id > 0", name="source_ayah_id_positive"),
        CheckConstraint("ayah_number > 0", name="ayah_number_positive"),
        CheckConstraint("page_number BETWEEN 1 AND 604", name="page_number_range"),
        CheckConstraint("juz_number BETWEEN 1 AND 30", name="juz_number_range"),
        CheckConstraint("hizb_number BETWEEN 1 AND 60", name="hizb_number_range"),
        CheckConstraint(
            "rub_el_hizb_number BETWEEN 1 AND 240",
            name="rub_el_hizb_number_range",
        ),
        CheckConstraint("length(text_sha256) = 64", name="text_sha256_length"),
    )

    global_ayah_number: Mapped[int] = mapped_column(Integer, primary_key=True)
    surah_number: Mapped[int] = mapped_column(
        ForeignKey("surahs.surah_number", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    source_release_id: Mapped[str] = mapped_column(
        ForeignKey("source_releases.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    source_ayah_id: Mapped[int] = mapped_column(Integer, nullable=False, unique=True)
    ayah_number: Mapped[int] = mapped_column(Integer, nullable=False)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    text_sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    page_number: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    juz_number: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    hizb_number: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    rub_el_hizb_number: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    sajda: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    metadata_json: Mapped[dict[str, Any] | None] = mapped_column(JSON)

    surah: Mapped["Surah"] = relationship(back_populates="ayahs")
    source_release: Mapped["SourceRelease"] = relationship(back_populates="ayahs")
    ayah_translations: Mapped[list["AyahTranslation"]] = relationship(back_populates="ayah")
    bookmarks: Mapped[list["Bookmark"]] = relationship(back_populates="ayah")
    notes: Mapped[list["Note"]] = relationship(back_populates="ayah")
    reading_sessions_started: Mapped[list["ReadingSession"]] = relationship(
        back_populates="started_ayah",
        foreign_keys="ReadingSession.started_ayah_global_number",
    )
    reading_sessions_ended: Mapped[list["ReadingSession"]] = relationship(
        back_populates="ended_ayah",
        foreign_keys="ReadingSession.ended_ayah_global_number",
    )
    reading_progress_entries: Mapped[list["ReadingProgress"]] = relationship(
        back_populates="current_ayah",
    )
    reading_plans_starting_here: Mapped[list["ReadingPlan"]] = relationship(
        back_populates="start_ayah",
        foreign_keys="ReadingPlan.start_ayah_global_number",
    )
    reading_plans_ending_here: Mapped[list["ReadingPlan"]] = relationship(
        back_populates="end_ayah",
        foreign_keys="ReadingPlan.end_ayah_global_number",
    )
    semantic_embeddings: Mapped[list["SemanticEmbedding"]] = relationship(back_populates="ayah")


class Translation(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "translations"
    __table_args__ = (
        UniqueConstraint(
            "source_release_id",
            "upstream_edition_id",
            name="source_release_edition_id",
        ),
        UniqueConstraint(
            "source_release_id",
            "upstream_identifier",
            name="source_release_identifier",
        ),
        CheckConstraint("upstream_edition_id > 0", name="upstream_edition_id_positive"),
        CheckConstraint("language_code <> ''", name="language_code_not_blank"),
        CheckConstraint(
            "NOT is_public OR review_status = 'approved'",
            name="public_requires_approved_review",
        ),
    )

    source_release_id: Mapped[str] = mapped_column(
        ForeignKey("source_releases.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    upstream_edition_id: Mapped[int] = mapped_column(Integer, nullable=False)
    upstream_identifier: Mapped[str] = mapped_column(String(255), nullable=False)
    language_code: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    translation_name: Mapped[str] = mapped_column(String(255), nullable=False)
    english_name: Mapped[str] = mapped_column(String(255), nullable=False)
    format: Mapped[str] = mapped_column(String(32), nullable=False)
    edition_type: Mapped[str] = mapped_column(String(32), nullable=False)
    attribution_text: Mapped[str | None] = mapped_column(Text)
    attribution_url: Mapped[str | None] = mapped_column(String(512))
    license_name: Mapped[str | None] = mapped_column(String(255))
    license_url: Mapped[str | None] = mapped_column(String(512))
    license_spdx: Mapped[str | None] = mapped_column(String(64))
    copyright_notice: Mapped[str | None] = mapped_column(Text)
    rights_notes: Mapped[str | None] = mapped_column(Text)
    review_status: Mapped[TranslationReviewStatus] = mapped_column(
        build_enum(TranslationReviewStatus, "translation_review_status"),
        nullable=False,
        default=TranslationReviewStatus.pending_review,
    )
    is_public: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    metadata_json: Mapped[dict[str, Any] | None] = mapped_column(JSON)

    source_release: Mapped["SourceRelease"] = relationship(back_populates="translations")
    ayah_translations: Mapped[list["AyahTranslation"]] = relationship(
        back_populates="translation",
        cascade="all, delete-orphan",
    )


class AyahTranslation(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "ayah_translations"
    __table_args__ = (
        UniqueConstraint("translation_id", "ayah_global_number", name="translation_ayah"),
        UniqueConstraint(
            "source_release_id",
            "source_ayah_edition_id",
            name="source_release_ayah_edition_id",
        ),
        CheckConstraint("source_ayah_edition_id > 0", name="source_ayah_edition_id_positive"),
        CheckConstraint("length(text_sha256) = 64", name="text_sha256_length"),
    )

    translation_id: Mapped[str] = mapped_column(
        ForeignKey("translations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    ayah_global_number: Mapped[int] = mapped_column(
        ForeignKey("ayahs.global_ayah_number", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    source_release_id: Mapped[str] = mapped_column(
        ForeignKey("source_releases.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    source_ayah_edition_id: Mapped[int] = mapped_column(Integer, nullable=False)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    text_sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    metadata_json: Mapped[dict[str, Any] | None] = mapped_column(JSON)

    translation: Mapped["Translation"] = relationship(back_populates="ayah_translations")
    ayah: Mapped["Ayah"] = relationship(back_populates="ayah_translations")
    source_release: Mapped["SourceRelease"] = relationship(back_populates="ayah_translations")
    semantic_embeddings: Mapped[list["SemanticEmbedding"]] = relationship(
        back_populates="ayah_translation",
    )


class SemanticEmbedding(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "semantic_embeddings"
    __table_args__ = (
        UniqueConstraint("index_namespace", "index_document_id", name="namespace_document"),
        CheckConstraint(
            "("
            "(ayah_global_number IS NOT NULL AND ayah_translation_id IS NULL) OR "
            "(ayah_global_number IS NULL AND ayah_translation_id IS NOT NULL)"
            ")",
            name="embedding_target_xor",
        ),
        CheckConstraint(
            "length(indexed_text_sha256) = 64",
            name="indexed_text_sha256_length",
        ),
    )

    ayah_global_number: Mapped[int | None] = mapped_column(
        ForeignKey("ayahs.global_ayah_number", ondelete="CASCADE"),
        index=True,
    )
    ayah_translation_id: Mapped[str | None] = mapped_column(
        ForeignKey("ayah_translations.id", ondelete="CASCADE"),
        index=True,
    )
    provider: Mapped[str] = mapped_column(String(128), nullable=False)
    model_name: Mapped[str] = mapped_column(String(128), nullable=False)
    embedding_version: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[SemanticEmbeddingStatus] = mapped_column(
        build_enum(SemanticEmbeddingStatus, "semantic_embedding_status"),
        nullable=False,
        default=SemanticEmbeddingStatus.pending,
    )
    indexed_text_sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    index_namespace: Mapped[str] = mapped_column(String(128), nullable=False)
    index_document_id: Mapped[str | None] = mapped_column(String(255))
    error_message: Mapped[str | None] = mapped_column(Text)
    last_indexed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    metadata_json: Mapped[dict[str, Any] | None] = mapped_column(JSON)

    ayah: Mapped["Ayah | None"] = relationship(back_populates="semantic_embeddings")
    ayah_translation: Mapped["AyahTranslation | None"] = relationship(
        back_populates="semantic_embeddings",
    )
