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
- Document upstream data sources, versioning, and validation rules before importing Quran data.
- Keep API, CLI, and web documentation explicit about the difference between exact search and semantic search.

## UI Review Expectations

- Prefer elegant, classical, Arabic-inspired presentation with restrained ornament.
- Keep Quran text readable, RTL-safe, and accessible on desktop and mobile.
- Avoid decorative choices that make Quran text harder to read or imply false authority.

## Release Checklist

- Verify upstream source provenance and attribution before shipping Quran data.
- Verify that privacy defaults for bookmarks, notes, and reading progress are still private.
- Verify that semantic-search copy remains descriptive and not interpretive.
- Verify that API, CLI, and web surfaces communicate limitations clearly.
- Verify that no changes normalize, rewrite, or otherwise alter Quran text.
