# Release Readiness

QuranKit should not be tagged or promoted without passing the following checks.

## Required

- `./scripts/release-readiness.sh`
- `./scripts/smoke-cli.sh`
- `./scripts/smoke-compose.sh`
- Updated `CHANGELOG.md`
- Updated repository docs for any changed guarantees, setup, or guardrails
- Updated source-evaluation and attribution docs when data inputs change
- Verified Docker Compose configuration
- Verified religious-safety and privacy guardrails

## Review Questions

- Does the release preserve Quran text exactly from its source?
- Is source attribution present and documented?
- Are semantic-search features clearly labeled as textual similarity only?
- Are bookmarks, notes, and reading progress private by default?
- Are README, API notes, CLI notes, and self-hosting docs consistent?

## GitHub Actions

- `Quality` runs on pull requests and pushes to `main`.
- `Release Readiness` can be triggered manually before a release cut.
