# QuranKit API

QuranKit's API currently exists in two layers:

- the bootstrap Docker service used by self-hosting docs and smoke checks
- the database-backed `apps/api` FastAPI service used for active backend development

## Current Status

- The bootstrap Docker service only exposes `GET /` and `GET /health` today.
- The versioned `/api/v1/...` routes remain the long-term production contract and the surface the CLI expects in `mode=remote`.
- `apps/api` now implements versioned health, browse, and exact-search endpoints against a migrated QuranKit database.
- `/api/v1/search/semantic` and authenticated `/api/v1/me/study` endpoints remain planned contract surfaces and are not implemented in `apps/api` yet.
- Use [docs/self-hosting.md](self-hosting.md), [docs/semantic-search.md](semantic-search.md), and [docs/reading-tracker.md](reading-tracker.md) for the operational details that sit around this contract.

## Design Rules

- Expose Quran text, metadata, translations, and search through clearly versioned endpoints.
- Preserve Quran text exactly as sourced. Do not normalize, paraphrase, or restyle ayah text in API payloads.
- Keep exact search and semantic search distinct in both endpoint naming and response copy.
- Include source attribution in responses that return Quran text, translations, or sourced metadata.
- Keep private user data such as bookmarks, notes, and reading progress authenticated and private by default.
- Support a local-first CLI flow now, with an optional authenticated private study-state API contract when remote sync is enabled.

## Bootstrap Endpoints Available Today

- `GET /`: returns bootstrap service metadata, status, and safety defaults.
- `GET /health`: returns a small readiness payload that includes `privacyMode` and `sourceAttributionRequired`.

Example bootstrap health response:

```json
{
  "status": "ok",
  "service": "QuranKit API Bootstrap",
  "privacyMode": "private-by-default",
  "sourceAttributionRequired": true
}
```

## Implemented Development API (`apps/api`)

Current database-backed endpoints:

- `GET /`
- `GET /api/v1/health`
- `GET /api/v1/surahs`
- `GET /api/v1/surahs/{surah_number}`
- `GET /api/v1/surahs/{surah_number}/ayahs`
- `GET /api/v1/ayahs/{reference}`
- `GET /api/v1/ayahs/random`
- `GET /api/v1/juz/{number}`
- `GET /api/v1/hizb/{number}`
- `GET /api/v1/pages/{number}`
- `GET /api/v1/search/exact`
- `GET /docs`
- `GET /openapi.json`

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

Browse- and search-specific errors use the same envelope with QuranKit-specific codes such as:

- `database_unavailable`
- `surah_not_found`
- `ayah_not_found`
- `juz_not_found`
- `hizb_not_found`
- `page_not_found`
- `invalid_ayah_reference`
- `invalid_search_query`
- `invalid_search_field`
- `translation_not_found`
- `unsupported_search_edition`

## Exact Search Contract

`GET /api/v1/search/exact` accepts:

- `q`: required exact substring query after QuranKit whitespace normalization
- `field`: optional repeated filter with `arabic_text`, `simple_text`, `normalized_text` (alias of `simple_text`), or `translation`
- `language`: optional edition language code filter such as `en` or `ar`
- `translation`: optional upstream edition identifier such as `en.sahih` or `quran-simple`
- `limit`: defaults to `20`, max `100`
- `offset`: defaults to `0`

Search behavior:

- When no field filter is provided, QuranKit searches Arabic source text, simple-text Quran editions, and translations.
- When `language` is provided without fields, the search defaults to edition-backed fields only.
- When `translation` is provided without fields, the search defaults to the one supported field for that edition type:
  - `translation` for translation editions
  - `simple_text` for Quran simple-text editions
- Results are deduplicated at the ayah level, paginated in canonical ayah order, and include per-field highlight excerpts where a match was found.

Exact-search responses include:

- `query`, `match_type`, `count`, and `searched_fields`
- normalized `filters`
- `results[].ayah` with exact-source Quran text and source attribution
- `results[].match_sources`
- `results[].highlights` with excerpt spans and edition attribution where relevant
- `pagination`
- top-level `arabic_source`
- `translation_attribution` when the request is scoped to one translation edition
- `edition_attributions` for the edition rows represented in the current page

## Planned Contract Surfaces

### Semantic Search

- `GET /api/v1/search/semantic` remains a planned endpoint for related passages ranked by textual similarity only, never interpretation.
- Semantic-search responses must keep the disclaimer explicit: related passages are similarity-ranked text matches, not tafsir, fatwa, or religious rulings.
- Planned responses should include `query`, `match_type`, `disclaimer`, `results`, `arabic_source`, `translation_attribution`, and optional similarity scores.

### Private Study State

- `GET /api/v1/me/study` and `PUT /api/v1/me/study` remain contract-first endpoints for private reading progress, plans, bookmarks, and notes.
- Those endpoints are expected to carry progress, plans, bookmarks, and notes in one private payload and require `Authorization: Bearer <token>`.
- They should reuse QuranKit's structured error envelope and send cache headers that prevent shared caching.

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
- `http://127.0.0.1:8000/api/v1/search/exact?q=book&translation=en.sahih`
- `http://127.0.0.1:8000/docs`
- `http://127.0.0.1:8000/openapi.json`

## Safety Defaults

- Quran text preservation is enforced in the data pipeline and browse API by returning the stored source text without local rewriting.
- Source attribution remains required for Quran text, translations, and sourced metadata.
- Semantic search is described as textual similarity only, not tafsir, fatwa, or religious ruling.
- Bookmarks, notes, and reading progress remain private-by-default requirements for future authenticated endpoints.

## Limitations Before Release

- The Docker bootstrap API is not a drop-in implementation of `mode=remote` yet.
- Remote study-state sync is contract-first; the current Compose stack proves health and safety defaults, not a full authenticated API.
- Semantic search must be described as textual similarity only. The API must not frame those results as tafsir, fatwa, or religious interpretation.
- Translation and audio exposure remain gated by attribution and rights review. See [docs/database.md](database.md).

## Self-Hosting References

- Use `docker compose up --build` to run the bootstrap stack described in [docs/self-hosting.md](self-hosting.md).
- Use `docker compose --profile semantic-search up --build` only when you are testing the optional semantic-search infrastructure path.
- Review `.env.api.example` for the current API-facing safety settings:
  - `QURANKIT_SOURCE_ATTRIBUTION_REQUIRED`
  - `QURANKIT_PRIVACY_MODE`
  - `QURANKIT_SEMANTIC_SEARCH_DISCLAIMER`
