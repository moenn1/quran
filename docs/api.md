# QuranKit API Notes

`apps/api` now contains the first FastAPI scaffold for QuranKit. It is intentionally runnable before database migrations, imports, and search services land.

## Current Endpoints

- `GET /` returns service metadata, docs locations, privacy defaults, and the semantic-search guardrail.
- `GET /api/v1/health` returns lightweight service status without depending on imported Quran data.
- `GET /docs` serves Swagger UI.
- `GET /openapi.json` serves the generated OpenAPI document.

## Error Format

Non-2xx responses use a consistent QuranKit error envelope:

```json
{
  "error": {
    "code": "not_found",
    "message": "Route not found.",
    "details": {
      "method": "GET",
      "path": "/api/v1/missing"
    }
  },
  "meta": {
    "request_id": "req-404"
  }
}
```

`X-Request-ID` is echoed in both the response header and the error body so logs and client traces can be correlated.

## Local Run

```bash
cd apps/api
python3 -m venv .venv
. .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
uvicorn qurankit_api.main:app --reload
```

Useful URLs after startup:

- `http://127.0.0.1:8000/`
- `http://127.0.0.1:8000/api/v1/health`
- `http://127.0.0.1:8000/docs`
- `http://127.0.0.1:8000/openapi.json`

## Safety Defaults

- Quran text preservation remains a source-ingestion requirement and is not implemented in this scaffold yet.
- Source attribution remains required for Quran text, translations, and sourced metadata.
- Semantic search is described as textual similarity only, not tafsir, fatwa, or religious ruling.
- Bookmarks, notes, and reading progress remain private-by-default requirements for future authenticated endpoints.
