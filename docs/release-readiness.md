# Release Readiness

QuranKit should not be tagged or promoted without passing the following checks.

## Required

- `./scripts/release-readiness.sh`
- `./scripts/smoke-cli.sh`
- `./scripts/smoke-compose.sh`
- Reviewed `docs/release-safety-checklist.md`
- Updated `CHANGELOG.md`
- Updated repository docs for any changed guarantees, setup, or guardrails
- Updated `docs/api.md`, `docs/cli.md`, `docs/semantic-search.md`, and `docs/reading-tracker.md` when their contracts or wording changed
- Updated source-evaluation and attribution docs when data inputs change
- Verified Docker Compose configuration
- Verified religious-safety and privacy guardrails

## Review Questions

- Does the release preserve Quran text exactly from its source?
- Is source attribution present and documented?
- Are semantic-search features clearly labeled as textual similarity only?
- Are bookmarks, notes, and reading progress private by default?
- Are private study export and delete or removal affordances still clear where the surface supports them?
- Does release-facing copy preserve the README note and avoid commercial framing?
- Do the API and CLI docs clearly distinguish the bootstrap stack from the future production contract?
- Are README, API notes, CLI notes, self-hosting docs, and the release-safety checklist consistent?

## GitHub Actions

- `Quality` runs on pull requests and pushes to `main`.
- `Release Readiness` can be triggered manually before a release cut.
