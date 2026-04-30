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

## Backend Development

The first QuranKit API scaffold now lives in `apps/api`.

Run it locally:

```bash
cd apps/api
python3 -m venv .venv
. .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
uvicorn qurankit_api.main:app --reload
```

Key endpoints:

- `GET /`
- `GET /api/v1/health`
- `GET /docs`
- `GET /openapi.json`

Run backend tests from the repository root:

```bash
./scripts/run-backend-tests.sh
```

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

The current schema foundation includes:

- source provenance tables for upstream release and artifact metadata
- canonical `surahs`, `ayahs`, `translations`, and `ayah_translations` tables
- private-by-default tables for reading sessions, progress, plans, bookmarks, and notes
- semantic embedding metadata records that target either an ayah or a translation row

The data pipeline now:

- validates the locked upstream dump for 114 surahs, 6236 ayahs, sequential global ayah numbers, per-surah sequencing, metadata ranges, and full edition coverage
- preserves exact sourced Quran text, including the upstream BOM artifact on the first ayah, while recording source checksums and dump metadata
- loads normalized QuranKit tables and emits SQLite, JSON, and PostgreSQL seed artifacts from the same locked source snapshot

Additional backend notes live in [docs/api.md](docs/api.md), [docs/database.md](docs/database.md), and [docs/testing.md](docs/testing.md).
