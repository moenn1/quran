from __future__ import annotations

from collections import defaultdict
from enum import StrEnum
from typing import TypeAlias

from fastapi import APIRouter, Depends, Query
from sqlalchemy import case, func, or_, select, union_all
from sqlalchemy.orm import Session

from qurankit_api.core.errors import ApiError
from qurankit_api.core.search import build_highlight, clean_search_query, normalize_search_text
from qurankit_api.db.dependencies import get_db_session
from qurankit_api.models import Ayah, AyahTranslation, SourceRelease, Surah, Translation
from qurankit_api.schemas.browse import (
    AyahResource,
    AyahSurahSummary,
    PaginationMeta,
    SourceAttribution,
)
from qurankit_api.schemas.errors import COMMON_ERROR_RESPONSES, ErrorEnvelope
from qurankit_api.schemas.search import (
    EditionAttribution,
    ExactSearchHitResource,
    ExactSearchResponse,
    SearchField,
    SearchFilters,
    SearchHighlight,
)


AyahRow: TypeAlias = tuple[Ayah, Surah, SourceRelease]

SEARCH_LIMIT_DEFAULT = 20
SEARCH_LIMIT_MAX = 100
HIGHLIGHT_LIMIT_PER_AYAH = 6
HIGHLIGHT_LIMIT_PER_FIELD = 3
MATCH_AYAH_ID_COLUMN = "ayah_global_number"
SEARCH_FIELD_ALIASES = {
    "normalized_text": SearchField.simple_text,
}
SEARCH_FIELD_ORDER = (
    SearchField.arabic_text,
    SearchField.simple_text,
    SearchField.translation,
)

SEARCH_ERROR_RESPONSES = {
    **COMMON_ERROR_RESPONSES,
    404: {
        "model": ErrorEnvelope,
        "description": "Requested search edition filter was not found.",
    },
    503: {
        "model": ErrorEnvelope,
        "description": "Database access is unavailable for this API instance.",
    },
}

router = APIRouter(tags=["Quran Search"])


class SupportedEditionType(StrEnum):
    quran = "quran"
    translation = "translation"


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


def _ayah_surah_summary(surah: Surah) -> AyahSurahSummary:
    return AyahSurahSummary(
        surah_number=surah.surah_number,
        arabic_name=surah.arabic_name,
        english_name=surah.english_name,
        english_name_translation=surah.english_name_translation,
        revelation_type=surah.revelation_type,
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


def _edition_attribution(translation: Translation) -> EditionAttribution:
    return EditionAttribution(
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


def _translation_not_found(identifier: str) -> ApiError:
    return ApiError(
        status_code=404,
        code="translation_not_found",
        message=f"Search edition `{identifier}` was not found.",
        details={"translation_identifier": identifier},
    )


def _invalid_search_query() -> ApiError:
    return ApiError(
        status_code=422,
        code="invalid_search_query",
        message="Query cannot be empty.",
        details={"parameter": "q"},
    )


def _invalid_search_field(field_name: str) -> ApiError:
    return ApiError(
        status_code=422,
        code="invalid_search_field",
        message=(
            "Search field must be one of `arabic_text`, `simple_text`, "
            "`normalized_text`, or `translation`."
        ),
        details={"field": field_name},
    )


def _unsupported_search_edition(identifier: str, edition_type: str) -> ApiError:
    return ApiError(
        status_code=422,
        code="unsupported_search_edition",
        message=(
            "Exact search currently supports only translation editions and Quran "
            "simple-text editions."
        ),
        details={
            "translation_identifier": identifier,
            "edition_type": edition_type,
        },
    )


def _parse_search_fields(raw_fields: list[str] | None) -> list[SearchField]:
    if raw_fields is None:
        return []

    parsed: list[SearchField] = []
    seen: set[SearchField] = set()
    for raw_value in raw_fields:
        for part in raw_value.split(","):
            normalized = part.strip().lower()
            if not normalized:
                continue

            field = SEARCH_FIELD_ALIASES.get(normalized)
            if field is None:
                try:
                    field = SearchField(normalized)
                except ValueError as exc:
                    raise _invalid_search_field(normalized) from exc

            if field not in seen:
                parsed.append(field)
                seen.add(field)

    if not parsed:
        raise _invalid_search_field("")

    return parsed


def _normalized_filter_value(value: str | None) -> str | None:
    if value is None:
        return None

    normalized = value.strip().lower()
    return normalized or None


def _resolve_translation_filter(
    session: Session,
    translation_identifier: str | None,
) -> Translation | None:
    if translation_identifier is None:
        return None

    translation = session.scalar(
        select(Translation).where(Translation.upstream_identifier == translation_identifier),
    )
    if translation is None:
        raise _translation_not_found(translation_identifier)

    if translation.edition_type not in {
        SupportedEditionType.quran.value,
        SupportedEditionType.translation.value,
    }:
        raise _unsupported_search_edition(
            translation_identifier,
            translation.edition_type,
        )

    return translation


def _resolve_search_fields(
    requested_fields: list[SearchField],
    *,
    language_code: str | None,
    translation_filter: Translation | None,
) -> list[SearchField]:
    if requested_fields:
        return requested_fields

    if translation_filter is not None:
        if translation_filter.edition_type == SupportedEditionType.quran.value:
            return [SearchField.simple_text]
        return [SearchField.translation]

    if language_code is not None:
        return [SearchField.simple_text, SearchField.translation]

    return list(SEARCH_FIELD_ORDER)


def _validate_search_filters(
    search_fields: list[SearchField],
    *,
    translation_filter: Translation | None,
) -> None:
    if translation_filter is None:
        return

    expected_field = (
        SearchField.simple_text
        if translation_filter.edition_type == SupportedEditionType.quran.value
        else SearchField.translation
    )
    if expected_field not in search_fields:
        raise ApiError(
            status_code=422,
            code="invalid_search_filters",
            message=(
                f"Edition `{translation_filter.upstream_identifier}` can only be searched "
                f"through `{expected_field.value}`."
            ),
            details={
                "translation_identifier": translation_filter.upstream_identifier,
                "expected_field": expected_field.value,
            },
        )


def _ayah_match_id_select(query: str):
    return select(
        Ayah.global_ayah_number.label(MATCH_AYAH_ID_COLUMN),
    ).where(Ayah.search_text.contains(query))


def _edition_match_id_select(
    query: str,
    *,
    search_fields: list[SearchField],
    language_code: str | None,
    translation_filter: Translation | None,
):
    edition_types: list[str] = []
    if SearchField.simple_text in search_fields:
        edition_types.append(SupportedEditionType.quran.value)
    if SearchField.translation in search_fields:
        edition_types.append(SupportedEditionType.translation.value)

    if not edition_types:
        return None

    statement = (
        select(
            AyahTranslation.ayah_global_number.label(MATCH_AYAH_ID_COLUMN),
        )
        .join(Translation, AyahTranslation.translation_id == Translation.id)
        .where(
            Translation.format == "text",
            Translation.edition_type.in_(edition_types),
            AyahTranslation.search_text.contains(query),
        )
    )
    if language_code is not None:
        statement = statement.where(Translation.language_code == language_code)
    if translation_filter is not None:
        statement = statement.where(Translation.id == translation_filter.id)

    return statement


@router.get(
    "/search/exact",
    response_model=ExactSearchResponse,
    responses=SEARCH_ERROR_RESPONSES,
    summary="Run an exact Quran search",
)
async def search_exact(
    q: str = Query(..., description="Exact substring to search for."),
    field: list[str] | None = Query(
        None,
        description=(
            "Repeat to restrict search fields. Supported values are `arabic_text`, "
            "`simple_text`, `normalized_text`, and `translation`."
        ),
    ),
    language: str | None = Query(
        None,
        description="Optional edition language code filter, such as `en` or `ar`.",
    ),
    translation: str | None = Query(
        None,
        description=(
            "Optional upstream edition identifier filter, such as `en.sahih` or "
            "`quran-simple`."
        ),
    ),
    limit: int = Query(SEARCH_LIMIT_DEFAULT, ge=1, le=SEARCH_LIMIT_MAX),
    offset: int = Query(0, ge=0),
    session: Session = Depends(get_db_session),
) -> ExactSearchResponse:
    try:
        cleaned_query = clean_search_query(q)
    except ValueError as exc:
        raise _invalid_search_query() from exc

    normalized_query = normalize_search_text(cleaned_query)
    language_code = _normalized_filter_value(language)
    translation_identifier = _normalized_filter_value(translation)
    translation_filter = _resolve_translation_filter(session, translation_identifier)
    requested_fields = _parse_search_fields(field)
    search_fields = _resolve_search_fields(
        requested_fields,
        language_code=language_code,
        translation_filter=translation_filter,
    )
    _validate_search_filters(
        search_fields,
        translation_filter=translation_filter,
    )

    id_selects = []
    if SearchField.arabic_text in search_fields:
        id_selects.append(_ayah_match_id_select(normalized_query))

    edition_id_select = _edition_match_id_select(
        normalized_query,
        search_fields=search_fields,
        language_code=language_code,
        translation_filter=translation_filter,
    )
    if edition_id_select is not None:
        id_selects.append(edition_id_select)

    if len(id_selects) == 1:
        match_id_subquery = id_selects[0].subquery()
    else:
        match_id_subquery = union_all(*id_selects).subquery()

    distinct_match_ids = (
        select(match_id_subquery.c[MATCH_AYAH_ID_COLUMN])
        .distinct()
        .subquery()
    )
    total = int(
        session.scalar(select(func.count()).select_from(distinct_match_ids)) or 0,
    )
    selected_ids = list(
        session.scalars(
            select(distinct_match_ids.c[MATCH_AYAH_ID_COLUMN])
            .order_by(distinct_match_ids.c[MATCH_AYAH_ID_COLUMN])
            .limit(limit)
            .offset(offset),
        ),
    )

    results: list[ExactSearchHitResource] = []
    edition_attributions: dict[str, EditionAttribution] = {}
    translation_attribution = None
    if translation_filter is not None:
        edition_summary = _edition_attribution(translation_filter)
        edition_attributions[translation_filter.id] = edition_summary
        if translation_filter.edition_type == SupportedEditionType.translation.value:
            translation_attribution = edition_summary

    arabic_source = None
    if selected_ids:
        ayah_rows = list(
            session.execute(
                select(Ayah, Surah, SourceRelease)
                .join(Surah, Ayah.surah_number == Surah.surah_number)
                .join(SourceRelease, Ayah.source_release_id == SourceRelease.id)
                .where(Ayah.global_ayah_number.in_(selected_ids))
                .order_by(Ayah.global_ayah_number),
            ),
        )
        ayah_by_id = {
            ayah.global_ayah_number: (ayah, surah, source_release)
            for ayah, surah, source_release in ayah_rows
        }

        matched_fields: dict[int, set[SearchField]] = defaultdict(set)
        matched_highlights: dict[int, list[SearchHighlight]] = defaultdict(list)
        per_field_highlights: dict[tuple[int, SearchField], int] = defaultdict(int)

        if SearchField.arabic_text in search_fields:
            for ayah_id in selected_ids:
                ayah, _, _ = ayah_by_id[ayah_id]
                if normalized_query not in ayah.search_text:
                    continue

                matched_fields[ayah_id].add(SearchField.arabic_text)
                highlight = build_highlight(ayah.text, cleaned_query)
                if highlight is None:
                    continue

                matched_highlights[ayah_id].append(
                    SearchHighlight(
                        field=SearchField.arabic_text,
                        text=ayah.text,
                        excerpt=highlight.excerpt,
                        match_start=highlight.match_start,
                        match_end=highlight.match_end,
                    ),
                )

        needs_edition_matches = any(
            field_name in search_fields
            for field_name in (SearchField.simple_text, SearchField.translation)
        )
        if needs_edition_matches:
            edition_type_conditions = []
            if SearchField.simple_text in search_fields:
                edition_type_conditions.append(
                    Translation.edition_type == SupportedEditionType.quran.value,
                )
            if SearchField.translation in search_fields:
                edition_type_conditions.append(
                    Translation.edition_type == SupportedEditionType.translation.value,
                )

            field_label = case(
                (
                    Translation.edition_type == SupportedEditionType.quran.value,
                    SearchField.simple_text.value,
                ),
                else_=SearchField.translation.value,
            )
            edition_rows = list(
                session.execute(
                    select(AyahTranslation, Translation, field_label.label("field"))
                    .join(Translation, AyahTranslation.translation_id == Translation.id)
                    .where(
                        AyahTranslation.ayah_global_number.in_(selected_ids),
                        Translation.format == "text",
                        AyahTranslation.search_text.contains(normalized_query),
                        or_(*edition_type_conditions),
                    )
                    .order_by(
                        AyahTranslation.ayah_global_number,
                        Translation.language_code,
                        Translation.upstream_identifier,
                    ),
                ),
            )
            if language_code is not None:
                edition_rows = [
                    row
                    for row in edition_rows
                    if row[1].language_code == language_code
                ]
            if translation_filter is not None:
                edition_rows = [
                    row
                    for row in edition_rows
                    if row[1].id == translation_filter.id
                ]

            for ayah_translation, edition, field_name in edition_rows:
                ayah_id = ayah_translation.ayah_global_number
                field_enum = SearchField(str(field_name))
                matched_fields[ayah_id].add(field_enum)

                field_key = (ayah_id, field_enum)
                total_highlights = len(matched_highlights[ayah_id])
                if total_highlights >= HIGHLIGHT_LIMIT_PER_AYAH:
                    continue
                if per_field_highlights[field_key] >= HIGHLIGHT_LIMIT_PER_FIELD:
                    continue

                highlight = build_highlight(ayah_translation.text, cleaned_query)
                if highlight is None:
                    continue

                edition_summary = _edition_attribution(edition)
                edition_attributions.setdefault(edition.id, edition_summary)
                matched_highlights[ayah_id].append(
                    SearchHighlight(
                        field=field_enum,
                        text=ayah_translation.text,
                        excerpt=highlight.excerpt,
                        match_start=highlight.match_start,
                        match_end=highlight.match_end,
                        edition=edition_summary,
                    ),
                )
                per_field_highlights[field_key] += 1

        for ayah_id in selected_ids:
            ayah, surah, source_release = ayah_by_id[ayah_id]
            if arabic_source is None:
                arabic_source = _source_resource(source_release)

            results.append(
                ExactSearchHitResource(
                    ayah=_ayah_resource(ayah, surah, source_release),
                    match_sources=[
                        field_name
                        for field_name in SEARCH_FIELD_ORDER
                        if field_name in matched_fields[ayah_id]
                    ],
                    highlights=matched_highlights[ayah_id],
                ),
            )

    return ExactSearchResponse(
        query=cleaned_query,
        count=len(results),
        searched_fields=search_fields,
        filters=SearchFilters(
            fields=search_fields,
            language_code=language_code,
            translation_identifier=translation_identifier,
        ),
        results=results,
        pagination=_pagination(total, limit, offset),
        arabic_source=arabic_source,
        translation_attribution=translation_attribution,
        edition_attributions=list(edition_attributions.values()),
    )
