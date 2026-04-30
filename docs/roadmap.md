# QuranKit Roadmap

This roadmap keeps the v1 release scope practical and aligned with QuranKit's current foundations. It is a sequencing guide, not a fixed-date promise.

## v1 Release Line

- Ship the database-backed API, CLI, and web reader/search surfaces with coherent docs, screenshots, release checks, and self-hosting guidance.
- Keep exact-source Quran text preservation, source attribution, semantic-search disclaimers, and private-by-default study-state rules visible across API, CLI, web, and release docs.
- Publish a clear demo path, changelog summary, and annotated tag workflow for the first public release.

## Next

- Replace the bootstrap Compose web and API containers with a documented deployment path for the production `apps/web` and `apps/api` services.
- Harden authenticated study-state flows, export routes, migration steps, and seed-data setup for real self-hosted installs.
- Expand the web experience to use live API data end to end, including authenticated private study sync where that improves privacy-preserving self-hosting.

## Later

- Offer hosted previews only after the environment has explicit privacy review, attribution review, and a safe posture for private user data.
- Expand semantic-search infrastructure beyond the current deterministic baseline while keeping the textual-similarity disclaimer unchanged.
- Add richer release automation, packaged CLI distribution, and better operator observability for self-hosted QuranKit deployments.
