import {
  getBundledAyah,
  getBundledSurahs,
  type BundledAyah,
  type BundledSurah,
} from "@/lib/reader-data";
import { getBundledJuz } from "@/lib/search-data";

export type StudyReference = {
  surahNumber: number;
  ayahNumber: number;
};

export type StudyRange = {
  start: StudyReference;
  end: StudyReference;
  label: string;
};

export type StudyProgress = {
  range: StudyRange;
  updatedAt: string;
  source: string;
};

export type StudyBookmark = {
  id: string;
  range: StudyRange;
  label: string | null;
  createdAt: string;
};

export type StudyNote = {
  id: string;
  range: StudyRange;
  body: string;
  createdAt: string;
  updatedAt: string;
};

export type StudyPlan = {
  id: string;
  name: string;
  range: StudyRange;
  dailyAyahTarget: number;
  createdAt: string;
  updatedAt: string;
  completedThrough: StudyReference | null;
};

export type ReaderTextView = "balanced" | "arabic" | "translation";
export type ReaderArabicScale = "standard" | "large" | "majlis";
export type ReaderTranslationScale = "compact" | "standard" | "roomy";

export type ReaderPreferences = {
  translationVisible: boolean;
  textView: ReaderTextView;
  arabicScale: ReaderArabicScale;
  translationScale: ReaderTranslationScale;
  reducedMotion: boolean;
};

export type StudyActivityKind = "progress" | "bookmark" | "note" | "plan";

export type StudyActivity = {
  id: string;
  kind: StudyActivityKind;
  message: string;
  createdAt: string;
};

export type StudyDocument = {
  progress: StudyProgress | null;
  bookmarks: StudyBookmark[];
  notes: StudyNote[];
  plans: StudyPlan[];
};

export type StudySnapshot = {
  state: StudyDocument;
  completedReferences: string[];
  activePlanId: string | null;
  preferences: ReaderPreferences;
  activity: StudyActivity[];
};

export type StudyAyahEntry = {
  surah: BundledSurah;
  ayah: BundledAyah;
  juz: number;
  index: number;
};

export type StudyProgressSummary = {
  completedAyahs: number;
  totalAyahs: number;
  percent: number;
};

export type StudyPlanMetrics = {
  totalAyahs: number;
  completedAyahs: number;
  remainingAyahs: number;
  completed: boolean;
  todayRange: StudyRange | null;
};

export const STUDY_STORAGE_KEY = "qurankit.study-state.v1";
export const STUDY_REMOTE_ENDPOINTS = [
  "GET /api/v1/me/study",
  "PUT /api/v1/me/study",
] as const;

export const defaultReaderPreferences: ReaderPreferences = {
  translationVisible: true,
  textView: "balanced",
  arabicScale: "standard",
  translationScale: "standard",
  reducedMotion: false,
};

const starterTimestamp = "2026-04-30T00:00:00.000Z";

const bundledAyahEntries = getBundledSurahs().flatMap((surah) =>
  surah.ayahs.map(
    (ayah, index) =>
      ({
        surah,
        ayah,
        juz: getBundledJuz(surah.number),
        index,
      }) satisfies StudyAyahEntry,
  ),
);

const starterPlan: StudyPlan = {
  id: "starter-plan",
  name: "Short evening review",
  range: createStudyRange(
    { surahNumber: 112, ayahNumber: 1 },
    { surahNumber: 114, ayahNumber: 6 },
  ),
  dailyAyahTarget: 3,
  createdAt: starterTimestamp,
  updatedAt: starterTimestamp,
  completedThrough: null,
};

export function createBlankStudySnapshot(): StudySnapshot {
  return {
    state: {
      progress: null,
      bookmarks: [],
      notes: [],
      plans: [],
    },
    completedReferences: [],
    activePlanId: null,
    preferences: defaultReaderPreferences,
    activity: [],
  };
}

export function createInitialStudySnapshot(): StudySnapshot {
  return {
    ...createBlankStudySnapshot(),
    state: {
      progress: null,
      bookmarks: [],
      notes: [],
      plans: [starterPlan],
    },
    activePlanId: starterPlan.id,
  };
}

export function normalizeStudySnapshot(payload: unknown): StudySnapshot {
  const source = isRecord(payload) ? payload : {};
  const defaults = createInitialStudySnapshot();
  const stateSource = isRecord(source.state) ? source.state : {};
  const preferencesSource = isRecord(source.preferences) ? source.preferences : {};

  return {
    state: {
      progress: isRecord(stateSource.progress)
        ? normalizeStudyProgress(stateSource.progress)
        : defaults.state.progress,
      bookmarks: Array.isArray(stateSource.bookmarks)
        ? stateSource.bookmarks
            .map((item) => (isRecord(item) ? normalizeStudyBookmark(item) : null))
            .filter((item): item is StudyBookmark => item !== null)
        : defaults.state.bookmarks,
      notes: Array.isArray(stateSource.notes)
        ? stateSource.notes
            .map((item) => (isRecord(item) ? normalizeStudyNote(item) : null))
            .filter((item): item is StudyNote => item !== null)
        : defaults.state.notes,
      plans: Array.isArray(stateSource.plans)
        ? stateSource.plans
            .map((item) => (isRecord(item) ? normalizeStudyPlan(item) : null))
            .filter((item): item is StudyPlan => item !== null)
        : defaults.state.plans,
    },
    completedReferences: Array.isArray(source.completedReferences)
      ? source.completedReferences.filter(
          (item): item is string => typeof item === "string",
        )
      : defaults.completedReferences,
    activePlanId:
      typeof source.activePlanId === "string" || source.activePlanId === null
        ? source.activePlanId
        : defaults.activePlanId,
    preferences: {
      translationVisible:
        typeof preferencesSource.translationVisible === "boolean"
          ? preferencesSource.translationVisible
          : defaults.preferences.translationVisible,
      textView: isTextView(preferencesSource.textView)
        ? preferencesSource.textView
        : defaults.preferences.textView,
      arabicScale: isArabicScale(preferencesSource.arabicScale)
        ? preferencesSource.arabicScale
        : defaults.preferences.arabicScale,
      translationScale: isTranslationScale(preferencesSource.translationScale)
        ? preferencesSource.translationScale
        : defaults.preferences.translationScale,
      reducedMotion:
        typeof preferencesSource.reducedMotion === "boolean"
          ? preferencesSource.reducedMotion
          : defaults.preferences.reducedMotion,
    },
    activity: Array.isArray(source.activity)
      ? source.activity
          .map((item) => (isRecord(item) ? normalizeStudyActivity(item) : null))
          .filter((item): item is StudyActivity => item !== null)
      : defaults.activity,
  };
}

export function createStudyRange(
  start: StudyReference,
  end: StudyReference,
): StudyRange {
  if (compareReferences(start, end) > 0) {
    throw new Error("Study ranges must end at or after the start reference.");
  }

  return {
    start,
    end,
    label: formatRangeLabel(start, end),
  };
}

export function parseReferenceLabel(value: string): StudyReference | null {
  const match = /^(\d+):(\d+)$/u.exec(value.trim());
  if (!match) {
    return null;
  }

  return {
    surahNumber: Number(match[1]),
    ayahNumber: Number(match[2]),
  };
}

export function formatReference(reference: StudyReference) {
  return `${reference.surahNumber}:${reference.ayahNumber}`;
}

export function compareReferences(left: StudyReference, right: StudyReference) {
  if (left.surahNumber !== right.surahNumber) {
    return left.surahNumber - right.surahNumber;
  }

  return left.ayahNumber - right.ayahNumber;
}

export function compareReferenceLabels(left: string, right: string) {
  const leftReference = parseReferenceLabel(left);
  const rightReference = parseReferenceLabel(right);

  if (!leftReference || !rightReference) {
    return 0;
  }

  return compareReferences(leftReference, rightReference);
}

export function formatRangeLabel(start: StudyReference, end: StudyReference) {
  if (start.surahNumber === end.surahNumber && start.ayahNumber === end.ayahNumber) {
    return formatReference(start);
  }

  if (start.surahNumber === end.surahNumber) {
    return `${start.surahNumber}:${start.ayahNumber}-${end.ayahNumber}`;
  }

  return `${formatReference(start)}-${formatReference(end)}`;
}

export function getBundledReferenceOptions() {
  return bundledAyahEntries.map((entry) => ({
    value: entry.ayah.reference,
    label: `${entry.ayah.reference} · ${entry.surah.nameEnglish}`,
  }));
}

export function getBundledAyahEntry(reference: string | StudyReference) {
  const label =
    typeof reference === "string" ? reference : formatReference(reference);

  return (
    bundledAyahEntries.find((entry) => entry.ayah.reference === label) ?? null
  );
}

export function getStudyRangeEntries(range: StudyRange) {
  const startIndex = bundledAyahEntries.findIndex(
    (entry) => entry.ayah.reference === formatReference(range.start),
  );
  const endIndex = bundledAyahEntries.findIndex(
    (entry) => entry.ayah.reference === formatReference(range.end),
  );

  if (startIndex === -1 || endIndex === -1 || endIndex < startIndex) {
    return [] as StudyAyahEntry[];
  }

  return bundledAyahEntries.slice(startIndex, endIndex + 1);
}

export function countStudyRangeAyahs(range: StudyRange) {
  return getStudyRangeEntries(range).length;
}

export function getActivePlan(snapshot: StudySnapshot) {
  if (snapshot.activePlanId) {
    const activePlan =
      snapshot.state.plans.find((plan) => plan.id === snapshot.activePlanId) ?? null;

    if (activePlan) {
      return activePlan;
    }
  }

  return snapshot.state.plans.find((plan) => !getPlanMetrics(plan, snapshot).completed) ?? null;
}

export function getPlanMetrics(
  plan: StudyPlan,
  snapshot: Pick<StudySnapshot, "completedReferences">,
): StudyPlanMetrics {
  const entries = getStudyRangeEntries(plan.range);
  const completedSet = new Set(snapshot.completedReferences);
  const completedAyahs = entries.filter((entry) =>
    completedSet.has(entry.ayah.reference),
  ).length;
  const totalAyahs = entries.length;
  const completedThroughIndex = getContiguousCompletionIndex(plan, completedSet);
  const nextStartIndex = completedThroughIndex + 1;
  const todayEntries = entries.slice(nextStartIndex, nextStartIndex + plan.dailyAyahTarget);

  return {
    totalAyahs,
    completedAyahs,
    remainingAyahs: Math.max(0, totalAyahs - completedAyahs),
    completed: totalAyahs > 0 && completedAyahs >= totalAyahs,
    todayRange:
      todayEntries.length > 0
        ? createStudyRange(
            parseReferenceLabel(todayEntries[0].ayah.reference)!,
            parseReferenceLabel(todayEntries.at(-1)!.ayah.reference)!,
          )
        : null,
  };
}

export function getOverallProgress(snapshot: StudySnapshot): StudyProgressSummary {
  const completedSet = new Set(snapshot.completedReferences);
  const totalAyahs = bundledAyahEntries.length;
  const completedAyahs = bundledAyahEntries.filter((entry) =>
    completedSet.has(entry.ayah.reference),
  ).length;

  return {
    completedAyahs,
    totalAyahs,
    percent: totalAyahs === 0 ? 0 : Math.round((completedAyahs / totalAyahs) * 100),
  };
}

export function getSurahProgressRows(snapshot: StudySnapshot) {
  const completedSet = new Set(snapshot.completedReferences);

  return getBundledSurahs().map((surah) => {
    const completedAyahs = surah.ayahs.filter((ayah) =>
      completedSet.has(ayah.reference),
    ).length;
    const totalAyahs = Number(surah.ayahs.length);

    return {
      surah,
      completedAyahs,
      totalAyahs,
      percent: totalAyahs === 0 ? 0 : Math.round((completedAyahs / totalAyahs) * 100),
    };
  });
}

export function getJuzProgressRows(snapshot: StudySnapshot) {
  const completedSet = new Set(snapshot.completedReferences);
  const groups = new Map<number, StudyAyahEntry[]>();

  for (const entry of bundledAyahEntries) {
    const current = groups.get(entry.juz) ?? [];
    current.push(entry);
    groups.set(entry.juz, current);
  }

  return Array.from(groups.entries())
    .sort((left, right) => left[0] - right[0])
    .map(([juz, entries]) => {
      const completedAyahs = entries.filter((entry) =>
        completedSet.has(entry.ayah.reference),
      ).length;
      const totalAyahs = entries.length;

      return {
        juz,
        completedAyahs,
        totalAyahs,
        percent: totalAyahs === 0 ? 0 : Math.round((completedAyahs / totalAyahs) * 100),
      };
    });
}

export function getReadingStreakDays(snapshot: StudySnapshot) {
  const dates = Array.from(
    new Set(
      snapshot.activity
        .filter((entry) => entry.kind === "progress" || entry.kind === "plan")
        .map((entry) => entry.createdAt.slice(0, 10)),
    ),
  ).sort()
    .reverse();

  if (dates.length === 0) {
    return 0;
  }

  let streak = 0;
  const cursor = new Date(`${dates[0]}T00:00:00Z`);

  for (const value of dates) {
    const current = new Date(`${value}T00:00:00Z`);

    if (current.getTime() !== cursor.getTime()) {
      break;
    }

    streak += 1;
    cursor.setUTCDate(cursor.getUTCDate() - 1);
  }

  return streak;
}

export function hasBookmarkForReference(snapshot: StudySnapshot, reference: string) {
  return snapshot.state.bookmarks.some((bookmark) => bookmark.range.label === reference);
}

export function getBookmarkForReference(snapshot: StudySnapshot, reference: string) {
  return (
    snapshot.state.bookmarks.find((bookmark) => bookmark.range.label === reference) ?? null
  );
}

export function buildStudyExportPayload(
  snapshot: StudySnapshot,
  scope: "full" | "progress" | "bookmarks" | "notes",
) {
  const exportedAt = new Date().toISOString();

  if (scope === "progress") {
    return {
      exported_at: exportedAt,
      storage: "browser-local-storage",
      progress: snapshot.state.progress,
      completed_references: snapshot.completedReferences,
      active_plan_id: snapshot.activePlanId,
    };
  }

  if (scope === "bookmarks") {
    return {
      exported_at: exportedAt,
      count: snapshot.state.bookmarks.length,
      bookmarks: snapshot.state.bookmarks,
    };
  }

  if (scope === "notes") {
    return {
      exported_at: exportedAt,
      count: snapshot.state.notes.length,
      notes: snapshot.state.notes,
    };
  }

  return {
    exported_at: exportedAt,
    storage_key: STUDY_STORAGE_KEY,
    state: snapshot.state,
    completed_references: snapshot.completedReferences,
    active_plan_id: snapshot.activePlanId,
    preferences: snapshot.preferences,
    activity: snapshot.activity,
  };
}

export function formatStudyDate(value: string) {
  if (!value) {
    return "Not recorded yet";
  }

  return new Intl.DateTimeFormat("en", {
    day: "numeric",
    month: "short",
    year: "numeric",
  }).format(new Date(value));
}

export function formatStudyDateTime(value: string) {
  if (!value) {
    return "Not recorded yet";
  }

  return new Intl.DateTimeFormat("en", {
    day: "numeric",
    month: "short",
    hour: "numeric",
    minute: "2-digit",
  }).format(new Date(value));
}

export function generateStudyId(prefix: string) {
  const cryptoId = globalThis.crypto?.randomUUID?.();

  if (cryptoId) {
    return `${prefix}-${cryptoId}`;
  }

  return `${prefix}-${Math.random().toString(36).slice(2, 10)}`;
}

export function getAyahPreview(reference: string | StudyReference) {
  const parsed =
    typeof reference === "string" ? parseReferenceLabel(reference) : reference;

  if (!parsed) {
    return null;
  }

  const result = getBundledAyah(parsed.surahNumber, parsed.ayahNumber);

  if (!result) {
    return null;
  }

  return {
    surah: result.surah,
    ayah: result.ayah,
    juz: getBundledJuz(result.surah.number),
  };
}

export function clampRangeToBundledSample(
  startLabel: string,
  endLabel: string,
): StudyRange | null {
  const start = parseReferenceLabel(startLabel);
  const end = parseReferenceLabel(endLabel);

  if (!start || !end || compareReferences(start, end) > 0) {
    return null;
  }

  const range = createStudyRange(start, end);

  return countStudyRangeAyahs(range) > 0 ? range : null;
}

function normalizeStudyProgress(payload: Record<string, unknown>) {
  const range = normalizeStudyRange(payload.range);

  if (!range) {
    return null;
  }

  return {
    range,
    updatedAt:
      typeof payload.updatedAt === "string"
        ? payload.updatedAt
        : typeof payload.updated_at === "string"
          ? payload.updated_at
          : "",
    source: typeof payload.source === "string" ? payload.source : "manual_mark",
  } satisfies StudyProgress;
}

function normalizeStudyBookmark(payload: Record<string, unknown>) {
  const range = normalizeStudyRange(payload.range);

  if (!range || typeof payload.id !== "string") {
    return null;
  }

  return {
    id: payload.id,
    range,
    label: typeof payload.label === "string" ? payload.label : null,
    createdAt:
      typeof payload.createdAt === "string"
        ? payload.createdAt
        : typeof payload.created_at === "string"
          ? payload.created_at
          : "",
  } satisfies StudyBookmark;
}

function normalizeStudyNote(payload: Record<string, unknown>) {
  const range = normalizeStudyRange(payload.range);

  if (!range || typeof payload.id !== "string") {
    return null;
  }

  return {
    id: payload.id,
    range,
    body: typeof payload.body === "string" ? payload.body : "",
    createdAt:
      typeof payload.createdAt === "string"
        ? payload.createdAt
        : typeof payload.created_at === "string"
          ? payload.created_at
          : "",
    updatedAt:
      typeof payload.updatedAt === "string"
        ? payload.updatedAt
        : typeof payload.updated_at === "string"
          ? payload.updated_at
          : "",
  } satisfies StudyNote;
}

function normalizeStudyPlan(payload: Record<string, unknown>) {
  const range = normalizeStudyRange(payload.range);

  if (!range || typeof payload.id !== "string") {
    return null;
  }

  return {
    id: payload.id,
    name: typeof payload.name === "string" ? payload.name : "Untitled plan",
    range,
    dailyAyahTarget:
      typeof payload.dailyAyahTarget === "number"
        ? payload.dailyAyahTarget
        : typeof payload.daily_ayah_target === "number"
          ? payload.daily_ayah_target
          : 1,
    createdAt:
      typeof payload.createdAt === "string"
        ? payload.createdAt
        : typeof payload.created_at === "string"
          ? payload.created_at
          : "",
    updatedAt:
      typeof payload.updatedAt === "string"
        ? payload.updatedAt
        : typeof payload.updated_at === "string"
          ? payload.updated_at
          : "",
    completedThrough: normalizeStudyReference(payload.completedThrough ?? payload.completed_through),
  } satisfies StudyPlan;
}

function normalizeStudyActivity(payload: Record<string, unknown>) {
  if (typeof payload.id !== "string" || !isStudyActivityKind(payload.kind)) {
    return null;
  }

  return {
    id: payload.id,
    kind: payload.kind,
    message: typeof payload.message === "string" ? payload.message : "",
    createdAt:
      typeof payload.createdAt === "string"
        ? payload.createdAt
        : typeof payload.created_at === "string"
          ? payload.created_at
          : "",
  } satisfies StudyActivity;
}

function normalizeStudyRange(value: unknown) {
  if (!isRecord(value)) {
    return null;
  }

  const start = normalizeStudyReference(value.start);
  const end = normalizeStudyReference(value.end);

  if (!start || !end || compareReferences(start, end) > 0) {
    return null;
  }

  return createStudyRange(start, end);
}

function normalizeStudyReference(value: unknown) {
  if (!isRecord(value)) {
    return null;
  }

  if (
    typeof value.surahNumber === "number" &&
    typeof value.ayahNumber === "number"
  ) {
    return {
      surahNumber: value.surahNumber,
      ayahNumber: value.ayahNumber,
    } satisfies StudyReference;
  }

  if (
    typeof value.surah_number === "number" &&
    typeof value.ayah_number === "number"
  ) {
    return {
      surahNumber: value.surah_number,
      ayahNumber: value.ayah_number,
    } satisfies StudyReference;
  }

  return null;
}

function getContiguousCompletionIndex(
  plan: StudyPlan,
  completedSet: ReadonlySet<string>,
) {
  const entries = getStudyRangeEntries(plan.range);
  const explicitIndex = plan.completedThrough
    ? entries.findIndex(
        (entry) => entry.ayah.reference === formatReference(plan.completedThrough!),
      )
    : -1;

  let contiguousIndex = -1;

  for (const entry of entries) {
    if (!completedSet.has(entry.ayah.reference)) {
      break;
    }

    contiguousIndex += 1;
  }

  return Math.max(explicitIndex, contiguousIndex);
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null;
}

function isTextView(value: unknown): value is ReaderTextView {
  return value === "balanced" || value === "arabic" || value === "translation";
}

function isArabicScale(value: unknown): value is ReaderArabicScale {
  return value === "standard" || value === "large" || value === "majlis";
}

function isTranslationScale(value: unknown): value is ReaderTranslationScale {
  return value === "compact" || value === "standard" || value === "roomy";
}

function isStudyActivityKind(value: unknown): value is StudyActivityKind {
  return value === "progress" || value === "bookmark" || value === "note" || value === "plan";
}
