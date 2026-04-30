from __future__ import annotations

import json
from pathlib import Path

import pytest

from qurankit.backends import AyahReference
from qurankit.config import BackendMode, Settings, StateMode
from qurankit.personal import (
    LocalStudyStateStore,
    PersonalDataConfigurationError,
    PersonalDataValidationError,
    RemoteStudyStateStore,
    StudyState,
    StudyTracker,
    parse_ayah_range,
    select_study_store,
)


class StubResponse:
    def __init__(self, payload: dict[str, object]) -> None:
        self.payload = payload

    def __enter__(self) -> StubResponse:
        return self

    def __exit__(self, exc_type, exc, tb) -> bool:
        return False

    def read(self) -> bytes:
        return json.dumps(self.payload, ensure_ascii=False).encode("utf-8")


def test_parse_ayah_range_supports_single_and_shorthand_ranges() -> None:
    single = parse_ayah_range("2:255")
    shorthand = parse_ayah_range("2:255-257")
    spanning = parse_ayah_range("2:255-3:5")

    assert single.label == "2:255"
    assert shorthand.start == AyahReference(surah_number=2, ayah_number=255)
    assert shorthand.end == AyahReference(surah_number=2, ayah_number=257)
    assert spanning.label == "2:255-3:5"


def test_parse_ayah_range_rejects_reverse_ranges() -> None:
    with pytest.raises(PersonalDataValidationError):
        parse_ayah_range("2:5-1:1")


def test_study_tracker_updates_progress_and_matching_plan(tmp_path: Path) -> None:
    tracker = StudyTracker(LocalStudyStateStore(tmp_path / "study-state.json"))

    tracker.create_plan(
        name="Morning review",
        reading_range=parse_ayah_range("1:1-1:4"),
        daily_ayah_target=2,
    )
    result = tracker.mark_progress(parse_ayah_range("1:1-2"))
    state = tracker.load_state()

    assert result.updated_plan_names == ("Morning review",)
    assert state.progress is not None
    assert state.progress.reading_range.label == "1:1-2"
    assert state.plans[0].completed_through == AyahReference(1, 2)


def test_remote_study_state_store_uses_bearer_auth() -> None:
    requests: list[dict[str, object]] = []
    responses = [
        StubResponse({"state": {"progress": None, "bookmarks": [], "notes": [], "plans": []}}),
        StubResponse({}),
    ]

    def opener(request, timeout):
        headers = {key.lower(): value for key, value in request.header_items()}
        body = None
        if request.data is not None:
            body = json.loads(request.data.decode("utf-8"))
        requests.append(
            {
                "url": request.full_url,
                "method": request.get_method(),
                "authorization": headers.get("authorization"),
                "body": body,
            }
        )
        return responses.pop(0)

    store = RemoteStudyStateStore(
        api_url="https://api.example.test",
        api_token="secret-token",
        opener=opener,
    )

    assert store.load() == StudyState()
    store.save(StudyState())

    assert requests == [
        {
            "url": "https://api.example.test/api/v1/me/study",
            "method": "GET",
            "authorization": "Bearer secret-token",
            "body": None,
        },
        {
            "url": "https://api.example.test/api/v1/me/study",
            "method": "PUT",
            "authorization": "Bearer secret-token",
            "body": {
                "state": {
                    "progress": None,
                    "bookmarks": [],
                    "notes": [],
                    "plans": [],
                }
            },
        },
    ]


def test_select_study_store_requires_token_for_remote_state_mode() -> None:
    settings = Settings(
        mode=BackendMode.REMOTE,
        state_mode=StateMode.REMOTE,
        api_url="https://api.example.test",
        db_path="/tmp/qurankit.sqlite3",
        state_path="/tmp/study-state.json",
        translation="en.sahih",
    )

    with pytest.raises(PersonalDataConfigurationError):
        select_study_store(settings)
