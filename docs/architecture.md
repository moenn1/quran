# QuranKit Architecture Direction

QuranKit is organized as a monorepo so the API, CLI, web UI, and data workflows can evolve independently while sharing one set of religious-safety, privacy, and attribution guardrails.

## Recommended Stack

- `apps/api`: FastAPI application for exact text, metadata, search, bookmarks, notes, reading progress, and semantic-search endpoints.
- `apps/cli`: Typer application for terminal reading, exact search, semantic search, and personal-study workflows.
- `apps/web`: Next.js application for browse, reader, search, semantic search, bookmarks, notes, and progress flows.
- `packages/database`: PostgreSQL schema, migrations, import helpers, and validation utilities.
- `packages/embeddings`: optional vector-search integration and embedding pipelines, with Qdrant as the current experimental direction.
- `packages/shared`: shared contracts, validators, and reusable utilities across surfaces.

## Data And Storage

- PostgreSQL is the primary source of truth for Quran metadata and private user state.
- Vector search is optional and must not replace exact search, attribution, or clear semantic-search disclaimers.
- Imported Quran content must be attributable, validated, and checksum-friendly before it is used by any application surface.

## Product Guardrails

- Preserve Quran text exactly from the selected upstream source.
- Semantic search must be labeled as textual similarity only, never as tafsir, fatwa, or scholarly interpretation.
- Bookmarks, notes, and reading progress remain private by default across API, CLI, and web surfaces.
- UI work should remain Arabic-aware, readable, RTL-safe, and respectful.

## Monorepo Boundaries

- `apps/*` own user-facing delivery surfaces.
- `packages/*` own reusable code, schema assets, and data plumbing.
- `docs/` defines public expectations, contracts, and release guardrails.
- `scripts/` remains the home for CI entry points and reproducible validation tasks.
- `data/` stores local or generated artifacts that are safe to keep in the repository.

## Recommended Delivery Sequence

1. Land the FastAPI service in `apps/api` with health, attribution, and exact-search fundamentals first.
2. Build shared PostgreSQL and validation assets in `packages/database` before importing Quran content.
3. Expand `apps/web` and `apps/cli` against shared contracts from `packages/shared`.
4. Add optional vector search through `packages/embeddings` only after exact search, attribution, and disclaimer flows are stable.
