# Religious Safety and Privacy Guardrails

These rules are release blockers for QuranKit.

## Non-Negotiables

- Do not alter Quran text.
- Preserve source attribution for Quran text, translations, metadata, and exports.
- Semantic search is textual similarity, not tafsir, fatwa, or religious ruling.
- Do not present generated or retrieved output as scholarly authority.
- Bookmarks, notes, and reading progress must be private by default.

## Documentation Requirements

- Keep the README maintainer note intact: the maintainer is not an Islamic scholar, the project has no commercial gain, and Islamic mistakes should be reported directly so they can be corrected.
- Keep release-facing copy non-commercial. Do not add pricing, subscriptions, customer language, or monetization framing.
- Document upstream data sources, versioning, and validation rules before importing Quran data.
- Keep API, CLI, and web documentation explicit about the difference between exact search and semantic search.

## UI Review Expectations

- Prefer elegant, classical, Arabic-inspired presentation with restrained ornament.
- Keep Quran text readable, RTL-safe, and accessible on desktop and mobile.
- Avoid decorative choices that make Quran text harder to read or imply false authority.

## Release Checklist

Use [docs/release-safety-checklist.md](release-safety-checklist.md) before tagging a release or marking a privacy or religious-safety issue done.

- Every unchecked item in that checklist is a release blocker.
- The checklist must stay aligned with README wording, export/delete affordances, semantic-search disclaimers, and private-by-default study-state behavior.
