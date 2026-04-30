# QuranKit Frontend Architecture

## Intent

The web app should feel Arabic-inspired, classical, and respectful without drifting into decorative landing-page design. Quran text remains the visual center. Exact search and semantic search are intentionally separate experiences. Progress, bookmarks, plans, and notes are private by default.

## Current Foundation

The initial foundation lives in `apps/web` and establishes:

- A Next.js App Router structure for the public browse and study surfaces.
- A shared visual system in `src/app/globals.css` using parchment-toned surfaces, restrained geometric framing, accessible contrast, and a Tailwind utility layer for layout composition.
- Reusable presentation components for the shell, page hero, section cards, semantic disclaimer, and attributed reader preview.
- A routed explore flow in `/explore`, `/surah/[number]`, and `/ayah/[surah]/[ayah]` with bundled sample data, surah filtering, previous/next navigation, attribution-safe copy controls, and private-by-default study actions.
- A root app provider with TanStack Query defaults and an API client layer that can target the QuranKit HTTP service without changing the current local-first study model.
- The API client defaults to `http://localhost:8000` and reads `NEXT_PUBLIC_API_URL` when the web app is pointed at another QuranKit API deployment.
- Route foundations for `/`, `/explore`, `/surah/[number]`, `/ayah/[surah]/[ayah]`, `/reader`, `/search`, `/semantic`, `/progress`, `/plans`, `/bookmarks`, `/notes`, and `/settings`.
- Initial Vitest coverage for reader attribution, semantic-search guardrails, route architecture data, explore filtering, bundled reader navigation, reader controls, API client setup, and the runtime foundation panel.

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
- `/search`: Exact search structure with transparent filters and explainable matches.
- `/semantic`: Similarity-based search guidance and guardrails.
- `/progress`: Private-by-default reading progress architecture.
- `/plans`: Reading-plan cadence and checkpoint model.
- `/bookmarks`: Saved-reference collections with context.
- `/notes`: Private linked notes and export boundaries.
- `/settings`: Reader preferences, translation/source choices, and storage-mode clarity.

## Component Boundaries

- `src/app/*`: Route entry points and page composition.
- `src/components/app-providers.tsx`: Root client provider for TanStack Query.
- `src/components/app-shell.tsx`: Shared shell with header, navigation, and footer safeguards.
- `src/components/site-navigation.tsx`: Small client island for active navigation state.
- `src/components/page-hero.tsx`: Route-level hero copy and pill metadata.
- `src/components/section-card.tsx` and `section-deck.tsx`: Reusable content grids for architecture pages.
- `src/components/explore-experience.tsx`: Client browse surface for bundled surah filtering and route entry points.
- `src/components/reader-workspace.tsx`: Client reader surface for translation toggles, text-view controls, font scaling, copy/bookmark/read actions, and attribution.
- `src/components/runtime-foundation.tsx`: Home-page status surface that exposes the current API base URL, query cache policy, and privacy-first study-state direction.
- `src/components/reader-preview.tsx`: Attributed Quran-text sample used to define reader spacing and hierarchy.
- `src/components/semantic-disclaimer.tsx`: Shared similarity-search guardrail copy.
- `src/lib/site-data.ts`: Central source for route metadata, card content, and the attributed preview ayat.
- `src/lib/reader-data.ts`: Bundled routed surah sample plus helpers for context windows and adjacent route navigation.
- `src/lib/api/*`: Shared API client and query-client setup for live data integration.

## Data and State Direction

- Server components should remain the default for read-heavy views.
- Small client islands are acceptable for navigation state, future reader preferences, interactive study tools, and TanStack Query-backed state that benefits from client-side caching.
- Progress, bookmarks, notes, and plans should default to local persistence first.
- Remote sync should remain opt-in and clearly explained when introduced.
- API transport details should stay centralized in the shared client layer so route components do not hand-roll fetch logic.
- Whenever Quran text or translations appear, attribution should remain attached to the visible surface.

## Search Safety Rules

- Exact search must never silently behave like semantic search.
- Semantic search must use language like `similarity-based` or `related passages`, not interpretive claims.
- Semantic results must never be presented as tafsir, fatwa, or rulings.
- Reader context should be one clear action away from every search result.

## Sample Quran Text

The current routed reader sample uses small bundled excerpts with visible attribution:

- Arabic text: Quran.com API, Uthmani script
- English translation: Saheeh International via AlQuran.Cloud

This sample powers the current `/explore`, `/surah/[number]`, and `/ayah/[surah]/[ayah]` routes while QuranKit's broader validated reading corpus is being wired into the web app.

## Next Steps

1. Replace the bundled sample in `src/lib/reader-data.ts` with real reader data adapters for remote API mode and local SQLite mode.
2. Introduce local persistence helpers for progress, bookmarks, notes, and plan state so the reader actions survive refreshes.
3. Expand the browse and reader routes from the bundled sample to the broader validated QuranKit corpus.
4. Add route-level accessibility and visual regression coverage once richer live-data interactions land.
