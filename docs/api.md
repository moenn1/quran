# QuranKit API

QuranKit's API currently exists in two layers:

- the bootstrap Docker service used by self-hosting docs and smoke checks
- the database-backed `apps/api` FastAPI service used for active backend development

## Current Status

- The bootstrap Docker service only exposes `GET /` and `GET /health` today.
- The versioned `/api/v1/...` routes remain the long-term production contract and the surface the CLI expects in `mode=remote`.
- `apps/api` now implements versioned health, browse, exact-search, semantic-search, auth, and authenticated private-study endpoints against a migrated QuranKit database.
- The bootstrap Docker service is still not a full `mode=remote` implementation for authenticated study state.
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
- `POST /api/v1/auth/register`
- `POST /api/v1/auth/login`
- `GET /api/v1/surahs`
- `GET /api/v1/surahs/{surah_number}`
- `GET /api/v1/surahs/{surah_number}/ayahs`
- `GET /api/v1/ayahs/{reference}`
- `GET /api/v1/ayahs/random`
- `GET /api/v1/juz/{number}`
- `GET /api/v1/hizb/{number}`
- `GET /api/v1/pages/{number}`
- `GET /api/v1/search/exact`
- `GET /api/v1/search/semantic`
- `GET /api/v1/me/study`
- `PUT /api/v1/me/study`
- `DELETE /api/v1/me/study`
- `GET|PUT|DELETE /api/v1/me/progress`
- `GET|POST|DELETE /api/v1/me/reading-sessions`
- `GET|POST|DELETE /api/v1/me/bookmarks`
- `GET|POST|PATCH|DELETE /api/v1/me/notes`
- `GET|POST|PATCH|DELETE /api/v1/me/plans`
- `GET /api/v1/me/plans/{plan_id}/today`
- `GET /api/v1/me/exports/{scope}`
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

Illustrative exact-search response:

`GET /api/v1/search/exact?q=guide&translation=en.sahih&limit=5`

```json
{
  "query": "guide",
  "match_type": "exact",
  "count": 1,
  "searched_fields": ["arabic_text", "translation"],
  "results": [
    {
      "ayah": {
        "reference": "1:6",
        "surah_number": 1,
        "ayah_number": 6,
        "surah_name_arabic": "<source-preserved surah name>",
        "surah_name_english": "Al-Fatihah",
        "arabic_text": "<source-preserved ayah text>",
        "translation_text": "<selected translation text>"
      },
      "match_sources": ["translation"]
    }
  ],
  "arabic_source": {
    "repository": "AbdullahGhanem/quran-database",
    "snapshot": "f6c4c805f22b0432677d79aafc12139b915e1a0d",
    "note": "Arabic Quran text is shown exactly as stored in the configured QuranKit backend."
  },
  "translation_attribution": {
    "identifier": "en.sahih",
    "language": "en",
    "english_name": "Saheeh International",
    "edition_type": "translation",
    "format": "text"
  }
}
```

## Semantic Search Contract

`GET /api/v1/search/semantic` accepts:

- `q`: required textual cue after QuranKit whitespace normalization
- `translation`: optional upstream text translation identifier such as `en.sahih`
- `limit`: defaults to `5`, max `100`
- `threshold`: optional similarity floor from `0.0` to `1.0`, defaults to `0.12`
- `include_scores`: optional boolean, defaults to `false`
- `search_scope`: optional scope selector with `all`, `surah`, `juz`, `hizb`, or `page`
- `surah`, `juz`, `hizb`, `page`: optional scope-reference parameter matching the selected `search_scope`

Semantic-search behavior:

- QuranKit ranks related passages by deterministic textual similarity over the stored Arabic ayah text plus one selected translation edition when `translation` is provided.
- The current backend uses token overlap, near-token matching, and a small `SequenceMatcher` boost. It is a ranking aid, not interpretation.
- `translation` currently supports text translation editions only. Quran simple-text editions remain available through exact search.
- `search_scope=all` does not accept additional scope-reference filters.
- Scoped searches require exactly one matching scope-reference parameter.
- Results are sorted by descending similarity score and then canonical ayah order.

Semantic-search responses include:

- `query`, `match_type`, `count`, and the explicit semantic-search `disclaimer`
- normalized `filters`
- `results[].ayah` with exact-source Quran text, source attribution, and `translation_text` when a translation edition was searched
- `results[].reason` with a mechanical explanation of why the result matched
- `results[].context` with adjacent ayah references for quick verification in the reader
- optional `results[].similarity_score` when `include_scores=true`
- top-level `arabic_source`
- `translation_attribution` when the request is scoped to one translation edition

The canonical disclaimer wording is:

```text
Related passages are ranked by textual similarity only. They are not tafsir, fatwa, or religious rulings.
```

## Authenticated Private Study State
Illustrative semantic-search response:

`GET /api/v1/search/semantic?q=guide+path&translation=en.sahih&limit=5`

```json
{
  "query": "guide path",
  "match_type": "semantic_similarity",
  "count": 2,
  "disclaimer": "Related passages are ranked by textual similarity only. They are not tafsir, fatwa, or religious rulings.",
  "results": [
    {
      "ayah": {
        "reference": "1:6",
        "surah_number": 1,
        "ayah_number": 6,
        "surah_name_english": "Al-Fatihah",
        "arabic_text": "<source-preserved ayah text>",
        "translation_text": "<selected translation text>"
      },
      "similarity_score": 0.842,
      "reason": "Shared terms in the selected text: guide, path."
    }
  ],
  "arabic_source": {
    "repository": "AbdullahGhanem/quran-database",
    "snapshot": "f6c4c805f22b0432677d79aafc12139b915e1a0d",
    "note": "Arabic Quran text is shown exactly as stored in the configured QuranKit backend."
  },
  "translation_attribution": {
    "identifier": "en.sahih",
    "language": "en",
    "english_name": "Saheeh International",
    "edition_type": "translation",
    "format": "text"
  }
}
```

The `reason` field should stay descriptive and mechanical. It should explain why the result matched, not what the ayah means.

## Authenticated Private Study State

`apps/api` now implements a password-based private study surface with opaque bearer tokens:

- `POST /api/v1/auth/register`
- `POST /api/v1/auth/login`
- `GET /api/v1/me/study`
- `PUT /api/v1/me/study`
- `DELETE /api/v1/me/study`
- `GET|PUT|DELETE /api/v1/me/progress`
- `GET|POST|DELETE /api/v1/me/reading-sessions`
- `GET|POST|DELETE /api/v1/me/bookmarks`
- `GET|POST|PATCH|DELETE /api/v1/me/notes`
- `GET|POST|PATCH|DELETE /api/v1/me/plans`
- `GET /api/v1/me/plans/{plan_id}/today`
- `GET /api/v1/me/exports/{scope}`

Private-study behavior:

- `Authorization: Bearer <token>` is required for every `/api/v1/me/...` route.
- `Cache-Control: private, no-store` is sent on private-study responses, including structured auth failures.
- `PUT /api/v1/me/study` remains a full document replacement contract for the CLI's remote-study sync mode.
- Granular progress, plan, bookmark, note, session, and export routes are implemented in the same service for web clients, tests, and manual API use.
- Reading plans compute per-day targets from either an explicit `daily_ayah_target` or an inclusive `start_date`/`end_date` span, and they expose derived `today_range`, projected completion, and streak-oriented progress summaries.

Illustrative private study-state request and response:

`GET /api/v1/me/study`

```http
Authorization: Bearer <token>
Accept: application/json
```

```json
{
  "state": {
    "progress": {
      "range": {
        "start": { "surah_number": 1, "ayah_number": 1 },
        "end": { "surah_number": 1, "ayah_number": 7 },
        "label": "1:1-7"
      },
      "updated_at": "2026-04-30T00:00:00+00:00",
      "source": "manual_mark"
    },
    "bookmarks": [
      {
        "id": "bookmark-id",
        "range": {
          "start": { "surah_number": 2, "ayah_number": 255 },
          "end": { "surah_number": 2, "ayah_number": 255 },
          "label": "2:255"
        },
        "label": "Evening review",
        "created_at": "2026-04-30T00:00:00+00:00"
      }
    ],
    "notes": [],
    "plans": []
  }
}
```

Related auth and validation failures continue to use the structured QuranKit error envelope, including machine-readable `401`/`403` auth failures and `404`/`422` resource or validation errors.

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
- `http://127.0.0.1:8000/api/v1/search/semantic?q=book&translation=en.sahih&include_scores=true`
- `http://127.0.0.1:8000/docs`
- `http://127.0.0.1:8000/openapi.json`

## Safety Defaults

- Quran text preservation is enforced in the data pipeline and browse API by returning the stored source text without local rewriting.
- Source attribution remains required for Quran text, translations, and sourced metadata.
- Semantic search is described as textual similarity only, not tafsir, fatwa, or religious rulings.
- Bookmarks, notes, reading progress, study exports, and session history remain private by default in the implemented authenticated endpoints.

## Limitations Before Release

- The Docker bootstrap API is not a drop-in implementation of `mode=remote` yet.
- Remote study-state sync now works in `apps/api`, but the current Compose bootstrap stack still proves health and safety defaults rather than the full authenticated API surface.
- Semantic search must be described as textual similarity only. The API must not frame those results as tafsir, fatwa, or religious interpretation.
- The current similarity backend is deterministic textual ranking inside `apps/api`; optional vector infrastructure remains future self-hosting work.
- Translation and audio exposure remain gated by attribution and rights review. See [docs/database.md](database.md).

## Self-Hosting References

- Use `docker compose up --build` to run the bootstrap stack described in [docs/self-hosting.md](self-hosting.md).
- Use `docker compose --profile semantic-search up --build` only when you are testing the optional semantic-search infrastructure path.
- Review `.env.api.example` for the current API-facing safety settings:
  - `QURANKIT_SOURCE_ATTRIBUTION_REQUIRED`
  - `QURANKIT_PRIVACY_MODE`
  - `QURANKIT_SEMANTIC_SEARCH_DISCLAIMER`
