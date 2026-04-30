# Changelog

All notable changes to QuranKit will be documented in this file.

The format is based on Keep a Changelog, and this project follows Semantic Versioning once versioned releases begin.

## [Unreleased]

### Added

- Added `docs/release-safety-checklist.md` as a dedicated privacy and religious-safety release gate covering Quran text preservation, attribution, semantic-search wording, private-by-default study data, export/delete affordances, README note preservation, and non-commercial framing.
- Added dedicated API, CLI, database, semantic-search, reading-tracker, and contributor docs so the repository now documents its contract surfaces, privacy defaults, source-attribution rules, and self-hosting caveats more concretely.
- Added interactive `/search` and `/semantic` web routes with bundled exact-match filtering, result context, similarity-preview controls, optional scores, and private bookmark/plan/copy actions.
- Added `/explore`, `/surah/[number]`, and `/ayah/[surah]/[ayah]` to the web app with bundled routed surah samples, surah filtering, translation and text-view toggles, font controls, private study actions, attribution-safe copy behavior, and previous/next navigation.
- Added interactive `/progress`, `/plans`, `/bookmarks`, `/notes`, and `/settings` study-state routes with local browser persistence, shared reader preferences, bundled-sample progress summaries, plan creation/recalculation, bookmark filtering, private note editing, JSON export previews, and deliberate local-data clearing.
- Added Playwright browser coverage for the web search, reader, progress, and bookmark flows, including axe accessibility checks, responsive screenshot baselines, and a real `./scripts/run-e2e.sh` path backed by `apps/web/e2e`.
- Added Tailwind and TanStack Query foundations to `apps/web`, including a shared app provider, API client utilities, PostCSS wiring, and a runtime foundation panel on the home route.
- Expanded the QuranKit CLI with local-first private study state, `progress`, `bookmark`, `note`, `plan`, and `export` commands, ayah-range parsing, authenticated optional remote study-state mode, attribution-safe surah export, and pytest coverage for private workflow behavior.
- Added the first `apps/cli` Typer package scaffold with persisted configuration, remote API and local SQLite backend selection, and initial `qurankit config show/set` commands.
- Expanded the QuranKit CLI with `surah`, `ayah`, `juz`, `random`, `search`, and `semantic` commands, shared `--json` and translation controls, remote/local backend execution, attribution-aware output, and Typer coverage for lookup, exact search, and textual-similarity search behavior.
- Added the first `apps/api` FastAPI backend with versioned health, structured error envelopes, request IDs, and generated OpenAPI metadata.
- Added normalized SQLAlchemy models, Alembic migrations, source provenance seed flows, and private-by-default reading-state tables for QuranKit's backend schema foundation.
- Added a locked-source normalization pipeline with checksum validation, exact-text loading, human-readable validation output, and SQLite, JSON, and PostgreSQL export generation.
- Added database-backed Quran browse endpoints for surahs, ayahs, juz, hizb, pages, and random ayah lookup with source attribution and backend pytest coverage.
- Added an exact-search API with Arabic, simple-text, and translation filters, normalized search columns and indexes, result pagination, attribution-aware highlights, and exact-search pytest coverage.
- Added repository backend scripts and docs for migrations, source metadata seeding, data loading, backend pytest, and data-validation flows.
- Bootstrapped the `apps/web` Next.js frontend foundation with Arabic-inspired theme tokens, shared layout components, and route scaffolding for browse, reader, search, semantic search, progress, plans, bookmarks, notes, and settings.
- Added an attributed Quran reader preview using a small sample from AlQuran.Cloud and a shared semantic-search disclaimer that keeps similarity search clearly separated from tafsir, fatwa, and religious rulings.
- Added `docs/frontend-architecture.md`, a public npm registry config for reproducible installs, and Vitest coverage for route architecture, reader attribution, and semantic-search guardrails.
- Added an upstream Quran database evaluation, attribution plan, reproducible SQL dump analyzer, summary artifact, and pytest coverage for QuranKit's data foundation.
- Added repository governance and contributor workflow docs for README, contributing, code of conduct, license, and changelog management.
- Added self-hosting bootstrap assets with Docker Compose, backend/frontend Dockerfiles, environment examples, and a smoke test that exercises the running stack.
- Added release-quality and safety documentation for religious guardrails, privacy defaults, testing strategy, API expectations, CLI expectations, database source evaluation, and release readiness.
- Added GitHub Actions and local scripts for documentation checks, linting, frontend quality checks, data validation, Docker validation, and release-readiness checks.

### Fixed

- Clarified that the current Docker bootstrap API is only a health-and-safety surface, while the documented `/api/v1/...` routes remain a production contract for future API work and CLI remote mode.
- Made CLI test automation reproducible in clean environments by installing `apps/cli[dev]` in GitHub Actions, updating `./scripts/run-cli-tests.sh` to use one Python interpreter consistently, and documenting the required local setup.
- Added `./scripts/smoke-cli.sh` and restored the CLI setup path in the release docs so QuranKit now verifies the installed `qurankit` console script and isolated config persistence as part of release-readiness.
- Unified `./scripts/run-cli-tests.sh` and `./scripts/smoke-cli.sh` on one shared Python-selection helper so CLI pytest and installed-entrypoint smoke checks stay aligned in clean environments.
- Tightened repository documentation checks so CLI install instructions, CLI README scope, privacy wording, and semantic-search disclaimers stay aligned across the tracked docs.
- Restored stable web unit coverage after adding browser tests by excluding Playwright specs from Vitest and pinning an in-memory `localStorage` shim for the study-state test harness.
