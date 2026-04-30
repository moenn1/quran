from __future__ import annotations

import math
import re
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from typing import Any

from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from qurankit_api.core.errors import ApiError
from qurankit_api.db.base import utcnow
from qurankit_api.models import (
    Ayah,
    Bookmark,
    Note,
    ReadingPlan,
    ReadingPlanStatus,
    ReadingProgress,
    ReadingSession,
    User,
)


REFERENCE_RE = re.compile(r"^(?P<surah>\d+):(?P<ayah>\d+)$")
RANGE_START_KEY = "start_ayah_global_number"
RANGE_END_KEY = "end_ayah_global_number"


@dataclass(frozen=True, slots=True)
class AyahPoint:
    global_ayah_number: int
    surah_number: int
    ayah_number: int

    @property
    def reference(self) -> str:
        return f"{self.surah_number}:{self.ayah_number}"


@dataclass(frozen=True, slots=True)
class AyahRangeRecord:
    start: AyahPoint
    end: AyahPoint

    @property
    def label(self) -> str:
        if self.start.reference == self.end.reference:
            return self.start.reference
        if self.start.surah_number == self.end.surah_number:
            return f"{self.start.reference}-{self.end.ayah_number}"
        return f"{self.start.reference}-{self.end.reference}"

    @property
    def ayah_count(self) -> int:
        return self.end.global_ayah_number - self.start.global_ayah_number + 1


def _reference_payload(reference: AyahPoint) -> dict[str, Any]:
    return {
        "reference": reference.reference,
        "surah_number": reference.surah_number,
        "ayah_number": reference.ayah_number,
    }


def _range_payload(reading_range: AyahRangeRecord) -> dict[str, Any]:
    return {
        "start": _reference_payload(reading_range.start),
        "end": _reference_payload(reading_range.end),
        "label": reading_range.label,
        "ayah_count": reading_range.ayah_count,
    }


def _point_from_ayah(ayah: Ayah) -> AyahPoint:
    return AyahPoint(
        global_ayah_number=ayah.global_ayah_number,
        surah_number=ayah.surah_number,
        ayah_number=ayah.ayah_number,
    )


def _require_mapping(payload: Any, *, field_name: str) -> Mapping[str, Any]:
    if not isinstance(payload, Mapping):
        raise ApiError(
            status_code=422,
            code="invalid_study_payload",
            message=f"`{field_name}` must be a JSON object.",
            details={"field": field_name},
        )
    return payload


def _required_text(value: Any, *, field_name: str) -> str:
    normalized = str(value).strip()
    if not normalized:
        raise ApiError(
            status_code=422,
            code="invalid_study_payload",
            message=f"`{field_name}` cannot be blank.",
            details={"field": field_name},
        )
    return normalized


def _optional_text(value: Any) -> str | None:
    if value is None:
        return None
    normalized = str(value).strip()
    return normalized or None


def _parse_datetime(value: Any, *, field_name: str) -> datetime | None:
    if value is None or value == "":
        return None
    if isinstance(value, datetime):
        parsed = value
    else:
        try:
            parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        except ValueError as exc:
            raise ApiError(
                status_code=422,
                code="invalid_datetime",
                message=f"`{field_name}` must be an ISO-8601 datetime.",
                details={"field": field_name, "value": value},
            ) from exc
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _parse_date(value: Any, *, field_name: str) -> date | None:
    if value is None or value == "":
        return None
    if isinstance(value, date) and not isinstance(value, datetime):
        return value
    try:
        return date.fromisoformat(str(value))
    except ValueError as exc:
        raise ApiError(
            status_code=422,
            code="invalid_date",
            message=f"`{field_name}` must be an ISO date.",
            details={"field": field_name, "value": value},
        ) from exc


def _parse_reference_text(value: str, *, field_name: str) -> tuple[int, int]:
    normalized = value.strip()
    match = REFERENCE_RE.fullmatch(normalized)
    if match is None:
        raise ApiError(
            status_code=422,
            code="invalid_ayah_reference",
            message="Ayah references must look like `surah:ayah`.",
            details={"field": field_name, "value": value},
        )
    surah_number = int(match.group("surah"))
    ayah_number = int(match.group("ayah"))
    if surah_number < 1 or ayah_number < 1:
        raise ApiError(
            status_code=422,
            code="invalid_ayah_reference",
            message="Ayah reference numbers must both be positive.",
            details={"field": field_name, "value": value},
        )
    return (surah_number, ayah_number)


def parse_range_label(value: str) -> tuple[tuple[int, int], tuple[int, int]]:
    normalized = value.strip()
    if not normalized:
        raise ApiError(
            status_code=422,
            code="invalid_ayah_range",
            message="Ayah range cannot be empty.",
            details={"field": "range_label"},
        )

    start_text, separator, end_text = normalized.partition("-")
    start_reference = _parse_reference_text(start_text, field_name="range_label")
    if separator != "-":
        return (start_reference, start_reference)

    normalized_end = end_text.strip()
    if not normalized_end:
        raise ApiError(
            status_code=422,
            code="invalid_ayah_range",
            message="Ayah range end cannot be empty after `-`.",
            details={"field": "range_label", "value": value},
        )

    if ":" in normalized_end:
        end_reference = _parse_reference_text(normalized_end, field_name="range_label")
    else:
        if not normalized_end.isdigit():
            raise ApiError(
                status_code=422,
                code="invalid_ayah_range",
                message="Ayah range end must be an ayah number or `surah:ayah` reference.",
                details={"field": "range_label", "value": value},
            )
        end_reference = (start_reference[0], int(normalized_end))

    return (start_reference, end_reference)


def _ayah_not_found(*, surah_number: int, ayah_number: int) -> ApiError:
    reference = f"{surah_number}:{ayah_number}"
    return ApiError(
        status_code=404,
        code="ayah_not_found",
        message=f"Ayah reference `{reference}` was not found.",
        details={"reference": reference},
    )


def _load_ayah(session: Session, *, surah_number: int, ayah_number: int) -> Ayah:
    ayah = session.scalar(
        select(Ayah).where(
            Ayah.surah_number == surah_number,
            Ayah.ayah_number == ayah_number,
        ),
    )
    if ayah is None:
        raise _ayah_not_found(surah_number=surah_number, ayah_number=ayah_number)
    return ayah


def _load_ayah_by_global(session: Session, global_ayah_number: int) -> Ayah:
    ayah = session.get(Ayah, global_ayah_number)
    if ayah is None:
        raise ApiError(
            status_code=404,
            code="ayah_not_found",
            message=f"Global ayah {global_ayah_number} was not found.",
            details={"global_ayah_number": global_ayah_number},
        )
    return ayah


def build_range_from_ayahs(start_ayah: Ayah, end_ayah: Ayah) -> AyahRangeRecord:
    if end_ayah.global_ayah_number < start_ayah.global_ayah_number:
        raise ApiError(
            status_code=422,
            code="invalid_ayah_range",
            message="Ayah ranges must end at or after their start reference.",
            details={
                "start_reference": f"{start_ayah.surah_number}:{start_ayah.ayah_number}",
                "end_reference": f"{end_ayah.surah_number}:{end_ayah.ayah_number}",
            },
        )
    return AyahRangeRecord(start=_point_from_ayah(start_ayah), end=_point_from_ayah(end_ayah))


def resolve_range_label(session: Session, value: str) -> AyahRangeRecord:
    (start_surah, start_ayah), (end_surah, end_ayah) = parse_range_label(value)
    start = _load_ayah(session, surah_number=start_surah, ayah_number=start_ayah)
    end = _load_ayah(session, surah_number=end_surah, ayah_number=end_ayah)
    return build_range_from_ayahs(start, end)


def _resolve_reference_value(
    session: Session,
    value: Any,
    *,
    field_name: str,
) -> AyahPoint:
    if isinstance(value, str):
        surah_number, ayah_number = _parse_reference_text(value, field_name=field_name)
        return _point_from_ayah(_load_ayah(session, surah_number=surah_number, ayah_number=ayah_number))

    mapping = _require_mapping(value, field_name=field_name)
    reference_text = mapping.get("reference")
    if reference_text is not None:
        surah_number, ayah_number = _parse_reference_text(str(reference_text), field_name=field_name)
    else:
        try:
            surah_number = int(mapping["surah_number"])
            ayah_number = int(mapping["ayah_number"])
        except (KeyError, TypeError, ValueError) as exc:
            raise ApiError(
                status_code=422,
                code="invalid_ayah_reference",
                message=f"`{field_name}` must include `reference` or `surah_number` and `ayah_number`.",
                details={"field": field_name},
            ) from exc
    return _point_from_ayah(_load_ayah(session, surah_number=surah_number, ayah_number=ayah_number))


def resolve_range_mapping(
    session: Session,
    payload: Any,
    *,
    field_name: str,
) -> AyahRangeRecord:
    mapping = _require_mapping(payload, field_name=field_name)
    nested = mapping.get("range")
    source = _require_mapping(nested, field_name=field_name) if nested is not None else mapping
    start = _resolve_reference_value(session, source.get("start"), field_name=f"{field_name}.start")
    end = _resolve_reference_value(session, source.get("end"), field_name=f"{field_name}.end")
    return build_range_from_ayahs(
        _load_ayah_by_global(session, start.global_ayah_number),
        _load_ayah_by_global(session, end.global_ayah_number),
    )


def resolve_range_input(
    session: Session,
    *,
    range_label: str | None = None,
    range_payload: Any | None = None,
    field_name: str = "range",
) -> AyahRangeRecord:
    if range_label:
        return resolve_range_label(session, range_label)
    if range_payload is not None:
        return resolve_range_mapping(session, range_payload, field_name=field_name)
    raise ApiError(
        status_code=422,
        code="invalid_ayah_range",
        message="An ayah range is required.",
        details={"field": field_name},
    )


def range_from_progress(session: Session, progress: ReadingProgress) -> AyahRangeRecord:
    metadata = progress.metadata_json or {}
    start_global = int(metadata.get(RANGE_START_KEY, progress.current_ayah_global_number))
    start = _load_ayah_by_global(session, start_global)
    end = _load_ayah_by_global(session, progress.current_ayah_global_number)
    return build_range_from_ayahs(start, end)


def range_from_bookmark(session: Session, bookmark: Bookmark) -> AyahRangeRecord:
    ayah = _load_ayah_by_global(session, bookmark.ayah_global_number)
    return build_range_from_ayahs(ayah, ayah)


def range_from_note(session: Session, note: Note) -> AyahRangeRecord | None:
    if note.ayah_global_number is None:
        return None
    metadata = note.metadata_json or {}
    start_global = int(metadata.get(RANGE_START_KEY, note.ayah_global_number))
    start = _load_ayah_by_global(session, start_global)
    end = _load_ayah_by_global(session, note.ayah_global_number)
    return build_range_from_ayahs(start, end)


def range_from_plan(session: Session, plan: ReadingPlan) -> AyahRangeRecord:
    start = _load_ayah_by_global(session, plan.start_ayah_global_number)
    end = _load_ayah_by_global(session, plan.end_ayah_global_number)
    return build_range_from_ayahs(start, end)


def completed_through_from_plan(session: Session, plan: ReadingPlan) -> AyahPoint | None:
    if plan.completed_through_ayah_global_number is None:
        return None
    ayah = _load_ayah_by_global(session, plan.completed_through_ayah_global_number)
    return _point_from_ayah(ayah)


def _resolved_plan_target(plan: ReadingPlan) -> int:
    if plan.target_ayahs_per_day and plan.target_ayahs_per_day > 0:
        return plan.target_ayahs_per_day
    if plan.start_date and plan.end_date:
        total_ayahs = plan.end_ayah_global_number - plan.start_ayah_global_number + 1
        days = (plan.end_date - plan.start_date).days + 1
        return max(1, math.ceil(total_ayahs / max(1, days)))
    return 1


def build_plan_metrics_payload(session: Session, plan: ReadingPlan) -> dict[str, Any]:
    reading_range = range_from_plan(session, plan)
    total_ayahs = reading_range.ayah_count
    daily_target = _resolved_plan_target(plan)

    completed_ayahs = 0
    completed_point = completed_through_from_plan(session, plan)
    if completed_point is not None:
        if completed_point.global_ayah_number < reading_range.start.global_ayah_number:
            raise ApiError(
                status_code=422,
                code="invalid_plan_checkpoint",
                message=f"Plan `{plan.title}` has a checkpoint before its saved range.",
                details={"plan_id": plan.id},
            )
        completed_ayahs = min(
            total_ayahs,
            completed_point.global_ayah_number - reading_range.start.global_ayah_number + 1,
        )

    remaining_ayahs = max(0, total_ayahs - completed_ayahs)
    next_start_global = reading_range.start.global_ayah_number + completed_ayahs
    today_range = None
    if remaining_ayahs > 0:
        today_start = _load_ayah_by_global(session, next_start_global)
        today_end = _load_ayah_by_global(
            session,
            min(reading_range.end.global_ayah_number, next_start_global + daily_target - 1),
        )
        today_range = _range_payload(build_range_from_ayahs(today_start, today_end))

    estimated_days = max(1, math.ceil(total_ayahs / daily_target))
    projected_end_date = (
        plan.start_date + timedelta(days=estimated_days - 1)
        if plan.start_date is not None
        else plan.end_date
    )
    remaining_days = 0 if remaining_ayahs == 0 else math.ceil(remaining_ayahs / daily_target)

    return {
        "total_ayahs": total_ayahs,
        "completed_ayahs": completed_ayahs,
        "remaining_ayahs": remaining_ayahs,
        "remaining_days": remaining_days,
        "completed": remaining_ayahs == 0,
        "daily_ayah_target": daily_target,
        "estimated_days": estimated_days,
        "projected_end_date": projected_end_date,
        "today_range": today_range,
    }


def build_progress_payload(session: Session, progress: ReadingProgress | None) -> dict[str, Any] | None:
    if progress is None:
        return None
    reading_range = range_from_progress(session, progress)
    return {
        "range": _range_payload(reading_range),
        "updated_at": progress.updated_at,
        "source": progress.source or "manual_mark",
    }


def build_bookmark_payload(session: Session, bookmark: Bookmark) -> dict[str, Any]:
    return {
        "id": bookmark.id,
        "range": _range_payload(range_from_bookmark(session, bookmark)),
        "label": bookmark.label,
        "created_at": bookmark.created_at,
        "is_private": bookmark.is_private,
    }


def build_note_payload(session: Session, note: Note) -> dict[str, Any]:
    reading_range = range_from_note(session, note)
    return {
        "id": note.id,
        "range": _range_payload(reading_range) if reading_range is not None else None,
        "title": note.title,
        "body": note.body,
        "created_at": note.created_at,
        "updated_at": note.updated_at,
        "is_private": note.is_private,
    }


def build_plan_payload(session: Session, plan: ReadingPlan) -> dict[str, Any]:
    metrics = build_plan_metrics_payload(session, plan)
    completed_through = completed_through_from_plan(session, plan)
    return {
        "id": plan.id,
        "name": plan.title,
        "range": _range_payload(range_from_plan(session, plan)),
        "daily_ayah_target": metrics["daily_ayah_target"],
        "created_at": plan.created_at,
        "updated_at": plan.updated_at,
        "completed_through": (
            _reference_payload(completed_through) if completed_through is not None else None
        ),
        "status": plan.status.value,
        "start_date": plan.start_date,
        "end_date": plan.end_date,
        "metrics": metrics,
        "is_private": plan.is_private,
    }


def build_session_payload(session: Session, reading_session: ReadingSession) -> dict[str, Any]:
    reading_range = None
    if reading_session.started_ayah_global_number is not None:
        start = _load_ayah_by_global(session, reading_session.started_ayah_global_number)
        end = (
            _load_ayah_by_global(session, reading_session.ended_ayah_global_number)
            if reading_session.ended_ayah_global_number is not None
            else start
        )
        reading_range = _range_payload(build_range_from_ayahs(start, end))

    duration_seconds = None
    if reading_session.ended_at is not None:
        duration_seconds = max(
            0,
            int((reading_session.ended_at - reading_session.started_at).total_seconds()),
        )

    metadata = reading_session.metadata_json or {}
    return {
        "id": reading_session.id,
        "range": reading_range,
        "started_at": reading_session.started_at,
        "ended_at": reading_session.ended_at,
        "duration_seconds": duration_seconds,
        "source": metadata.get("source"),
        "is_private": reading_session.is_private,
    }


def build_study_state_payload(session: Session, user: User) -> dict[str, Any]:
    progress = session.scalar(
        select(ReadingProgress).where(ReadingProgress.user_id == user.id),
    )
    bookmarks = session.scalars(
        select(Bookmark)
        .where(Bookmark.user_id == user.id)
        .order_by(Bookmark.created_at.desc(), Bookmark.id.desc()),
    ).all()
    notes = session.scalars(
        select(Note)
        .where(Note.user_id == user.id)
        .order_by(Note.updated_at.desc(), Note.id.desc()),
    ).all()
    plans = session.scalars(
        select(ReadingPlan)
        .where(ReadingPlan.user_id == user.id)
        .order_by(ReadingPlan.created_at.asc(), ReadingPlan.id.asc()),
    ).all()

    return {
        "progress": build_progress_payload(session, progress),
        "bookmarks": [build_bookmark_payload(session, bookmark) for bookmark in bookmarks],
        "notes": [build_note_payload(session, note) for note in notes],
        "plans": [build_plan_payload(session, plan) for plan in plans],
    }


def _reading_dates(session: Session, user: User) -> list[date]:
    dates: set[date] = set()

    session_dates = session.scalars(
        select(ReadingSession.started_at).where(ReadingSession.user_id == user.id),
    ).all()
    for value in session_dates:
        if value is None:
            continue
        normalized = value.astimezone(timezone.utc) if value.tzinfo else value.replace(tzinfo=timezone.utc)
        dates.add(normalized.date())

    progress = session.scalar(
        select(ReadingProgress).where(ReadingProgress.user_id == user.id),
    )
    if progress is not None:
        normalized = (
            progress.updated_at.astimezone(timezone.utc)
            if progress.updated_at.tzinfo
            else progress.updated_at.replace(tzinfo=timezone.utc)
        )
        dates.add(normalized.date())

    return sorted(dates, reverse=True)


def calculate_streak_days(session: Session, user: User) -> int:
    dates = _reading_dates(session, user)
    if not dates:
        return 0

    streak = 0
    cursor = dates[0]
    for value in dates:
        if value != cursor:
            break
        streak += 1
        cursor = cursor - timedelta(days=1)
    return streak


def build_study_summary_payload(session: Session, user: User) -> dict[str, Any]:
    latest_session_at = session.scalar(
        select(func.max(ReadingSession.started_at)).where(ReadingSession.user_id == user.id),
    )
    return {
        "streak_days": calculate_streak_days(session, user),
        "session_count": int(
            session.scalar(
                select(func.count()).select_from(ReadingSession).where(ReadingSession.user_id == user.id),
            )
            or 0
        ),
        "bookmark_count": int(
            session.scalar(
                select(func.count()).select_from(Bookmark).where(Bookmark.user_id == user.id),
            )
            or 0
        ),
        "note_count": int(
            session.scalar(select(func.count()).select_from(Note).where(Note.user_id == user.id))
            or 0
        ),
        "plan_count": int(
            session.scalar(
                select(func.count()).select_from(ReadingPlan).where(ReadingPlan.user_id == user.id),
            )
            or 0
        ),
        "latest_session_at": latest_session_at,
    }


def _range_metadata(reading_range: AyahRangeRecord) -> dict[str, Any]:
    return {
        RANGE_START_KEY: reading_range.start.global_ayah_number,
        RANGE_END_KEY: reading_range.end.global_ayah_number,
    }


def _normalize_completed_through(
    session: Session,
    *,
    reading_range: AyahRangeRecord,
    value: Any,
    field_name: str,
) -> int | None:
    if value is None or value == "":
        return None
    point = _resolve_reference_value(session, value, field_name=field_name)
    if not (
        reading_range.start.global_ayah_number
        <= point.global_ayah_number
        <= reading_range.end.global_ayah_number
    ):
        raise ApiError(
            status_code=422,
            code="invalid_plan_checkpoint",
            message="Completed-through reference must stay inside the saved plan range.",
            details={"field": field_name},
        )
    return point.global_ayah_number


def resolve_plan_target(
    *,
    total_ayahs: int,
    daily_ayah_target: Any,
    start_date: date | None,
    end_date: date | None,
) -> int:
    if daily_ayah_target not in {None, ""}:
        try:
            target = int(daily_ayah_target)
        except (TypeError, ValueError) as exc:
            raise ApiError(
                status_code=422,
                code="invalid_plan_target",
                message="`daily_ayah_target` must be a positive integer.",
                details={"field": "daily_ayah_target"},
            ) from exc
        if target < 1:
            raise ApiError(
                status_code=422,
                code="invalid_plan_target",
                message="`daily_ayah_target` must be at least 1.",
                details={"field": "daily_ayah_target"},
            )
        return target

    if start_date is not None and end_date is not None and end_date < start_date:
        raise ApiError(
            status_code=422,
            code="invalid_plan_dates",
            message="`end_date` must be on or after `start_date`.",
            details={"start_date": start_date, "end_date": end_date},
        )

    if start_date is not None and end_date is not None:
        days = (end_date - start_date).days + 1
        if days < 1:
            raise ApiError(
                status_code=422,
                code="invalid_plan_dates",
                message="`end_date` must be on or after `start_date`.",
                details={"start_date": start_date, "end_date": end_date},
            )
        return max(1, math.ceil(total_ayahs / days))

    raise ApiError(
        status_code=422,
        code="missing_plan_target",
        message="Reading plans need `daily_ayah_target` or both `start_date` and `end_date`.",
        details={"fields": ["daily_ayah_target", "start_date", "end_date"]},
    )


def apply_progress_checkpoint(
    session: Session,
    *,
    user: User,
    reading_range: AyahRangeRecord,
    source: str,
) -> tuple[ReadingProgress, tuple[str, ...]]:
    progress = session.scalar(
        select(ReadingProgress).where(ReadingProgress.user_id == user.id),
    )
    if progress is None:
        progress = ReadingProgress(
            user_id=user.id,
            current_ayah_global_number=reading_range.end.global_ayah_number,
            source=source,
            metadata_json=_range_metadata(reading_range),
        )
        session.add(progress)
    else:
        progress.current_ayah_global_number = reading_range.end.global_ayah_number
        progress.source = source
        progress.metadata_json = _range_metadata(reading_range)

    updated_plan_names: list[str] = []
    plans = session.scalars(
        select(ReadingPlan).where(ReadingPlan.user_id == user.id),
    ).all()
    for plan in plans:
        overlap_start = max(plan.start_ayah_global_number, reading_range.start.global_ayah_number)
        overlap_end = min(plan.end_ayah_global_number, reading_range.end.global_ayah_number)
        if overlap_start > overlap_end:
            continue
        if (
            plan.completed_through_ayah_global_number is not None
            and overlap_end <= plan.completed_through_ayah_global_number
        ):
            continue
        plan.completed_through_ayah_global_number = overlap_end
        updated_plan_names.append(plan.title)

    recorded_at = utcnow()
    session.add(
        ReadingSession(
            user_id=user.id,
            started_at=recorded_at,
            ended_at=recorded_at,
            started_ayah_global_number=reading_range.start.global_ayah_number,
            ended_ayah_global_number=reading_range.end.global_ayah_number,
            metadata_json={
                "source": source,
                "derived_from": "progress_checkpoint",
            },
        ),
    )

    session.flush()
    return (progress, tuple(updated_plan_names))


def replace_study_state(session: Session, *, user: User, payload: Any) -> None:
    state = _require_mapping(payload, field_name="state")

    progress_payload = state.get("progress")
    existing_progress = session.scalar(
        select(ReadingProgress).where(ReadingProgress.user_id == user.id),
    )
    if progress_payload is None:
        if existing_progress is not None:
            session.delete(existing_progress)
    else:
        progress_mapping = _require_mapping(progress_payload, field_name="progress")
        reading_range = resolve_range_mapping(session, progress_mapping, field_name="progress")
        updated_at = _parse_datetime(progress_mapping.get("updated_at"), field_name="progress.updated_at")
        source = _optional_text(progress_mapping.get("source")) or "remote_sync"
        progress = existing_progress or ReadingProgress(user_id=user.id)
        progress.current_ayah_global_number = reading_range.end.global_ayah_number
        progress.source = source
        progress.metadata_json = _range_metadata(reading_range)
        if updated_at is not None:
            progress.created_at = progress.created_at if existing_progress is not None else updated_at
            progress.updated_at = updated_at
        session.add(progress)

    session.execute(delete(Bookmark).where(Bookmark.user_id == user.id))
    session.execute(delete(Note).where(Note.user_id == user.id))
    session.execute(delete(ReadingPlan).where(ReadingPlan.user_id == user.id))

    bookmark_items = state.get("bookmarks", [])
    if not isinstance(bookmark_items, list):
        raise ApiError(
            status_code=422,
            code="invalid_study_payload",
            message="`bookmarks` must be an array.",
            details={"field": "bookmarks"},
        )
    for index, item in enumerate(bookmark_items):
        bookmark = _require_mapping(item, field_name=f"bookmarks[{index}]")
        reading_range = resolve_range_mapping(session, bookmark, field_name=f"bookmarks[{index}]")
        if reading_range.start.global_ayah_number != reading_range.end.global_ayah_number:
            raise ApiError(
                status_code=422,
                code="invalid_bookmark_range",
                message="Bookmarks currently support one ayah per record.",
                details={"field": f"bookmarks[{index}].range"},
            )
        entry = Bookmark(
            user_id=user.id,
            ayah_global_number=reading_range.end.global_ayah_number,
            label=_optional_text(bookmark.get("label")),
            metadata_json=_range_metadata(reading_range),
        )
        if bookmark.get("id") is not None:
            entry.id = str(bookmark["id"])
        created_at = _parse_datetime(bookmark.get("created_at"), field_name=f"bookmarks[{index}].created_at")
        if created_at is not None:
            entry.created_at = created_at
            entry.updated_at = created_at
        session.add(entry)

    note_items = state.get("notes", [])
    if not isinstance(note_items, list):
        raise ApiError(
            status_code=422,
            code="invalid_study_payload",
            message="`notes` must be an array.",
            details={"field": "notes"},
        )
    for index, item in enumerate(note_items):
        note = _require_mapping(item, field_name=f"notes[{index}]")
        reading_range = resolve_range_mapping(session, note, field_name=f"notes[{index}]")
        entry = Note(
            user_id=user.id,
            ayah_global_number=reading_range.end.global_ayah_number,
            title=_optional_text(note.get("title")),
            body=_required_text(note.get("body"), field_name=f"notes[{index}].body"),
            metadata_json=_range_metadata(reading_range),
        )
        if note.get("id") is not None:
            entry.id = str(note["id"])
        created_at = _parse_datetime(note.get("created_at"), field_name=f"notes[{index}].created_at")
        updated_at = _parse_datetime(note.get("updated_at"), field_name=f"notes[{index}].updated_at")
        if created_at is not None:
            entry.created_at = created_at
        if updated_at is not None:
            entry.updated_at = updated_at
        elif created_at is not None:
            entry.updated_at = created_at
        session.add(entry)

    plan_items = state.get("plans", [])
    if not isinstance(plan_items, list):
        raise ApiError(
            status_code=422,
            code="invalid_study_payload",
            message="`plans` must be an array.",
            details={"field": "plans"},
        )
    for index, item in enumerate(plan_items):
        plan = _require_mapping(item, field_name=f"plans[{index}]")
        reading_range = resolve_range_mapping(session, plan, field_name=f"plans[{index}]")
        start_date = _parse_date(plan.get("start_date"), field_name=f"plans[{index}].start_date")
        end_date = _parse_date(plan.get("end_date"), field_name=f"plans[{index}].end_date")
        target = resolve_plan_target(
            total_ayahs=reading_range.ayah_count,
            daily_ayah_target=plan.get("daily_ayah_target"),
            start_date=start_date,
            end_date=end_date,
        )
        status_value = _optional_text(plan.get("status")) or ReadingPlanStatus.draft.value
        try:
            status = ReadingPlanStatus(status_value)
        except ValueError as exc:
            raise ApiError(
                status_code=422,
                code="invalid_plan_status",
                message="Plan status must be one of `draft`, `active`, `paused`, `completed`, or `archived`.",
                details={"field": f"plans[{index}].status", "value": status_value},
            ) from exc

        entry = ReadingPlan(
            user_id=user.id,
            title=_required_text(plan.get("name") or plan.get("title"), field_name=f"plans[{index}].name"),
            start_ayah_global_number=reading_range.start.global_ayah_number,
            end_ayah_global_number=reading_range.end.global_ayah_number,
            completed_through_ayah_global_number=_normalize_completed_through(
                session,
                reading_range=reading_range,
                value=plan.get("completed_through"),
                field_name=f"plans[{index}].completed_through",
            ),
            start_date=start_date,
            end_date=end_date,
            target_ayahs_per_day=target,
            status=status,
            metadata_json=_range_metadata(reading_range),
        )
        if plan.get("id") is not None:
            entry.id = str(plan["id"])
        created_at = _parse_datetime(plan.get("created_at"), field_name=f"plans[{index}].created_at")
        updated_at = _parse_datetime(plan.get("updated_at"), field_name=f"plans[{index}].updated_at")
        if created_at is not None:
            entry.created_at = created_at
        if updated_at is not None:
            entry.updated_at = updated_at
        elif created_at is not None:
            entry.updated_at = created_at
        session.add(entry)

    session.flush()


def delete_study_state(session: Session, *, user: User) -> None:
    session.execute(delete(ReadingSession).where(ReadingSession.user_id == user.id))
    session.execute(delete(ReadingProgress).where(ReadingProgress.user_id == user.id))
    session.execute(delete(Bookmark).where(Bookmark.user_id == user.id))
    session.execute(delete(Note).where(Note.user_id == user.id))
    session.execute(delete(ReadingPlan).where(ReadingPlan.user_id == user.id))
    session.flush()


def build_export_payload(session: Session, *, user: User, scope: str) -> dict[str, Any]:
    state = build_study_state_payload(session, user)
    summary = build_study_summary_payload(session, user)
    exported_at = utcnow()

    if scope == "progress":
        return {
            "exported_at": exported_at,
            "storage": "qurankit-api",
            "progress": state["progress"],
            "streak_days": summary["streak_days"],
        }

    if scope == "bookmarks":
        return {
            "exported_at": exported_at,
            "count": len(state["bookmarks"]),
            "bookmarks": state["bookmarks"],
        }

    if scope == "notes":
        return {
            "exported_at": exported_at,
            "count": len(state["notes"]),
            "notes": state["notes"],
        }

    if scope != "study":
        raise ApiError(
            status_code=404,
            code="export_scope_not_found",
            message=f"Export scope `{scope}` is not supported.",
            details={"scope": scope},
        )

    return {
        "exported_at": exported_at,
        "state": state,
        "summary": summary,
    }
