"use client";

import { useState } from "react";

import Link from "next/link";

import { useStudyState } from "@/components/study-state-provider";
import {
  compareReferenceLabels,
  formatReference,
  formatStudyDateTime,
  getActivePlan,
  getBundledReferenceOptions,
  getJuzProgressRows,
  getOverallProgress,
  getPlanMetrics,
  getReadingStreakDays,
  getSurahProgressRows,
} from "@/lib/study-data";

const referenceOptions = getBundledReferenceOptions();

export function ProgressExperience() {
  const { snapshot, clearProgress, completeTodayTarget, markProgress } =
    useStudyState();
  const [startReference, setStartReference] = useState<string>(
    snapshot.state.progress?.range.start
      ? formatReference(snapshot.state.progress.range.start)
      : referenceOptions[0]?.value ?? "1:1",
  );
  const [endReference, setEndReference] = useState<string>(
    snapshot.state.progress?.range.end
      ? formatReference(snapshot.state.progress.range.end)
      : referenceOptions[0]?.value ?? "1:1",
  );
  const [status, setStatus] = useState(
    "Latest checkpoints, completed ayahs, and plan updates stay in private browser storage.",
  );

  const activePlan = getActivePlan(snapshot);
  const activePlanMetrics = activePlan ? getPlanMetrics(activePlan, snapshot) : null;
  const overallProgress = getOverallProgress(snapshot);
  const streakDays = getReadingStreakDays(snapshot);
  const surahRows = getSurahProgressRows(snapshot);
  const juzRows = getJuzProgressRows(snapshot);
  const endOptions = referenceOptions.filter(
    (option) => compareReferenceLabels(option.value, startReference) >= 0,
  );

  function handleManualCheckpoint(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const result = markProgress({
      startReference,
      endReference,
      source: "manual_mark",
    });

    setStatus(result.message);
  }

  function handleCompleteTodayTarget() {
    const result = completeTodayTarget(activePlan?.id);
    setStatus(result.message);
  }

  function handleClearProgress() {
    const result = clearProgress();
    setStatus(result.message);
  }

  return (
    <div className="reader-layout">
      <section className="reader-panel reader-panel--spacious">
        <div className="section-copy max-w-3xl">
          <p className="section-label">Private reading tracker</p>
          <h2 className="section-title">
            Resume quietly, track steadily, and keep the Quran text central
          </h2>
          <p className="section-description">
            Progress in the web app is local-first and private by default. While
            QuranKit is still using the bundled reader sample, overall totals and
            checkpoints are calculated against the ayahs available in this web
            preview.
          </p>
        </div>

        <div className="study-stat-grid">
          <article className="surface-card surface-card--accent">
            <p className="section-label">Overall progress</p>
            <h3 className="surface-card__title">
              {overallProgress.completedAyahs} of {overallProgress.totalAyahs} ayahs
            </h3>
            <p className="surface-card__description">
              {overallProgress.percent}% of the bundled sample is marked complete.
            </p>
          </article>
          <article className="surface-card surface-card--warm">
            <p className="section-label">Last read</p>
            <h3 className="surface-card__title">
              {snapshot.state.progress?.range.label ?? "No checkpoint yet"}
            </h3>
            <p className="surface-card__description">
              {snapshot.state.progress
                ? `${formatStudyDateTime(snapshot.state.progress.updatedAt)} · ${snapshot.state.progress.source.replaceAll("_", " ")}`
                : "Mark a checkpoint here or from the reader to make resuming easier."}
            </p>
          </article>
          <article className="surface-card">
            <p className="section-label">Reading streak</p>
            <h3 className="surface-card__title">
              {streakDays} {streakDays === 1 ? "day" : "days"}
            </h3>
            <p className="surface-card__description">
              Streaks are derived from private checkpoint activity and are kept
              intentionally quiet.
            </p>
          </article>
          <article className="surface-card">
            <p className="section-label">Active plan</p>
            <h3 className="surface-card__title">
              {activePlan ? activePlan.name : "No active plan"}
            </h3>
            <p className="surface-card__description">
              {activePlanMetrics?.todayRange
                ? `Today's target: ${activePlanMetrics.todayRange.label}`
                : "Create or activate a plan to keep today's target visible here."}
            </p>
          </article>
        </div>

        <form className="reader-control-panel" onSubmit={handleManualCheckpoint}>
          <div className="search-filter-grid">
            <label className="reader-control-group">
              <span className="reader-control-label">Checkpoint start</span>
              <select
                value={startReference}
                onChange={(event) => {
                  const nextStartReference = event.target.value;
                  setStartReference(nextStartReference);

                  if (compareReferenceLabels(endReference, nextStartReference) < 0) {
                    setEndReference(nextStartReference);
                  }
                }}
                className="reader-select-input"
                aria-label="Checkpoint start"
              >
                {referenceOptions.map((option) => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </select>
            </label>
            <label className="reader-control-group">
              <span className="reader-control-label">Checkpoint end</span>
              <select
                value={endReference}
                onChange={(event) => setEndReference(event.target.value)}
                className="reader-select-input"
                aria-label="Checkpoint end"
              >
                {endOptions.map((option) => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </select>
            </label>
          </div>
          <div className="study-form-actions">
            <button type="submit" className="action-button action-button--selected">
              Save checkpoint
            </button>
            <button type="button" className="action-button" onClick={handleClearProgress}>
              Clear latest checkpoint
            </button>
            {activePlan ? (
              <button
                type="button"
                className="action-button"
                onClick={handleCompleteTodayTarget}
              >
                Mark today&apos;s target complete
              </button>
            ) : null}
          </div>
        </form>

        <p className="reader-status" aria-live="polite">
          {status}
        </p>

        <div className="card-grid">
          <article className="surface-card surface-card--accent">
            <p className="section-label">Today&apos;s target</p>
            <h3 className="surface-card__title">
              {activePlanMetrics?.todayRange?.label ?? "No target yet"}
            </h3>
            <p className="surface-card__description">
              {activePlan
                ? `${activePlan.name} is pacing ${activePlan.dailyAyahTarget} ayahs per day.`
                : "Create a plan on the plans page to surface today&apos;s target here."}
            </p>
            <div className="reader-inline-links">
              <Link href="/plans" className="reader-link">
                Review plans
              </Link>
              {snapshot.state.progress ? (
                <Link
                  href={`/ayah/${snapshot.state.progress.range.end.surahNumber}/${snapshot.state.progress.range.end.ayahNumber}`}
                  className="reader-link reader-link--muted"
                >
                  Resume last read
                </Link>
              ) : null}
            </div>
          </article>

          <article className="surface-card">
            <p className="section-label">Recent study activity</p>
            <h3 className="surface-card__title">Private timeline</h3>
            {snapshot.activity.length > 0 ? (
              <ul className="study-activity-list">
                {snapshot.activity.slice(0, 5).map((entry) => (
                  <li key={entry.id} className="study-activity-item">
                    <strong>{entry.message}</strong>
                    <span>{formatStudyDateTime(entry.createdAt)}</span>
                  </li>
                ))}
              </ul>
            ) : (
              <p className="surface-card__description">
                Progress activity will start appearing here after the first
                checkpoint, bookmark, note, or plan update.
              </p>
            )}
          </article>
        </div>

        <section className="section-block">
          <div className="section-copy">
            <p className="section-label">Progress by surah</p>
            <h3 className="section-title">Bundled sample coverage</h3>
            <p className="section-description">
              These rows reflect completed ayahs within the routed sample already
              available in QuranKit&apos;s web reader.
            </p>
          </div>
          <div className="study-meter-list">
            {surahRows.map((row) => (
              <ProgressMeterRow
                key={row.surah.number}
                label={`${row.surah.number} · ${row.surah.nameEnglish}`}
                detail={`${row.completedAyahs}/${row.totalAyahs} ayahs`}
                percent={row.percent}
              />
            ))}
          </div>
        </section>

        <section className="section-block">
          <div className="section-copy">
            <p className="section-label">Progress by juz</p>
            <h3 className="section-title">High-level bundled pacing</h3>
            <p className="section-description">
              Juz progress remains visible, but the interface stays restrained so
              the tracker supports reading instead of becoming a scoreboard.
            </p>
          </div>
          <div className="study-meter-list">
            {juzRows.map((row) => (
              <ProgressMeterRow
                key={row.juz}
                label={`Juz ${row.juz}`}
                detail={`${row.completedAyahs}/${row.totalAyahs} ayahs`}
                percent={row.percent}
              />
            ))}
          </div>
        </section>
      </section>

      <aside className="reader-panel reader-panel--support">
        <p className="section-label">Privacy cues</p>
        <h2 className="surface-card__title">
          Progress stays private and readable, not public or gamified
        </h2>
        <p className="surface-card__description">
          The tracker keeps resume cues, plan pacing, and completion summaries in
          browser storage by default. There is no public profile, leaderboard, or
          shared streak surface in this workflow.
        </p>
        <ul className="surface-card__list">
          <li>Progress totals are scoped to the bundled sample that powers the current web reader.</li>
          <li>Clearing the latest checkpoint does not wipe completed ayah totals unless local study data is cleared intentionally.</li>
          <li>Exports and storage details live in settings so the privacy boundary stays visible.</li>
        </ul>
        <div className="reader-inline-links">
          <Link href="/settings" className="reader-link">
            Export or clear local data
          </Link>
          <Link href="/bookmarks" className="reader-link reader-link--muted">
            Review bookmarks
          </Link>
          <Link href="/notes" className="reader-link reader-link--muted">
            Review notes
          </Link>
        </div>
      </aside>
    </div>
  );
}

type ProgressMeterRowProps = {
  label: string;
  detail: string;
  percent: number;
};

function ProgressMeterRow({ label, detail, percent }: ProgressMeterRowProps) {
  return (
    <article className="study-meter">
      <div className="study-meter__header">
        <div>
          <h4 className="surface-card__title">{label}</h4>
          <p className="surface-card__description">{detail}</p>
        </div>
        <strong className="study-meter__percent">{percent}%</strong>
      </div>
      <div className="study-meter__track" aria-hidden="true">
        <span className="study-meter__value" style={{ width: `${percent}%` }} />
      </div>
    </article>
  );
}
