# QuranKit Privacy and Religious-Safety Release Checklist

Use this checklist before tagging a release, merging release-quality work into `main`, or marking a privacy or religious-safety issue done. Any unchecked item is a release blocker.

## Quran Text and Attribution

- [ ] Quran text shown in API, CLI, web, and exports still matches the validated source exactly.
- [ ] Quran source attribution is visible or preserved wherever Quran text is returned, copied, cached, or exported.
- [ ] Translation attribution remains visible or preserved whenever translation text is shown or exported.
- [ ] Upstream snapshot, edition review notes, and known rights gaps are still documented before any new data input is enabled.

## Search Claims and Religious Wording

- [ ] Exact search and semantic search remain separate in commands, routes, filters, docs, and UI labels.
- [ ] Semantic search copy still says "Related passages by textual similarity only" and never describes results as tafsir, fatwa, religious ruling, or scholarly authority.
- [ ] Similarity reasons, previews, and scores stay mechanical; they do not explain what an ayah means or what a reader should believe or do.

## Privacy and Study-State Controls

- [ ] Reading progress, bookmarks, notes, and plans remain private by default across CLI, web, API docs, self-hosting defaults, and sample deployments.
- [ ] No public or unauthenticated surface exposes another user's study state.
- [ ] Export surfaces for private study data are clearly described as user-controlled data movement, not public sharing or default sync.
- [ ] Where a private-study surface supports deletion or removal, the affordance remains visible and documented. If a surface lacks deletion today, the limitation is called out before release.
- [ ] Private by default does not mean encrypted; local storage caveats remain documented anywhere private study data is stored or exported.

## Project Framing

- [ ] The README personal note still says the maintainer is not an Islamic scholar, the project has no commercial gain, and people should DM directly for Islamic corrections.
- [ ] Release notes, README copy, web metadata, and docs avoid commercial framing such as pricing, subscriptions, customers, growth, monetization, or product claims.
- [ ] UI copy stays respectful and does not imply QuranKit replaces scholarship, tafsir, or pastoral guidance.

## Surfaces To Review

- `README.md`
- `docs/religious-safety.md`
- `docs/release-readiness.md`
- `docs/api.md`
- `docs/cli.md`
- `docs/semantic-search.md`
- `docs/reading-tracker.md`
- `docs/self-hosting.md`

## Verification Commands

- `./scripts/check-docs.sh`
- `./scripts/run-cli-tests.sh`
- `./scripts/smoke-cli.sh`
- `./scripts/release-readiness.sh`
