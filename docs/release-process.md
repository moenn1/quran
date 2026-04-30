# QuranKit Release Process

Use this process when cutting the first public tag or any later QuranKit release.

## Before You Tag

1. Confirm the repo-local Git identity:

   ```bash
   git config user.name "Mohamed En-Nassibi"
   git config user.email "mohamed.enn2001@gmail.com"
   ```

2. Update `CHANGELOG.md`, `README.md`, `docs/release-demo.md`, `docs/roadmap.md`, and any affected feature docs.
3. Refresh the release screenshots when web visuals changed:

   ```bash
   npm run test:e2e:update --workspace @qurankit/web
   ./scripts/export-release-screenshots.sh
   ```

4. Review `docs/release-safety-checklist.md`.
5. Run the full release gate:

   ```bash
   ./scripts/release-readiness.sh
   ```

Do not tag if any release-readiness step is failing.

## Merge To Main

Merge the release-preparation branch into `main` before tagging so the tag always points at the reviewed mainline commit.

```bash
git fetch origin
git switch main
git pull --ff-only
git merge --ff-only <release-branch>
git push origin main
```

If fast-forward merge is not possible, resolve the branch first and rerun the release checks before pushing `main`.

## Create The Tag

Create an annotated Semantic Version tag on the pushed `main` commit:

```bash
git tag -a v1.0.0 -m "QuranKit v1.0.0"
git push origin v1.0.0
```

Use annotated tags for QuranKit releases so the version history carries the release message and can be audited later.

## Publish The GitHub Release

- Title the release `QuranKit v1.0.0`.
- Copy the user-facing summary from `CHANGELOG.md`.
- Link the demo guide, roadmap, self-hosting guide, and API docs overview:
  - `docs/release-demo.md`
  - `docs/roadmap.md`
  - `docs/self-hosting.md`
  - `docs/api.md`
- If no public hosted demo exists yet, say that directly and point people to the local demo or self-hosting docs instead.
- Include the current release screenshots or GIFs when they help explain the web experience.

## After Publish

- Verify the `main` branch and the tag both exist on GitHub.
- Confirm the `Quality` workflow passed on the tagged commit's `main` push.
- Check that the README maintainer note, semantic-search disclaimer, and privacy wording still match the release notes.
