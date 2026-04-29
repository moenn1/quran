from fastapi.testclient import TestClient

from qurankit_api.core.config import Settings


def test_root_service_metadata_documents_openapi_entrypoints(
    client: TestClient,
    settings: Settings,
) -> None:
    response = client.get("/")

    assert response.status_code == 200
    assert response.json() == {
        "service": settings.app_name,
        "version": settings.app_version,
        "environment": settings.environment,
        "api_prefix": settings.api_v1_prefix,
        "docs_url": settings.docs_url,
        "openapi_url": settings.openapi_url,
        "privacy_mode": settings.privacy_mode,
        "source_attribution_required": settings.source_attribution_required,
        "semantic_search_disclaimer": settings.semantic_search_disclaimer,
    }


def test_health_endpoint_reports_service_status(
    client: TestClient,
    settings: Settings,
) -> None:
    response = client.get("/api/v1/health", headers={"X-Request-ID": "health-001"})

    assert response.status_code == 200
    assert response.headers["X-Request-ID"] == "health-001"
    assert response.json() == {
        "status": "ok",
        "service": settings.app_name,
        "version": settings.app_version,
        "environment": settings.environment,
        "api_prefix": settings.api_v1_prefix,
        "database_configured": False,
        "privacy_mode": settings.privacy_mode,
        "source_attribution_required": settings.source_attribution_required,
    }
