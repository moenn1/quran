# QuranKit Frontend Architecture

## Intent

The web app should feel Arabic-inspired, classical, and respectful without drifting into decorative landing-page design. Quran text remains the visual center. Exact search and semantic search are intentionally separate experiences. Progress, bookmarks, plans, and notes are private by default.

## Current Foundation

The initial foundation lives in `apps/web` and establishes:

- A Next.js App Router structure for the public browse and study surfaces.
- A shared visual system in `src/app/globals.css` using parchment-toned surfaces, restrained geometric framing, and accessible contrast.
- Reusable presentation components for the shell, page hero, section cards, semantic disclaimer, and attributed reader preview.
- Route foundations for `/`, `/reader`, `/search`, `/semantic`, `/progress`, `/plans`, `/bookmarks`, `/notes`, and `/settings`.
- Initial Vitest coverage for reader attribution, semantic-search guardrails, and route architecture data.

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
- `/reader`: Reader-focused layout, attribution treatment, and Quran-text hierarchy.
- `/search`: Exact search structure with transparent filters and explainable matches.
- `/semantic`: Similarity-based search guidance and guardrails.
- `/progress`: Private-by-default reading progress architecture.
- `/plans`: Reading-plan cadence and checkpoint model.
- `/bookmarks`: Saved-reference collections with context.
- `/notes`: Private linked notes and export boundaries.
- `/settings`: Reader preferences, translation/source choices, and storage-mode clarity.

## Component Boundaries

- `src/app/*`: Route entry points and page composition.
- `src/components/app-shell.tsx`: Shared shell with header, navigation, and footer safeguards.
- `src/components/site-navigation.tsx`: Small client island for active navigation state.
- `src/components/page-hero.tsx`: Route-level hero copy and pill metadata.
- `src/components/section-card.tsx` and `section-deck.tsx`: Reusable content grids for architecture pages.
- `src/components/reader-preview.tsx`: Attributed Quran-text sample used to define reader spacing and hierarchy.
- `src/components/semantic-disclaimer.tsx`: Shared similarity-search guardrail copy.
- `src/lib/site-data.ts`: Central source for route metadata, card content, and the attributed preview ayat.

## Data and State Direction

- Server components should remain the default for read-heavy views.
- Small client islands are acceptable for navigation state, future reader preferences, and interactive study tools.
- Progress, bookmarks, notes, and plans should default to local persistence first.
- Remote sync should remain opt-in and clearly explained when introduced.
- Whenever Quran text or translations appear, attribution should remain attached to the visible surface.

## Search Safety Rules

- Exact search must never silently behave like semantic search.
- Semantic search must use language like `similarity-based` or `related passages`, not interpretive claims.
- Semantic results must never be presented as tafsir, fatwa, or rulings.
- Reader context should be one clear action away from every search result.

## Sample Quran Text

The current reader preview uses a small attributed sample from AlQuran.Cloud:

- Arabic text: Uthmani edition
- English translation: Mohammed Marmaduke William Pickthall

This is only for layout and attribution treatment until QuranKit's validated data pipeline is wired into the reader.

## Next Steps

1. Add real reader data adapters for remote API mode and local SQLite mode.
2. Introduce local persistence helpers for progress, bookmarks, notes, and plan state.
3. Replace architecture-copy cards with live reader, search, and study interactions.
4. Add route-level accessibility and visual regression coverage once interactive flows land.
