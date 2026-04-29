# Changelog

All notable changes to QuranKit will be documented in this file.

The format is based on Keep a Changelog, and this project follows Semantic Versioning once versioned releases begin.

## [Unreleased]

### Added

- Added the first `apps/cli` Typer package scaffold with persisted configuration, remote API and local SQLite backend selection, and initial `qurankit config show/set` commands.
- Bootstrapped the `apps/web` Next.js frontend foundation with Arabic-inspired theme tokens, shared layout components, and route scaffolding for browse, reader, search, semantic search, progress, plans, bookmarks, notes, and settings.
- Added an attributed Quran reader preview using a small sample from AlQuran.Cloud and a shared semantic-search disclaimer that keeps similarity search clearly separated from tafsir, fatwa, and religious rulings.
- Added `docs/frontend-architecture.md`, a public npm registry config for reproducible installs, and Vitest coverage for route architecture, reader attribution, and semantic-search guardrails.
- Added an upstream Quran database evaluation, attribution plan, reproducible SQL dump analyzer, summary artifact, and pytest coverage for QuranKit's data foundation.
- Added repository governance and contributor workflow docs for README, contributing, code of conduct, license, and changelog management.
- Added self-hosting bootstrap assets with Docker Compose, backend/frontend Dockerfiles, environment examples, and a smoke test that exercises the running stack.
- Added release-quality and safety documentation for religious guardrails, privacy defaults, testing strategy, API expectations, CLI expectations, database source evaluation, and release readiness.
- Added GitHub Actions and local scripts for documentation checks, linting, frontend quality checks, data validation, Docker validation, and release-readiness checks.
