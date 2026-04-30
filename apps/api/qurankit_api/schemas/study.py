from __future__ import annotations

from datetime import date, datetime
from typing import Any

from pydantic import BaseModel, ConfigDict


class OperationStatus(BaseModel):
    model_config = ConfigDict(extra="forbid")

    ok: bool = True
    message: str


class AyahReferenceResource(BaseModel):
    model_config = ConfigDict(extra="forbid")

    reference: str
    surah_number: int
    ayah_number: int


class AyahRangeResource(BaseModel):
    model_config = ConfigDict(extra="forbid")

    start: AyahReferenceResource
    end: AyahReferenceResource
    label: str
    ayah_count: int | None = None


class ProgressUpdateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    range_label: str
    source: str | None = None


class ProgressResource(BaseModel):
    model_config = ConfigDict(extra="forbid")

    range: AyahRangeResource
    updated_at: datetime
    source: str


class ProgressResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    progress: ProgressResource | None = None
    streak_days: int
    updated_plan_names: list[str] = []


class ReadingSessionCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    started_at: datetime
    ended_at: datetime | None = None
    range_label: str | None = None
    source: str | None = None


class ReadingSessionResource(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    range: AyahRangeResource | None = None
    started_at: datetime
    ended_at: datetime | None = None
    duration_seconds: int | None = None
    source: str | None = None
    is_private: bool


class ReadingSessionListResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    count: int
    sessions: list[ReadingSessionResource]


class BookmarkCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    reference: str
    label: str | None = None


class BookmarkResource(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    range: AyahRangeResource
    label: str | None = None
    created_at: datetime
    is_private: bool


class BookmarkListResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    count: int
    bookmarks: list[BookmarkResource]


class NoteCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    reference: str | None = None
    range_label: str | None = None
    title: str | None = None
    body: str


class NoteUpdateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    reference: str | None = None
    range_label: str | None = None
    title: str | None = None
    body: str | None = None


class NoteResource(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    range: AyahRangeResource | None = None
    title: str | None = None
    body: str
    created_at: datetime
    updated_at: datetime
    is_private: bool


class NoteListResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    count: int
    notes: list[NoteResource]


class PlanCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    range_label: str
    daily_ayah_target: int | None = None
    start_date: date | None = None
    end_date: date | None = None
    status: str | None = None


class PlanUpdateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str | None = None
    range_label: str | None = None
    daily_ayah_target: int | None = None
    start_date: date | None = None
    end_date: date | None = None
    status: str | None = None


class ReadingPlanMetrics(BaseModel):
    model_config = ConfigDict(extra="forbid")

    total_ayahs: int
    completed_ayahs: int
    remaining_ayahs: int
    remaining_days: int
    completed: bool
    daily_ayah_target: int
    estimated_days: int
    projected_end_date: date | None = None
    today_range: AyahRangeResource | None = None


class ReadingPlanResource(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    name: str
    range: AyahRangeResource
    daily_ayah_target: int
    created_at: datetime
    updated_at: datetime
    completed_through: AyahReferenceResource | None = None
    status: str
    start_date: date | None = None
    end_date: date | None = None
    metrics: ReadingPlanMetrics
    is_private: bool


class ReadingPlanListResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    count: int
    plans: list[ReadingPlanResource]


class StudyStateDocument(BaseModel):
    model_config = ConfigDict(extra="forbid")

    progress: ProgressResource | None = None
    bookmarks: list[BookmarkResource]
    notes: list[NoteResource]
    plans: list[ReadingPlanResource]


class StudySummary(BaseModel):
    model_config = ConfigDict(extra="forbid")

    streak_days: int
    session_count: int
    bookmark_count: int
    note_count: int
    plan_count: int
    latest_session_at: datetime | None = None


class StudyResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    state: StudyStateDocument
    summary: StudySummary


class StudyReplaceRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    state: dict[str, Any]
