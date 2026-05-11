from fastapi.testclient import TestClient

from qurankit_api.data.source_metadata import SOURCE_RELEASE_ID


def test_browse_endpoints_require_database_configuration(client: TestClient) -> None:
    response = client.get("/api/v1/surahs", headers={"X-Request-ID": "browse-no-db"})

    assert response.status_code == 503
    assert response.headers["X-Request-ID"] == "browse-no-db"
    assert response.json() == {
        "error": {
            "code": "database_unavailable",
            "message": "Database is not configured for this API instance.",
            "details": {"setting": "QURANKIT_DATABASE_URL"},
        },
        "meta": {"request_id": "browse-no-db"},
    }


def test_list_surahs_returns_paginated_source_aware_results(
    browse_client: TestClient,
) -> None:
    response = browse_client.get("/api/v1/surahs?limit=1&offset=1")

    assert response.status_code == 200
    assert response.json() == {
        "items": [
            {
                "surah_number": 2,
                "arabic_name": "سورة البقرة",
                "english_name": "Al-Baqara",
                "english_name_translation": "The Cow",
                "revelation_type": "medinan",
                    "ayah_count": 2,
                    "source": {
                        "source_release_id": SOURCE_RELEASE_ID,
                        "source_name": "AbdullahGhanem/quran-database",
                        "repository_url": "https://github.com/AbdullahGhanem/quran-database",
                        "upstream_commit_sha": "f6c4c805f22b0432677d79aafc12139b915e1a0d",
                    "retrieved_artifact_name": "quran.sql.zip",
                    "retrieved_artifact_sha256": "ff9033de414a1a18fe42e241dc81f4528c3b194a1e8304d3ac06c9d5b0d7f155",
                },
            }
        ],
        "pagination": {
            "total": 2,
            "limit": 1,
            "offset": 1,
            "has_more": False,
        },
    }


def test_read_surah_returns_detail_and_404_for_missing_surah(
    browse_client: TestClient,
) -> None:
    response = browse_client.get("/api/v1/surahs/1")

    assert response.status_code == 200
    assert response.json()["surah_number"] == 1
    assert response.json()["ayah_count"] == 1

    missing = browse_client.get("/api/v1/surahs/99", headers={"X-Request-ID": "surah-404"})

    assert missing.status_code == 404
    assert missing.json() == {
        "error": {
            "code": "surah_not_found",
            "message": "Surah 99 was not found.",
            "details": {"surah_number": 99},
        },
        "meta": {"request_id": "surah-404"},
    }


def test_list_surah_ayahs_preserves_exact_source_text(
    browse_client: TestClient,
) -> None:
    response = browse_client.get("/api/v1/surahs/1/ayahs")

    assert response.status_code == 200
    payload = response.json()

    assert payload["surah"]["surah_number"] == 1
    assert payload["pagination"] == {
        "total": 1,
        "limit": 50,
        "offset": 0,
        "has_more": False,
    }
    assert payload["items"][0]["reference"] == "1:1"
    assert payload["items"][0]["text"].startswith("\ufeff")


def test_browse_lookup_endpoints_support_translation_text_and_attribution(
    browse_client: TestClient,
) -> None:
    surah_response = browse_client.get("/api/v1/surahs/1/ayahs?translation=en.sahih")

    assert surah_response.status_code == 200
    surah_payload = surah_response.json()
    assert surah_payload["items"][0]["translation_text"] == "In the name of Allah"
    assert surah_payload["items"][0]["translation_attribution"] == {
        "id": surah_payload["items"][0]["translation_attribution"]["id"],
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
    }

    ayah_response = browse_client.get("/api/v1/ayahs/2:2?translation=en.sahih")

    assert ayah_response.status_code == 200
    ayah_payload = ayah_response.json()
    assert ayah_payload["translation_text"] == "That is the Book"
    assert ayah_payload["translation_attribution"]["upstream_identifier"] == "en.sahih"


def test_read_ayah_supports_global_and_surah_local_references(
    browse_client: TestClient,
) -> None:
    by_global = browse_client.get("/api/v1/ayahs/2")
    assert by_global.status_code == 200
    assert by_global.json()["reference"] == "2:1"
    assert by_global.json()["global_ayah_number"] == 2

    by_pair = browse_client.get("/api/v1/ayahs/2:2")
    assert by_pair.status_code == 200
    assert by_pair.json()["global_ayah_number"] == 3
    assert by_pair.json()["sajda"] is True


def test_read_ayah_translation_filter_rejects_unknown_and_unsupported_editions(
    browse_client: TestClient,
) -> None:
    missing = browse_client.get(
        "/api/v1/ayahs/2:2?translation=en.unknown",
        headers={"X-Request-ID": "ayah-translation-404"},
    )

    assert missing.status_code == 404
    assert missing.json() == {
        "error": {
            "code": "translation_not_found",
            "message": "Translation edition `en.unknown` was not found.",
            "details": {"translation_identifier": "en.unknown"},
        },
        "meta": {"request_id": "ayah-translation-404"},
    }

    unsupported = browse_client.get(
        "/api/v1/ayahs/2:2?translation=quran-simple",
        headers={"X-Request-ID": "ayah-translation-422"},
    )

    assert unsupported.status_code == 422
    assert unsupported.json() == {
        "error": {
            "code": "unsupported_translation_edition",
            "message": "Browse translation must reference a text translation edition.",
            "details": {
                "translation_identifier": "quran-simple",
                "edition_type": "quran",
                "format": "text",
            },
        },
        "meta": {"request_id": "ayah-translation-422"},
    }


def test_read_ayah_rejects_invalid_and_missing_references(
    browse_client: TestClient,
) -> None:
    invalid = browse_client.get("/api/v1/ayahs/not-a-reference", headers={"X-Request-ID": "ayah-422"})

    assert invalid.status_code == 422
    assert invalid.json() == {
        "error": {
            "code": "invalid_ayah_reference",
            "message": "Ayah reference must be a global ayah number or `surah:ayah`.",
            "details": {
                "reference": "not-a-reference",
                "accepted_formats": ["123", "2:255"],
            },
        },
        "meta": {"request_id": "ayah-422"},
    }

    missing = browse_client.get("/api/v1/ayahs/2:9", headers={"X-Request-ID": "ayah-404"})

    assert missing.status_code == 404
    assert missing.json() == {
        "error": {
            "code": "ayah_not_found",
            "message": "Ayah reference `2:9` was not found.",
            "details": {"reference": "2:9"},
        },
        "meta": {"request_id": "ayah-404"},
    }


def test_random_ayah_returns_any_loaded_row(browse_client: TestClient) -> None:
    response = browse_client.get("/api/v1/ayahs/random")

    assert response.status_code == 200
    assert response.json()["reference"] in {"1:1", "2:1", "2:2"}


def test_juz_hizb_and_page_endpoints_paginate_loaded_ayahs(
    browse_client: TestClient,
) -> None:
    juz = browse_client.get("/api/v1/juz/1?limit=2&offset=1")
    assert juz.status_code == 200
    assert juz.json()["juz_number"] == 1
    assert juz.json()["pagination"] == {
        "total": 3,
        "limit": 2,
        "offset": 1,
        "has_more": False,
    }
    assert [item["reference"] for item in juz.json()["items"]] == ["2:1", "2:2"]

    hizb = browse_client.get("/api/v1/hizb/1")
    assert hizb.status_code == 200
    assert hizb.json()["hizb_number"] == 1
    assert len(hizb.json()["items"]) == 3

    page = browse_client.get("/api/v1/pages/2")
    assert page.status_code == 200
    assert page.json()["page_number"] == 2
    assert [item["reference"] for item in page.json()["items"]] == ["2:1", "2:2"]


def test_juz_hizb_and_page_endpoints_return_404_when_dataset_has_no_match(
    browse_client: TestClient,
) -> None:
    juz = browse_client.get("/api/v1/juz/2", headers={"X-Request-ID": "juz-404"})
    assert juz.status_code == 404
    assert juz.json()["error"]["code"] == "juz_not_found"

    hizb = browse_client.get("/api/v1/hizb/2", headers={"X-Request-ID": "hizb-404"})
    assert hizb.status_code == 404
    assert hizb.json()["error"]["code"] == "hizb_not_found"

    page = browse_client.get("/api/v1/pages/3", headers={"X-Request-ID": "page-404"})
    assert page.status_code == 404
    assert page.json()["error"]["code"] == "page_not_found"
