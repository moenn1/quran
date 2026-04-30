from __future__ import annotations

import json
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, field, replace
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Protocol
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
from uuid import uuid4

from .backends import AyahRangeResult, AyahReference, QuranBackend
from .config import Settings, StateMode

UrlOpenFn = Callable[..., Any]


class PersonalDataError(RuntimeError):
    """Base error for private study-state handling."""


class PersonalDataConfigurationError(PersonalDataError):
    """Raised when private study-state storage is misconfigured."""


class PersonalDataNotFoundError(PersonalDataError):
    """Raised when a private study-state record is missing."""


class PersonalDataRequestError(PersonalDataError):
    """Raised when a remote private study-state request fails."""


class PersonalDataValidationError(PersonalDataError):
    """Raised when a private study-state input is invalid."""


@dataclass(frozen=True)
class AyahRange:
    start: AyahReference
    end: AyahReference

    def __post_init__(self) -> None:
        if _reference_key(self.end) < _reference_key(self.start):
            raise PersonalDataValidationError(
                "Ayah ranges must end at or after their start reference."
            )

    @property
    def label(self) -> str:
        if self.start == self.end:
            return self.start.text

        if self.start.surah_number == self.end.surah_number:
            return (
                f"{self.start.surah_number}:{self.start.ayah_number}"
                f"-{self.end.ayah_number}"
            )

        return f"{self.start.text}-{self.end.text}"

    def to_dict(self) -> dict[str, Any]:
        return {
            "start": _reference_to_dict(self.start),
            "end": _reference_to_dict(self.end),
            "label": self.label,
        }

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> AyahRange:
        source = _unwrap_mapping(payload, "range")
        return cls(
            start=_reference_from_value(source.get("start")),
            end=_reference_from_value(source.get("end")),
        )


@dataclass(frozen=True)
class ReadingProgress:
    reading_range: AyahRange
    updated_at: str
    source: str = "manual_mark"

    def to_dict(self) -> dict[str, Any]:
        return {
            "range": self.reading_range.to_dict(),
            "updated_at": self.updated_at,
            "source": self.source,
        }

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> ReadingProgress:
        source = _unwrap_mapping(payload, "progress")
        return cls(
            reading_range=AyahRange.from_dict(source),
            updated_at=str(source.get("updated_at", "")),
            source=str(source.get("source", "manual_mark")),
        )


@dataclass(frozen=True)
class BookmarkEntry:
    id: str
    reading_range: AyahRange
    label: str | None
    created_at: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "range": self.reading_range.to_dict(),
            "label": self.label,
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> BookmarkEntry:
        return cls(
            id=str(payload["id"]),
            reading_range=AyahRange.from_dict(payload),
            label=_optional_text(payload.get("label")),
            created_at=str(payload.get("created_at", "")),
        )


@dataclass(frozen=True)
class NoteEntry:
    id: str
    reading_range: AyahRange
    body: str
    created_at: str
    updated_at: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "range": self.reading_range.to_dict(),
            "body": self.body,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> NoteEntry:
        return cls(
            id=str(payload["id"]),
            reading_range=AyahRange.from_dict(payload),
            body=str(payload.get("body", "")),
            created_at=str(payload.get("created_at", "")),
            updated_at=str(payload.get("updated_at", payload.get("created_at", ""))),
        )


@dataclass(frozen=True)
class ReadingPlan:
    id: str
    name: str
    reading_range: AyahRange
    daily_ayah_target: int
    created_at: str
    updated_at: str
    completed_through: AyahReference | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "range": self.reading_range.to_dict(),
            "daily_ayah_target": self.daily_ayah_target,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "completed_through": (
                _reference_to_dict(self.completed_through)
                if self.completed_through is not None
                else None
            ),
        }

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> ReadingPlan:
        completed = payload.get("completed_through")
        return cls(
            id=str(payload["id"]),
            name=str(payload.get("name", "")),
            reading_range=AyahRange.from_dict(payload),
            daily_ayah_target=int(payload.get("daily_ayah_target", 1)),
            created_at=str(payload.get("created_at", "")),
            updated_at=str(payload.get("updated_at", payload.get("created_at", ""))),
            completed_through=(
                _reference_from_value(completed)
                if completed is not None
                else None
            ),
        )


@dataclass(frozen=True)
class StudyState:
    progress: ReadingProgress | None = None
    bookmarks: tuple[BookmarkEntry, ...] = ()
    notes: tuple[NoteEntry, ...] = ()
    plans: tuple[ReadingPlan, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "progress": self.progress.to_dict() if self.progress is not None else None,
            "bookmarks": [bookmark.to_dict() for bookmark in self.bookmarks],
            "notes": [note.to_dict() for note in self.notes],
            "plans": [plan.to_dict() for plan in self.plans],
        }

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> StudyState:
        source = _unwrap_mapping(payload, "state")
        progress_payload = source.get("progress")

        return cls(
            progress=(
                ReadingProgress.from_dict(progress_payload)
                if isinstance(progress_payload, Mapping)
                else None
            ),
            bookmarks=tuple(
                BookmarkEntry.from_dict(item)
                for item in source.get("bookmarks", [])
                if isinstance(item, Mapping)
            ),
            notes=tuple(
                NoteEntry.from_dict(item)
                for item in source.get("notes", [])
                if isinstance(item, Mapping)
            ),
            plans=tuple(
                ReadingPlan.from_dict(item)
                for item in source.get("plans", [])
                if isinstance(item, Mapping)
            ),
        )


@dataclass(frozen=True)
class ProgressMarkResult:
    progress: ReadingProgress
    updated_plan_names: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "progress": self.progress.to_dict(),
            "updated_plan_names": list(self.updated_plan_names),
        }


@dataclass(frozen=True)
class PlanTodayResult:
    plan: ReadingPlan
    today_range: AyahRangeResult | None
    completed: bool
    total_ayahs: int
    completed_ayahs: int
    remaining_ayahs: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "plan": self.plan.to_dict(),
            "completed": self.completed,
            "total_ayahs": self.total_ayahs,
            "completed_ayahs": self.completed_ayahs,
            "remaining_ayahs": self.remaining_ayahs,
            "today_range": (
                self.today_range.to_dict() if self.today_range is not None else None
            ),
        }


class StudyStateStore(Protocol):
    @property
    def description(self) -> str: ...

    def load(self) -> StudyState: ...

    def save(self, state: StudyState) -> None: ...


@dataclass(frozen=True)
class LocalStudyStateStore:
    path: Path

    @property
    def description(self) -> str:
        return f"Private local study state at {self.path}"

    def load(self) -> StudyState:
        if not self.path.exists():
            return StudyState()

        payload = json.loads(self.path.read_text(encoding="utf-8"))
        if not isinstance(payload, Mapping):
            raise PersonalDataConfigurationError(
                f"Study state at {self.path} is not valid JSON object data."
            )

        return StudyState.from_dict(payload)

    def save(self, state: StudyState) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(
            json.dumps(state.to_dict(), ensure_ascii=False, indent=2, sort_keys=True)
            + "\n",
            encoding="utf-8",
        )


@dataclass(frozen=True)
class RemoteStudyStateStore:
    api_url: str
    api_token: str
    timeout_seconds: float = 10.0
    opener: UrlOpenFn | None = None

    @property
    def description(self) -> str:
        return f"Authenticated QuranKit study state at {self.api_url}"

    def load(self) -> StudyState:
        payload = self._request_json("/api/v1/me/study", method="GET")
        return StudyState.from_dict(payload)

    def save(self, state: StudyState) -> None:
        self._request_json(
            "/api/v1/me/study",
            method="PUT",
            body={"state": state.to_dict()},
        )

    def _request_json(
        self,
        path: str,
        *,
        method: str,
        body: Mapping[str, Any] | None = None,
    ) -> Mapping[str, Any]:
        url = f"{self.api_url.rstrip('/')}{path}"
        data: bytes | None = None
        headers = {
            "Accept": "application/json",
            "Authorization": f"Bearer {self.api_token}",
            "User-Agent": "qurankit-cli/0.1.0",
        }

        if body is not None:
            headers["Content-Type"] = "application/json"
            data = json.dumps(body, ensure_ascii=False).encode("utf-8")

        request = Request(url, data=data, headers=headers, method=method)
        opener = self.opener or urlopen

        try:
            with opener(request, timeout=self.timeout_seconds) as response:
                raw_body = response.read().decode("utf-8")
        except HTTPError as exc:
            if exc.code in {401, 403}:
                raise PersonalDataRequestError(
                    "Authenticated private study commands were rejected by the "
                    "QuranKit API. Check the configured API token."
                ) from exc

            detail = exc.read().decode("utf-8", errors="replace").strip()
            message = (
                f"Private study-state request failed with HTTP {exc.code} at {url}."
            )
            if detail:
                message = f"{message} {detail}"
            raise PersonalDataRequestError(message) from exc
        except URLError as exc:
            raise PersonalDataRequestError(
                f"Could not reach the QuranKit API at {self.api_url}: {exc.reason}"
            ) from exc

        if not raw_body.strip():
            return {}

        try:
            payload = json.loads(raw_body)
        except json.JSONDecodeError as exc:
            raise PersonalDataRequestError(
                f"Remote study-state API at {self.api_url} returned invalid JSON."
            ) from exc

        if not isinstance(payload, Mapping):
            raise PersonalDataRequestError(
                f"Remote study-state API at {self.api_url} returned an "
                "unexpected payload."
            )

        return payload


class StudyTracker:
    def __init__(self, store: StudyStateStore) -> None:
        self.store = store

    @property
    def description(self) -> str:
        return self.store.description

    def load_state(self) -> StudyState:
        return self.store.load()

    def list_bookmarks(self) -> tuple[BookmarkEntry, ...]:
        state = self.store.load()
        return tuple(sorted(state.bookmarks, key=lambda item: item.created_at, reverse=True))

    def list_notes(self, reading_range: AyahRange | None = None) -> tuple[NoteEntry, ...]:
        state = self.store.load()
        notes = state.notes
        if reading_range is not None:
            notes = tuple(
                note
                for note in notes
                if _ranges_overlap(note.reading_range, reading_range)
            )
        return tuple(sorted(notes, key=lambda item: item.updated_at, reverse=True))

    def list_plans(self) -> tuple[ReadingPlan, ...]:
        state = self.store.load()
        return tuple(sorted(state.plans, key=lambda item: item.created_at))

    def mark_progress(self, reading_range: AyahRange) -> ProgressMarkResult:
        state = self.store.load()
        timestamp = _now_iso()
        progress = ReadingProgress(
            reading_range=reading_range,
            updated_at=timestamp,
            source="manual_mark",
        )

        updated_plan_names: list[str] = []
        plans: list[ReadingPlan] = []
        for plan in state.plans:
            if not _range_contains_reference(plan.reading_range, reading_range.end):
                plans.append(plan)
                continue

            next_completed = reading_range.end
            if (
                plan.completed_through is not None
                and _reference_key(next_completed) < _reference_key(plan.completed_through)
            ):
                plans.append(plan)
                continue

            plans.append(
                replace(
                    plan,
                    completed_through=next_completed,
                    updated_at=timestamp,
                )
            )
            updated_plan_names.append(plan.name)

        self.store.save(replace(state, progress=progress, plans=tuple(plans)))
        return ProgressMarkResult(
            progress=progress,
            updated_plan_names=tuple(updated_plan_names),
        )

    def add_bookmark(
        self,
        reading_range: AyahRange,
        *,
        label: str | None = None,
    ) -> BookmarkEntry:
        state = self.store.load()
        normalized_label = _optional_text(label)

        for bookmark in state.bookmarks:
            if (
                bookmark.reading_range == reading_range
                and bookmark.label == normalized_label
            ):
                raise PersonalDataValidationError("That bookmark is already saved.")

        bookmark = BookmarkEntry(
            id=_new_id("bookmark"),
            reading_range=reading_range,
            label=normalized_label,
            created_at=_now_iso(),
        )
        self.store.save(
            replace(state, bookmarks=state.bookmarks + (bookmark,))
        )
        return bookmark

    def remove_bookmark(self, entry_id: str) -> BookmarkEntry:
        state = self.store.load()
        kept: list[BookmarkEntry] = []
        removed: BookmarkEntry | None = None

        for bookmark in state.bookmarks:
            if bookmark.id == entry_id:
                removed = bookmark
                continue
            kept.append(bookmark)

        if removed is None:
            raise PersonalDataNotFoundError(f"Bookmark '{entry_id}' was not found.")

        self.store.save(replace(state, bookmarks=tuple(kept)))
        return removed

    def add_note(self, reading_range: AyahRange, *, body: str) -> NoteEntry:
        normalized_body = _required_text(body, field_name="note")
        state = self.store.load()
        timestamp = _now_iso()
        note = NoteEntry(
            id=_new_id("note"),
            reading_range=reading_range,
            body=normalized_body,
            created_at=timestamp,
            updated_at=timestamp,
        )
        self.store.save(replace(state, notes=state.notes + (note,)))
        return note

    def remove_note(self, entry_id: str) -> NoteEntry:
        state = self.store.load()
        kept: list[NoteEntry] = []
        removed: NoteEntry | None = None

        for note in state.notes:
            if note.id == entry_id:
                removed = note
                continue
            kept.append(note)

        if removed is None:
            raise PersonalDataNotFoundError(f"Note '{entry_id}' was not found.")

        self.store.save(replace(state, notes=tuple(kept)))
        return removed

    def create_plan(
        self,
        *,
        name: str,
        reading_range: AyahRange,
        daily_ayah_target: int,
    ) -> ReadingPlan:
        normalized_name = _required_text(name, field_name="plan name")
        if daily_ayah_target < 1:
            raise PersonalDataValidationError(
                "Daily ayah target must be at least 1."
            )

        state = self.store.load()
        for plan in state.plans:
            if plan.name.casefold() == normalized_name.casefold():
                raise PersonalDataValidationError(
                    f"A plan named '{normalized_name}' already exists."
                )

        timestamp = _now_iso()
        plan = ReadingPlan(
            id=_new_id("plan"),
            name=normalized_name,
            reading_range=reading_range,
            daily_ayah_target=daily_ayah_target,
            created_at=timestamp,
            updated_at=timestamp,
        )
        self.store.save(replace(state, plans=state.plans + (plan,)))
        return plan

    def today(
        self,
        *,
        backend: QuranBackend,
        plan_selector: str | None,
        translation_identifier: str | None,
    ) -> PlanTodayResult:
        state = self.store.load()
        plan = _select_plan(state.plans, plan_selector)
        full_range = backend.get_range(
            plan.reading_range.start,
            plan.reading_range.end,
            translation_identifier,
        )

        completed_ayahs = 0
        if plan.completed_through is not None:
            for index, ayah in enumerate(full_range.ayahs):
                if ayah.reference == plan.completed_through.text:
                    completed_ayahs = index + 1
                    break
            else:
                raise PersonalDataValidationError(
                    f"Plan '{plan.name}' has a checkpoint outside its saved range."
                )

        if completed_ayahs >= len(full_range.ayahs):
            return PlanTodayResult(
                plan=plan,
                today_range=None,
                completed=True,
                total_ayahs=len(full_range.ayahs),
                completed_ayahs=len(full_range.ayahs),
                remaining_ayahs=0,
            )

        today_ayahs = full_range.ayahs[
            completed_ayahs : completed_ayahs + plan.daily_ayah_target
        ]
        today_range = AyahRangeResult(
            start_reference=today_ayahs[0].reference,
            end_reference=today_ayahs[-1].reference,
            ayahs=today_ayahs,
            arabic_source=full_range.arabic_source,
            translation_attribution=full_range.translation_attribution,
        )

        return PlanTodayResult(
            plan=plan,
            today_range=today_range,
            completed=False,
            total_ayahs=len(full_range.ayahs),
            completed_ayahs=completed_ayahs,
            remaining_ayahs=len(full_range.ayahs) - completed_ayahs,
        )


def parse_ayah_range(value: str) -> AyahRange:
    normalized = value.strip()
    if not normalized:
        raise PersonalDataValidationError("Ayah range cannot be empty.")

    start_text, separator, end_text = normalized.partition("-")
    start_reference = _parse_reference(start_text)
    if separator != "-":
        return AyahRange(start=start_reference, end=start_reference)

    normalized_end = end_text.strip()
    if not normalized_end:
        raise PersonalDataValidationError(
            "Ayah range end cannot be empty after '-'."
        )

    if ":" in normalized_end:
        end_reference = _parse_reference(normalized_end)
    else:
        if not normalized_end.isdigit():
            raise PersonalDataValidationError(
                "Ayah range end must be an ayah number or SURAH:AYAH reference."
            )
        end_reference = AyahReference(
            surah_number=start_reference.surah_number,
            ayah_number=int(normalized_end),
        )

    return AyahRange(start=start_reference, end=end_reference)


def describe_study_store(settings: Settings) -> tuple[str, str]:
    if settings.state_mode is StateMode.LOCAL:
        return ("local", f"Private local study state at {settings.state_path}")

    suffix = "authentication required"
    if settings.api_token:
        suffix = "authenticated"
    return ("remote", f"Remote QuranKit study state at {settings.api_url} ({suffix})")


def select_study_store(settings: Settings) -> StudyStateStore:
    if settings.state_mode is StateMode.LOCAL:
        return LocalStudyStateStore(Path(settings.state_path))

    if not settings.api_token:
        raise PersonalDataConfigurationError(
            "Remote study-state mode requires an API token. Set one with "
            "`qurankit config set api-token ...`, `QURANKIT_API_TOKEN`, or switch "
            "back to local private state with `qurankit config set state-mode local`."
        )

    return RemoteStudyStateStore(
        api_url=settings.api_url,
        api_token=settings.api_token,
    )


def _new_id(prefix: str) -> str:
    return f"{prefix}-{uuid4().hex[:10]}"


def _now_iso() -> str:
    return (
        datetime.now(timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )


def _reference_key(reference: AyahReference) -> tuple[int, int]:
    return (reference.surah_number, reference.ayah_number)


def _reference_to_dict(reference: AyahReference) -> dict[str, Any]:
    return {
        "reference": reference.text,
        "surah_number": reference.surah_number,
        "ayah_number": reference.ayah_number,
    }


def _parse_reference(value: str) -> AyahReference:
    normalized = value.strip()
    surah_text, separator, ayah_text = normalized.partition(":")
    if separator != ":" or not surah_text.isdigit() or not ayah_text.isdigit():
        raise PersonalDataValidationError(
            "Ayah references must look like SURAH:AYAH, for example 2:255."
        )

    surah_number = int(surah_text)
    ayah_number = int(ayah_text)
    if surah_number < 1 or ayah_number < 1:
        raise PersonalDataValidationError(
            "Ayah reference numbers must both be positive."
        )

    return AyahReference(surah_number=surah_number, ayah_number=ayah_number)


def _reference_from_value(value: Any) -> AyahReference:
    if isinstance(value, Mapping):
        reference_text = value.get("reference")
        if reference_text is not None:
            return _parse_reference(str(reference_text))

        surah_number = value.get("surah_number")
        ayah_number = value.get("ayah_number")
        if surah_number is None or ayah_number is None:
            raise PersonalDataValidationError("Reference mappings need surah and ayah numbers.")
        return AyahReference(
            surah_number=int(surah_number),
            ayah_number=int(ayah_number),
        )

    if isinstance(value, str):
        return _parse_reference(value)

    raise PersonalDataValidationError("Reference values must be strings or mappings.")


def _range_contains_reference(reading_range: AyahRange, reference: AyahReference) -> bool:
    key = _reference_key(reference)
    return _reference_key(reading_range.start) <= key <= _reference_key(reading_range.end)


def _ranges_overlap(left: AyahRange, right: AyahRange) -> bool:
    return not (
        _reference_key(left.end) < _reference_key(right.start)
        or _reference_key(right.end) < _reference_key(left.start)
    )


def _select_plan(
    plans: Sequence[ReadingPlan], selector: str | None
) -> ReadingPlan:
    if not plans:
        raise PersonalDataNotFoundError("No reading plans have been created yet.")

    if selector is None:
        if len(plans) == 1:
            return plans[0]
        raise PersonalDataValidationError(
            "Multiple plans are saved. Pass `--plan` with the plan id or exact name."
        )

    normalized_selector = selector.strip()
    if not normalized_selector:
        raise PersonalDataValidationError("--plan cannot be empty.")

    for plan in plans:
        if plan.id == normalized_selector:
            return plan

    matching_names = [
        plan for plan in plans if plan.name.casefold() == normalized_selector.casefold()
    ]
    if len(matching_names) == 1:
        return matching_names[0]
    if len(matching_names) > 1:
        raise PersonalDataValidationError(
            f"Plan name '{normalized_selector}' is ambiguous. Use the plan id instead."
        )

    raise PersonalDataNotFoundError(
        f"No reading plan matched '{normalized_selector}'."
    )


def _required_text(value: str, *, field_name: str) -> str:
    normalized = value.strip()
    if not normalized:
        raise PersonalDataValidationError(f"{field_name} cannot be empty.")
    return normalized


def _optional_text(value: Any) -> str | None:
    if value is None:
        return None

    normalized = str(value).strip()
    if not normalized:
        return None
    return normalized


def _unwrap_mapping(payload: Mapping[str, Any], key: str) -> Mapping[str, Any]:
    nested = payload.get(key)
    if isinstance(nested, Mapping):
        return nested
    return payload
