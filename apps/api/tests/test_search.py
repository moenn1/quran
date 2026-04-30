from fastapi.testclient import TestClient

from qurankit_api.data.source_metadata import SOURCE_RELEASE_ID


def test_exact_search_requires_database_configuration(client: TestClient) -> None:
    response = client.get("/api/v1/search/exact?q=book", headers={"X-Request-ID": "search-no-db"})

    assert response.status_code == 503
    assert response.headers["X-Request-ID"] == "search-no-db"
    assert response.json() == {
        "error": {
            "code": "database_unavailable",
            "message": "Database is not configured for this API instance.",
            "details": {"setting": "QURANKIT_DATABASE_URL"},
        },
        "meta": {"request_id": "search-no-db"},
    }


def test_exact_search_supports_translation_filter_and_highlights(
    browse_client: TestClient,
) -> None:
    response = browse_client.get("/api/v1/search/exact?q=Book&translation=en.sahih")

    assert response.status_code == 200
    payload = response.json()

    assert payload["query"] == "Book"
    assert payload["match_type"] == "exact"
    assert payload["count"] == 1
    assert payload["searched_fields"] == ["translation"]
    assert payload["filters"] == {
        "fields": ["translation"],
        "language_code": None,
        "translation_identifier": "en.sahih",
    }
    assert payload["pagination"] == {
        "total": 1,
        "limit": 20,
        "offset": 0,
        "has_more": False,
    }
    assert payload["arabic_source"]["source_release_id"] == SOURCE_RELEASE_ID
    assert payload["translation_attribution"]["upstream_identifier"] == "en.sahih"
    assert [item["upstream_identifier"] for item in payload["edition_attributions"]] == [
        "en.sahih",
    ]
    assert payload["results"] == [
        {
            "ayah": {
                "reference": "2:2",
                "global_ayah_number": 3,
                "ayah_number": 2,
                "text": "ذَٰلِكَ ٱلْكِتَٰبُ",
                "page_number": 2,
                "juz_number": 1,
                "hizb_number": 1,
                "rub_el_hizb_number": 4,
                "sajda": True,
                "surah": {
                    "surah_number": 2,
                    "arabic_name": "سورة البقرة",
                    "english_name": "Al-Baqara",
                    "english_name_translation": "The Cow",
                    "revelation_type": "medinan",
                },
                "source": {
                    "source_release_id": SOURCE_RELEASE_ID,
                    "source_name": "AbdullahGhanem/quran-database",
                    "repository_url": "https://github.com/AbdullahGhanem/quran-database",
                    "upstream_commit_sha": "f6c4c805f22b0432677d79aafc12139b915e1a0d",
                    "retrieved_artifact_name": "quran.sql.zip",
                    "retrieved_artifact_sha256": "ff9033de414a1a18fe42e241dc81f4528c3b194a1e8304d3ac06c9d5b0d7f155",
                },
            },
            "match_sources": ["translation"],
            "highlights": [
                {
                    "field": "translation",
                    "text": "That is the Book",
                    "excerpt": "That is the Book",
                    "match_start": 12,
                    "match_end": 16,
                    "edition": {
                        "id": payload["edition_attributions"][0]["id"],
                        "upstream_identifier": "en.sahih",
                        "language_code": "en",
                        "translation_name": "Sahih",
                        "english_name": "Saheeh International",
                        "format": "text",
                        "edition_type": "translation",
                        "attribution_text": (
                            "Imported into QuranKit from AbdullahGhanem/quran-database "
                            "(f6c4c805f22b0432677d79aafc12139b915e1a0d) using upstream edition "
                            "`en.sahih`."
                        ),
                        "attribution_url": "https://github.com/AbdullahGhanem/quran-database",
                        "review_status": "pending_review",
                        "is_public": False,
                    },
                }
            ],
        }
    ]


def test_exact_search_supports_simple_text_alias_and_pagination(
    browse_client: TestClient,
) -> None:
    response = browse_client.get(
        "/api/v1/search/exact?q=%D8%A8%D9%90%D8%B3%D9%92%D9%85%D9%90"
        "&field=normalized_text&translation=quran-simple&limit=1&offset=1",
    )

    assert response.status_code == 200
    payload = response.json()

    assert payload["searched_fields"] == ["simple_text"]
    assert payload["filters"] == {
        "fields": ["simple_text"],
        "language_code": None,
        "translation_identifier": "quran-simple",
    }
    assert payload["translation_attribution"] is None
    assert payload["pagination"] == {
        "total": 2,
        "limit": 1,
        "offset": 1,
        "has_more": False,
    }
    assert payload["results"][0]["ayah"]["reference"] == "2:1"
    assert payload["results"][0]["match_sources"] == ["simple_text"]
    assert payload["results"][0]["highlights"][0]["edition"]["upstream_identifier"] == (
        "quran-simple"
    )
    assert payload["edition_attributions"][0]["edition_type"] == "quran"


def test_exact_search_supports_language_filter_for_simple_text_matches(
    browse_client: TestClient,
) -> None:
    response = browse_client.get("/api/v1/search/exact?q=%D8%A8%D9%90%D8%B3%D9%92%D9%85%D9%90&language=ar")

    assert response.status_code == 200
    payload = response.json()

    assert payload["searched_fields"] == ["simple_text", "translation"]
    assert payload["filters"]["language_code"] == "ar"
    assert payload["count"] == 2
    assert [item["ayah"]["reference"] for item in payload["results"]] == ["1:1", "2:1"]
    assert all(item["match_sources"] == ["simple_text"] for item in payload["results"])


def test_exact_search_rejects_blank_queries_unknown_editions_and_invalid_fields(
    browse_client: TestClient,
) -> None:
    blank = browse_client.get("/api/v1/search/exact?q=+++", headers={"X-Request-ID": "search-422"})
    assert blank.status_code == 422
    assert blank.json() == {
        "error": {
            "code": "invalid_search_query",
            "message": "Query cannot be empty.",
            "details": {"parameter": "q"},
        },
        "meta": {"request_id": "search-422"},
    }

    missing = browse_client.get(
        "/api/v1/search/exact?q=book&translation=en.unknown",
        headers={"X-Request-ID": "search-404"},
    )
    assert missing.status_code == 404
    assert missing.json() == {
        "error": {
            "code": "translation_not_found",
            "message": "Search edition `en.unknown` was not found.",
            "details": {"translation_identifier": "en.unknown"},
        },
        "meta": {"request_id": "search-404"},
    }

    invalid_field = browse_client.get(
        "/api/v1/search/exact?q=book&field=semantic",
        headers={"X-Request-ID": "search-field-422"},
    )
    assert invalid_field.status_code == 422
    assert invalid_field.json() == {
        "error": {
            "code": "invalid_search_field",
            "message": (
                "Search field must be one of `arabic_text`, `simple_text`, "
                "`normalized_text`, or `translation`."
            ),
            "details": {"field": "semantic"},
        },
        "meta": {"request_id": "search-field-422"},
    }
