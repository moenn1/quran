# QuranKit Frontend Architecture

## Intent

The web app should feel Arabic-inspired, classical, and respectful without drifting into decorative landing-page design. Quran text remains the visual center. Exact search and semantic search are intentionally separate experiences. Progress, bookmarks, plans, and notes are private by default.

## Current Foundation

The initial foundation lives in `apps/web` and establishes:

- A Next.js App Router structure for the public browse and study surfaces.
- A shared visual system in `src/app/globals.css` using parchment-toned surfaces, restrained geometric framing, accessible contrast, and a Tailwind utility layer for layout composition.
- Reusable presentation components for the shell, page hero, section cards, semantic disclaimer, and attributed reader preview.
- A routed explore flow in `/explore`, `/surah/[number]`, and `/ayah/[surah]/[ayah]` with bundled sample data, surah filtering, previous/next navigation, attribution-safe copy controls, and private-by-default study actions.
- Interactive `/search` and `/semantic` client surfaces with exact-match filtering, bundled result context, similarity-preview controls, optional scores, and private study actions that stay visibly separate from interpretation.
- Interactive `/progress`, `/plans`, `/bookmarks`, `/notes`, and `/settings` surfaces with local-first browser persistence, manual checkpoints, plan creation/recalculation, bookmark filtering, private note editing, export previews, and reader-default controls.
- A shared study-state provider in `src/components/study-state-provider.tsx` backed by `src/lib/study-data.ts`, so reader checkpoints, bookmarks, notes, plans, preferences, and export previews resolve against one private local model.
- A root app provider with TanStack Query defaults and an API client layer that can target the QuranKit HTTP service without changing the current local-first study model.
- The API client defaults to `http://localhost:8000` and reads `NEXT_PUBLIC_API_URL` when the web app is pointed at another QuranKit API deployment.
- Routed reader preference persistence so translation visibility, text-view defaults, and type scale changes survive refreshes and stay aligned with `/settings`.
- Vitest coverage for reader attribution, semantic-search guardrails, explore filtering, exact-search filters, reader controls, and the new progress, plans, bookmarks, notes, and settings flows.
- Playwright coverage for exact-search routing, semantic-search guardrails and bookmark persistence, reader-to-progress flows, axe accessibility checks, and responsive search/reader screenshots.

## Visual Direction

### Typography

- Quran text uses `Noto Naskh Arabic` with larger sizing and generous line height.
- English UI uses `Newsreader` to keep a classical manuscript rhythm without making the interface ornamental.
- Arabic content receives `lang="ar"` and `dir="rtl"` at the text block level, keeping mixed-language layouts stable.

### Color and surfaces

- Backgrounds use warm parchment tones rather than stark white.
- Accent color is teal-green for focus states and trusted actions.
- Warm bronze-brown is used sparingly for framing and ayah numbering.
- Ornament appears through borders, seals, and rhythm lines, not through heavy illustration.

### Motion and interaction

- Motion is limited to subtle rise-in transitions and hover elevation.
- `prefers-reduced-motion` is respected globally.
- Focus states are high-contrast and visible on all interactive elements.

## Route Architecture

- `/`: Browse surface and architecture summary.
- `/explore`: Surah browse route with search, revelation-place filtering, and direct reader entry points.
- `/surah/[number]`: Surah reader with translation visibility, text emphasis, font controls, attribution, and local study actions.
- `/ayah/[surah]/[ayah]`: Ayah detail route with immediate context and previous/next verse navigation.
- `/reader`: Compatibility redirect to `/explore` from the earlier scaffold route.
- `/search`: Exact search route with visible scope/revelation/surah filters, matched-field chips, and bundled before/after ayah context.
- `/semantic`: Similarity-preview route with limit, translation, scope, surah/juz filters, optional scores, and private bookmark/plan/copy actions.
- `/progress`: Private-by-default reading progress, manual checkpoints, streak summaries, active-plan targets, and progress-by-surah/juz rows.
- `/plans`: Reading-plan creation, active-plan switching, daily-target recalculation, and bundled-sample completion summaries.
- `/bookmarks`: Saved-reference collections with search, label filtering, Quran text previews, and direct note/reader links.
- `/notes`: Private linked notes with reference-prefill support from reader/search routes, editing, and delete flows.
- `/settings`: Reader preferences, source-attribution visibility, local-storage clarity, export previews, and deliberate local-data clearing.

## Component Boundaries

- `src/app/*`: Route entry points and page composition.
- `src/components/app-providers.tsx`: Root client provider for TanStack Query.
- `src/components/app-shell.tsx`: Shared shell with header, navigation, and footer safeguards.
- `src/components/site-navigation.tsx`: Small client island for active navigation state.
- `src/components/page-hero.tsx`: Route-level hero copy and pill metadata.
- `src/components/section-card.tsx` and `section-deck.tsx`: Reusable content grids for architecture pages.
- `src/components/explore-experience.tsx`: Client browse surface for bundled surah filtering and route entry points.
- `src/components/reader-workspace.tsx`: Client reader surface for translation toggles, text-view controls, font scaling, copy/bookmark/read actions, and attribution.
- `src/components/exact-search-experience.tsx`: Client exact-search surface for visible filters, lexical matches, and result context.
- `src/components/semantic-search-experience.tsx`: Client semantic-search surface for similarity-preview controls, optional scores, and private study actions.
- `src/components/study-state-provider.tsx`: Client study-state context backed by browser storage for checkpoints, bookmarks, notes, plans, activity, and reader preferences.
- `src/components/progress-experience.tsx`: Client progress dashboard for manual checkpoints, active-plan targets, and surah/juz completion rows.
- `src/components/plans-experience.tsx`: Client plan-management surface for creation, recalculation, activation, and plan-driven progress marking.
- `src/components/bookmarks-experience.tsx`: Client bookmark-management surface for filtering, Quran text previews, and direct study actions.
- `src/components/notes-experience.tsx`: Client note-management surface for prefilled references, note editing, and linked bookmark context.
- `src/components/settings-experience.tsx`: Client settings surface for reader defaults, export previews, motion preferences, and local-data clearing.
- `src/components/runtime-foundation.tsx`: Home-page status surface that exposes the current API base URL, query cache policy, and privacy-first study-state direction.
- `src/components/reader-preview.tsx`: Attributed Quran-text sample used to define reader spacing and hierarchy.
- `src/components/semantic-disclaimer.tsx`: Shared similarity-search guardrail copy.
- `src/lib/site-data.ts`: Central source for route metadata, card content, and the attributed preview ayat.
- `src/lib/reader-data.ts`: Bundled routed surah sample plus helpers for context windows and adjacent route navigation.
- `src/lib/search-data.ts`: Bundled exact-search and semantic-preview helpers, filter options, and result scoring utilities.
- `src/lib/study-data.ts`: Browser-local study-state schema, progress helpers, bundled reference options, export payload builders, and plan/progress derivation.
- `src/lib/api/*`: Shared API client and query-client setup for live data integration.

## Data and State Direction

- Server components should remain the default for read-heavy views.
- Small client islands are acceptable for navigation state, future reader preferences, interactive study tools, and TanStack Query-backed state that benefits from client-side caching.
- Progress, bookmarks, notes, and plans should default to local persistence first.
- Browser-local study state currently lives under `qurankit.study-state.v1` and includes both the core study document and web-only local metadata such as completed-reference history, activity summaries, and reader defaults.
- Remote sync should remain opt-in and clearly explained when introduced.
- API transport details should stay centralized in the shared client layer so route components do not hand-roll fetch logic.
- Whenever Quran text or translations appear, attribution should remain attached to the visible surface.

## Search Safety Rules

- Exact search must never silently behave like semantic search.
- Semantic search must use language like `similarity-based` or `related passages`, not interpretive claims.
- Semantic results must never be presented as tafsir, fatwa, or rulings.
- Similarity scores are supportive preview cues only and should remain optional in the interface.
- Reader context should be one clear action away from every search result.

## Sample Quran Text

The current routed reader sample uses small bundled excerpts with visible attribution:

- Arabic text: Quran.com API, Uthmani script
- English translation: Saheeh International via AlQuran.Cloud

This sample powers the current `/explore`, `/surah/[number]`, and `/ayah/[surah]/[ayah]` routes while QuranKit's broader validated reading corpus is being wired into the web app.

## Next Steps

1. Replace the bundled sample in `src/lib/reader-data.ts` with real reader data adapters for remote API mode and local SQLite mode.
2. Map the browser-local study-state model onto the future authenticated `/api/v1/me/study` document without losing privacy cues, export boundaries, or reader-preference clarity.
3. Expand private study actions from the reader into the exact-search and semantic-search result cards wherever those actions materially improve the workflow.
4. Expand the browse and reader routes from the bundled sample to the broader validated QuranKit corpus.
5. Expand the current Playwright coverage from bundled sample routes to future live-data reader, search, and authenticated sync flows without weakening the privacy and attribution guardrails already under test.
