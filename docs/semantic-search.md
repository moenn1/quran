# QuranKit Semantic Search

Semantic search in QuranKit is a discovery aid for related passages. It must always be described as textual similarity only, never as tafsir, fatwa, or scholarly interpretation.

## Current Surface Area

- CLI command: `qurankit semantic ...`
- Planned API route: `GET /api/v1/search/semantic`
- Web route scaffold: `apps/web/src/app/semantic/page.tsx`
- Optional self-hosting infrastructure path: `docker compose --profile semantic-search up --build`

Today, the repository's Compose stack only provisions an optional Qdrant profile and a bootstrap API. It does not ship a live semantic-search service yet.

## Guardrails

- Keep exact search and semantic search on separate routes, commands, and labels.
- Always show a disclaimer in user-facing semantic-search output.
- Preserve source attribution for any Quran text or translation text shown with results.
- Do not imply religious authority, correctness ranking, or interpretive intent.
- Do not present similarity matches as answers to fiqh, creed, or fatwa questions.

## User-Facing Wording

The current CLI baseline uses wording like this:

```text
Related passages by textual similarity for "guide path"
Related passages are ranked by textual similarity only. They are not tafsir, fatwa, or religious rulings.
```

That wording should stay stable across the CLI, API payloads, docs, and web UI.

## Current Local CLI Baseline

In local SQLite mode, QuranKit currently computes related passages with textual-overlap heuristics over the Arabic text and the selected translation:

- token overlap
- near-token matching
- a small `SequenceMatcher` ratio boost

That baseline is intentionally simple. It is useful for repository bootstrapping, but it should not be marketed as deep semantic understanding.

## API Contract Shape

Illustrative request:

```http
GET /api/v1/search/semantic?q=guide+path&translation=en.sahih&limit=5
Accept: application/json
```

Illustrative response:

```json
{
  "query": "guide path",
  "match_type": "semantic_similarity",
  "count": 2,
  "disclaimer": "Related passages are ranked by textual similarity only. They are not tafsir, fatwa, or religious rulings.",
  "results": [
    {
      "ayah": {
        "reference": "1:6",
        "surah_number": 1,
        "ayah_number": 6,
        "arabic_text": "<source-preserved ayah text>",
        "translation_text": "<selected translation text>"
      },
      "similarity_score": 0.842,
      "reason": "Shared terms in the selected text: guide, path."
    }
  ]
}
```

The `reason` field should stay descriptive and mechanical. It should explain why the result matched, not what the ayah means.

## Self-Hosting Path

- Keep semantic search opt-in in self-hosted setups.
- The repository already reserves `QURANKIT_ENABLE_SEMANTIC_SEARCH=false` in `.env.example`.
- The API bootstrap environment includes `QURANKIT_SEMANTIC_SEARCH_DISCLAIMER` in `.env.api.example`.
- Use `docker compose --profile semantic-search up --build` only when testing the future vector-search path.

If semantic-search infrastructure is disabled, the UI and docs should say so plainly instead of silently falling back to misleading copy.

## Attribution and Data Rules

- Only index Quran text and reviewed editions whose attribution and reuse posture are documented.
- Keep the upstream source snapshot and edition metadata linked to any served result.
- If translations are indexed, the served response must still identify which translation was searched or displayed.
- Do not detach semantic-search results from their source attribution during exports or caching.

## Limitations Before Release

- The current bootstrap stack does not provide live semantic-search HTTP endpoints.
- Ranking quality may change as the implementation moves from local heuristics to optional vector search.
- Similarity scores are relative ranking aids, not truth scores.
- Semantic search is textual similarity only; it must never be described as interpretation, explanation, or religious ruling.
