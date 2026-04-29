export type CardTone = "neutral" | "accent" | "warm";

export type ContentCard = {
  title: string;
  description: string;
  items?: string[];
  footer?: string;
  href?: string;
  linkLabel?: string;
  tone?: CardTone;
};

export const navigationItems = [
  { href: "/", label: "Browse" },
  { href: "/reader", label: "Reader" },
  { href: "/search", label: "Exact Search" },
  { href: "/semantic", label: "Semantic Search" },
  { href: "/progress", label: "Progress" },
  { href: "/plans", label: "Plans" },
  { href: "/bookmarks", label: "Bookmarks" },
  { href: "/notes", label: "Notes" },
  { href: "/settings", label: "Settings" },
] as const;

export const heroPills = {
  home: [
    "Arabic-first reader",
    "Private study data by default",
    "Similarity-based semantic search",
  ],
  reader: [
    "Quran text stays primary",
    "RTL-safe typography",
    "Source attribution always visible",
  ],
  search: [
    "Exact match workflows",
    "Clear filters and scope",
    "Explainable results",
  ],
  semantic: [
    "Similarity-based exploration",
    "Not tafsir or fatwa",
    "Guardrails in the interface",
  ],
  progress: [
    "Local-first tracking",
    "Quiet reminders",
    "Private by default",
  ],
  plans: [
    "Flexible cadences",
    "Reader-friendly checkpoints",
    "Personal study only",
  ],
  bookmarks: [
    "Quick return points",
    "Private collections",
    "Context-aware labels",
  ],
  notes: [
    "Private reflections",
    "Linked references",
    "Respectful export boundaries",
  ],
  settings: [
    "Reader scale controls",
    "Translation preferences",
    "Storage mode clarity",
  ],
} as const;

export const homeFeatureCards: ContentCard[] = [
  {
    title: "Reader",
    description:
      "A surah-first reading surface that gives Arabic text the most space, keeps translation secondary, and keeps references easy to scan.",
    footer: "Designed for calm, continuous reading on desktop and mobile.",
    href: "/reader",
    linkLabel: "Open the reader blueprint",
    tone: "warm",
  },
  {
    title: "Exact Search",
    description:
      "Word- and phrase-level search stays explainable, with visible query scope and result context instead of opaque ranking.",
    footer: "Useful for precise recall and study.",
    href: "/search",
    linkLabel: "Open the exact search page",
    tone: "neutral",
  },
  {
    title: "Semantic Search",
    description:
      "Similarity-based search is framed as exploratory discovery, with explicit copy that it is not tafsir, fatwa, or scholarly judgment.",
    footer: "Every result view must carry this distinction clearly.",
    href: "/semantic",
    linkLabel: "Open the semantic search page",
    tone: "accent",
  },
  {
    title: "Private Study Tools",
    description:
      "Progress, plans, bookmarks, and notes are organized as personal study aids with local-first storage and restrained UI copy.",
    footer: "Privacy is a default, not an advanced setting.",
    href: "/progress",
    linkLabel: "Open the study tools foundation",
    tone: "neutral",
  },
];

export const architecturePillars: ContentCard[] = [
  {
    title: "Arabic-first typography",
    description:
      "Quran text uses Noto Naskh Arabic with generous line height and strong contrast so the recitation text remains the visual center.",
    items: [
      "Arabic text scales independently from surrounding UI copy.",
      "English UI uses Newsreader for a classical manuscript rhythm without decorative excess.",
      "RTL direction is applied only where it belongs, keeping bilingual layouts stable.",
    ],
    tone: "warm",
  },
  {
    title: "Manuscript-inspired layout",
    description:
      "Cards, borders, and spacing borrow from manuscript framing and geometric ornament, but the layout remains practical and readable.",
    items: [
      "Soft parchment surfaces keep glare low without reducing contrast.",
      "Borders and seals provide structure instead of decoration for decoration's sake.",
      "Mobile layouts collapse cleanly without losing reading rhythm.",
    ],
    tone: "neutral",
  },
  {
    title: "Privacy defaults",
    description:
      "Progress, bookmarks, and notes are designed as private data first, with explicit future opt-in for sync or account-backed storage.",
    items: [
      "Local persistence should be the default storage layer for study data.",
      "Privacy language stays visible in progress, notes, and settings pages.",
      "Export actions remain deliberate and clearly scoped.",
    ],
    tone: "accent",
  },
  {
    title: "Search integrity",
    description:
      "Exact and semantic search are separate experiences so the UI never confuses lexical matches with similarity-based recall.",
    items: [
      "Exact search highlights what matched.",
      "Semantic search explains why passages feel related without claiming interpretation.",
      "Attribution and metadata remain attached to all displayed Quran text.",
    ],
    tone: "neutral",
  },
];

export const readerExperienceCards: ContentCard[] = [
  {
    title: "Visual hierarchy",
    description:
      "Arabic ayah text carries the largest type and the widest column, while translation and metadata sit beneath it with quieter styling.",
    items: [
      "Ayah numbers stay close to the text without interrupting reading flow.",
      "Surah metadata is visible at the top of the reading surface, not repeated on every line.",
      "Whitespace should feel manuscript-like rather than dashboard-like.",
    ],
    tone: "warm",
  },
  {
    title: "Reading rhythm",
    description:
      "The interface is built for sustained reading, with clear resume points, restrained controls, and strong focus states for keyboard users.",
    items: [
      "Primary actions sit near the top of the page and never crowd the ayah text.",
      "Scrollable regions should be avoided inside the main reader whenever possible.",
      "Focus rings use the accent color with high contrast on light surfaces.",
    ],
    tone: "neutral",
  },
  {
    title: "Attribution treatment",
    description:
      "Whenever Quran text or translation appears, source attribution is displayed as part of the reading surface rather than buried in settings.",
    items: [
      "Arabic text source sits adjacent to the preview footer.",
      "Translation attribution is separate and equally visible.",
      "Future audio or tafsir integrations should use the same pattern.",
    ],
    tone: "accent",
  },
];

export const exactSearchCards: ContentCard[] = [
  {
    title: "Explainable queries",
    description:
      "Exact search favors visible query rules and transparent filters so users can tell whether they are searching Arabic text, translations, or metadata.",
    items: [
      "Search mode and scope appear before the results list.",
      "Matches should be highlighted in-place.",
      "Empty states should suggest alternative exact strategies, not silently pivot to similarity.",
    ],
    tone: "neutral",
  },
  {
    title: "Result layout",
    description:
      "Result cards lead with the ayah reference, then show Arabic text, then translation and matching context in a stable order.",
    items: [
      "References should remain easy to copy into notes or bookmarks.",
      "Translation lines remain visually secondary to Arabic text.",
      "Filters should not move when result counts change.",
    ],
    tone: "warm",
  },
  {
    title: "Study workflow",
    description:
      "Exact search should connect naturally to reader, bookmarks, and notes without turning the page into a general-purpose dashboard.",
    items: [
      "Users can move from a result into reader mode with one clear action.",
      "Bookmarking and note-taking remain private by default.",
      "Search history should be optional and local-first.",
    ],
    tone: "accent",
  },
];

export const semanticSearchCards: ContentCard[] = [
  {
    title: "Similarity language",
    description:
      "The page language makes it explicit that semantic search groups passages by similarity signals, not by religious authority or interpretation.",
    items: [
      "Use the phrase similarity-based instead of meaning this is what the verse teaches.",
      "Display the disclaimer near the top of the page and beside results.",
      "Do not market the feature as an answer engine.",
    ],
    tone: "accent",
  },
  {
    title: "Result framing",
    description:
      "Semantic results should show the query, a short similarity explanation, and direct links into the reader for verification in context.",
    items: [
      "Users need the surrounding ayah context quickly.",
      "Similarity scores should be supportive, not dominant.",
      "Translation and source attribution stay attached to each result.",
    ],
    tone: "neutral",
  },
  {
    title: "Guardrails",
    description:
      "When the interface suggests related passages, it should also remind users to verify the text directly and avoid treating results as rulings.",
    items: [
      "No fatwa or tafsir framing.",
      "No auto-generated religious conclusions.",
      "Interface copy should stay modest and specific.",
    ],
    tone: "warm",
  },
];

export const progressCards: ContentCard[] = [
  {
    title: "Local-first tracking",
    description:
      "Reading progress is designed around private checkpoints stored locally until a reader explicitly opts into sync.",
    items: [
      "Last-read markers should be reversible.",
      "Daily progress summaries stay concise and optional.",
      "No public profile assumptions are baked into the UI.",
    ],
    tone: "accent",
  },
  {
    title: "Resume cues",
    description:
      "The progress page should foreground the next meaningful reading action rather than flood the page with charts.",
    items: [
      "Readers can resume the last surah or ayah quickly.",
      "Milestones should feel encouraging, not gamified.",
      "Numbers never compete with Quran text on the page.",
    ],
    tone: "neutral",
  },
  {
    title: "Reflection support",
    description:
      "Progress can connect to notes and plans, but those links remain quiet and optional.",
    items: [
      "A reading streak should never be the main goal of the interface.",
      "Reflections belong in notes, not in public feeds.",
      "Shared-device privacy needs clear sign-out or clear-data actions later.",
    ],
    tone: "warm",
  },
];

export const planCards: ContentCard[] = [
  {
    title: "Flexible cadences",
    description:
      "Plans can follow daily ayah counts, juz pacing, or a custom pace without forcing one devotional routine onto every reader.",
    items: [
      "Preset templates should be editable.",
      "Start dates and catch-up rules remain visible.",
      "The default layout privileges today and next, not a dense calendar.",
    ],
    tone: "neutral",
  },
  {
    title: "Checkpoint design",
    description:
      "Readers should understand where a plan starts, where they paused, and what is next at a glance.",
    items: [
      "Plan cards show the current checkpoint and remaining span.",
      "Completed segments collapse into lighter visual weight.",
      "Plan detail pages should link back into the reader directly.",
    ],
    tone: "warm",
  },
  {
    title: "Private ownership",
    description:
      "Plans are personal study structures and should not presume sharing, competition, or public accountability.",
    items: [
      "Any future sync needs an explicit privacy explanation.",
      "Export remains deliberate and user-initiated.",
      "Notifications should default to off until chosen.",
    ],
    tone: "accent",
  },
];

export const bookmarkCards: ContentCard[] = [
  {
    title: "Collections",
    description:
      "Bookmarks should support quick saving and optional grouping without forcing complex folder management on first use.",
    items: [
      "Single-tap save from reader and search views.",
      "Optional labels for revision, memorization, or study topics.",
      "Recent saves stay easy to revisit.",
    ],
    tone: "warm",
  },
  {
    title: "Context on return",
    description:
      "Saved references should reopen with enough local context to help the reader remember why the ayah mattered.",
    items: [
      "Preview the ayah text and surah metadata.",
      "Link directly into the surrounding reader context.",
      "Keep translation attribution attached in the preview.",
    ],
    tone: "neutral",
  },
  {
    title: "Private by default",
    description:
      "Bookmarks are private study artifacts unless a future sharing feature is intentionally added and explained.",
    items: [
      "No public visibility assumptions.",
      "Clear local export and deletion flows.",
      "Settings should show where bookmark data lives.",
    ],
    tone: "accent",
  },
];

export const noteCards: ContentCard[] = [
  {
    title: "Linked notes",
    description:
      "Notes stay anchored to a surah and ayah reference so they remain readable later without reconstructing the surrounding context.",
    items: [
      "Reference chips should remain visible in the editor.",
      "Notes can open back into the reader in one step.",
      "Bookmarked references and notes should feel related but distinct.",
    ],
    tone: "neutral",
  },
  {
    title: "Respectful study tone",
    description:
      "The notes surface is private and plainspoken, avoiding social phrasing or anything that implies scholarly authority.",
    items: [
      "No leaderboards, feeds, or public comments.",
      "Draft states stay local by default.",
      "The UI should feel like a personal study margin, not a chat app.",
    ],
    tone: "warm",
  },
  {
    title: "Export boundaries",
    description:
      "Export actions should make it clear whether users are exporting notes, references, or both, and keep Quran text attribution intact.",
    items: [
      "Exports remain user-initiated.",
      "Reference-only export should be available.",
      "Translation attribution should stay attached when included.",
    ],
    tone: "accent",
  },
];

export const settingsCards: ContentCard[] = [
  {
    title: "Reader preferences",
    description:
      "Settings should foreground text scale, line spacing, and translation visibility before lower-value visual toggles.",
    items: [
      "Arabic font sizing should be independent from UI sizing.",
      "Contrast and focus states must remain accessible at every scale.",
      "Reduced motion should be honored globally.",
    ],
    tone: "warm",
  },
  {
    title: "Translation and source choices",
    description:
      "When multiple translations or text editions are available, the settings page should show them with clear attribution and no ambiguity.",
    items: [
      "Each translation lists the translator name.",
      "Edition changes should preview their effect in the reader.",
      "Switching a translation should never hide attribution.",
    ],
    tone: "neutral",
  },
  {
    title: "Storage mode clarity",
    description:
      "Users should understand whether they are using local data, remote sync, or a future hybrid mode before they change that setting.",
    items: [
      "Local mode remains the default for private study data.",
      "Remote mode must explain what is stored and why.",
      "Clear-data actions should be easy to find and hard to trigger accidentally.",
    ],
    tone: "accent",
  },
];

export const sampleSurahPreview = {
  label: "Reader preview",
  heading: "Surah-first reading with visible attribution",
  description:
    "This preview defines spacing, contrast, and hierarchy for the reader surface. Arabic text stays primary, translations remain secondary, and the source lines remain part of the reading frame.",
  surahNameEnglish: "Al-Faatiha",
  surahNameArabic: "سُورَةُ ٱلْفَاتِحَةِ",
  revelationType: "Meccan",
  ayahs: [
    {
      number: 1,
      arabic: "بِسْمِ ٱللَّهِ ٱلرَّحْمَٰنِ ٱلرَّحِيمِ",
      translation: "In the name of Allah, the Beneficent, the Merciful.",
    },
    {
      number: 2,
      arabic: "ٱلْحَمْدُ لِلَّهِ رَبِّ ٱلْعَٰلَمِينَ",
      translation: "Praise be to Allah, Lord of the Worlds,",
    },
    {
      number: 3,
      arabic: "ٱلرَّحْمَٰنِ ٱلرَّحِيمِ",
      translation: "The Beneficent, the Merciful.",
    },
  ],
  arabicAttribution: "Arabic text sample: AlQuran.Cloud, Uthmani edition.",
  translationAttribution:
    "English translation sample: Mohammed Marmaduke William Pickthall via AlQuran.Cloud.",
  sourceNote:
    "This sample exists to define layout and attribution treatment until QuranKit's validated text pipeline is connected to the reader.",
} as const;
