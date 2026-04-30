from __future__ import annotations

from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from qurankit_api.schemas.browse import AyahResource, PaginationMeta, SourceAttribution


class SearchField(StrEnum):
    arabic_text = "arabic_text"
    simple_text = "simple_text"
    translation = "translation"


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
