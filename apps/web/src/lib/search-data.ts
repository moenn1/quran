import {
  formatRevelationPlace,
  getBundledAyahContext,
  type BundledAyah,
  type BundledSurah,
  type RevelationPlace,
} from "@/lib/reader-data";

export type ExactSearchScope = "all" | "arabic" | "translation" | "metadata";
export type SemanticScope = "all" | "longer-passages" | "short-final-surahs";
export type SemanticTranslationMode = "saheeh" | "arabic-only";

export type ExactSearchResult = {
  surah: BundledSurah;
  ayah: BundledAyah;
  juz: number;
  revelationLabel: string;
  matchedIn: readonly string[];
  contextBefore: BundledAyah | null;
  contextAfter: BundledAyah | null;
};

export type SemanticSearchResult = {
  surah: BundledSurah;
  ayah: BundledAyah;
  juz: number;
  revelationLabel: string;
  score: number;
  explanation: string;
  matchedTerms: readonly string[];
};

type ExactSearchOptions = {
  surahs: readonly BundledSurah[];
  query: string;
  scope: ExactSearchScope;
  surahFilter: number | "all";
  revelationFilter: RevelationPlace | "all";
};

type SemanticSearchOptions = {
  surahs: readonly BundledSurah[];
  query: string;
  scope: SemanticScope;
  surahFilter: number | "all";
  juzFilter: number | "all";
  limit: number;
};

type FlattenedAyahEntry = {
  surah: BundledSurah;
  ayah: BundledAyah;
  juz: number;
  revelationLabel: string;
};

const stopWords = new Set([
  "a",
  "an",
  "and",
  "are",
  "as",
  "at",
  "be",
  "but",
  "by",
  "for",
  "from",
  "has",
  "have",
  "he",
  "his",
  "i",
  "if",
  "in",
  "into",
  "is",
  "it",
  "its",
  "of",
  "on",
  "or",
  "so",
  "that",
  "the",
  "their",
  "them",
  "there",
  "they",
  "this",
  "to",
  "was",
  "we",
  "were",
  "with",
  "you",
  "your",
]);

const semanticCueAdditions: Record<string, readonly string[]> = {
  "1:1": ["mercy", "compassion", "opening"],
  "1:5": ["worship", "help", "devotion"],
  "1:6": ["guidance", "straight path"],
  "1:7": ["guidance", "favor", "path"],
  "98:1": ["clear evidence", "scripture"],
  "98:5": ["truth", "prayer", "sincerity"],
  "99:7": ["accountability", "good deeds"],
  "99:8": ["accountability", "evil deeds"],
  "103:3": ["truth", "patience", "righteous deeds"],
  "108:1": ["abundance", "gift"],
  "110:3": ["forgiveness", "praise", "repentance"],
  "112:1": ["oneness", "sincerity"],
  "112:2": ["refuge", "dependence"],
  "113:1": ["refuge", "protection", "daybreak"],
  "113:5": ["envy", "protection"],
  "114:1": ["refuge", "protection", "mankind"],
  "114:4": ["whispers", "protection"],
  "114:5": ["whispers", "hearts"],
} as const;

export const exactSearchScopeOptions = [
  { value: "all", label: "All fields" },
  { value: "arabic", label: "Arabic text" },
  { value: "translation", label: "Translation" },
  { value: "metadata", label: "Metadata" },
] as const satisfies readonly { value: ExactSearchScope; label: string }[];

export const semanticScopeOptions = [
  { value: "all", label: "All bundled passages" },
  { value: "longer-passages", label: "Longer passages" },
  { value: "short-final-surahs", label: "Short final surahs" },
] as const satisfies readonly { value: SemanticScope; label: string }[];

export const semanticTranslationOptions = [
  { value: "saheeh", label: "Saheeh International sample" },
  { value: "arabic-only", label: "Arabic only" },
] as const satisfies readonly {
  value: SemanticTranslationMode;
  label: string;
}[];

export const revelationFilterOptions = [
  { value: "all", label: "All" },
  { value: "makkah", label: "Meccan" },
  { value: "madinah", label: "Medinan" },
] as const satisfies readonly {
  value: RevelationPlace | "all";
  label: string;
}[];

export function getBundledJuz(surahNumber: number) {
  return surahNumber === 1 ? 1 : 30;
}

export function getBundledJuzOptions(surahs: readonly BundledSurah[]) {
  const values = Array.from(new Set(surahs.map((surah) => getBundledJuz(surah.number))));

  return values
    .sort((left, right) => left - right)
    .map((value) => ({
      value,
      label: `Juz ${value}`,
    }));
}

export function getBundledSurahOptions(surahs: readonly BundledSurah[]) {
  return surahs.map((surah) => ({
    value: surah.number,
    label: `${surah.number} · ${surah.nameEnglish}`,
  }));
}

export function runExactSearch({
  surahs,
  query,
  scope,
  surahFilter,
  revelationFilter,
}: ExactSearchOptions) {
  const trimmedQuery = query.trim();
  const normalizedQuery = trimmedQuery.toLowerCase();

  if (normalizedQuery.length === 0) {
    return [] as ExactSearchResult[];
  }

  return flattenAyahs(surahs).flatMap((entry) => {
    if (surahFilter !== "all" && entry.surah.number !== surahFilter) {
      return [];
    }

    if (revelationFilter !== "all" && entry.surah.revelationPlace !== revelationFilter) {
      return [];
    }

    const matchedIn = [
      matchesArabic(entry, trimmedQuery, scope) ? "Arabic text" : null,
      matchesTranslation(entry, normalizedQuery, scope) ? "Translation" : null,
      matchesMetadata(entry, normalizedQuery, scope) ? "Metadata" : null,
    ].filter(Boolean) as string[];

    if (matchedIn.length === 0) {
      return [];
    }

    const context = getBundledAyahContext(entry.surah.number, entry.ayah.ayahNumber);
    const focusIndex = context.findIndex(
      (ayah) => ayah.ayahNumber === entry.ayah.ayahNumber,
    );

    return [
      {
        ...entry,
        matchedIn,
        contextBefore: focusIndex > 0 ? context[focusIndex - 1] : null,
        contextAfter:
          focusIndex >= 0 && focusIndex < context.length - 1
            ? context[focusIndex + 1]
            : null,
      } satisfies ExactSearchResult,
    ];
  });
}

export function runSemanticSearch({
  surahs,
  query,
  scope,
  surahFilter,
  juzFilter,
  limit,
}: SemanticSearchOptions) {
  const trimmedQuery = query.trim();
  const tokens = tokenize(trimmedQuery);

  if (tokens.length === 0) {
    return [] as SemanticSearchResult[];
  }

  return flattenAyahs(surahs)
    .filter((entry) => {
      if (surahFilter !== "all" && entry.surah.number !== surahFilter) {
        return false;
      }

      if (juzFilter !== "all" && entry.juz !== juzFilter) {
        return false;
      }

      if (scope === "longer-passages") {
        return entry.surah.number < 103;
      }

      if (scope === "short-final-surahs") {
        return entry.surah.number >= 103;
      }

      return true;
    })
    .flatMap((entry) => {
      const scored = scoreSemanticEntry(entry, tokens);
      return scored ? [scored] : [];
    })
    .sort((left, right) => {
      if (right.score !== left.score) {
        return right.score - left.score;
      }

      if (left.surah.number !== right.surah.number) {
        return left.surah.number - right.surah.number;
      }

      return left.ayah.ayahNumber - right.ayah.ayahNumber;
    })
    .slice(0, limit);
}

function flattenAyahs(surahs: readonly BundledSurah[]) {
  return surahs.flatMap((surah) =>
    surah.ayahs.map(
      (ayah) =>
        ({
          surah,
          ayah,
          juz: getBundledJuz(surah.number),
          revelationLabel: formatRevelationPlace(surah.revelationPlace),
        }) satisfies FlattenedAyahEntry,
    ),
  );
}

function matchesArabic(
  entry: FlattenedAyahEntry,
  trimmedQuery: string,
  scope: ExactSearchScope,
) {
  if (scope !== "all" && scope !== "arabic") {
    return false;
  }

  return entry.ayah.arabicText.includes(trimmedQuery);
}

function matchesTranslation(
  entry: FlattenedAyahEntry,
  normalizedQuery: string,
  scope: ExactSearchScope,
) {
  if (scope !== "all" && scope !== "translation") {
    return false;
  }

  return entry.ayah.translationText.toLowerCase().includes(normalizedQuery);
}

function matchesMetadata(
  entry: FlattenedAyahEntry,
  normalizedQuery: string,
  scope: ExactSearchScope,
) {
  if (scope !== "all" && scope !== "metadata") {
    return false;
  }

  const metadataFields = [
    entry.ayah.reference,
    `Surah ${entry.surah.number}`,
    entry.surah.nameEnglish,
    entry.surah.nameArabic,
    entry.surah.nameTranslation,
    entry.revelationLabel,
    `Juz ${entry.juz}`,
  ];

  return metadataFields.some((field) => field.toLowerCase().includes(normalizedQuery));
}

function scoreSemanticEntry(entry: FlattenedAyahEntry, tokens: readonly string[]) {
  const translationTokens = tokenize(entry.ayah.translationText);
  const metadataTokens = tokenize(
    [
      entry.ayah.reference,
      entry.surah.nameEnglish,
      entry.surah.nameTranslation,
      entry.revelationLabel,
      `juz ${entry.juz}`,
    ].join(" "),
  );
  const cueTokens = tokenize(semanticCueAdditions[entry.ayah.reference]?.join(" ") ?? "");
  const searchableTerms = Array.from(
    new Set([...translationTokens, ...metadataTokens, ...cueTokens]),
  );
  const matchedTerms = searchableTerms.filter((term) =>
    tokens.some((token) => term.includes(token) || token.includes(term)),
  );

  if (matchedTerms.length === 0) {
    return null;
  }

  const matchedCueTerms = matchedTerms.filter((term) => cueTokens.includes(term));
  const matchedTranslationTerms = matchedTerms.filter((term) =>
    translationTokens.includes(term),
  );
  const score = Number(
    Math.min(
      0.99,
      0.42 +
        matchedTerms.length * 0.1 +
        matchedCueTerms.length * 0.08 +
        matchedTranslationTerms.length * 0.04,
    ).toFixed(2),
  );

  return {
    ...entry,
    score,
    matchedTerms: matchedTerms.slice(0, 4),
    explanation: buildSemanticExplanation(matchedCueTerms, matchedTranslationTerms),
  } satisfies SemanticSearchResult;
}

function buildSemanticExplanation(
  matchedCueTerms: readonly string[],
  matchedTranslationTerms: readonly string[],
) {
  if (matchedCueTerms.length > 0) {
    return `Related by similarity cues in the bundled preview: ${matchedCueTerms
      .slice(0, 2)
      .join(", ")}.`;
  }

  if (matchedTranslationTerms.length > 0) {
    return `Related by nearby wording in the bundled translation sample: ${matchedTranslationTerms
      .slice(0, 2)
      .join(", ")}.`;
  }

  return "Related by bundled phrasing and metadata cues in the sample search preview.";
}

function tokenize(value: string) {
  return value
    .toLowerCase()
    .split(/[^a-z0-9\u0600-\u06ff]+/u)
    .map((token) => token.trim())
    .filter((token) => token.length > 1 && !stopWords.has(token));
}
