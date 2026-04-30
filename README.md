# QuranKit

QuranKit is an open-source developer and study platform for exploring the Quran through a public API, command-line interface, semantic search interface, and personal reading tracker.

The project is intended to be respectful, educational, source-transparent, and useful for developers, students, researchers, and personal study.

## Personal Note

I am not an Islamic scholar. This is a personal project with no commercial gain.

If I am doing anything wrong Islamically, please DM me directly so I can correct it.

## Planned Scope

- A clean REST API for Quran text, metadata, translations, search, bookmarks, notes, and reading progress.
- A CLI for terminal-based reading, exact search, semantic search, progress tracking, reading plans, bookmarks, notes, and exports.
- A web UI for browsing, exact search, semantic search, reading plans, bookmarks, and notes.
- A normalized Quran database with validation scripts and source attribution.
- Self-hostable local development with Docker Compose, PostgreSQL, and optional vector search.

## Religious Safety

- Quran text must be preserved exactly from its source.
- Quran text and translations must include clear source attribution.
- Semantic search results are related passages by textual similarity, not tafsir, fatwa, or scholarly interpretation.
- The project must not generate religious rulings.
- Notes, bookmarks, and reading progress should be private by default.

## Data Source Direction

The initial data foundation should evaluate and document the open-source `AbdullahGhanem/quran-database` repository as an upstream source, then normalize the data into QuranKit's own schema with validation, attribution, and export scripts.

## Development Status

This repository is being bootstrapped.

## Current Foundation

- `apps/api` contains the FastAPI backend, Alembic migrations, normalized data pipeline, browse routes, exact-search endpoint, and semantic-search endpoint.
- `apps/cli` contains the Typer CLI with persisted config, local-first private study state, and `surah`, `ayah`, `juz`, `random`, `search`, `semantic`, `progress`, `bookmark`, `note`, `plan`, and `export` commands.
- `apps/web` contains the Next.js web app scaffold with the Arabic-inspired design system, Tailwind utility layer, and TanStack Query/API client foundation for live data.
- `docs/frontend-architecture.md` documents the Arabic-inspired UI direction, route structure, and frontend component boundaries.
- `docs/api.md`, `docs/cli.md`, `docs/semantic-search.md`, `docs/reading-tracker.md`, `docs/testing.md`, and `docs/release-safety-checklist.md` document the API contract, implemented backend behavior, CLI workflows, semantic-search guardrails, private study-state behavior, release-blocking safety checks, and test expectations that future services must preserve.
- `docs/database.md` and `docs/contributing.md` document upstream data provenance, attribution constraints, normalization details, and contributor workflow expectations.
- `CHANGELOG.md` tracks repository changes across the API, CLI, frontend, data, and release-safety foundations.

## Development

Set up the Python tooling used by the CLI, backend, and repository Python checks:

```bash
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -e 'apps/cli[dev]'
python -m pip install -e 'apps/api[dev]'
```

Install JavaScript workspace dependencies:

```bash
npm ci
```

`./scripts/run-cli-tests.sh`, `./scripts/smoke-cli.sh`, `./scripts/run-backend-tests.sh`, and `./scripts/run-data-validation.sh` prefer `.venv/bin/python` when it exists so local Python checks use the same environment consistently.

Run the backend API:

```bash
cd apps/api
uvicorn qurankit_api.main:app --reload
```

Run the web app:

```bash
npm run dev:web
```

Run checks:

```bash
npm test
npm run lint
npm run build
./scripts/run-backend-tests.sh
./scripts/run-cli-tests.sh
./scripts/smoke-cli.sh
./scripts/run-data-validation.sh
```

## Backend Development

The first QuranKit API scaffold lives in `apps/api`.

Key endpoints:

- `GET /`
- `GET /api/v1/health`
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
- `GET /docs`
- `GET /openapi.json`

Validate and load the locked upstream dataset:

```bash
./scripts/run-data-validation.sh
./scripts/run-db-migrations.sh
./scripts/load-quran-data.sh
```

Build normalized SQLite, JSON, and PostgreSQL seed artifacts:

```bash
./scripts/build-data-artifacts.sh --output-dir .data/exports
```

If `QURANKIT_DATABASE_URL` is unset, the database scripts default to `apps/api/.data/qurankit.db`.
The locked upstream archive is cached at `apps/api/.data/upstream/quran.sql.zip`.
Build artifacts default to `apps/api/.data/exports` unless `--output-dir` is provided.

## Repository Layout

- `apps/api`: FastAPI backend package, normalized data pipeline, Alembic migrations, browse and search routes, and backend tests.
- `apps/cli`: Typer CLI package, config storage, private study state, lookup/search commands, export flows, backend selection, and CLI tests.
- `apps/web`: Next.js web app shell, Arabic-inspired styling, Tailwind/Query foundation, route pages, and frontend tests.
- `docs/api.md`: Bootstrap-vs-backend API notes, exact-search and semantic-search contract details, and planned private API surfaces.
- `docs/database.md`: Source evaluation, attribution plan, and normalization guidance for the upstream Quran data.
- `docs/frontend-architecture.md`: Frontend direction, route map, and implementation boundaries.

## Repository Foundation

The repository now includes a release-quality bootstrap for self-hosting, documentation, and CI so the API, CLI, web, and data work can land on a stable base.

- `compose.yaml` provisions PostgreSQL, a bootstrap API container, a bootstrap web container, and an optional Qdrant profile for semantic-search experiments.
- `.github/workflows/quality.yml` and `.github/workflows/release-readiness.yml` run documentation, safety, Docker, and bootstrap test checks.
- `./scripts/smoke-compose.sh` proves the bootstrap stack can start, answer health checks, and shut down cleanly.
- `docs/` tracks self-hosting, testing strategy, religious safety, API expectations, CLI expectations, and release readiness.

## Quick Start

1. Copy `.env.example` to `.env`.
2. Run `docker compose up --build`.
3. Visit `http://localhost:3000` for the bootstrap web UI and `http://localhost:8000/health` for the bootstrap API health check.
4. Run `./scripts/release-readiness.sh` before pushing repository-quality changes.

## Documentation

- [CONTRIBUTING.md](CONTRIBUTING.md)
- [CHANGELOG.md](CHANGELOG.md)
- [docs/self-hosting.md](docs/self-hosting.md)
- [docs/testing.md](docs/testing.md)
- [docs/religious-safety.md](docs/religious-safety.md)
- [docs/database.md](docs/database.md)
- [docs/frontend-architecture.md](docs/frontend-architecture.md)
- [docs/api.md](docs/api.md)
- [docs/cli.md](docs/cli.md)
- [docs/semantic-search.md](docs/semantic-search.md)
- [docs/reading-tracker.md](docs/reading-tracker.md)
- [docs/release-safety-checklist.md](docs/release-safety-checklist.md)
- [docs/contributing.md](docs/contributing.md)
- [docs/release-readiness.md](docs/release-readiness.md)
