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
