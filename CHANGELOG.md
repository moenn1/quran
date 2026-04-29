# Changelog

All notable changes to QuranKit will be documented in this file.

The format is based on Keep a Changelog, and this project follows Semantic Versioning once versioned releases begin.

## [Unreleased]

### Added

- Added a bootstrap self-hosting stack with Docker Compose, PostgreSQL, an optional Qdrant profile, a bootstrap API container, and a bootstrap web container.
- Added shared, API, web, and CLI environment examples so contributors can keep privacy defaults, attribution requirements, and semantic-search wording consistent across surfaces.
- Added repository governance and release-quality docs for contributing, code of conduct, license, self-hosting, testing, religious safety, API notes, CLI notes, and release readiness.
- Added GitHub Actions and local scripts for documentation checks, repository tests, backend/frontend/CLI/data/E2E entry points, Docker validation, and self-hosting smoke checks.
- Added repository-level tests that verify the bootstrap API guardrails and the required self-hosting assets.
