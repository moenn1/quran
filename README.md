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

- `compose.yaml` provisions PostgreSQL, a bootstrap API container, a bootstrap web container, and an optional Qdrant profile for semantic-search experiments.
- `docker/` contains the bootstrap API and web images used to validate self-hosting before the production API, CLI, and web applications land.
- `.github/workflows/quality.yml` and `.github/workflows/release-readiness.yml` enforce documentation, safety, repository-test, and Docker checks.
- `docs/` captures self-hosting, testing, religious-safety, API, CLI, and release-readiness guardrails.

## Quick Start

1. Copy `.env.example` to `.env`.
2. Review `.env.api.example`, `.env.web.example`, and `.env.cli.example` for service-specific overrides.
3. Set `COMPOSE_PROFILES=semantic-search` in `.env` if you want the optional Qdrant service.
4. Run `docker compose up --build`.
5. Visit `http://localhost:3000` for the bootstrap web surface and `http://localhost:8000/health` for the bootstrap API health check.
6. Run `./scripts/release-readiness.sh` before pushing repository-quality changes.

## Repository Layout

- `.github/workflows`: GitHub Actions for quality and release-readiness gates.
- `docker/`: Bootstrap API and web container assets for local self-hosting.
- `docs/`: Self-hosting, testing, safety, API, CLI, and release-readiness documentation.
- `scripts/`: Repository-quality, test, and smoke-check entry points.

## Documentation

- [CONTRIBUTING.md](CONTRIBUTING.md)
- [CHANGELOG.md](CHANGELOG.md)
- [docs/self-hosting.md](docs/self-hosting.md)
- [docs/testing.md](docs/testing.md)
- [docs/religious-safety.md](docs/religious-safety.md)
- [docs/api.md](docs/api.md)
- [docs/cli.md](docs/cli.md)
- [docs/release-readiness.md](docs/release-readiness.md)
