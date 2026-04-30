"use client";

import { createContext, useContext, useEffect, useState } from "react";
import type { ReactNode } from "react";

import {
  clampRangeToBundledSample,
  createBlankStudySnapshot,
  createInitialStudySnapshot,
  formatReference,
  generateStudyId,
  getActivePlan,
  getBookmarkForReference,
  getPlanMetrics,
  getStudyRangeEntries,
  normalizeStudySnapshot,
  parseReferenceLabel,
  STUDY_STORAGE_KEY,
  type ReaderPreferences,
  type StudyActivity,
  type StudyBookmark,
  type StudyNote,
  type StudyPlan,
  type StudyRange,
  type StudyReference,
  type StudySnapshot,
} from "@/lib/study-data";

type StudyActionResult = {
  ok: boolean;
  message: string;
};

type MarkProgressInput = {
  startReference: string;
  endReference?: string;
  source?: string;
};

type SaveBookmarkInput = {
  reference: string;
  label?: string;
};

type SaveNoteInput = {
  id?: string;
  reference: string;
  body: string;
};

type CreatePlanInput = {
  name: string;
  startReference: string;
  endReference: string;
  dailyAyahTarget: number;
};

type UpdatePlanInput = {
  name?: string;
  dailyAyahTarget?: number;
};

type StudyStateContextValue = {
  snapshot: StudySnapshot;
  hydrated: boolean;
  markProgress: (input: MarkProgressInput) => StudyActionResult;
  clearProgress: () => StudyActionResult;
  saveBookmark: (input: SaveBookmarkInput) => StudyActionResult;
  toggleBookmark: (input: SaveBookmarkInput) => StudyActionResult;
  removeBookmark: (bookmarkId: string) => StudyActionResult;
  saveNote: (input: SaveNoteInput) => StudyActionResult;
  deleteNote: (noteId: string) => StudyActionResult;
  createPlan: (input: CreatePlanInput) => StudyActionResult;
  updatePlan: (planId: string, input: UpdatePlanInput) => StudyActionResult;
  removePlan: (planId: string) => StudyActionResult;
  setActivePlan: (planId: string) => StudyActionResult;
  completeTodayTarget: (planId?: string) => StudyActionResult;
  setReaderPreferences: (
    patch: Partial<ReaderPreferences>,
  ) => StudyActionResult;
  clearStudyData: () => StudyActionResult;
};

const StudyStateContext = createContext<StudyStateContextValue | null>(null);

type StudyStateProviderProps = {
  children: ReactNode;
};

export function StudyStateProvider({ children }: StudyStateProviderProps) {
  const [snapshot, setSnapshot] = useState<StudySnapshot>(createInitialStudySnapshot());
  const [hydrated, setHydrated] = useState(false);

  useEffect(() => {
    let cancelled = false;

    queueMicrotask(() => {
      if (cancelled) {
        return;
      }

      try {
        const raw = window.localStorage.getItem(STUDY_STORAGE_KEY);

        if (raw) {
          setSnapshot(normalizeStudySnapshot(JSON.parse(raw)));
        }
      } catch {
        setSnapshot(createInitialStudySnapshot());
      } finally {
        setHydrated(true);
      }
    });

    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    if (!hydrated) {
      return;
    }

    window.localStorage.setItem(STUDY_STORAGE_KEY, JSON.stringify(snapshot));
  }, [hydrated, snapshot]);

  useEffect(() => {
    if (!hydrated) {
      return;
    }

    function handleStorage(event: StorageEvent) {
      if (event.key !== STUDY_STORAGE_KEY || !event.newValue) {
        return;
      }

      try {
        setSnapshot(normalizeStudySnapshot(JSON.parse(event.newValue)));
      } catch {
        setSnapshot(createInitialStudySnapshot());
      }
    }

    window.addEventListener("storage", handleStorage);

    return () => window.removeEventListener("storage", handleStorage);
  }, [hydrated]);

  useEffect(() => {
    document.documentElement.dataset.motion = snapshot.preferences.reducedMotion
      ? "reduced"
      : "full";
  }, [snapshot.preferences.reducedMotion]);

  const value: StudyStateContextValue = {
    snapshot,
    hydrated,
    markProgress(input) {
      const range = clampRangeToBundledSample(
        input.startReference,
        input.endReference ?? input.startReference,
      );

      if (!range) {
        return {
          ok: false,
          message: "Choose a valid bundled sample range before saving progress.",
        };
      }

      const timestamp = new Date().toISOString();
      const activity = createActivity(
        "progress",
        `Marked ${range.label} as the latest private checkpoint.`,
        timestamp,
      );

      setSnapshot((current) => {
        const completedReferences = new Set(current.completedReferences);

        for (const entry of getStudyRangeEntries(range)) {
          completedReferences.add(entry.ayah.reference);
        }

        return {
          ...current,
          state: {
            ...current.state,
            progress: {
              range,
              updatedAt: timestamp,
              source: input.source ?? "manual_mark",
            },
            plans: updatePlansAfterProgress(current.state.plans, range, timestamp),
          },
          completedReferences: Array.from(completedReferences),
          activity: appendActivity(current.activity, activity),
        };
      });

      return {
        ok: true,
        message: `${range.label} saved as the latest private checkpoint.`,
      };
    },
    clearProgress() {
      if (!snapshot.state.progress) {
        return {
          ok: false,
          message: "There is no latest checkpoint to clear.",
        };
      }

      setSnapshot((current) => ({
        ...current,
        state: {
          ...current.state,
          progress: null,
        },
      }));

      return {
        ok: true,
        message: "The latest checkpoint was cleared. Completed ayah totals stayed intact.",
      };
    },
    saveBookmark(input) {
      const reference = parseReferenceLabel(input.reference);

      if (!reference) {
        return {
          ok: false,
          message: "Choose a bundled sample ayah before saving a bookmark.",
        };
      }

      const timestamp = new Date().toISOString();
      const range = singleAyahRange(reference);

      setSnapshot((current) => {
        const existing = getBookmarkForReference(current, input.reference);

        if (existing) {
          const bookmarks = current.state.bookmarks.map((bookmark) =>
            bookmark.id === existing.id
              ? {
                  ...bookmark,
                  label: sanitizeLabel(input.label) ?? bookmark.label,
                  createdAt: bookmark.createdAt || timestamp,
                }
              : bookmark,
          );

          return {
            ...current,
            state: {
              ...current.state,
              bookmarks,
            },
            activity: appendActivity(
              current.activity,
              createActivity(
                "bookmark",
                `${range.label} was kept in private bookmarks.`,
                timestamp,
              ),
            ),
          };
        }

        const bookmark: StudyBookmark = {
          id: generateStudyId("bookmark"),
          range,
          label: sanitizeLabel(input.label),
          createdAt: timestamp,
        };

        return {
          ...current,
          state: {
            ...current.state,
            bookmarks: [bookmark, ...current.state.bookmarks],
          },
          activity: appendActivity(
            current.activity,
            createActivity(
              "bookmark",
              `${range.label} was added to private bookmarks.`,
              timestamp,
            ),
          ),
        };
      });

      return {
        ok: true,
        message: `${range.label} saved to private bookmarks.`,
      };
    },
    toggleBookmark(input) {
      const existing = getBookmarkForReference(snapshot, input.reference);

      if (existing) {
        return value.removeBookmark(existing.id);
      }

      return value.saveBookmark(input);
    },
    removeBookmark(bookmarkId) {
      const bookmark = snapshot.state.bookmarks.find((item) => item.id === bookmarkId);

      if (!bookmark) {
        return {
          ok: false,
          message: "That bookmark is no longer in local study state.",
        };
      }

      setSnapshot((current) => ({
        ...current,
        state: {
          ...current.state,
          bookmarks: current.state.bookmarks.filter((item) => item.id !== bookmarkId),
        },
      }));

      return {
        ok: true,
        message: `${bookmark.range.label} was removed from private bookmarks.`,
      };
    },
    saveNote(input) {
      const reference = parseReferenceLabel(input.reference);
      const body = input.body.trim();

      if (!reference) {
        return {
          ok: false,
          message: "Choose a bundled sample ayah before saving a note.",
        };
      }

      if (!body) {
        return {
          ok: false,
          message: "Notes need some text before they can be saved.",
        };
      }

      const timestamp = new Date().toISOString();
      const range = singleAyahRange(reference);

      setSnapshot((current) => {
        const existing = input.id
          ? current.state.notes.find((note) => note.id === input.id) ?? null
          : null;

        const nextNote: StudyNote = existing
          ? {
              ...existing,
              range,
              body,
              updatedAt: timestamp,
            }
          : {
              id: generateStudyId("note"),
              range,
              body,
              createdAt: timestamp,
              updatedAt: timestamp,
            };

        const notes = existing
          ? current.state.notes.map((note) =>
              note.id === existing.id ? nextNote : note,
            )
          : [nextNote, ...current.state.notes];

        return {
          ...current,
          state: {
            ...current.state,
            notes,
          },
          activity: appendActivity(
            current.activity,
            createActivity(
              "note",
              `${range.label} was ${existing ? "updated in" : "added to"} private notes.`,
              timestamp,
            ),
          ),
        };
      });

      return {
        ok: true,
        message: `${range.label} saved in private notes.`,
      };
    },
    deleteNote(noteId) {
      const note = snapshot.state.notes.find((item) => item.id === noteId);

      if (!note) {
        return {
          ok: false,
          message: "That note is no longer in local study state.",
        };
      }

      setSnapshot((current) => ({
        ...current,
        state: {
          ...current.state,
          notes: current.state.notes.filter((item) => item.id !== noteId),
        },
      }));

      return {
        ok: true,
        message: `Removed the private note linked to ${note.range.label}.`,
      };
    },
    createPlan(input) {
      const range = clampRangeToBundledSample(input.startReference, input.endReference);
      const name = input.name.trim();
      const target = Math.max(1, Math.floor(input.dailyAyahTarget));

      if (!range) {
        return {
          ok: false,
          message: "Plan ranges need valid bundled sample start and end references.",
        };
      }

      if (!name) {
        return {
          ok: false,
          message: "Plans need a name before they can be saved.",
        };
      }

      const timestamp = new Date().toISOString();
      const plan: StudyPlan = {
        id: generateStudyId("plan"),
        name,
        range,
        dailyAyahTarget: target,
        createdAt: timestamp,
        updatedAt: timestamp,
        completedThrough: null,
      };

      setSnapshot((current) => ({
        ...current,
        state: {
          ...current.state,
          plans: [plan, ...current.state.plans],
        },
        activePlanId: plan.id,
        activity: appendActivity(
          current.activity,
          createActivity(
            "plan",
            `Created the private plan “${name}” for ${range.label}.`,
            timestamp,
          ),
        ),
      }));

      return {
        ok: true,
        message: `Created “${name}” and set it as the active private plan.`,
      };
    },
    updatePlan(planId, input) {
      const plan = snapshot.state.plans.find((item) => item.id === planId);

      if (!plan) {
        return {
          ok: false,
          message: "That plan is no longer available.",
        };
      }

      const timestamp = new Date().toISOString();
      const nextName =
        typeof input.name === "string" && input.name.trim().length > 0
          ? input.name.trim()
          : plan.name;
      const nextDailyAyahTarget =
        typeof input.dailyAyahTarget === "number" && input.dailyAyahTarget > 0
          ? Math.floor(input.dailyAyahTarget)
          : plan.dailyAyahTarget;

      setSnapshot((current) => ({
        ...current,
        state: {
          ...current.state,
          plans: current.state.plans.map((item) =>
            item.id === planId
              ? {
                  ...item,
                  name: nextName,
                  dailyAyahTarget: nextDailyAyahTarget,
                  updatedAt: timestamp,
                }
              : item,
          ),
        },
      }));

      return {
        ok: true,
        message: `Recalculated “${nextName}” for ${nextDailyAyahTarget} ayahs per day.`,
      };
    },
    removePlan(planId) {
      const plan = snapshot.state.plans.find((item) => item.id === planId);

      if (!plan) {
        return {
          ok: false,
          message: "That plan is no longer available.",
        };
      }

      setSnapshot((current) => {
        const nextPlans = current.state.plans.filter((item) => item.id !== planId);
        const nextActivePlanId =
          current.activePlanId === planId ? nextPlans[0]?.id ?? null : current.activePlanId;

        return {
          ...current,
          state: {
            ...current.state,
            plans: nextPlans,
          },
          activePlanId: nextActivePlanId,
        };
      });

      return {
        ok: true,
        message: `Removed the private plan “${plan.name}”.`,
      };
    },
    setActivePlan(planId) {
      const plan = snapshot.state.plans.find((item) => item.id === planId);

      if (!plan) {
        return {
          ok: false,
          message: "Choose an existing plan before setting it active.",
        };
      }

      setSnapshot((current) => ({
        ...current,
        activePlanId: planId,
      }));

      return {
        ok: true,
        message: `“${plan.name}” is now the active private plan.`,
      };
    },
    completeTodayTarget(planId) {
      const plan = planId
        ? snapshot.state.plans.find((item) => item.id === planId) ?? null
        : getActivePlan(snapshot);

      if (!plan) {
        return {
          ok: false,
          message: "Create a plan or set one active before completing today's target.",
        };
      }

      const metrics = getPlanMetrics(plan, snapshot);

      if (!metrics.todayRange) {
        return {
          ok: false,
          message: `“${plan.name}” is already complete.`,
        };
      }

      const result = value.markProgress({
        startReference: formatReference(metrics.todayRange.start),
        endReference: formatReference(metrics.todayRange.end),
        source: "plan_today",
      });

      if (!result.ok) {
        return result;
      }

      return {
        ok: true,
        message: `Completed today's target for “${plan.name}”: ${metrics.todayRange.label}.`,
      };
    },
    setReaderPreferences(patch) {
      setSnapshot((current) => ({
        ...current,
        preferences: {
          ...current.preferences,
          ...patch,
        },
      }));

      return {
        ok: true,
        message: "Reader defaults were saved to private browser storage.",
      };
    },
    clearStudyData() {
      setSnapshot(createBlankStudySnapshot());

      return {
        ok: true,
        message: "Local study state was cleared from this browser.",
      };
    },
  };

  return (
    <StudyStateContext.Provider value={value}>
      {children}
    </StudyStateContext.Provider>
  );
}

export function useStudyState() {
  const context = useContext(StudyStateContext);

  if (!context) {
    throw new Error("useStudyState must be used inside StudyStateProvider.");
  }

  return context;
}

function updatePlansAfterProgress(
  plans: readonly StudyPlan[],
  range: StudyRange,
  updatedAt: string,
) {
  const rangeEntries = getStudyRangeEntries(range);

  if (rangeEntries.length === 0) {
    return [...plans];
  }

  const coveredReferences = new Set(
    rangeEntries.map((entry) => entry.ayah.reference),
  );

  return plans.map((plan) => {
    const planEntries = getStudyRangeEntries(plan.range);
    const matchedEntries = planEntries.filter((entry) =>
      coveredReferences.has(entry.ayah.reference),
    );

    if (matchedEntries.length === 0) {
      return plan;
    }

    const latestReference = parseReferenceLabel(matchedEntries.at(-1)!.ayah.reference);

    if (!latestReference) {
      return plan;
    }

    const currentCompleted = plan.completedThrough
      ? compareReferenceOrder(plan.completedThrough, latestReference) > 0
        ? plan.completedThrough
        : latestReference
      : latestReference;

    return {
      ...plan,
      completedThrough: currentCompleted,
      updatedAt,
    };
  });
}

function singleAyahRange(reference: StudyReference) {
  return {
    start: reference,
    end: reference,
    label: formatReference(reference),
  };
}

function sanitizeLabel(value?: string) {
  const trimmed = value?.trim();
  return trimmed ? trimmed : null;
}

function appendActivity(
  activity: readonly StudyActivity[],
  nextEntry: StudyActivity,
) {
  return [nextEntry, ...activity].slice(0, 16);
}

function createActivity(
  kind: StudyActivity["kind"],
  message: string,
  createdAt: string,
): StudyActivity {
  return {
    id: generateStudyId("activity"),
    kind,
    message,
    createdAt,
  };
}

function compareReferenceOrder(left: StudyReference, right: StudyReference) {
  return left.surahNumber === right.surahNumber
    ? left.ayahNumber - right.ayahNumber
    : left.surahNumber - right.surahNumber;
}
