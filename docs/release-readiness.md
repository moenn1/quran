# Release Readiness

QuranKit should not be tagged or promoted without passing the following checks.

## Required

- `./scripts/release-readiness.sh`
- `./scripts/smoke-cli.sh`
- `./scripts/smoke-compose.sh`
- Reviewed `docs/release-safety-checklist.md`
- Reviewed `docs/release-demo.md`, `docs/roadmap.md`, and `docs/release-process.md`
- Updated `CHANGELOG.md`
- Updated repository docs for any changed guarantees, setup, or guardrails
- Refreshed `docs/screenshots/` with `./scripts/export-release-screenshots.sh` when web visuals changed
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
- Does the release demo clearly distinguish the bootstrap Compose stack from the database-backed `apps/api` service and live `http://127.0.0.1:8000/docs` API docs?
- If no public hosted demo exists, do the release notes point people to local demo or self-hosting docs instead of implying a public preview?
- Are README, release demo notes, roadmap, API notes, CLI notes, self-hosting docs, and the release-safety checklist consistent?

## GitHub Actions

- `Quality` runs on pull requests and pushes to `main`, and its test job provisions `apps/api[dev]` plus the Chromium browser runtime before data validation and Playwright-backed checks.
- `Release Readiness` can be triggered manually before a release cut, and it provisions `apps/api[dev]` plus the Chromium browser runtime before `./scripts/release-readiness.sh`.
