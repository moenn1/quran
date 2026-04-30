# Changelog

## Unreleased

### Added

- Added an upstream Quran database evaluation, attribution plan, and a reproducible SQL dump analyzer for QuranKit's data foundation.
- Added the initial `apps/api` FastAPI scaffold with versioned health, structured error envelopes, request IDs, and generated OpenAPI metadata.
- Added the first SQLAlchemy model layer, Alembic migration scaffold, and source provenance seed flow for QuranKit's normalized database foundation.
- Added private-by-default persistence tables for reading state plus semantic embedding metadata constraints for future search indexing.
- Added backend run instructions, API/testing docs, and a repository-level backend pytest entrypoint.
- Added a locked-source normalization pipeline with checksum validation, exact-text loading, human-readable validation output, and SQLite/JSON/PostgreSQL export generation.
- Added database-backed Quran browse endpoints for surahs, ayahs, juz, hizb, pages, and random ayah lookup with source attribution and browse API pytest coverage.
- Added an exact-search API with Arabic, simple-text, and translation filters, search-only normalized columns and indexes, result pagination, and attribution-aware highlights.
