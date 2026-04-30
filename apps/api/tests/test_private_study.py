from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient

from qurankit_api.app import create_app
from qurankit_api.core.config import Settings


@pytest.fixture
def study_client(loaded_database_url: str) -> TestClient:
    settings = Settings(
        app_name="QuranKit API Test",
        app_version="0.1.0-test",
        environment="test",
        redoc_url=None,
        database_url=loaded_database_url,
    )

    with TestClient(create_app(settings)) as test_client:
        yield test_client


def _register(
    client: TestClient,
    *,
    email: str = "reader@example.com",
    password: str = "strong-password-123",
    display_name: str = "Reader",
) -> str:
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": password,
            "display_name": display_name,
        },
    )
    assert response.status_code == 201, response.text
    assert response.headers["Cache-Control"] == "no-store"
    return response.json()["token"]["access_token"]


def _login(
    client: TestClient,
    *,
    email: str = "reader@example.com",
    password: str = "strong-password-123",
) -> str:
    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": email,
            "password": password,
        },
    )
    assert response.status_code == 200, response.text
    assert response.headers["Cache-Control"] == "no-store"
    return response.json()["token"]["access_token"]


def _auth_headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def _reference(value: str) -> dict[str, int | str]:
    surah_text, ayah_text = value.split(":")
    return {
        "reference": value,
        "surah_number": int(surah_text),
        "ayah_number": int(ayah_text),
    }


def _range(start: str, end: str | None = None) -> dict[str, object]:
    resolved_end = end or start
    start_ref = _reference(start)
    end_ref = _reference(resolved_end)
    if start == resolved_end:
        label = start
    elif start_ref["surah_number"] == end_ref["surah_number"]:
        label = f"{start}-{end_ref['ayah_number']}"
    else:
        label = f"{start}-{resolved_end}"
    return {
        "start": start_ref,
        "end": end_ref,
        "label": label,
    }


def test_private_study_endpoints_require_bearer_auth(study_client: TestClient) -> None:
    response = study_client.get("/api/v1/me/study", headers={"X-Request-ID": "study-401"})

    assert response.status_code == 401
    assert response.headers["Cache-Control"] == "private, no-store"
    assert response.json() == {
        "error": {
            "code": "authentication_required",
            "message": "This private QuranKit endpoint requires `Authorization: Bearer <token>`.",
            "details": None,
        },
        "meta": {"request_id": "study-401"},
    }


def test_register_login_and_study_document_round_trip(study_client: TestClient) -> None:
    register_token = _register(study_client)
    login_token = _login(study_client)

    assert login_token != register_token

    payload = {
        "state": {
            "progress": {
                "range": _range("1:1", "1:1"),
                "updated_at": "2026-04-30T00:00:00Z",
                "source": "remote_sync",
            },
            "bookmarks": [
                {
                    "id": "bookmark-1",
                    "range": _range("2:2"),
                    "label": "Study later",
                    "created_at": "2026-04-30T00:00:00Z",
                }
            ],
            "notes": [
                {
                    "id": "note-1",
                    "range": _range("1:1", "2:1"),
                    "title": "Opening",
                    "body": "Keep this passage close.",
                    "created_at": "2026-04-30T00:00:00Z",
                    "updated_at": "2026-04-30T00:10:00Z",
                }
            ],
            "plans": [
                {
                    "id": "plan-1",
                    "name": "Sample khatm",
                    "range": _range("1:1", "2:2"),
                    "daily_ayah_target": 2,
                    "created_at": "2026-04-30T00:00:00Z",
                    "updated_at": "2026-04-30T00:00:00Z",
                    "completed_through": _reference("1:1"),
                    "status": "active",
                }
            ],
        }
    }

    put_response = study_client.put(
        "/api/v1/me/study",
        json=payload,
        headers=_auth_headers(register_token),
    )

    assert put_response.status_code == 200, put_response.text
    body = put_response.json()

    assert body["state"]["bookmarks"][0]["id"] == "bookmark-1"
    assert body["state"]["notes"][0]["id"] == "note-1"
    assert body["state"]["notes"][0]["range"]["label"] == "1:1-2:1"
    assert body["state"]["plans"][0]["id"] == "plan-1"
    assert body["state"]["plans"][0]["completed_through"]["reference"] == "1:1"
    assert body["state"]["plans"][0]["metrics"]["today_range"]["label"] == "2:1-2"
    assert body["summary"] == {
        "streak_days": 1,
        "session_count": 0,
        "bookmark_count": 1,
        "note_count": 1,
        "plan_count": 1,
        "latest_session_at": None,
    }

    delete_response = study_client.delete(
        "/api/v1/me/study",
        headers=_auth_headers(register_token),
    )
    assert delete_response.status_code == 200
    assert delete_response.json()["ok"] is True

    empty_response = study_client.get(
        "/api/v1/me/study",
        headers=_auth_headers(register_token),
    )
    assert empty_response.status_code == 200
    assert empty_response.json() == {
        "state": {
            "progress": None,
            "bookmarks": [],
            "notes": [],
            "plans": [],
        },
        "summary": {
            "streak_days": 0,
            "session_count": 0,
            "bookmark_count": 0,
            "note_count": 0,
            "plan_count": 0,
            "latest_session_at": None,
        },
    }


def test_progress_updates_plans_and_streak_days(study_client: TestClient) -> None:
    token = _register(study_client, email="progress@example.com")
    headers = _auth_headers(token)

    plan_response = study_client.post(
        "/api/v1/me/plans",
        json={
            "name": "Whole sample",
            "range_label": "1:1-2:2",
            "daily_ayah_target": 2,
            "start_date": "2026-04-30",
            "status": "active",
        },
        headers=headers,
    )
    assert plan_response.status_code == 201, plan_response.text
    plan_id = plan_response.json()["id"]

    today = datetime.now(timezone.utc).date()
    for offset in (2, 1, 0):
        current_day = today - timedelta(days=offset)
        session_response = study_client.post(
            "/api/v1/me/reading-sessions",
            json={
                "started_at": f"{current_day.isoformat()}T06:00:00Z",
                "ended_at": f"{current_day.isoformat()}T06:10:00Z",
                "range_label": "1:1",
                "source": "manual_session",
            },
            headers=headers,
        )
        assert session_response.status_code == 201, session_response.text

    progress_response = study_client.put(
        "/api/v1/me/progress",
        json={
            "range_label": "1:1-2:1",
            "source": "manual_mark",
        },
        headers=headers,
    )
    assert progress_response.status_code == 200, progress_response.text
    progress_body = progress_response.json()

    assert progress_body["progress"]["range"]["label"] == "1:1-2:1"
    assert progress_body["updated_plan_names"] == ["Whole sample"]
    assert progress_body["streak_days"] == 3

    plan_today_response = study_client.get(
        f"/api/v1/me/plans/{plan_id}/today",
        headers=headers,
    )
    assert plan_today_response.status_code == 200
    plan_body = plan_today_response.json()

    assert plan_body["completed_through"]["reference"] == "2:1"
    assert plan_body["metrics"] == {
        "total_ayahs": 3,
        "completed_ayahs": 2,
        "remaining_ayahs": 1,
        "remaining_days": 1,
        "completed": False,
        "daily_ayah_target": 2,
        "estimated_days": 2,
        "projected_end_date": "2026-05-01",
        "today_range": {
            "start": _reference("2:2"),
            "end": _reference("2:2"),
            "label": "2:2",
            "ayah_count": 1,
        },
    }


def test_plan_derivation_exports_and_private_notes(study_client: TestClient) -> None:
    token_one = _register(study_client, email="reader-one@example.com")
    token_two = _register(study_client, email="reader-two@example.com")

    headers_one = _auth_headers(token_one)
    headers_two = _auth_headers(token_two)

    plan_response = study_client.post(
        "/api/v1/me/plans",
        json={
            "name": "Two day review",
            "range_label": "1:1-2:2",
            "start_date": "2026-05-01",
            "end_date": "2026-05-02",
        },
        headers=headers_one,
    )
    assert plan_response.status_code == 201, plan_response.text
    plan_body = plan_response.json()

    assert plan_body["daily_ayah_target"] == 2
    assert plan_body["metrics"]["daily_ayah_target"] == 2
    assert plan_body["metrics"]["estimated_days"] == 2
    assert plan_body["metrics"]["projected_end_date"] == "2026-05-02"
    assert plan_body["metrics"]["today_range"]["label"] == "1:1-2:1"

    bookmark_response = study_client.post(
        "/api/v1/me/bookmarks",
        json={"reference": "2:2", "label": "Review"},
        headers=headers_one,
    )
    assert bookmark_response.status_code == 201, bookmark_response.text

    note_response = study_client.post(
        "/api/v1/me/notes",
        json={"reference": "2:2", "body": "Reflect on the Book."},
        headers=headers_one,
    )
    assert note_response.status_code == 201, note_response.text
    note_id = note_response.json()["id"]

    export_response = study_client.get(
        "/api/v1/me/exports/notes",
        headers=headers_one,
    )
    assert export_response.status_code == 200
    assert export_response.json()["count"] == 1
    assert export_response.json()["notes"][0]["body"] == "Reflect on the Book."

    other_user_notes = study_client.get("/api/v1/me/notes", headers=headers_two)
    assert other_user_notes.status_code == 200
    assert other_user_notes.json() == {"count": 0, "notes": []}

    blocked_delete = study_client.delete(
        f"/api/v1/me/notes/{note_id}",
        headers=headers_two | {"X-Request-ID": "note-404"},
    )
    assert blocked_delete.status_code == 404
    assert blocked_delete.json() == {
        "error": {
            "code": "note_not_found",
            "message": f"Note `{note_id}` was not found.",
            "details": {"id": note_id},
        },
        "meta": {"request_id": "note-404"},
    }
