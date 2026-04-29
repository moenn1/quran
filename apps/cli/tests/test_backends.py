from __future__ import annotations

import json
from pathlib import Path

import pytest

from qurankit.backends import (
    AyahRecord,
    BackendNotFoundError,
    ExactSearchHit,
    ExactSearchResult,
    LocalSQLiteBackend,
    RemoteBackend,
    SemanticSearchHit,
    SemanticSearchResult,
    TranslationAttribution,
    select_backend,
)
from qurankit.config import BackendMode, Settings


class StubResponse:
    def __init__(self, payload: dict[str, object]) -> None:
        self.payload = payload

    def __enter__(self) -> StubResponse:
        return self

    def __exit__(self, exc_type, exc, tb) -> bool:
        return False

    def read(self) -> bytes:
        return json.dumps(self.payload, ensure_ascii=False).encode("utf-8")


def test_select_backend_uses_remote_mode() -> None:
    settings = Settings(
        mode=BackendMode.REMOTE,
        api_url="https://example.com/api",
        db_path="/tmp/qurankit.sqlite3",
        translation="en.sahih",
    )

    backend = select_backend(settings)

    assert isinstance(backend, RemoteBackend)
    assert backend.summary == "Remote API at https://example.com/api"


def test_select_backend_uses_local_sqlite_mode(tmp_path: Path) -> None:
    db_path = tmp_path / "qurankit.sqlite3"
    settings = Settings(
        mode=BackendMode.LOCAL,
        api_url="https://example.com/api",
        db_path=str(db_path),
        translation="en.sahih",
    )

    backend = select_backend(settings)

    assert isinstance(backend, LocalSQLiteBackend)
    assert backend.summary.endswith("(file not found yet)")


def test_local_sqlite_backend_supports_lookup_search_and_semantic(
    sample_sqlite_db: Path,
) -> None:
    backend = LocalSQLiteBackend(sample_sqlite_db)

    ayah = backend.get_ayah(reference=_ref(1, 6), translation_identifier="en.sahih")
    exact = backend.search("Merciful", translation_identifier="en.sahih", limit=5)
    semantic = backend.semantic_search(
        "guide path", translation_identifier="en.sahih", limit=5
    )

    assert ayah.ayah.reference == "1:6"
    assert ayah.ayah.translation_text == "Guide us to the straight path."
    assert [hit.ayah.reference for hit in exact.results] == ["1:1", "1:3"]
    assert exact.results[0].match_sources == ("translation",)
    assert semantic.results
    assert semantic.results[0].ayah.reference == "1:6"
    assert "Shared terms" in semantic.results[0].reason


def test_local_sqlite_backend_requires_known_translation(
    sample_sqlite_db: Path,
) -> None:
    backend = LocalSQLiteBackend(sample_sqlite_db)

    with pytest.raises(BackendNotFoundError):
        backend.get_surah(1, translation_identifier="en.unknown")


def test_remote_backend_uses_versioned_search_endpoints() -> None:
    requested_urls: list[str] = []
    sample_ayah = AyahRecord(
        surah_number=1,
        ayah_number=6,
        surah_name_arabic="ٱلْفَاتِحَةِ",
        surah_name_english="Al-Fatihah",
        surah_name_translation="The Opening",
        revelation_type="Meccan",
        arabic_text="ٱهْدِنَا ٱلصِّرَٰطَ ٱلْمُسْتَقِيمَ",
        translation_text="Guide us to the straight path.",
        page_number=1,
        juz_number=1,
        hizb_number=1,
        sajda=False,
    )
    translation = TranslationAttribution(
        identifier="en.sahih",
        language="en",
        name="Saheeh International",
        english_name="Saheeh International",
        edition_type="translation",
        format="text",
    )
    exact_payload = ExactSearchResult(
        query="guide",
        results=(ExactSearchHit(ayah=sample_ayah, match_sources=("translation",)),),
        searched_fields=("arabic_text", "translation"),
        translation_attribution=translation,
    ).to_dict()
    semantic_payload = SemanticSearchResult(
        query="guide path",
        results=(
            SemanticSearchHit(
                ayah=sample_ayah,
                similarity_score=0.91,
                reason="Shared terms in the selected text: guide, path.",
            ),
        ),
        translation_attribution=translation,
    ).to_dict()

    def opener(request, timeout):
        requested_urls.append(request.full_url)
        if request.full_url.endswith(
            "/api/v1/search/exact?q=guide&translation=en.sahih&limit=2"
        ):
            return StubResponse(exact_payload)
        if request.full_url.endswith(
            "/api/v1/search/semantic?q=guide+path&translation=en.sahih&limit=2"
        ):
            return StubResponse(semantic_payload)
        raise AssertionError(f"Unexpected URL: {request.full_url}")

    backend = RemoteBackend("https://api.example.test", opener=opener)

    exact = backend.search("guide", translation_identifier="en.sahih", limit=2)
    semantic = backend.semantic_search(
        "guide path", translation_identifier="en.sahih", limit=2
    )

    assert requested_urls == [
        "https://api.example.test/api/v1/search/exact?q=guide&translation=en.sahih&limit=2",
        "https://api.example.test/api/v1/search/semantic?q=guide+path&translation=en.sahih&limit=2",
    ]
    assert exact.results[0].ayah.reference == "1:6"
    assert semantic.results[0].similarity_score == 0.91


def _ref(surah_number: int, ayah_number: int):
    from qurankit.backends import AyahReference

    return AyahReference(surah_number=surah_number, ayah_number=ayah_number)
