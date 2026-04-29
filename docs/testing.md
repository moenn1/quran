# QuranKit Testing Strategy

QuranKit needs layered verification across repository quality, backend behavior, CLI behavior, frontend usability, data integrity, and end-to-end flows.

## Repository Baseline

- `./scripts/lint-repo.sh` checks shell syntax and bootstrap Python syntax.
- `./scripts/check-docs.sh` enforces required files and repository guarantees such as the maintainer note, semantic-search disclaimer, privacy defaults, and release docs.
- `./scripts/check-docs.sh` also pins the CLI install path and CLI-facing safety wording so release docs do not drift from the tested setup.
- `docker compose -f compose.yaml config` validates the self-hosting configuration.
- `./scripts/smoke-compose.sh` boots the bootstrap stack under an isolated Compose project, checks the API and web endpoints, and shuts the stack down.

## Backend and API

- Unit tests should cover parsers, service objects, validation logic, and API handlers.
- Integration tests should run against PostgreSQL for persistence, privacy defaults, and attribution behavior.
- Contract tests should verify exact-search responses, source attribution, and clear semantic-search disclaimers.

## CLI

- Command tests should cover reading flows, exact search, semantic-search wording, bookmark management, note management, and export behavior.
- Snapshot or golden tests are acceptable for stable text output as long as Quran text itself is not mutated by test fixtures.
- The current CLI baseline lives in `apps/cli` and uses pytest coverage for config persistence, backend selection, and the initial `qurankit config` command surface.

## Frontend

- Component tests should verify rendering, accessibility, and RTL safety.
- Browser tests should cover search flows, reading views, bookmark/note privacy defaults, and Arabic typography regressions.
- Visual review should preserve elegant, Arabic-inspired presentation without reducing readability.
- The current baseline includes Vitest coverage in `apps/web/src/test` for route architecture, reader attribution, and semantic-search wording.

## Data Validation

- Validate source provenance, attribution metadata, schema invariants, and checksums for imported Quran content.
- Reject unexpected text mutations, incomplete ayah ranges, or missing source metadata.
- Track validation outputs in reproducible scripts rather than ad hoc manual steps.
- The current baseline includes `scripts/analyze_upstream_quran_sql.py`, `docs/upstream/quran-database-summary.json`, and `tests/test_analyze_upstream_quran_sql.py` as the first reproducible data-validation path.

## End-to-End

- E2E checks should run on the Docker Compose stack and cover exact search, semantic-search disclaimers, bookmarks, notes, and reading-progress behavior.
- Privacy-sensitive E2E data should use local development fixtures only and never public production data.

## Current Bootstrap Commands

- `./scripts/run-backend-tests.sh`
- `./scripts/run-frontend-tests.sh`
- `./scripts/run-cli-tests.sh`
- `./scripts/run-data-validation.sh`
- `./scripts/run-e2e.sh`
- `./scripts/smoke-compose.sh`

Some commands intentionally no-op until their corresponding codebases exist. The CLI target now runs `pytest` in `apps/cli`, while the remaining placeholders should be replaced as their codebases land.
