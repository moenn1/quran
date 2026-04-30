from __future__ import annotations

from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from qurankit_api.schemas.browse import AyahResource, PaginationMeta, SourceAttribution


class SearchField(StrEnum):
    arabic_text = "arabic_text"
    simple_text = "simple_text"
    translation = "translation"


class SemanticSearchScope(StrEnum):
    all = "all"
    surah = "surah"
    juz = "juz"
    hizb = "hizb"
    page = "page"


class EditionAttribution(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    upstream_identifier: str
    language_code: str
    translation_name: str
    english_name: str
    format: str
    edition_type: str
    attribution_text: str | None = None
    attribution_url: str | None = None
    review_status: str
    is_public: bool


class SearchFilters(BaseModel):
    model_config = ConfigDict(extra="forbid")

    fields: list[SearchField]
    language_code: str | None = None
    translation_identifier: str | None = None


class SearchHighlight(BaseModel):
    model_config = ConfigDict(extra="forbid")

    field: SearchField
    text: str
    excerpt: str
    match_start: int
    match_end: int
    edition: EditionAttribution | None = None


class ExactSearchHitResource(BaseModel):
    model_config = ConfigDict(extra="forbid")

    ayah: AyahResource
    match_sources: list[SearchField]
    highlights: list[SearchHighlight] = Field(default_factory=list)


class ExactSearchResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    query: str
    match_type: Literal["exact"] = "exact"
    count: int
    searched_fields: list[SearchField]
    filters: SearchFilters
    results: list[ExactSearchHitResource]
    pagination: PaginationMeta
    arabic_source: SourceAttribution | None = None
    translation_attribution: EditionAttribution | None = None
    edition_attributions: list[EditionAttribution] = Field(default_factory=list)


class SemanticSearchFilters(BaseModel):
    model_config = ConfigDict(extra="forbid")

    search_scope: SemanticSearchScope = SemanticSearchScope.all
    translation_identifier: str | None = None
    surah_number: int | None = None
    juz_number: int | None = None
    hizb_number: int | None = None
    page_number: int | None = None
    threshold: float
    include_scores: bool


class SemanticContextReferences(BaseModel):
    model_config = ConfigDict(extra="forbid")

    previous_reference: str | None = None
    next_reference: str | None = None


class SemanticAyahResource(AyahResource):
    translation_text: str | None = None


class SemanticSearchHitResource(BaseModel):
    model_config = ConfigDict(extra="forbid")

    ayah: SemanticAyahResource
    reason: str
    context: SemanticContextReferences
    similarity_score: float | None = None


class SemanticSearchResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    query: str
    match_type: Literal["semantic_similarity"] = "semantic_similarity"
    count: int
    disclaimer: str
    filters: SemanticSearchFilters
    results: list[SemanticSearchHitResource]
    arabic_source: SourceAttribution | None = None
    translation_attribution: EditionAttribution | None = None
