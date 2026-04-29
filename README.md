# QuranKit

QuranKit is an open-source developer and study platform for exploring the Quran through a public API, command-line interface, semantic search interface, and personal reading tracker.

The project is intended to be respectful, educational, source-transparent, and useful for developers, students, researchers, and personal study.

## Personal Note

I am not an Islamic scholar. This is a personal project with no commercial gain.

If I am doing anything wrong Islamically, please DM me directly so I can correct it.

## Planned Scope

- A clean REST API for Quran text, metadata, translations, search, bookmarks, notes, and reading progress.
- A CLI for terminal-based reading, exact search, semantic search, and progress tracking.
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

- `apps/cli` contains the initial Typer CLI scaffold with persisted config for remote API and local SQLite modes.
- `apps/web` contains the initial Next.js web app scaffold for QuranKit.
- `docs/frontend-architecture.md` documents the Arabic-inspired UI direction, route structure, and frontend component boundaries.
- `docs/cli.md` documents installation, config storage, and backend selection for the CLI scaffold.
- `CHANGELOG.md` tracks repository changes across the repository foundation, CLI scaffold, and frontend architecture.

## Development

Install dependencies:

```bash
npm ci
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
./scripts/run-cli-tests.sh
```

## Repository Layout

- `apps/cli`: Typer CLI package, config storage, backend selection, and CLI tests.
- `apps/web`: Next.js web app shell, pages, styling, and tests.
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
- [docs/release-readiness.md](docs/release-readiness.md)
