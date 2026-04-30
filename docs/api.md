# QuranKit API Notes

`apps/api` now contains the first database-backed FastAPI API surface for QuranKit browse flows.

## Current Endpoints

- `GET /` returns service metadata, docs locations, privacy defaults, and the semantic-search guardrail.
- `GET /api/v1/health` returns lightweight service status without depending on imported Quran data.
- `GET /api/v1/surahs` lists canonical surahs with pagination.
- `GET /api/v1/surahs/{surah_number}` returns one surah by number.
- `GET /api/v1/surahs/{surah_number}/ayahs` lists ayahs inside a surah with pagination.
- `GET /api/v1/ayahs/{reference}` resolves either a global ayah number like `255` or a surah-local reference like `2:255`.
- `GET /api/v1/ayahs/random` returns a random ayah from the loaded QuranKit dataset.
- `GET /api/v1/juz/{number}` lists ayahs in a normalized juz number.
- `GET /api/v1/hizb/{number}` lists ayahs in a normalized hizb number (`1..60`).
- `GET /api/v1/pages/{number}` lists ayahs on a mushaf page.
- `GET /docs` serves Swagger UI.
- `GET /openapi.json` serves the generated OpenAPI document.

## Browse Contract Notes

- Browse endpoints require `QURANKIT_DATABASE_URL` plus a migrated and loaded database.
- Surah list pagination defaults to `limit=114` and `offset=0`.
- Ayah collection endpoints default to `limit=50` and `offset=0`, with a maximum `limit=200`.
- Quran browse responses include source attribution fields from the locked upstream release metadata.
- The browse API returns stored Quran text exactly as loaded from source. If the source row contains a BOM artifact, that byte-order mark remains present in the returned text.

## Ayah References

`GET /api/v1/ayahs/{reference}` accepts two formats:

- global ayah number: `1`
- surah-local reference: `2:255`

Invalid formats return QuranKit's structured `422` error envelope with code `invalid_ayah_reference`.

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

Browse-specific errors use the same envelope with QuranKit-specific codes such as:

- `database_unavailable`
- `surah_not_found`
- `ayah_not_found`
- `juz_not_found`
- `hizb_not_found`
- `page_not_found`

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
- `http://127.0.0.1:8000/api/v1/surahs`
- `http://127.0.0.1:8000/api/v1/ayahs/1`
- `http://127.0.0.1:8000/api/v1/ayahs/2:255`
- `http://127.0.0.1:8000/docs`
- `http://127.0.0.1:8000/openapi.json`

## Safety Defaults

- Quran text preservation is enforced in the data pipeline and browse API by returning the stored source text without local rewriting.
- Source attribution remains required for Quran text, translations, and sourced metadata.
- Semantic search is described as textual similarity only, not tafsir, fatwa, or religious ruling.
- Bookmarks, notes, and reading progress remain private-by-default requirements for future authenticated endpoints.
