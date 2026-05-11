from __future__ import annotations

import re
from typing import TypeAlias

from fastapi import APIRouter, Depends, Path, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from qurankit_api.core.errors import ApiError
from qurankit_api.db.dependencies import get_db_session
from qurankit_api.models import Ayah, AyahTranslation, SourceRelease, Surah, Translation
from qurankit_api.schemas.browse import (
    AyahResource,
    AyahSurahSummary,
    HizbAyahListResponse,
    JuzAyahListResponse,
    PageAyahListResponse,
    PaginationMeta,
    SourceAttribution,
    SurahAyahListResponse,
    SurahListResponse,
    SurahResource,
    TranslatedAyahResource,
    TranslationAttribution,
)
from qurankit_api.schemas.errors import COMMON_ERROR_RESPONSES, ErrorEnvelope


AyahRow: TypeAlias = tuple[Ayah, Surah, SourceRelease]

AYAH_REFERENCE_RE = re.compile(r"^(?:(?P<global>\d+)|(?P<surah>\d+):(?P<ayah>\d+))$")
AYAH_LIST_LIMIT_DEFAULT = 50
AYAH_LIST_LIMIT_MAX = 200
SURAH_LIST_LIMIT_DEFAULT = 114

BROWSE_ERROR_RESPONSES = {
    **COMMON_ERROR_RESPONSES,
    404: {
        "model": ErrorEnvelope,
        "description": "Requested Quran resource was not found.",
    },
    503: {
        "model": ErrorEnvelope,
        "description": "Database access is unavailable for this API instance.",
    },
}

router = APIRouter(tags=["Quran Browse"])


def _pagination(total: int, limit: int, offset: int) -> PaginationMeta:
    return PaginationMeta(
        total=total,
        limit=limit,
        offset=offset,
        has_more=offset + limit < total,
    )


def _source_resource(source_release: SourceRelease) -> SourceAttribution:
    return SourceAttribution(
        source_release_id=source_release.id,
        source_name=source_release.source_name,
        repository_url=source_release.repository_url,
        upstream_commit_sha=source_release.upstream_commit_sha,
        retrieved_artifact_name=source_release.retrieved_artifact_name,
        retrieved_artifact_sha256=source_release.retrieved_artifact_sha256,
    )


def _translation_resource(translation: Translation) -> TranslationAttribution:
    return TranslationAttribution(
        id=translation.id,
        upstream_identifier=translation.upstream_identifier,
        language_code=translation.language_code,
        translation_name=translation.translation_name,
        english_name=translation.english_name,
        format=translation.format,
        edition_type=translation.edition_type,
        attribution_text=translation.attribution_text,
        attribution_url=translation.attribution_url,
        review_status=translation.review_status.value,
        is_public=translation.is_public,
    )


def _ayah_surah_summary(surah: Surah) -> AyahSurahSummary:
    return AyahSurahSummary(
        surah_number=surah.surah_number,
        arabic_name=surah.arabic_name,
        english_name=surah.english_name,
        english_name_translation=surah.english_name_translation,
        revelation_type=surah.revelation_type,
    )


def _surah_resource(surah: Surah, source_release: SourceRelease) -> SurahResource:
    return SurahResource(
        **_ayah_surah_summary(surah).model_dump(),
        ayah_count=surah.ayah_count,
        source=_source_resource(source_release),
    )


def _ayah_resource(ayah: Ayah, surah: Surah, source_release: SourceRelease) -> AyahResource:
    return AyahResource(
        reference=f"{ayah.surah_number}:{ayah.ayah_number}",
        global_ayah_number=ayah.global_ayah_number,
        ayah_number=ayah.ayah_number,
        text=ayah.text,
        page_number=ayah.page_number,
        juz_number=ayah.juz_number,
        hizb_number=ayah.hizb_number,
        rub_el_hizb_number=ayah.rub_el_hizb_number,
        sajda=ayah.sajda,
        surah=_ayah_surah_summary(surah),
        source=_source_resource(source_release),
    )


def _translated_ayah_resource(
    ayah: Ayah,
    surah: Surah,
    source_release: SourceRelease,
    *,
    translation_text: str | None,
    translation_attribution: TranslationAttribution | None,
) -> TranslatedAyahResource:
    return TranslatedAyahResource(
        **_ayah_resource(ayah, surah, source_release).model_dump(),
        translation_text=translation_text,
        translation_attribution=translation_attribution,
    )


def _surah_not_found(surah_number: int) -> ApiError:
    return ApiError(
        status_code=404,
        code="surah_not_found",
        message=f"Surah {surah_number} was not found.",
        details={"surah_number": surah_number},
    )


def _ayah_not_found(reference: str) -> ApiError:
    return ApiError(
        status_code=404,
        code="ayah_not_found",
        message=f"Ayah reference `{reference}` was not found.",
        details={"reference": reference},
    )


def _collection_not_found(code: str, label: str, number: int) -> ApiError:
    return ApiError(
        status_code=404,
        code=code,
        message=f"{label} {number} has no ayahs in the current QuranKit dataset.",
        details={f"{label.lower()}_number": number},
    )


def _translation_not_found(identifier: str) -> ApiError:
    return ApiError(
        status_code=404,
        code="translation_not_found",
        message=f"Translation edition `{identifier}` was not found.",
        details={"translation_identifier": identifier},
    )


def _unsupported_translation(identifier: str, edition_type: str, edition_format: str) -> ApiError:
    return ApiError(
        status_code=422,
        code="unsupported_translation_edition",
        message="Browse translation must reference a text translation edition.",
        details={
            "translation_identifier": identifier,
            "edition_type": edition_type,
            "format": edition_format,
        },
    )


def _normalized_translation_identifier(value: str | None) -> str | None:
    if value is None:
        return None

    normalized = value.strip().lower()
    return normalized or None


def _resolve_translation_filter(
    session: Session,
    translation_identifier: str | None,
) -> Translation | None:
    normalized_identifier = _normalized_translation_identifier(translation_identifier)
    if normalized_identifier is None:
        return None

    translation = session.scalar(
        select(Translation).where(Translation.upstream_identifier == normalized_identifier),
    )
    if translation is None:
        raise _translation_not_found(normalized_identifier)

    if translation.edition_type != "translation" or translation.format != "text":
        raise _unsupported_translation(
            translation.upstream_identifier,
            translation.edition_type,
            translation.format,
        )

    return translation


def _get_surah(session: Session, surah_number: int) -> tuple[Surah, SourceRelease]:
    row = session.execute(
        select(Surah, SourceRelease)
        .join(SourceRelease, Surah.source_release_id == SourceRelease.id)
        .where(Surah.surah_number == surah_number),
    ).one_or_none()

    if row is None:
        raise _surah_not_found(surah_number)

    return row


def _parse_ayah_reference(reference: str) -> tuple[str, int, int | None]:
    match = AYAH_REFERENCE_RE.fullmatch(reference)
    if match is None:
        raise ApiError(
            status_code=422,
            code="invalid_ayah_reference",
            message="Ayah reference must be a global ayah number or `surah:ayah`.",
            details={
                "reference": reference,
                "accepted_formats": ["123", "2:255"],
            },
        )

    global_ayah = match.group("global")
    if global_ayah is not None:
        return ("global", int(global_ayah), None)

    return ("surah_ayah", int(match.group("surah")), int(match.group("ayah")))


def _ayah_row_for_reference(session: Session, reference: str) -> AyahRow:
    reference_kind, primary, secondary = _parse_ayah_reference(reference)

    statement = (
        select(Ayah, Surah, SourceRelease)
        .join(Surah, Ayah.surah_number == Surah.surah_number)
        .join(SourceRelease, Ayah.source_release_id == SourceRelease.id)
    )

    if reference_kind == "global":
        statement = statement.where(Ayah.global_ayah_number == primary)
    else:
        statement = statement.where(
            Ayah.surah_number == primary,
            Ayah.ayah_number == secondary,
        )

    row = session.execute(statement).one_or_none()
    if row is None:
        raise _ayah_not_found(reference)
    return row


def _ayah_rows_for_collection(
    session: Session,
    *,
    where_clause,
    limit: int,
    offset: int,
) -> list[AyahRow]:
    return list(
        session.execute(
            select(Ayah, Surah, SourceRelease)
            .join(Surah, Ayah.surah_number == Surah.surah_number)
            .join(SourceRelease, Ayah.source_release_id == SourceRelease.id)
            .where(where_clause)
            .order_by(Ayah.global_ayah_number)
            .limit(limit)
            .offset(offset),
        ),
    )


def _translation_text_map(
    session: Session,
    *,
    ayahs: list[Ayah],
    translation: Translation | None,
) -> dict[int, str]:
    if translation is None or not ayahs:
        return {}

    rows = session.execute(
        select(AyahTranslation.ayah_global_number, AyahTranslation.text).where(
            AyahTranslation.translation_id == translation.id,
            AyahTranslation.ayah_global_number.in_(
                [ayah.global_ayah_number for ayah in ayahs],
            ),
        ),
    ).all()

    return {
        global_ayah_number: text
        for global_ayah_number, text in rows
    }


@router.get(
    "/surahs",
    response_model=SurahListResponse,
    responses=BROWSE_ERROR_RESPONSES,
    summary="List Quran surahs",
)
async def list_surahs(
    limit: int = Query(SURAH_LIST_LIMIT_DEFAULT, ge=1, le=SURAH_LIST_LIMIT_DEFAULT),
    offset: int = Query(0, ge=0),
    session: Session = Depends(get_db_session),
) -> SurahListResponse:
    total = int(session.scalar(select(func.count()).select_from(Surah)) or 0)
    rows = session.execute(
        select(Surah, SourceRelease)
        .join(SourceRelease, Surah.source_release_id == SourceRelease.id)
        .order_by(Surah.surah_number)
        .limit(limit)
        .offset(offset),
    ).all()

    return SurahListResponse(
        items=[_surah_resource(surah, source_release) for surah, source_release in rows],
        pagination=_pagination(total, limit, offset),
    )


@router.get(
    "/surahs/{surah_number}",
    response_model=SurahResource,
    responses=BROWSE_ERROR_RESPONSES,
    summary="Read a surah by number",
)
async def read_surah(
    surah_number: int = Path(..., ge=1, le=114),
    session: Session = Depends(get_db_session),
) -> SurahResource:
    surah, source_release = _get_surah(session, surah_number)
    return _surah_resource(surah, source_release)


@router.get(
    "/surahs/{surah_number}/ayahs",
    response_model=SurahAyahListResponse,
    response_model_exclude_none=True,
    responses=BROWSE_ERROR_RESPONSES,
    summary="List ayahs in a surah",
)
async def list_surah_ayahs(
    surah_number: int = Path(..., ge=1, le=114),
    limit: int = Query(AYAH_LIST_LIMIT_DEFAULT, ge=1, le=AYAH_LIST_LIMIT_MAX),
    offset: int = Query(0, ge=0),
    translation: str | None = Query(
        None,
        description="Optional upstream text translation identifier, such as `en.sahih`.",
    ),
    session: Session = Depends(get_db_session),
) -> SurahAyahListResponse:
    surah, source_release = _get_surah(session, surah_number)
    translation_filter = _resolve_translation_filter(session, translation)
    rows = list(
        session.execute(
            select(Ayah, Surah, SourceRelease)
            .join(Surah, Ayah.surah_number == Surah.surah_number)
            .join(SourceRelease, Ayah.source_release_id == SourceRelease.id)
            .where(Ayah.surah_number == surah_number)
            .order_by(Ayah.ayah_number)
            .limit(limit)
            .offset(offset),
        ),
    )
    translation_attribution = (
        _translation_resource(translation_filter) if translation_filter is not None else None
    )
    translation_texts = _translation_text_map(
        session,
        ayahs=[ayah for ayah, _, _ in rows],
        translation=translation_filter,
    )

    return SurahAyahListResponse(
        surah=_surah_resource(surah, source_release),
        items=[
            _translated_ayah_resource(
                ayah,
                row_surah,
                row_source,
                translation_text=translation_texts.get(ayah.global_ayah_number),
                translation_attribution=translation_attribution,
            )
            for ayah, row_surah, row_source in rows
        ],
        pagination=_pagination(surah.ayah_count, limit, offset),
    )


@router.get(
    "/ayahs/random",
    response_model=TranslatedAyahResource,
    response_model_exclude_none=True,
    responses=BROWSE_ERROR_RESPONSES,
    summary="Read a random ayah",
)
async def read_random_ayah(
    translation: str | None = Query(
        None,
        description="Optional upstream text translation identifier, such as `en.sahih`.",
    ),
    session: Session = Depends(get_db_session),
) -> TranslatedAyahResource:
    translation_filter = _resolve_translation_filter(session, translation)
    row = session.execute(
        select(Ayah, Surah, SourceRelease)
        .join(Surah, Ayah.surah_number == Surah.surah_number)
        .join(SourceRelease, Ayah.source_release_id == SourceRelease.id)
        .order_by(func.random())
        .limit(1),
    ).one_or_none()

    if row is None:
        raise _ayah_not_found("random")

    ayah, surah, source_release = row
    translation_attribution = (
        _translation_resource(translation_filter) if translation_filter is not None else None
    )
    translation_text = _translation_text_map(
        session,
        ayahs=[ayah],
        translation=translation_filter,
    ).get(ayah.global_ayah_number)
    return _translated_ayah_resource(
        ayah,
        surah,
        source_release,
        translation_text=translation_text,
        translation_attribution=translation_attribution,
    )


@router.get(
    "/ayahs/{reference}",
    response_model=TranslatedAyahResource,
    response_model_exclude_none=True,
    responses=BROWSE_ERROR_RESPONSES,
    summary="Read an ayah by global or surah-local reference",
)
async def read_ayah(
    reference: str,
    translation: str | None = Query(
        None,
        description="Optional upstream text translation identifier, such as `en.sahih`.",
    ),
    session: Session = Depends(get_db_session),
) -> TranslatedAyahResource:
    translation_filter = _resolve_translation_filter(session, translation)
    ayah, surah, source_release = _ayah_row_for_reference(session, reference)
    translation_attribution = (
        _translation_resource(translation_filter) if translation_filter is not None else None
    )
    translation_text = _translation_text_map(
        session,
        ayahs=[ayah],
        translation=translation_filter,
    ).get(ayah.global_ayah_number)
    return _translated_ayah_resource(
        ayah,
        surah,
        source_release,
        translation_text=translation_text,
        translation_attribution=translation_attribution,
    )


@router.get(
    "/juz/{number}",
    response_model=JuzAyahListResponse,
    response_model_exclude_none=True,
    responses=BROWSE_ERROR_RESPONSES,
    summary="List ayahs in a juz",
)
async def list_juz_ayahs(
    number: int = Path(..., ge=1, le=30),
    limit: int = Query(AYAH_LIST_LIMIT_DEFAULT, ge=1, le=AYAH_LIST_LIMIT_MAX),
    offset: int = Query(0, ge=0),
    translation: str | None = Query(
        None,
        description="Optional upstream text translation identifier, such as `en.sahih`.",
    ),
    session: Session = Depends(get_db_session),
) -> JuzAyahListResponse:
    translation_filter = _resolve_translation_filter(session, translation)
    total = int(
        session.scalar(
            select(func.count()).select_from(Ayah).where(Ayah.juz_number == number),
        )
        or 0
    )
    if total == 0:
        raise _collection_not_found("juz_not_found", "Juz", number)

    rows = _ayah_rows_for_collection(
        session,
        where_clause=Ayah.juz_number == number,
        limit=limit,
        offset=offset,
    )
    translation_attribution = (
        _translation_resource(translation_filter) if translation_filter is not None else None
    )
    translation_texts = _translation_text_map(
        session,
        ayahs=[ayah for ayah, _, _ in rows],
        translation=translation_filter,
    )

    return JuzAyahListResponse(
        juz_number=number,
        items=[
            _translated_ayah_resource(
                ayah,
                surah,
                source_release,
                translation_text=translation_texts.get(ayah.global_ayah_number),
                translation_attribution=translation_attribution,
            )
            for ayah, surah, source_release in rows
        ],
        pagination=_pagination(total, limit, offset),
    )


@router.get(
    "/hizb/{number}",
    response_model=HizbAyahListResponse,
    response_model_exclude_none=True,
    responses=BROWSE_ERROR_RESPONSES,
    summary="List ayahs in a hizb",
)
async def list_hizb_ayahs(
    number: int = Path(..., ge=1, le=60),
    limit: int = Query(AYAH_LIST_LIMIT_DEFAULT, ge=1, le=AYAH_LIST_LIMIT_MAX),
    offset: int = Query(0, ge=0),
    translation: str | None = Query(
        None,
        description="Optional upstream text translation identifier, such as `en.sahih`.",
    ),
    session: Session = Depends(get_db_session),
) -> HizbAyahListResponse:
    translation_filter = _resolve_translation_filter(session, translation)
    total = int(
        session.scalar(
            select(func.count()).select_from(Ayah).where(Ayah.hizb_number == number),
        )
        or 0
    )
    if total == 0:
        raise _collection_not_found("hizb_not_found", "Hizb", number)

    rows = _ayah_rows_for_collection(
        session,
        where_clause=Ayah.hizb_number == number,
        limit=limit,
        offset=offset,
    )
    translation_attribution = (
        _translation_resource(translation_filter) if translation_filter is not None else None
    )
    translation_texts = _translation_text_map(
        session,
        ayahs=[ayah for ayah, _, _ in rows],
        translation=translation_filter,
    )

    return HizbAyahListResponse(
        hizb_number=number,
        items=[
            _translated_ayah_resource(
                ayah,
                surah,
                source_release,
                translation_text=translation_texts.get(ayah.global_ayah_number),
                translation_attribution=translation_attribution,
            )
            for ayah, surah, source_release in rows
        ],
        pagination=_pagination(total, limit, offset),
    )


@router.get(
    "/pages/{number}",
    response_model=PageAyahListResponse,
    response_model_exclude_none=True,
    responses=BROWSE_ERROR_RESPONSES,
    summary="List ayahs on a mushaf page",
)
async def list_page_ayahs(
    number: int = Path(..., ge=1, le=604),
    limit: int = Query(AYAH_LIST_LIMIT_DEFAULT, ge=1, le=AYAH_LIST_LIMIT_MAX),
    offset: int = Query(0, ge=0),
    translation: str | None = Query(
        None,
        description="Optional upstream text translation identifier, such as `en.sahih`.",
    ),
    session: Session = Depends(get_db_session),
) -> PageAyahListResponse:
    translation_filter = _resolve_translation_filter(session, translation)
    total = int(
        session.scalar(
            select(func.count()).select_from(Ayah).where(Ayah.page_number == number),
        )
        or 0
    )
    if total == 0:
        raise _collection_not_found("page_not_found", "Page", number)

    rows = _ayah_rows_for_collection(
        session,
        where_clause=Ayah.page_number == number,
        limit=limit,
        offset=offset,
    )
    translation_attribution = (
        _translation_resource(translation_filter) if translation_filter is not None else None
    )
    translation_texts = _translation_text_map(
        session,
        ayahs=[ayah for ayah, _, _ in rows],
        translation=translation_filter,
    )

    return PageAyahListResponse(
        page_number=number,
        items=[
            _translated_ayah_resource(
                ayah,
                surah,
                source_release,
                translation_text=translation_texts.get(ayah.global_ayah_number),
                translation_attribution=translation_attribution,
            )
            for ayah, surah, source_release in rows
        ],
        pagination=_pagination(total, limit, offset),
    )
