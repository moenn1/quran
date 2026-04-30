# QuranKit API Notes

The production API is not implemented yet, but its documentation constraints are already defined.

## Expectations

- Expose Quran text, metadata, translations, and search through clearly versioned endpoints.
- Keep exact search and semantic search distinct in both endpoint naming and response copy.
- Include source attribution in responses that return Quran text, translations, or sourced metadata.
- Keep private user data such as bookmarks, notes, and reading progress authenticated and private by default.
- Support a local-first CLI flow now, with an optional authenticated private study-state API contract when remote sync is enabled.

## Current CLI-Facing Remote State Contract

The QuranKit CLI now treats private study state as local by default, but it can opt into authenticated remote state with:

- `GET /api/v1/me/study`
- `PUT /api/v1/me/study`

Those endpoints are expected to carry progress, plans, bookmarks, and notes in one private payload and require `Authorization: Bearer <token>`.

## Semantic Search Guardrail

When semantic search is introduced, the API must describe results as textually similar passages only. The API must not frame those results as tafsir, fatwa, or religious interpretation.

## Minimum Documentation Before Release

- Authentication model and privacy defaults
- Source attribution fields
- Error handling
- Rate-limiting or resource-usage guidance
- Search semantics and limitations
