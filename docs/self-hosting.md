# Self-Hosting QuranKit

QuranKit now includes a bootstrap self-hosting path so infrastructure, privacy defaults, and contributor workflows can be exercised before the full application surfaces land.

## Requirements

- Docker Engine
- Docker Compose v2

## Quick Start

1. Copy `.env.example` to `.env`.
2. Review `.env.api.example` and `.env.web.example` if you want service-specific overrides.
3. Run `docker compose up --build`.
4. Open `http://localhost:3000` for the bootstrap web surface.
5. Call `http://localhost:8000/health` for the bootstrap API health check.
6. Run `./scripts/smoke-compose.sh` when you want a scripted self-hosting verification pass. The smoke test uses an isolated Compose project and high host ports so it does not interfere with a normal local stack.

## Services

- `db`: PostgreSQL 16 for QuranKit data, bookmarks, notes, and reading progress.
- `api`: Bootstrap API container with health and metadata endpoints.
- `web`: Bootstrap web container that communicates the current project state and safety guarantees.
- `qdrant`: Optional semantic-search profile for future vector indexing experiments. Start it with `docker compose --profile semantic-search up --build`.

## Environment Files

- `.env.example`: shared Compose defaults for ports, database credentials, privacy mode, and semantic-search toggles.
- `.env.api.example`: API-specific defaults, including attribution and semantic-search warning text.
- `.env.web.example`: web-specific defaults, including API base URL and privacy notice text.

## Persistence and Privacy

- PostgreSQL data persists in the `postgres-data` Docker volume.
- Qdrant data persists in the `qdrant-data` Docker volume when the semantic-search profile is enabled.
- Bookmarks, notes, and reading progress must remain private by default. Do not expose those records publicly in Docker defaults or sample deployments.
- Semantic search must remain opt-in and clearly labeled as textual similarity, not tafsir, fatwa, or religious ruling.

## Bootstrap Limitations

- The current `api` and `web` containers are bootstrap services that prove the self-hosting path and surface the project guardrails.
- They are intentionally minimal and should be replaced with the production API and web applications as those codebases land.
- The bootstrap stack does not ship Quran data yet. Data import and validation must be added only after source attribution and integrity checks are in place.
