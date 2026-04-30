from fastapi.testclient import TestClient


def test_unknown_route_uses_qurankit_error_envelope(client: TestClient) -> None:
    response = client.get("/api/v1/missing", headers={"X-Request-ID": "req-404"})

    assert response.status_code == 404
    assert response.headers["X-Request-ID"] == "req-404"
    assert response.json() == {
        "error": {
            "code": "not_found",
            "message": "Route not found.",
            "details": {
                "method": "GET",
                "path": "/api/v1/missing",
            },
        },
        "meta": {
            "request_id": "req-404",
        },
    }


def test_method_not_allowed_uses_qurankit_error_envelope(client: TestClient) -> None:
    response = client.post("/api/v1/health", headers={"X-Request-ID": "req-405"})

    assert response.status_code == 405
    assert response.headers["X-Request-ID"] == "req-405"
    assert response.json() == {
        "error": {
            "code": "method_not_allowed",
            "message": "Method not allowed.",
            "details": {
                "method": "POST",
                "path": "/api/v1/health",
            },
        },
        "meta": {
            "request_id": "req-405",
        },
    }


def test_internal_errors_use_qurankit_error_envelope(
    no_raise_client: TestClient,
) -> None:
    response = no_raise_client.get(
        "/api/v1/_boom",
        headers={"X-Request-ID": "req-500"},
    )

    assert response.status_code == 500
    assert response.headers["X-Request-ID"] == "req-500"
    assert response.json() == {
        "error": {
            "code": "internal_server_error",
            "message": "Internal server error.",
            "details": None,
        },
        "meta": {
            "request_id": "req-500",
        },
    }
