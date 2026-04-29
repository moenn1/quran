# QuranKit Testing Strategy

QuranKit needs layered verification across repository quality, self-hosting, backend behavior, CLI behavior, frontend usability, data integrity, and end-to-end flows.

## Repository Baseline

- `./scripts/lint-repo.sh` checks shell syntax and bootstrap Python syntax.
- `./scripts/check-docs.sh` enforces required files and repository guarantees such as the maintainer note, semantic-search disclaimer, privacy defaults, and release docs.
- `./scripts/run-repository-tests.sh` exercises the bootstrap API contract and verifies the required self-hosting assets exist.
- `docker compose -f compose.yaml config` validates the self-hosting configuration.
- `./scripts/smoke-compose.sh` boots the bootstrap stack under an isolated Compose project, checks the API and web endpoints, and shuts the stack down.

## Backend and API

- Unit tests should cover parsers, service objects, validation logic, and API handlers.
- Integration tests should run against PostgreSQL for persistence, privacy defaults, and attribution behavior.
- Contract tests should verify exact-search responses, source attribution, and clear semantic-search disclaimers.
- The current repository baseline covers the bootstrap API behavior through `tests/test_self_hosting_baseline.py`.

## CLI

- Command tests should cover reading flows, exact search, semantic-search wording, bookmark management, note management, and export behavior.
- Snapshot or golden tests are acceptable for stable text output as long as Quran text itself is not mutated by test fixtures.
- `.env.cli.example` defines the initial CLI privacy and wording contract until the production CLI code lands.

## Frontend

- Component tests should verify rendering, accessibility, and RTL safety.
- Browser tests should cover search flows, reading views, bookmark and note privacy defaults, and Arabic typography regressions.
- Visual review should preserve elegant, Arabic-inspired presentation without reducing readability.
- The current bootstrap web container is covered by the Docker smoke test until the tracked frontend workspace lands.

## Data Validation

- Validate source provenance, attribution metadata, schema invariants, and checksums for imported Quran content.
- Reject unexpected text mutations, incomplete ayah ranges, or missing source metadata.
- Track validation outputs in reproducible scripts rather than ad hoc manual steps.
- The current data-validation entry point intentionally no-ops until the first tracked data-validation suite lands.

## End-to-End

- E2E checks should run on the Docker Compose stack and cover exact search, semantic-search disclaimers, bookmarks, notes, and reading-progress behavior.
- Privacy-sensitive E2E data should use local development fixtures only and never public production data.
- The current minimum end-to-end verification is `./scripts/smoke-compose.sh`.

## Current Bootstrap Commands

- `./scripts/run-repository-tests.sh`
- `./scripts/run-backend-tests.sh`
- `./scripts/run-frontend-tests.sh`
- `./scripts/run-cli-tests.sh`
- `./scripts/run-data-validation.sh`
- `./scripts/run-e2e.sh`
- `./scripts/smoke-compose.sh`

These commands intentionally no-op until the corresponding codebases exist. Once API, CLI, web, data, or E2E suites land, the owning team should wire each script to the real test command rather than inventing a new entry point.
