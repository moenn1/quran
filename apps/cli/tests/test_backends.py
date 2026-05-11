from __future__ import annotations

import json
from pathlib import Path

import pytest

from qurankit.backends import (
    BackendNotFoundError,
    LocalSQLiteBackend,
    RemoteBackend,
    select_backend,
)
from qurankit.config import BackendMode, Settings, StateMode


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
        state_mode=StateMode.LOCAL,
        api_url="https://example.com/api",
        db_path="/tmp/qurankit.sqlite3",
        state_path="/tmp/study-state.json",
        translation="en.sahih",
    )

    backend = select_backend(settings)

    assert isinstance(backend, RemoteBackend)
    assert backend.summary == "Remote API at https://example.com/api"


def test_select_backend_uses_local_sqlite_mode(tmp_path: Path) -> None:
    db_path = tmp_path / "qurankit.sqlite3"
    settings = Settings(
        mode=BackendMode.LOCAL,
        state_mode=StateMode.LOCAL,
        api_url="https://example.com/api",
        db_path=str(db_path),
        state_path=str(tmp_path / "study-state.json"),
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
    ayah_range = backend.get_range(
        _ref(1, 5),
        _ref(2, 2),
        translation_identifier="en.sahih",
    )
    exact = backend.search("Merciful", translation_identifier="en.sahih", limit=5)
    semantic = backend.semantic_search(
        "guide path", translation_identifier="en.sahih", limit=5
    )

    assert ayah.ayah.reference == "1:6"
    assert ayah.ayah.translation_text == "Guide us to the straight path."
    assert ayah_range.start_reference == "1:5"
    assert ayah_range.end_reference == "2:2"
    assert [item.reference for item in ayah_range.ayahs] == ["1:5", "1:6", "2:1", "2:2"]
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
    exact_payload = {
        "query": "guide",
        "count": 1,
        "searched_fields": ["arabic_text", "translation"],
        "results": [
            {
                "ayah": {
                    "reference": "1:6",
                    "ayah_number": 6,
                    "text": "ٱهْدِنَا ٱلصِّرَٰطَ ٱلْمُسْتَقِيمَ",
                    "page_number": 1,
                    "juz_number": 1,
                    "hizb_number": 1,
                    "sajda": False,
                    "surah": {
                        "surah_number": 1,
                        "arabic_name": "ٱلْفَاتِحَةِ",
                        "english_name": "Al-Fatihah",
                        "english_name_translation": "The Opening",
                        "revelation_type": "meccan",
                    },
                    "source": {
                        "source_name": "AbdullahGhanem/quran-database",
                        "upstream_commit_sha": "f6c4c805f22b0432677d79aafc12139b915e1a0d",
                    },
                },
                "match_sources": ["translation"],
            }
        ],
        "arabic_source": {
            "source_name": "AbdullahGhanem/quran-database",
            "upstream_commit_sha": "f6c4c805f22b0432677d79aafc12139b915e1a0d",
        },
        "translation_attribution": {
            "upstream_identifier": "en.sahih",
            "language_code": "en",
            "translation_name": "Sahih",
            "english_name": "Saheeh International",
            "edition_type": "translation",
            "format": "text",
        },
    }
    semantic_payload = {
        "query": "guide path",
        "count": 1,
        "results": [
            {
                "ayah": {
                    "reference": "1:6",
                    "ayah_number": 6,
                    "text": "ٱهْدِنَا ٱلصِّرَٰطَ ٱلْمُسْتَقِيمَ",
                    "translation_text": "Guide us to the straight path.",
                    "page_number": 1,
                    "juz_number": 1,
                    "hizb_number": 1,
                    "sajda": False,
                    "surah": {
                        "surah_number": 1,
                        "arabic_name": "ٱلْفَاتِحَةِ",
                        "english_name": "Al-Fatihah",
                        "english_name_translation": "The Opening",
                        "revelation_type": "meccan",
                    },
                    "source": {
                        "source_name": "AbdullahGhanem/quran-database",
                        "upstream_commit_sha": "f6c4c805f22b0432677d79aafc12139b915e1a0d",
                    },
                },
                "similarity_score": 0.91,
                "reason": "Shared terms in the selected text: guide, path.",
            }
        ],
        "arabic_source": {
            "source_name": "AbdullahGhanem/quran-database",
            "upstream_commit_sha": "f6c4c805f22b0432677d79aafc12139b915e1a0d",
        },
        "translation_attribution": {
            "upstream_identifier": "en.sahih",
            "language_code": "en",
            "translation_name": "Sahih",
            "english_name": "Saheeh International",
            "edition_type": "translation",
            "format": "text",
        },
    }

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
    assert exact.translation_attribution is not None
    assert exact.translation_attribution.identifier == "en.sahih"
    assert semantic.results[0].similarity_score == 0.91
    assert semantic.translation_attribution is not None
    assert semantic.translation_attribution.name == "Sahih"


def test_remote_backend_builds_ayah_ranges_from_surah_endpoints() -> None:
    requested_urls: list[str] = []
    translation_attribution = {
        "upstream_identifier": "en.sahih",
        "language_code": "en",
        "translation_name": "Sahih",
        "english_name": "Saheeh International",
        "edition_type": "translation",
        "format": "text",
    }
    surah_one = {
        "surah": {
            "surah_number": 1,
            "arabic_name": "ٱلْفَاتِحَةِ",
            "english_name": "Al-Fatihah",
            "english_name_translation": "The Opening",
            "revelation_type": "meccan",
            "ayah_count": 2,
            "source": {
                "source_name": "AbdullahGhanem/quran-database",
                "upstream_commit_sha": "f6c4c805f22b0432677d79aafc12139b915e1a0d",
            },
        },
        "items": [
            {
                "reference": "1:5",
                "surah_number": 1,
                "ayah_number": 5,
                "text": "إِيَّاكَ نَعْبُدُ وَإِيَّاكَ نَسْتَعِينُ",
                "translation_text": "It is You we worship and You we ask for help.",
                "page_number": 1,
                "juz_number": 1,
                "hizb_number": 1,
                "sajda": False,
                "surah": {
                    "surah_number": 1,
                    "arabic_name": "ٱلْفَاتِحَةِ",
                    "english_name": "Al-Fatihah",
                    "english_name_translation": "The Opening",
                    "revelation_type": "meccan",
                },
                "source": {
                    "source_name": "AbdullahGhanem/quran-database",
                    "upstream_commit_sha": "f6c4c805f22b0432677d79aafc12139b915e1a0d",
                },
                "translation_attribution": translation_attribution,
            },
            {
                "reference": "1:6",
                "surah_number": 1,
                "ayah_number": 6,
                "text": "ٱهْدِنَا ٱلصِّرَٰطَ ٱلْمُسْتَقِيمَ",
                "translation_text": "Guide us to the straight path.",
                "page_number": 1,
                "juz_number": 1,
                "hizb_number": 1,
                "sajda": False,
                "surah": {
                    "surah_number": 1,
                    "arabic_name": "ٱلْفَاتِحَةِ",
                    "english_name": "Al-Fatihah",
                    "english_name_translation": "The Opening",
                    "revelation_type": "meccan",
                },
                "source": {
                    "source_name": "AbdullahGhanem/quran-database",
                    "upstream_commit_sha": "f6c4c805f22b0432677d79aafc12139b915e1a0d",
                },
                "translation_attribution": translation_attribution,
            },
        ],
    }
    surah_two = {
        "surah": {
            "surah_number": 2,
            "arabic_name": "ٱلْبَقَرَةِ",
            "english_name": "Al-Baqarah",
            "english_name_translation": "The Cow",
            "revelation_type": "medinan",
            "ayah_count": 2,
            "source": {
                "source_name": "AbdullahGhanem/quran-database",
                "upstream_commit_sha": "f6c4c805f22b0432677d79aafc12139b915e1a0d",
            },
        },
        "items": [
            {
                "reference": "2:1",
                "surah_number": 2,
                "ayah_number": 1,
                "text": "الٓمٓ",
                "translation_text": "Alif, Lam, Meem.",
                "page_number": 2,
                "juz_number": 1,
                "hizb_number": 1,
                "sajda": False,
                "surah": {
                    "surah_number": 2,
                    "arabic_name": "ٱلْبَقَرَةِ",
                    "english_name": "Al-Baqarah",
                    "english_name_translation": "The Cow",
                    "revelation_type": "medinan",
                },
                "source": {
                    "source_name": "AbdullahGhanem/quran-database",
                    "upstream_commit_sha": "f6c4c805f22b0432677d79aafc12139b915e1a0d",
                },
                "translation_attribution": translation_attribution,
            },
            {
                "reference": "2:2",
                "surah_number": 2,
                "ayah_number": 2,
                "text": "ذَٰلِكَ ٱلْكِتَٰبُ لَا رَيْبَ ۛ فِيهِ هُدًى لِّلْمُتَّقِينَ",
                "translation_text": (
                    "This is the Book about which there is no doubt, a guidance "
                    "for those conscious of Allah."
                ),
                "page_number": 2,
                "juz_number": 1,
                "hizb_number": 1,
                "sajda": False,
                "surah": {
                    "surah_number": 2,
                    "arabic_name": "ٱلْبَقَرَةِ",
                    "english_name": "Al-Baqarah",
                    "english_name_translation": "The Cow",
                    "revelation_type": "medinan",
                },
                "source": {
                    "source_name": "AbdullahGhanem/quran-database",
                    "upstream_commit_sha": "f6c4c805f22b0432677d79aafc12139b915e1a0d",
                },
                "translation_attribution": translation_attribution,
            },
        ],
    }

    def opener(request, timeout):
        requested_urls.append(request.full_url)
        if request.full_url.endswith("/api/v1/surahs/1/ayahs?translation=en.sahih"):
            return StubResponse(surah_one)
        if request.full_url.endswith("/api/v1/surahs/2/ayahs?translation=en.sahih"):
            return StubResponse(surah_two)
        raise AssertionError(f"Unexpected URL: {request.full_url}")

    backend = RemoteBackend("https://api.example.test", opener=opener)

    result = backend.get_range(_ref(1, 5), _ref(2, 2), translation_identifier="en.sahih")

    assert requested_urls == [
        "https://api.example.test/api/v1/surahs/1/ayahs?translation=en.sahih",
        "https://api.example.test/api/v1/surahs/2/ayahs?translation=en.sahih",
    ]
    assert result.start_reference == "1:5"
    assert result.end_reference == "2:2"
    assert [ayah.reference for ayah in result.ayahs] == ["1:5", "1:6", "2:1", "2:2"]
    assert result.translation_attribution is not None
    assert result.translation_attribution.identifier == "en.sahih"


def test_remote_backend_uses_live_lookup_browse_endpoints() -> None:
    requested_urls: list[str] = []
    translation_attribution = {
        "upstream_identifier": "en.sahih",
        "language_code": "en",
        "translation_name": "Sahih",
        "english_name": "Saheeh International",
        "edition_type": "translation",
        "format": "text",
    }
    ayah_payload = {
        "reference": "2:2",
        "ayah_number": 2,
        "text": "ذَٰلِكَ ٱلْكِتَٰبُ",
        "translation_text": "That is the Book",
        "page_number": 2,
        "juz_number": 1,
        "hizb_number": 1,
        "sajda": True,
        "surah": {
            "surah_number": 2,
            "arabic_name": "سورة البقرة",
            "english_name": "Al-Baqara",
            "english_name_translation": "The Cow",
            "revelation_type": "medinan",
        },
        "source": {
            "source_name": "AbdullahGhanem/quran-database",
            "upstream_commit_sha": "f6c4c805f22b0432677d79aafc12139b915e1a0d",
        },
        "translation_attribution": translation_attribution,
    }
    juz_payload = {
        "juz_number": 1,
        "items": [ayah_payload],
        "pagination": {"total": 1, "limit": 50, "offset": 0, "has_more": False},
    }
    random_payload = {
        "reference": "1:1",
        "ayah_number": 1,
        "text": "﻿بِسْمِ ٱللَّهِ",
        "page_number": 1,
        "juz_number": 1,
        "hizb_number": 1,
        "sajda": False,
        "surah": {
            "surah_number": 1,
            "arabic_name": "سورة الفاتحة",
            "english_name": "Al-Faatiha",
            "english_name_translation": "The Opening",
            "revelation_type": "meccan",
        },
        "source": {
            "source_name": "AbdullahGhanem/quran-database",
            "upstream_commit_sha": "f6c4c805f22b0432677d79aafc12139b915e1a0d",
        },
    }

    def opener(request, timeout):
        requested_urls.append(request.full_url)
        if request.full_url.endswith("/api/v1/ayahs/2:2?translation=en.sahih"):
            return StubResponse(ayah_payload)
        if request.full_url.endswith("/api/v1/juz/1?translation=en.sahih"):
            return StubResponse(juz_payload)
        if request.full_url.endswith("/api/v1/ayahs/random"):
            return StubResponse(random_payload)
        raise AssertionError(f"Unexpected URL: {request.full_url}")

    backend = RemoteBackend("https://api.example.test", opener=opener)

    ayah = backend.get_ayah(_ref(2, 2), translation_identifier="en.sahih")
    juz = backend.get_juz(1, translation_identifier="en.sahih")
    random = backend.get_random_ayah(translation_identifier=None)

    assert requested_urls == [
        "https://api.example.test/api/v1/ayahs/2:2?translation=en.sahih",
        "https://api.example.test/api/v1/juz/1?translation=en.sahih",
        "https://api.example.test/api/v1/ayahs/random",
    ]
    assert ayah.ayah.reference == "2:2"
    assert ayah.translation_attribution is not None
    assert ayah.translation_attribution.identifier == "en.sahih"
    assert juz.start_reference == "2:2"
    assert juz.end_reference == "2:2"
    assert random.selection_kind == "random"


def _ref(surah_number: int, ayah_number: int):
    from qurankit.backends import AyahReference

    return AyahReference(surah_number=surah_number, ayah_number=ayah_number)
