# QuranKit API

QuranKit's production API is not implemented yet, but the repository now defines one contract surface for the CLI, web app, self-hosting docs, and release checks.

## Current Status

- The bootstrap Docker service only exposes `GET /` and `GET /health` today.
- The versioned `/api/v1/...` routes below describe the target production contract and the surface the CLI expects in `mode=remote`.
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

## Planned Versioned Contract

### Public Read Endpoints

| Method | Path | Purpose |
| --- | --- | --- |
| `GET` | `/api/v1/surahs/{surahNumber}` | Surah metadata and ayah rows, with optional translation selection |
| `GET` | `/api/v1/ayahs/{surah}:{ayah}` | One ayah with metadata and attribution |
| `GET` | `/api/v1/juzs/{juzNumber}` | Juz range metadata and ayah rows |
| `GET` | `/api/v1/ayahs/random` | One random ayah with attribution |
| `GET` | `/api/v1/search/exact` | Exact-match search over Arabic text and optional translation text |
| `GET` | `/api/v1/search/semantic` | Related passages ranked by textual similarity, never interpretation |

Shared query parameters:

- `translation`: optional edition identifier such as `en.sahih`
- `limit`: optional maximum result count for search endpoints

### Authenticated Private Endpoints

| Method | Path | Purpose |
| --- | --- | --- |
| `GET` | `/api/v1/me/study` | Read the authenticated user's study-state document |
| `PUT` | `/api/v1/me/study` | Replace the authenticated user's study-state document |

Those endpoints are expected to carry progress, plans, bookmarks, and notes in one private payload and require `Authorization: Bearer <token>`.

## Example Contract Payloads

The examples below are illustrative contract shapes. They are not the live output of the bootstrap container.

### Exact Search

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

### Semantic Search

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

### Private Study State

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

## Error Model, Auth, and Caching

- Return JSON errors with at least `status` and `message`. `code` and `details` are recommended when validation fails.
- Return `401` or `403` when `/api/v1/me/study` is requested without a valid token.
- Return `404` when a surah, ayah, juz, edition, or search resource does not exist.
- Return `422` when references, ranges, or search parameters are structurally invalid.
- Treat `/api/v1/me/study` as private user state and send cache headers that prevent shared caching.
- Public read endpoints may be cached, but attribution fields and semantic-search disclaimer fields must remain intact.

Recommended error shape:

```json
{
  "status": "validation_error",
  "message": "Ayah reference must look like SURAH:AYAH.",
  "code": "invalid_reference"
}
```

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
