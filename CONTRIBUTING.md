# Contributing to QuranKit

Thank you for contributing to QuranKit.

## Core Principles

- Preserve Quran text exactly from its upstream source. Do not change Quran text for styling, normalization, or convenience.
- Keep source attribution visible and verifiable for Quran text, translations, metadata, and any derived exports.
- Describe semantic search as textual similarity only. It is not tafsir, fatwa, or a religious ruling.
- Keep bookmarks, notes, and reading progress private by default.
- Maintain respectful Arabic presentation with strong readability, reliable RTL behavior, and accessible typography.

## Local Setup

1. Clone the repository and enter it.
2. Configure the repo-local Git identity:
   `git config user.name "Mohamed En-Nassibi"`
   `git config user.email "mohamed.enn2001@gmail.com"`
3. Copy `.env.example` to `.env`.
4. Create a local Python virtual environment for CLI and data-validation tooling:
   `python3 -m venv .venv`
   `. .venv/bin/activate`
   `python -m pip install -e 'apps/cli[dev]'`
5. Install JavaScript workspace dependencies with `npm ci` when frontend code is present.
6. Start the bootstrap stack with `docker compose up --build`.
7. Run `./scripts/release-readiness.sh` before pushing changes that affect repository quality, docs, Docker, CI, or data validation.

`./scripts/run-cli-tests.sh` and `./scripts/smoke-cli.sh` prefer `.venv/bin/python` when it exists, so keep the CLI development dependencies installed in that environment for local verification.

## Workflow

- Create a focused branch from `main`.
- Keep commits small and repository-facing language centered on QuranKit.
- Add or update the tests that cover the behavior you changed when practical.
- Update `CHANGELOG.md` and relevant documentation when behavior, workflows, or guarantees change.
- Do not commit secrets, local `.env` files, or private data.
- Avoid destructive Git commands that could discard other work in the repository.

## Test Targets

- `./scripts/lint-repo.sh`
- `./scripts/check-docs.sh`
- `./scripts/run-backend-tests.sh`
- `./scripts/run-frontend-tests.sh`
- `./scripts/run-cli-tests.sh`
- `./scripts/smoke-cli.sh`
- `./scripts/run-data-validation.sh`
- `./scripts/run-e2e.sh`
- `./scripts/smoke-compose.sh`
- `./scripts/release-readiness.sh`

Some scripts intentionally no-op until their corresponding application surfaces exist. That keeps CI green now while defining the expected quality entry points for future implementation.

## Documentation Expectations

- Keep `README.md` coherent with the current project state and preserve the maintainer note.
- Update `docs/self-hosting.md` when Compose services, container assumptions, or environment variables change.
- Update `docs/testing.md` when new test suites or verification rules are introduced.
- Update `docs/religious-safety.md` whenever religious-safety, privacy, source-attribution, or UI-readability rules change.
- Update `docs/api.md` and `docs/cli.md` when interfaces or guarantees change.
- Update `docs/semantic-search.md` when similarity-search behavior, disclaimers, ranking inputs, or vector-search infrastructure assumptions change.
- Update `docs/reading-tracker.md` when progress, bookmarks, notes, plans, exports, privacy defaults, or remote study-state contracts change.
- Update `docs/contributing.md` when repository workflow expectations or documentation ownership rules change.

## Reporting Religious or Privacy Concerns

If something in QuranKit appears Islamically wrong, privacy-hostile, or misleading, open an issue when appropriate and DM the maintainer directly for urgent Islamic corrections.
