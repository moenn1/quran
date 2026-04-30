from fastapi.testclient import TestClient

from qurankit_api.core.config import Settings


def test_openapi_document_exposes_health_contract(
    client: TestClient,
    settings: Settings,
) -> None:
    response = client.get("/openapi.json")

    assert response.status_code == 200

    document = response.json()
    health_path = document["paths"]["/api/v1/health"]["get"]

    assert document["info"]["title"] == settings.app_name
    assert document["info"]["version"] == settings.app_version
    assert "source-transparent Quran API scaffold" in document["info"]["description"]
    assert "private by default" in document["info"]["description"]
    assert settings.semantic_search_disclaimer in document["info"]["description"]
    assert any(tag["name"] == "Health" for tag in document["tags"])
    assert any(tag["name"] == "Quran Browse" for tag in document["tags"])
    assert any(tag["name"] == "Quran Search" for tag in document["tags"])
    assert health_path["summary"] == "Read API health status"
    assert "/api/v1/surahs" in document["paths"]
    assert "/api/v1/ayahs/{reference}" in document["paths"]
    assert "/api/v1/search/exact" in document["paths"]
    assert "500" in health_path["responses"]
    assert "ErrorEnvelope" in document["components"]["schemas"]
