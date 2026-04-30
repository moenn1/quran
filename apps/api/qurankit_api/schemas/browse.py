from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class PaginationMeta(BaseModel):
    model_config = ConfigDict(extra="forbid")

    total: int
    limit: int
    offset: int
    has_more: bool


class SourceAttribution(BaseModel):
    model_config = ConfigDict(extra="forbid")

    source_release_id: str
    source_name: str
    repository_url: str
    upstream_commit_sha: str
    retrieved_artifact_name: str
    retrieved_artifact_sha256: str


class AyahSurahSummary(BaseModel):
    model_config = ConfigDict(extra="forbid")

    surah_number: int
    arabic_name: str
    english_name: str
    english_name_translation: str
    revelation_type: str | None = None


class SurahResource(AyahSurahSummary):
    ayah_count: int
    source: SourceAttribution


class AyahResource(BaseModel):
    model_config = ConfigDict(extra="forbid")

    reference: str
    global_ayah_number: int
    ayah_number: int
    text: str
    page_number: int
    juz_number: int
    hizb_number: int
    rub_el_hizb_number: int
    sajda: bool
    surah: AyahSurahSummary
    source: SourceAttribution


class SurahListResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    items: list[SurahResource]
    pagination: PaginationMeta


class SurahAyahListResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    surah: SurahResource
    items: list[AyahResource]
    pagination: PaginationMeta


class JuzAyahListResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    juz_number: int
    items: list[AyahResource]
    pagination: PaginationMeta


class HizbAyahListResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    hizb_number: int
    items: list[AyahResource]
    pagination: PaginationMeta


class PageAyahListResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    page_number: int
    items: list[AyahResource]
    pagination: PaginationMeta
