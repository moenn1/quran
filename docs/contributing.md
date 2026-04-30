# QuranKit Contributor Docs Map

This document complements the repository-root [CONTRIBUTING.md](../CONTRIBUTING.md). The root file is the main contributor entry point; this page maps which QuranKit docs should move together when a feature changes.

## When To Update Which Docs

- API contract changes:
  Update `docs/api.md`, and also `docs/semantic-search.md` or `docs/reading-tracker.md` when those surfaces are affected.
- CLI behavior changes:
  Update `docs/cli.md`, plus the narrower semantic-search or reading-tracker docs when the change is feature-specific.
- Data-source or schema changes:
  Update `docs/database.md`, any attribution notes, and `README.md` when project guarantees change.
- Docker, environment, or self-hosting changes:
  Update `docs/self-hosting.md`, `README.md`, and release-readiness notes together.
- Release demo, screenshots, roadmap, or tagging changes:
  Update `docs/release-demo.md`, `docs/roadmap.md`, `docs/release-process.md`, `README.md`, and `CHANGELOG.md` together.
- Religious-safety or privacy review criteria changes:
  Update `docs/religious-safety.md`, `docs/release-safety-checklist.md`, and any affected API, CLI, semantic-search, or reading-tracker docs together.
- Contributor workflow changes:
  Update both `CONTRIBUTING.md` and this file so the root entry point and the docs map stay aligned.

## Documentation Checklist

- Keep repository-facing wording focused on QuranKit.
- Preserve the maintainer note in `README.md`.
- Keep the semantic-search disclaimer consistent across docs and UI copy.
- Keep privacy defaults consistent across API, CLI, reading-tracker, and self-hosting docs.
- Keep source-attribution rules consistent across database, API, CLI, and export docs.
- Keep the release-safety checklist aligned with the README note, privacy wording, and semantic-search guardrails.

## Validation Workflow

Run the docs guardrails before pushing documentation changes:

```bash
./scripts/check-docs.sh
./scripts/release-readiness.sh
```

Use narrower checks too when relevant:

```bash
./scripts/run-cli-tests.sh
./scripts/smoke-cli.sh
./scripts/run-data-validation.sh
```

## Practical Ownership Guide

- If a change affects command names, flags, or output wording, the CLI docs are incomplete until examples are updated.
- If a change affects privacy defaults or authenticated study state, the reading-tracker docs are incomplete until local and remote behavior are both described.
- If a change affects search semantics or ranking copy, the semantic-search docs are incomplete until the disclaimer and self-hosting implications are updated.
- If a change affects source provenance, edition review, or normalization rules, the database docs are incomplete until attribution and validation notes are updated.
- If a change affects release demos, screenshot assets, or tag instructions, the release-demo, roadmap, and release-process docs are incomplete until the README and changelog point at the same story.
