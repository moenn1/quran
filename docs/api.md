# QuranKit API Notes

The production API is not implemented yet, but its documentation constraints are already defined.

## Expectations

- Expose Quran text, metadata, translations, and search through clearly versioned endpoints.
- Keep exact search and semantic search distinct in both endpoint naming and response copy.
- Include source attribution in responses that return Quran text, translations, or sourced metadata.
- Keep private user data such as bookmarks, notes, and reading progress authenticated and private by default.

## Semantic Search Guardrail

When semantic search is introduced, the API must describe results as textually similar passages only. The API must not frame those results as tafsir, fatwa, or religious interpretation.

## Current Bootstrap Contract

- `GET /health` returns service status, the current privacy mode, and whether source attribution is required.
- `GET /` returns bootstrap metadata and safety guardrails without exposing raw database credentials.

## Minimum Documentation Before Release

- Authentication model and privacy defaults
- Source attribution fields
- Error handling
- Rate-limiting or resource-usage guidance
- Search semantics and limitations
