# QuranKit Testing Strategy

QuranKit needs layered verification across repository quality, backend behavior, CLI behavior, frontend usability, data integrity, and end-to-end flows.

## Repository Baseline

- `./scripts/lint-repo.sh` checks shell syntax and bootstrap Python syntax.
- `./scripts/check-docs.sh` enforces required files and repository guarantees such as the maintainer note, semantic-search disclaimer, privacy defaults, and release docs.
- `./scripts/check-docs.sh` also requires the dedicated API, CLI, database, semantic-search, reading-tracker, and contributor docs so release notes and implementation docs do not drift apart.
- `./scripts/check-docs.sh` also pins the CLI install path and CLI-facing safety wording so release docs do not drift from the tested setup.
- `./scripts/check-docs.sh` also pins the privacy and religious-safety release checklist so export/delete review points and non-commercial framing checks do not drift.
- `docker compose -f compose.yaml config` validates the self-hosting configuration.
- `./scripts/smoke-compose.sh` boots the bootstrap stack under an isolated Compose project, checks the API and web endpoints, and shuts the stack down.

## Backend and API

- Unit tests should cover parsers, service objects, validation logic, and API handlers.
- Integration tests should run against PostgreSQL for persistence, privacy defaults, and attribution behavior.
- Contract tests should verify exact-search responses, semantic-search responses, source attribution, and clear similarity-only disclaimers.
- The current backend baseline lives in `apps/api`.
- `./scripts/run-backend-tests.sh` prefers `.venv/bin/python` when it exists, falls back to `apps/api/.venv/bin/python` or `python3`, and runs `python -m pytest` in `apps/api`.

The current API test suite covers:

- service metadata at `GET /`
- health reporting at `GET /api/v1/health`
- QuranKit error envelopes for `404`, `405`, and `500` responses
- generated OpenAPI metadata and the published health contract
- Alembic migration application against a temporary SQLite database
- ORM-level constraint checks for ayah metadata ranges, translation review gating, privacy defaults, and semantic embedding targeting rules
- source metadata seed idempotency for the evaluated upstream snapshot
- locked-source validation, normalized load, and export coverage using a zipped SQL fixture
- browse endpoint coverage for surah, ayah, juz, hizb, page, random lookup, invalid ayah references, and database-unavailable error handling
- exact-search endpoint coverage for field selection, edition filters, language filters, pagination, highlights, and invalid query handling
- semantic-search endpoint coverage for disclaimer wording, translation attribution, scope filters, optional scores, context references, and invalid scope or edition handling

## CLI

- Command tests should cover reading flows, exact search, semantic-search wording, bookmark management, note management, and export behavior.
- Snapshot or golden tests are acceptable for stable text output as long as Quran text itself is not mutated by test fixtures.
- The current CLI baseline lives in `apps/cli` and uses pytest coverage for config persistence, backend selection, and the initial `qurankit config` command surface.
- `./scripts/run-cli-tests.sh` and `./scripts/smoke-cli.sh` both prefer `.venv/bin/python` when it exists so the CLI pytest suite and the installed-entrypoint smoke check use one prepared environment.
- `./scripts/run-cli-tests.sh` expects `python -m pip install -e 'apps/cli[dev]'` and runs `python -m pytest` in `apps/cli`.
- `./scripts/smoke-cli.sh` verifies the installed `qurankit` entrypoint, temporary config storage, and isolated `config show/set` behavior outside the in-process pytest runner.
- The current CLI pytest suite also covers remote semantic-search command wiring and bookmark removal so the user-facing Typer surface keeps its privacy wording, route selection, and API contracts aligned.

## Frontend

- Component tests should verify rendering, accessibility, and RTL safety.
- Browser tests should cover search flows, explore filtering, reading views, bookmark/note privacy defaults, ayah navigation, and Arabic typography regressions.
- Visual review should preserve elegant, Arabic-inspired presentation without reducing readability.
- The current component baseline includes Vitest coverage in `apps/web/src/test` for route architecture, bundled reader-data helpers, explore filtering, reader attribution, reader controls, exact-search filters and context, semantic-search wording and private actions, study-state routes, API client URL handling, and the TanStack Query runtime foundation surface.
- The current browser baseline includes Playwright coverage in `apps/web/e2e` for exact search into ayah detail, semantic-search guardrails plus bookmark persistence, reader progress actions, axe-based accessibility checks, and responsive visual snapshots for search and reader routes.
- Install the browser runtime once before local E2E work with `npx playwright install chromium`.

## Data Validation

- Validate source provenance, attribution metadata, schema invariants, and checksums for imported Quran content.
- Reject unexpected text mutations, incomplete ayah ranges, or missing source metadata.
- Track validation outputs in reproducible scripts rather than ad hoc manual steps.
- The current baseline includes `scripts/analyze_upstream_quran_sql.py`, `docs/upstream/quran-database-summary.json`, and `tests/test_analyze_upstream_quran_sql.py` as the first reproducible data-validation path.
- `./scripts/run-data-validation.sh` prefers `.venv/bin/python` when it exists, falls back to `apps/api/.venv/bin/python` or `python3`, and runs `python -m qurankit_api.data.pipeline validate` when `apps/api` exists. If the backend package is absent, it falls back to the repository analyzer test.

The current validation workflow checks the locked upstream dataset for:

- 114 surahs
- 6236 ayahs
- sequential global ayah numbering
- sequential ayah numbering inside each surah
- expected page, juz, hizb, and rub el hizb ranges
- complete per-edition ayah coverage

## End-to-End

- E2E checks should cover exact search, semantic-search disclaimers, bookmarks, notes, and reading-progress behavior.
- Privacy-sensitive E2E data should use local development fixtures only and never public production data.
- `./scripts/run-e2e.sh` now runs the Playwright suite from `apps/web`, starts the Next.js web app on a local test port, and exercises the bundled sample routes in Chromium.
- `./scripts/export-release-screenshots.sh` copies the approved Playwright visual baselines into `docs/screenshots` so release/demo images stay tied to browser-tested layouts.
- For visual regression updates, run `npm run test:e2e:update --workspace @qurankit/web` after reviewing the new snapshots.

## Current Bootstrap Commands

- `./scripts/run-backend-tests.sh`
- `./scripts/run-frontend-tests.sh`
- `./scripts/run-cli-tests.sh`
- `./scripts/smoke-cli.sh`
- `./scripts/run-data-validation.sh`
- `./scripts/run-e2e.sh`
- `./scripts/smoke-compose.sh`

The backend, frontend, CLI, data-validation, and browser E2E targets all run today. `./scripts/run-frontend-tests.sh` executes the Vitest component suite in `apps/web`, `./scripts/run-cli-tests.sh` runs `python -m pytest` in `apps/cli`, and `./scripts/run-e2e.sh` exercises the Playwright browser flows against the local Next.js app.
