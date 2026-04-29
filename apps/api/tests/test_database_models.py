from __future__ import annotations

import hashlib
from datetime import datetime, timezone

import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from qurankit_api.models import (
    Ayah,
    AyahTranslation,
    Bookmark,
    Note,
    ReadingPlan,
    ReadingProgress,
    ReadingSession,
    SemanticEmbedding,
    SourceRelease,
    Surah,
    Translation,
    TranslationReviewStatus,
    User,
)


def _sha256(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _source_release(session: Session) -> SourceRelease:
    source_release = SourceRelease(
        source_name="Upstream Quran Snapshot",
        repository_url="https://example.com/quran-database",
        upstream_commit_sha="a" * 40,
        retrieved_artifact_name="quran.sql.zip",
        retrieved_artifact_sha256="b" * 64,
    )
    session.add(source_release)
    session.flush()
    return source_release


def _surah(session: Session, source_release: SourceRelease) -> Surah:
    surah = Surah(
        surah_number=1,
        source_release_id=source_release.id,
        source_surah_id=1,
        arabic_name="الفاتحة",
        english_name="Al-Fatihah",
        english_name_translation="The Opening",
        revelation_type="meccan",
        ayah_count=7,
    )
    session.add(surah)
    session.flush()
    return surah


def _ayah(session: Session, source_release: SourceRelease, surah: Surah) -> Ayah:
    ayah = Ayah(
        global_ayah_number=1,
        surah_number=surah.surah_number,
        source_release_id=source_release.id,
        source_ayah_id=1,
        ayah_number=1,
        text="بِسْمِ اللَّهِ الرَّحْمَٰنِ الرَّحِيمِ",
        text_sha256=_sha256("بِسْمِ اللَّهِ الرَّحْمَٰنِ الرَّحِيمِ"),
        page_number=1,
        juz_number=1,
        hizb_number=1,
        rub_el_hizb_number=1,
        sajda=False,
    )
    session.add(ayah)
    session.flush()
    return ayah


def _translation(session: Session, source_release: SourceRelease) -> Translation:
    translation = Translation(
        source_release_id=source_release.id,
        upstream_edition_id=1001,
        upstream_identifier="en.example.translation",
        language_code="en",
        translation_name="Example Translation",
        english_name="Example Translation",
        format="text",
        edition_type="translation",
    )
    session.add(translation)
    session.flush()
    return translation


def test_privacy_and_translation_review_defaults(db_session: Session) -> None:
    source_release = _source_release(db_session)
    surah = _surah(db_session, source_release)
    ayah = _ayah(db_session, source_release, surah)
    user = User(email="reader@example.com")
    translation = _translation(db_session, source_release)

    reading_session = ReadingSession(
        user=user,
        started_at=datetime.now(timezone.utc),
        started_ayah_global_number=ayah.global_ayah_number,
    )
    reading_progress = ReadingProgress(
        user=user,
        current_ayah_global_number=ayah.global_ayah_number,
    )
    reading_plan = ReadingPlan(
        user=user,
        title="Start Here",
        start_ayah_global_number=ayah.global_ayah_number,
        end_ayah_global_number=ayah.global_ayah_number,
    )
    bookmark = Bookmark(
        user=user,
        ayah_global_number=ayah.global_ayah_number,
    )
    note = Note(
        user=user,
        ayah_global_number=ayah.global_ayah_number,
        body="Reflect on the opening.",
    )

    db_session.add_all([user, reading_session, reading_progress, reading_plan, bookmark, note])
    db_session.commit()

    assert translation.review_status is TranslationReviewStatus.pending_review
    assert translation.is_public is False
    assert reading_session.is_private is True
    assert reading_progress.is_private is True
    assert reading_plan.is_private is True
    assert bookmark.is_private is True
    assert note.is_private is True


def test_ayah_metadata_ranges_are_enforced(db_session: Session) -> None:
    source_release = _source_release(db_session)
    surah = _surah(db_session, source_release)

    db_session.add(
        Ayah(
            global_ayah_number=2,
            surah_number=surah.surah_number,
            source_release_id=source_release.id,
            source_ayah_id=2,
            ayah_number=2,
            text="الْحَمْدُ لِلَّهِ رَبِّ الْعَالَمِينَ",
            text_sha256=_sha256("الْحَمْدُ لِلَّهِ رَبِّ الْعَالَمِينَ"),
            page_number=605,
            juz_number=1,
            hizb_number=1,
            rub_el_hizb_number=1,
        ),
    )

    with pytest.raises(IntegrityError):
        db_session.commit()


def test_public_translation_requires_approved_review(db_session: Session) -> None:
    source_release = _source_release(db_session)

    db_session.add(
        Translation(
            source_release_id=source_release.id,
            upstream_edition_id=2002,
            upstream_identifier="en.example.public",
            language_code="en",
            translation_name="Public Before Review",
            english_name="Public Before Review",
            format="text",
            edition_type="translation",
            is_public=True,
        ),
    )

    with pytest.raises(IntegrityError):
        db_session.commit()


def test_semantic_embeddings_require_exactly_one_target(db_session: Session) -> None:
    source_release = _source_release(db_session)
    surah = _surah(db_session, source_release)
    ayah = _ayah(db_session, source_release, surah)
    translation = _translation(db_session, source_release)
    ayah_translation = AyahTranslation(
        translation_id=translation.id,
        ayah_global_number=ayah.global_ayah_number,
        source_release_id=source_release.id,
        source_ayah_edition_id=1,
        text="In the name of Allah, the Entirely Merciful, the Especially Merciful.",
        text_sha256=_sha256(
            "In the name of Allah, the Entirely Merciful, the Especially Merciful.",
        ),
    )
    db_session.add(ayah_translation)
    db_session.flush()

    db_session.add(
        SemanticEmbedding(
            ayah_global_number=ayah.global_ayah_number,
            ayah_translation_id=ayah_translation.id,
            provider="openai",
            model_name="text-embedding-3-large",
            embedding_version="2026-04-29",
            indexed_text_sha256=_sha256("duplicate target"),
            index_namespace="ayah-search",
        ),
    )

    with pytest.raises(IntegrityError):
        db_session.commit()
