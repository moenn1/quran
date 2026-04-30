from __future__ import annotations

from collections.abc import Callable
from datetime import datetime
from typing import Any, TypeVar

from fastapi import APIRouter, Depends, Path, Query, Request, Response, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.orm import Session

from qurankit_api.core.auth import AuthenticatedIdentity, resolve_access_token
from qurankit_api.core.errors import ApiError
from qurankit_api.core.study import (
    apply_progress_checkpoint,
    build_bookmark_payload,
    build_export_payload,
    build_note_payload,
    build_plan_payload,
    build_session_payload,
    build_study_state_payload,
    build_study_summary_payload,
    build_progress_payload,
    calculate_streak_days,
    delete_study_state,
    range_from_note,
    replace_study_state,
    resolve_plan_target,
    resolve_range_label,
    resolve_range_mapping,
    resolve_range_input,
)
from qurankit_api.db.dependencies import get_db_session
from qurankit_api.models import Bookmark, Note, ReadingPlan, ReadingPlanStatus, ReadingProgress, ReadingSession
from qurankit_api.schemas.errors import COMMON_ERROR_RESPONSES, ErrorEnvelope
from qurankit_api.schemas.study import (
    BookmarkCreateRequest,
    BookmarkListResponse,
    BookmarkResource,
    NoteCreateRequest,
    NoteListResponse,
    NoteResource,
    NoteUpdateRequest,
    OperationStatus,
    PlanCreateRequest,
    PlanUpdateRequest,
    ProgressResponse,
    ProgressUpdateRequest,
    ReadingPlanListResponse,
    ReadingPlanResource,
    ReadingSessionCreateRequest,
    ReadingSessionListResponse,
    ReadingSessionResource,
    StudyReplaceRequest,
    StudyResponse,
)


PRIVATE_ERROR_RESPONSES = {
    **COMMON_ERROR_RESPONSES,
    401: {
        "model": ErrorEnvelope,
        "description": "Authentication is required for this private endpoint.",
    },
    404: {
        "model": ErrorEnvelope,
        "description": "The requested private study record was not found.",
    },
    409: {
        "model": ErrorEnvelope,
        "description": "The requested private study change conflicts with existing data.",
    },
    503: {
        "model": ErrorEnvelope,
        "description": "Database access is unavailable for this API instance.",
    },
}

router = APIRouter(prefix="/me", tags=["Private Study"])
bearer_scheme = HTTPBearer(auto_error=False)
OwnedModelT = TypeVar("OwnedModelT", Bookmark, Note, ReadingPlan, ReadingSession, ReadingProgress)


def _apply_private_headers(response: Response) -> None:
    response.headers["Cache-Control"] = "private, no-store"
    response.headers["Pragma"] = "no-cache"


def _private_headers_dependency(response: Response) -> None:
    _apply_private_headers(response)


def _optional_text(value: str | None) -> str | None:
    if value is None:
        return None
    normalized = value.strip()
    return normalized or None


def _required_text(value: str | None, *, field_name: str) -> str:
    normalized = (value or "").strip()
    if not normalized:
        raise ApiError(
            status_code=422,
            code="invalid_study_payload",
            message=f"`{field_name}` cannot be blank.",
            details={"field": field_name},
        )
    return normalized


def _ranges_overlap(left: dict[str, Any], right: dict[str, Any]) -> bool:
    left_start = left["start"]["surah_number"], left["start"]["ayah_number"]
    left_end = left["end"]["surah_number"], left["end"]["ayah_number"]
    right_start = right["start"]["surah_number"], right["start"]["ayah_number"]
    right_end = right["end"]["surah_number"], right["end"]["ayah_number"]
    return not (left_end < right_start or right_end < left_start)


def get_current_identity(
    request: Request,
    response: Response,
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    session: Session = Depends(get_db_session),
) -> AuthenticatedIdentity:
    request.state.private_no_store = True
    _apply_private_headers(response)
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise ApiError(
            status_code=401,
            code="authentication_required",
            message="This private QuranKit endpoint requires `Authorization: Bearer <token>`.",
            details=None,
        )
    identity = resolve_access_token(session, credentials.credentials)
    session.commit()
    return identity


def _study_response(session: Session, identity: AuthenticatedIdentity) -> StudyResponse:
    return StudyResponse(
        state=build_study_state_payload(session, identity.user),
        summary=build_study_summary_payload(session, identity.user),
    )


def _progress_response(
    session: Session,
    identity: AuthenticatedIdentity,
    *,
    updated_plan_names: tuple[str, ...] = (),
) -> ProgressResponse:
    progress = session.scalar(
        select(ReadingProgress).where(ReadingProgress.user_id == identity.user.id),
    )
    return ProgressResponse(
        progress=build_progress_payload(session, progress),
        streak_days=calculate_streak_days(session, identity.user),
        updated_plan_names=list(updated_plan_names),
    )


def _owned_record(
    session: Session,
    *,
    model: type[OwnedModelT],
    record_id: str,
    user_id: str,
    code: str,
    label: str,
) -> OwnedModelT:
    record = session.get(model, record_id)
    if record is None or getattr(record, "user_id", None) != user_id:
        raise ApiError(
            status_code=404,
            code=code,
            message=f"{label} `{record_id}` was not found.",
            details={"id": record_id},
        )
    return record


def _plan_status(value: str | None) -> ReadingPlanStatus:
    normalized = _optional_text(value) or ReadingPlanStatus.draft.value
    try:
        return ReadingPlanStatus(normalized)
    except ValueError as exc:
        raise ApiError(
            status_code=422,
            code="invalid_plan_status",
            message="Plan status must be one of `draft`, `active`, `paused`, `completed`, or `archived`.",
            details={"value": normalized},
        ) from exc


def _coerce_range_label(reference: str | None, range_label: str | None, *, field_name: str) -> str:
    candidate = _optional_text(range_label) or _optional_text(reference)
    if candidate is None:
        raise ApiError(
            status_code=422,
            code="invalid_ayah_range",
            message=f"`{field_name}` requires an ayah reference or range.",
            details={"field": field_name},
        )
    return candidate


@router.get(
    "/study",
    response_model=StudyResponse,
    responses=PRIVATE_ERROR_RESPONSES,
    summary="Read the authenticated QuranKit study document",
)
async def read_study(
    identity: AuthenticatedIdentity = Depends(get_current_identity),
    session: Session = Depends(get_db_session),
    _headers: None = Depends(_private_headers_dependency),
) -> StudyResponse:
    return _study_response(session, identity)


@router.put(
    "/study",
    response_model=StudyResponse,
    responses=PRIVATE_ERROR_RESPONSES,
    summary="Replace the authenticated QuranKit study document",
)
async def replace_study(
    request: StudyReplaceRequest,
    identity: AuthenticatedIdentity = Depends(get_current_identity),
    session: Session = Depends(get_db_session),
    _headers: None = Depends(_private_headers_dependency),
) -> StudyResponse:
    replace_study_state(session, user=identity.user, payload=request.state)
    session.commit()
    return _study_response(session, identity)


@router.delete(
    "/study",
    response_model=OperationStatus,
    responses=PRIVATE_ERROR_RESPONSES,
    summary="Delete all authenticated QuranKit study state",
)
async def delete_study(
    identity: AuthenticatedIdentity = Depends(get_current_identity),
    session: Session = Depends(get_db_session),
    _headers: None = Depends(_private_headers_dependency),
) -> OperationStatus:
    delete_study_state(session, user=identity.user)
    session.commit()
    return OperationStatus(message="Private study sessions, progress, plans, bookmarks, and notes were deleted.")


@router.get(
    "/progress",
    response_model=ProgressResponse,
    responses=PRIVATE_ERROR_RESPONSES,
    summary="Read the authenticated QuranKit reading checkpoint",
)
async def read_progress(
    identity: AuthenticatedIdentity = Depends(get_current_identity),
    session: Session = Depends(get_db_session),
    _headers: None = Depends(_private_headers_dependency),
) -> ProgressResponse:
    return _progress_response(session, identity)


@router.put(
    "/progress",
    response_model=ProgressResponse,
    responses=PRIVATE_ERROR_RESPONSES,
    summary="Mark a private QuranKit reading checkpoint",
)
async def mark_progress(
    request: ProgressUpdateRequest,
    identity: AuthenticatedIdentity = Depends(get_current_identity),
    session: Session = Depends(get_db_session),
    _headers: None = Depends(_private_headers_dependency),
) -> ProgressResponse:
    reading_range = resolve_range_label(session, request.range_label)
    _progress, updated_plan_names = apply_progress_checkpoint(
        session,
        user=identity.user,
        reading_range=reading_range,
        source=_optional_text(request.source) or "manual_mark",
    )
    session.commit()
    return _progress_response(session, identity, updated_plan_names=updated_plan_names)


@router.delete(
    "/progress",
    response_model=OperationStatus,
    responses=PRIVATE_ERROR_RESPONSES,
    summary="Clear the latest authenticated QuranKit checkpoint",
)
async def clear_progress(
    identity: AuthenticatedIdentity = Depends(get_current_identity),
    session: Session = Depends(get_db_session),
    _headers: None = Depends(_private_headers_dependency),
) -> OperationStatus:
    progress = session.scalar(
        select(ReadingProgress).where(ReadingProgress.user_id == identity.user.id),
    )
    if progress is not None:
        session.delete(progress)
        session.commit()
        return OperationStatus(message="The latest private checkpoint was cleared.")

    return OperationStatus(message="No latest private checkpoint was stored.")


@router.get(
    "/reading-sessions",
    response_model=ReadingSessionListResponse,
    responses=PRIVATE_ERROR_RESPONSES,
    summary="List authenticated QuranKit reading sessions",
)
async def list_reading_sessions(
    identity: AuthenticatedIdentity = Depends(get_current_identity),
    session: Session = Depends(get_db_session),
    _headers: None = Depends(_private_headers_dependency),
) -> ReadingSessionListResponse:
    sessions = session.scalars(
        select(ReadingSession)
        .where(ReadingSession.user_id == identity.user.id)
        .order_by(ReadingSession.started_at.desc(), ReadingSession.id.desc()),
    ).all()
    return ReadingSessionListResponse(
        count=len(sessions),
        sessions=[build_session_payload(session, reading_session) for reading_session in sessions],
    )


@router.post(
    "/reading-sessions",
    response_model=ReadingSessionResource,
    responses=PRIVATE_ERROR_RESPONSES,
    status_code=status.HTTP_201_CREATED,
    summary="Create an authenticated QuranKit reading session",
)
async def create_reading_session(
    request: ReadingSessionCreateRequest,
    identity: AuthenticatedIdentity = Depends(get_current_identity),
    session: Session = Depends(get_db_session),
    _headers: None = Depends(_private_headers_dependency),
) -> ReadingSessionResource:
    if request.ended_at is not None and request.ended_at < request.started_at:
        raise ApiError(
            status_code=422,
            code="invalid_reading_session",
            message="`ended_at` must be on or after `started_at`.",
            details={"started_at": request.started_at, "ended_at": request.ended_at},
        )

    reading_range = resolve_range_label(session, request.range_label) if request.range_label else None
    entry = ReadingSession(
        user_id=identity.user.id,
        started_at=request.started_at,
        ended_at=request.ended_at,
        started_ayah_global_number=(
            reading_range.start.global_ayah_number if reading_range is not None else None
        ),
        ended_ayah_global_number=(
            reading_range.end.global_ayah_number if reading_range is not None else None
        ),
        metadata_json={"source": _optional_text(request.source) or "manual_session"},
    )
    session.add(entry)
    session.commit()
    session.refresh(entry)
    return ReadingSessionResource.model_validate(build_session_payload(session, entry))


@router.delete(
    "/reading-sessions/{session_id}",
    response_model=OperationStatus,
    responses=PRIVATE_ERROR_RESPONSES,
    summary="Delete an authenticated QuranKit reading session",
)
async def delete_reading_session(
    session_id: str = Path(...),
    identity: AuthenticatedIdentity = Depends(get_current_identity),
    session: Session = Depends(get_db_session),
    _headers: None = Depends(_private_headers_dependency),
) -> OperationStatus:
    entry = _owned_record(
        session,
        model=ReadingSession,
        record_id=session_id,
        user_id=identity.user.id,
        code="reading_session_not_found",
        label="Reading session",
    )
    session.delete(entry)
    session.commit()
    return OperationStatus(message=f"Reading session `{session_id}` was deleted.")


@router.get(
    "/bookmarks",
    response_model=BookmarkListResponse,
    responses=PRIVATE_ERROR_RESPONSES,
    summary="List authenticated QuranKit bookmarks",
)
async def list_bookmarks(
    identity: AuthenticatedIdentity = Depends(get_current_identity),
    session: Session = Depends(get_db_session),
    _headers: None = Depends(_private_headers_dependency),
) -> BookmarkListResponse:
    bookmarks = session.scalars(
        select(Bookmark)
        .where(Bookmark.user_id == identity.user.id)
        .order_by(Bookmark.created_at.desc(), Bookmark.id.desc()),
    ).all()
    return BookmarkListResponse(
        count=len(bookmarks),
        bookmarks=[build_bookmark_payload(session, bookmark) for bookmark in bookmarks],
    )


@router.post(
    "/bookmarks",
    response_model=BookmarkResource,
    responses=PRIVATE_ERROR_RESPONSES,
    status_code=status.HTTP_201_CREATED,
    summary="Save a private QuranKit bookmark",
)
async def create_bookmark(
    request: BookmarkCreateRequest,
    identity: AuthenticatedIdentity = Depends(get_current_identity),
    session: Session = Depends(get_db_session),
    _headers: None = Depends(_private_headers_dependency),
) -> BookmarkResource:
    reading_range = resolve_range_label(session, request.reference)
    if reading_range.start.global_ayah_number != reading_range.end.global_ayah_number:
        raise ApiError(
            status_code=422,
            code="invalid_bookmark_range",
            message="Bookmarks currently support one ayah per record.",
            details={"reference": request.reference},
        )

    existing = session.scalar(
        select(Bookmark).where(
            Bookmark.user_id == identity.user.id,
            Bookmark.ayah_global_number == reading_range.end.global_ayah_number,
        ),
    )
    if existing is not None:
        raise ApiError(
            status_code=409,
            code="bookmark_exists",
            message=f"A bookmark for `{reading_range.label}` already exists.",
            details={"reference": reading_range.label},
        )

    bookmark = Bookmark(
        user_id=identity.user.id,
        ayah_global_number=reading_range.end.global_ayah_number,
        label=_optional_text(request.label),
    )
    session.add(bookmark)
    session.commit()
    session.refresh(bookmark)
    return BookmarkResource.model_validate(build_bookmark_payload(session, bookmark))


@router.delete(
    "/bookmarks/{bookmark_id}",
    response_model=OperationStatus,
    responses=PRIVATE_ERROR_RESPONSES,
    summary="Delete a private QuranKit bookmark",
)
async def delete_bookmark(
    bookmark_id: str = Path(...),
    identity: AuthenticatedIdentity = Depends(get_current_identity),
    session: Session = Depends(get_db_session),
    _headers: None = Depends(_private_headers_dependency),
) -> OperationStatus:
    bookmark = _owned_record(
        session,
        model=Bookmark,
        record_id=bookmark_id,
        user_id=identity.user.id,
        code="bookmark_not_found",
        label="Bookmark",
    )
    session.delete(bookmark)
    session.commit()
    return OperationStatus(message=f"Bookmark `{bookmark_id}` was deleted.")


@router.get(
    "/notes",
    response_model=NoteListResponse,
    responses=PRIVATE_ERROR_RESPONSES,
    summary="List authenticated QuranKit notes",
)
async def list_notes(
    range_label: str | None = Query(None),
    identity: AuthenticatedIdentity = Depends(get_current_identity),
    session: Session = Depends(get_db_session),
    _headers: None = Depends(_private_headers_dependency),
) -> NoteListResponse:
    notes = session.scalars(
        select(Note)
        .where(Note.user_id == identity.user.id)
        .order_by(Note.updated_at.desc(), Note.id.desc()),
    ).all()
    note_payloads = [build_note_payload(session, note) for note in notes]
    if range_label:
        filter_range = resolve_range_label(session, range_label)
        filter_payload = {
            "start": {
                "surah_number": filter_range.start.surah_number,
                "ayah_number": filter_range.start.ayah_number,
            },
            "end": {
                "surah_number": filter_range.end.surah_number,
                "ayah_number": filter_range.end.ayah_number,
            },
        }
        note_payloads = [
            payload
            for payload in note_payloads
            if payload["range"] is not None and _ranges_overlap(payload["range"], filter_payload)
        ]
    return NoteListResponse(count=len(note_payloads), notes=note_payloads)


@router.post(
    "/notes",
    response_model=NoteResource,
    responses=PRIVATE_ERROR_RESPONSES,
    status_code=status.HTTP_201_CREATED,
    summary="Save a private QuranKit note",
)
async def create_note(
    request: NoteCreateRequest,
    identity: AuthenticatedIdentity = Depends(get_current_identity),
    session: Session = Depends(get_db_session),
    _headers: None = Depends(_private_headers_dependency),
) -> NoteResource:
    reading_range = resolve_range_input(
        session,
        range_label=_coerce_range_label(request.reference, request.range_label, field_name="note"),
        field_name="note",
    )
    note = Note(
        user_id=identity.user.id,
        ayah_global_number=reading_range.end.global_ayah_number,
        title=_optional_text(request.title),
        body=_required_text(request.body, field_name="body"),
        metadata_json={
            "start_ayah_global_number": reading_range.start.global_ayah_number,
            "end_ayah_global_number": reading_range.end.global_ayah_number,
        },
    )
    session.add(note)
    session.commit()
    session.refresh(note)
    return NoteResource.model_validate(build_note_payload(session, note))


@router.patch(
    "/notes/{note_id}",
    response_model=NoteResource,
    responses=PRIVATE_ERROR_RESPONSES,
    summary="Update a private QuranKit note",
)
async def update_note(
    request: NoteUpdateRequest,
    note_id: str = Path(...),
    identity: AuthenticatedIdentity = Depends(get_current_identity),
    session: Session = Depends(get_db_session),
    _headers: None = Depends(_private_headers_dependency),
) -> NoteResource:
    note = _owned_record(
        session,
        model=Note,
        record_id=note_id,
        user_id=identity.user.id,
        code="note_not_found",
        label="Note",
    )
    if request.reference is not None or request.range_label is not None:
        reading_range = resolve_range_input(
            session,
            range_label=_coerce_range_label(request.reference, request.range_label, field_name="note"),
            field_name="note",
        )
        note.ayah_global_number = reading_range.end.global_ayah_number
        note.metadata_json = {
            "start_ayah_global_number": reading_range.start.global_ayah_number,
            "end_ayah_global_number": reading_range.end.global_ayah_number,
        }
    if request.title is not None:
        note.title = _optional_text(request.title)
    if request.body is not None:
        note.body = _required_text(request.body, field_name="body")
    session.commit()
    session.refresh(note)
    return NoteResource.model_validate(build_note_payload(session, note))


@router.delete(
    "/notes/{note_id}",
    response_model=OperationStatus,
    responses=PRIVATE_ERROR_RESPONSES,
    summary="Delete a private QuranKit note",
)
async def delete_note(
    note_id: str = Path(...),
    identity: AuthenticatedIdentity = Depends(get_current_identity),
    session: Session = Depends(get_db_session),
    _headers: None = Depends(_private_headers_dependency),
) -> OperationStatus:
    note = _owned_record(
        session,
        model=Note,
        record_id=note_id,
        user_id=identity.user.id,
        code="note_not_found",
        label="Note",
    )
    session.delete(note)
    session.commit()
    return OperationStatus(message=f"Note `{note_id}` was deleted.")


@router.get(
    "/plans",
    response_model=ReadingPlanListResponse,
    responses=PRIVATE_ERROR_RESPONSES,
    summary="List authenticated QuranKit reading plans",
)
async def list_plans(
    identity: AuthenticatedIdentity = Depends(get_current_identity),
    session: Session = Depends(get_db_session),
    _headers: None = Depends(_private_headers_dependency),
) -> ReadingPlanListResponse:
    plans = session.scalars(
        select(ReadingPlan)
        .where(ReadingPlan.user_id == identity.user.id)
        .order_by(ReadingPlan.created_at.asc(), ReadingPlan.id.asc()),
    ).all()
    return ReadingPlanListResponse(
        count=len(plans),
        plans=[build_plan_payload(session, plan) for plan in plans],
    )


@router.post(
    "/plans",
    response_model=ReadingPlanResource,
    responses=PRIVATE_ERROR_RESPONSES,
    status_code=status.HTTP_201_CREATED,
    summary="Create an authenticated QuranKit reading plan",
)
async def create_plan(
    request: PlanCreateRequest,
    identity: AuthenticatedIdentity = Depends(get_current_identity),
    session: Session = Depends(get_db_session),
    _headers: None = Depends(_private_headers_dependency),
) -> ReadingPlanResource:
    reading_range = resolve_range_label(session, request.range_label)
    name = _required_text(request.name, field_name="name")

    duplicate = session.scalar(
        select(ReadingPlan).where(
            ReadingPlan.user_id == identity.user.id,
            ReadingPlan.title == name,
        ),
    )
    if duplicate is not None:
        raise ApiError(
            status_code=409,
            code="plan_exists",
            message=f"A reading plan named `{name}` already exists.",
            details={"name": name},
        )

    target = resolve_plan_target(
        total_ayahs=reading_range.ayah_count,
        daily_ayah_target=request.daily_ayah_target,
        start_date=request.start_date,
        end_date=request.end_date,
    )
    plan = ReadingPlan(
        user_id=identity.user.id,
        title=name,
        start_ayah_global_number=reading_range.start.global_ayah_number,
        end_ayah_global_number=reading_range.end.global_ayah_number,
        start_date=request.start_date,
        end_date=request.end_date,
        target_ayahs_per_day=target,
        status=_plan_status(request.status),
        metadata_json={
            "start_ayah_global_number": reading_range.start.global_ayah_number,
            "end_ayah_global_number": reading_range.end.global_ayah_number,
        },
    )
    session.add(plan)
    session.commit()
    session.refresh(plan)
    return ReadingPlanResource.model_validate(build_plan_payload(session, plan))


@router.patch(
    "/plans/{plan_id}",
    response_model=ReadingPlanResource,
    responses=PRIVATE_ERROR_RESPONSES,
    summary="Update an authenticated QuranKit reading plan",
)
async def update_plan(
    request: PlanUpdateRequest,
    plan_id: str = Path(...),
    identity: AuthenticatedIdentity = Depends(get_current_identity),
    session: Session = Depends(get_db_session),
    _headers: None = Depends(_private_headers_dependency),
) -> ReadingPlanResource:
    plan = _owned_record(
        session,
        model=ReadingPlan,
        record_id=plan_id,
        user_id=identity.user.id,
        code="plan_not_found",
        label="Reading plan",
    )
    payload = request if isinstance(request, dict) else None
    if payload is None:
        payload = {}
        if hasattr(request, "model_dump"):
            payload = request.model_dump(exclude_unset=True)
    name = _optional_text(payload.get("name")) if payload else None

    if name is not None:
        duplicate = session.scalar(
            select(ReadingPlan).where(
                ReadingPlan.user_id == identity.user.id,
                ReadingPlan.title == name,
                ReadingPlan.id != plan.id,
            ),
        )
        if duplicate is not None:
            raise ApiError(
                status_code=409,
                code="plan_exists",
                message=f"A reading plan named `{name}` already exists.",
                details={"name": name},
            )
        plan.title = name

    current_range_label = payload.get("range_label") if payload else None
    if current_range_label:
        reading_range = resolve_range_label(session, current_range_label)
        plan.start_ayah_global_number = reading_range.start.global_ayah_number
        plan.end_ayah_global_number = reading_range.end.global_ayah_number
        if (
            plan.completed_through_ayah_global_number is not None
            and not (
                reading_range.start.global_ayah_number
                <= plan.completed_through_ayah_global_number
                <= reading_range.end.global_ayah_number
            )
        ):
            plan.completed_through_ayah_global_number = None

    start_date = payload.get("start_date", plan.start_date) if payload else plan.start_date
    end_date = payload.get("end_date", plan.end_date) if payload else plan.end_date
    daily_target = (
        payload["daily_ayah_target"] if payload and "daily_ayah_target" in payload else plan.target_ayahs_per_day
    )
    plan.start_date = start_date
    plan.end_date = end_date
    plan.target_ayahs_per_day = resolve_plan_target(
        total_ayahs=plan.end_ayah_global_number - plan.start_ayah_global_number + 1,
        daily_ayah_target=daily_target,
        start_date=plan.start_date,
        end_date=plan.end_date,
    )
    if payload and "status" in payload:
        plan.status = _plan_status(payload.get("status"))

    session.commit()
    session.refresh(plan)
    return ReadingPlanResource.model_validate(build_plan_payload(session, plan))


@router.delete(
    "/plans/{plan_id}",
    response_model=OperationStatus,
    responses=PRIVATE_ERROR_RESPONSES,
    summary="Delete an authenticated QuranKit reading plan",
)
async def delete_plan(
    plan_id: str = Path(...),
    identity: AuthenticatedIdentity = Depends(get_current_identity),
    session: Session = Depends(get_db_session),
    _headers: None = Depends(_private_headers_dependency),
) -> OperationStatus:
    plan = _owned_record(
        session,
        model=ReadingPlan,
        record_id=plan_id,
        user_id=identity.user.id,
        code="plan_not_found",
        label="Reading plan",
    )
    session.delete(plan)
    session.commit()
    return OperationStatus(message=f"Reading plan `{plan_id}` was deleted.")


@router.get(
    "/plans/{plan_id}/today",
    response_model=ReadingPlanResource,
    responses=PRIVATE_ERROR_RESPONSES,
    summary="Read today's target for an authenticated QuranKit reading plan",
)
async def read_plan_today(
    plan_id: str = Path(...),
    identity: AuthenticatedIdentity = Depends(get_current_identity),
    session: Session = Depends(get_db_session),
    _headers: None = Depends(_private_headers_dependency),
) -> ReadingPlanResource:
    plan = _owned_record(
        session,
        model=ReadingPlan,
        record_id=plan_id,
        user_id=identity.user.id,
        code="plan_not_found",
        label="Reading plan",
    )
    return ReadingPlanResource.model_validate(build_plan_payload(session, plan))


@router.get(
    "/exports/{scope}",
    responses=PRIVATE_ERROR_RESPONSES,
    summary="Export authenticated QuranKit study data",
)
async def export_study_data(
    scope: str = Path(...),
    identity: AuthenticatedIdentity = Depends(get_current_identity),
    session: Session = Depends(get_db_session),
    _headers: None = Depends(_private_headers_dependency),
) -> dict[str, Any]:
    return build_export_payload(session, user=identity.user, scope=scope)
