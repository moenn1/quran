"use client";

import { useState } from "react";

import Link from "next/link";

import { useStudyState } from "@/components/study-state-provider";
import {
  compareReferenceLabels,
  formatStudyDate,
  getActivePlan,
  getBundledReferenceOptions,
  getPlanMetrics,
  type StudyPlan,
} from "@/lib/study-data";

const referenceOptions = getBundledReferenceOptions();

export function PlansExperience() {
  const { completeTodayTarget, createPlan, setActivePlan, snapshot } = useStudyState();
  const [name, setName] = useState("Morning review");
  const [startReference, setStartReference] = useState<string>("112:1");
  const [endReference, setEndReference] = useState<string>("114:6");
  const [dailyAyahTarget, setDailyAyahTarget] = useState(3);
  const [status, setStatus] = useState(
    "Plans stay private by default and are stored in the browser until QuranKit adds authenticated sync.",
  );

  const activePlan = getActivePlan(snapshot);
  const endOptions = referenceOptions.filter(
    (option) => compareReferenceLabels(option.value, startReference) >= 0,
  );

  function handleCreatePlan(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();

    const result = createPlan({
      name,
      startReference,
      endReference,
      dailyAyahTarget,
    });

    setStatus(result.message);

    if (result.ok) {
      setName("Steady review");
      setDailyAyahTarget(3);
    }
  }

  return (
    <div className="reader-layout">
      <section className="reader-panel reader-panel--spacious">
        <div className="section-copy max-w-3xl">
          <p className="section-label">Reading plans</p>
          <h2 className="section-title">
            Create a private cadence, then recalculate it without friction
          </h2>
          <p className="section-description">
            Plans in QuranKit stay personal and editable. They are meant to make
            today&apos;s reading clearer, not force a rigid calendar or a public
            accountability layer.
          </p>
        </div>

        <form className="reader-control-panel" onSubmit={handleCreatePlan}>
          <div className="search-filter-grid">
            <label className="reader-control-group search-filter-grid__wide">
              <span className="reader-control-label">Plan name</span>
              <input
                type="text"
                value={name}
                onChange={(event) => setName(event.target.value)}
                className="reader-search-input"
                placeholder="Morning review"
              />
            </label>
            <label className="reader-control-group">
              <span className="reader-control-label">Start reference</span>
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
                aria-label="Plan start reference"
              >
                {referenceOptions.map((option) => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </select>
            </label>
            <label className="reader-control-group">
              <span className="reader-control-label">End reference</span>
              <select
                value={endReference}
                onChange={(event) => setEndReference(event.target.value)}
                className="reader-select-input"
                aria-label="Plan end reference"
              >
                {endOptions.map((option) => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </select>
            </label>
            <label className="reader-control-group">
              <span className="reader-control-label">Daily target</span>
              <select
                value={dailyAyahTarget}
                onChange={(event) => setDailyAyahTarget(Number(event.target.value))}
                className="reader-select-input"
                aria-label="Daily target"
              >
                {[1, 2, 3, 4, 5, 6].map((value) => (
                  <option key={value} value={value}>
                    {value} {value === 1 ? "ayah" : "ayahs"} per day
                  </option>
                ))}
              </select>
            </label>
          </div>
          <div className="study-form-actions">
            <button type="submit" className="action-button action-button--selected">
              Create private plan
            </button>
            {activePlan ? (
              <button
                type="button"
                className="action-button"
                onClick={() => {
                  const result = setActivePlan(activePlan.id);
                  setStatus(result.message);
                }}
              >
                Keep current active plan
              </button>
            ) : null}
          </div>
        </form>

        <p className="reader-status" aria-live="polite">
          {status}
        </p>

        {snapshot.state.plans.length > 0 ? (
          <div className="study-card-list">
            {snapshot.state.plans.map((plan) => (
              <PlanCard
                key={plan.id}
                plan={plan}
                isActive={plan.id === activePlan?.id}
                onStatusChange={setStatus}
                onCompleteTodayTarget={completeTodayTarget}
                onSetActivePlan={setActivePlan}
              />
            ))}
          </div>
        ) : (
          <div className="reader-empty-state">
            <h3 className="surface-card__title">No private plan yet</h3>
            <p className="surface-card__description">
              Create a reading cadence above, or use the reader and progress pages
              first, then come back once you know which bundled sample range you
              want to pace.
            </p>
          </div>
        )}
      </section>

      <aside className="reader-panel reader-panel--support">
        <p className="section-label">Plan guidance</p>
        <h2 className="surface-card__title">
          Active plans surface today&apos;s target without overbuilding the workflow
        </h2>
        <p className="surface-card__description">
          Each plan exposes a current checkpoint, a daily ayah target, and a
          direct path back into the reader. Recalculation is limited to what a
          private study tool actually needs right now.
        </p>
        <ul className="surface-card__list">
          <li>Creating a plan automatically sets it active so progress pages can highlight today&apos;s target.</li>
          <li>Recalculation adjusts only the daily ayah target and the next visible range.</li>
          <li>Plan completion is derived from local checkpoint history inside the bundled sample.</li>
        </ul>
        <div className="reader-inline-links">
          <Link href="/progress" className="reader-link">
            View progress summary
          </Link>
          <Link href="/reader" className="reader-link reader-link--muted">
            Return to the reader
          </Link>
        </div>
      </aside>
    </div>
  );
}

type PlanCardProps = {
  plan: StudyPlan;
  isActive: boolean;
  onStatusChange: (message: string) => void;
  onCompleteTodayTarget: (planId?: string) => { ok: boolean; message: string };
  onSetActivePlan: (planId: string) => { ok: boolean; message: string };
};

function PlanCard({
  plan,
  isActive,
  onStatusChange,
  onCompleteTodayTarget,
  onSetActivePlan,
}: PlanCardProps) {
  const { removePlan, updatePlan, snapshot } = useStudyState();
  const [nextDailyTarget, setNextDailyTarget] = useState(plan.dailyAyahTarget);
  const metrics = getPlanMetrics(plan, snapshot);

  return (
    <article className="surface-card surface-card--warm">
      <div className="study-card-header">
        <div>
          <div className="study-tag-row">
            <span className="surah-chip">{plan.range.label}</span>
            {isActive ? <span className="study-tag study-tag--accent">Active plan</span> : null}
          </div>
          <h3 className="surface-card__title">{plan.name}</h3>
          <p className="surface-card__description">
            {metrics.completedAyahs}/{metrics.totalAyahs} ayahs complete · updated{" "}
            {formatStudyDate(plan.updatedAt)}
          </p>
        </div>
        <strong className="study-meter__percent">
          {metrics.completed ? "Done" : `${metrics.remainingAyahs} left`}
        </strong>
      </div>

      <div className="study-meter__track" aria-hidden="true">
        <span
          className="study-meter__value"
          style={{
            width:
              metrics.totalAyahs === 0
                ? "0%"
                : `${Math.round((metrics.completedAyahs / metrics.totalAyahs) * 100)}%`,
          }}
        />
      </div>

      <div className="study-plan-summary">
        <p className="study-plan-summary__item">
          <strong>Today&apos;s target</strong>
          <span>{metrics.todayRange?.label ?? "Plan complete"}</span>
        </p>
        <p className="study-plan-summary__item">
          <strong>Daily target</strong>
          <span>
            {plan.dailyAyahTarget} {plan.dailyAyahTarget === 1 ? "ayah" : "ayahs"}
          </span>
        </p>
      </div>

      <div className="study-plan-recalibrate">
        <label className="reader-control-group">
          <span className="reader-control-label">{plan.name} target</span>
          <select
            value={nextDailyTarget}
            onChange={(event) => setNextDailyTarget(Number(event.target.value))}
            className="reader-select-input"
            aria-label={`${plan.name} daily target`}
          >
            {[1, 2, 3, 4, 5, 6].map((value) => (
              <option key={value} value={value}>
                {value} {value === 1 ? "ayah" : "ayahs"} per day
              </option>
            ))}
          </select>
        </label>
      </div>

      <div className="study-form-actions">
        <button
          type="button"
          className="action-button action-button--selected"
          onClick={() => {
            const result = onCompleteTodayTarget(plan.id);
            onStatusChange(result.message);
          }}
        >
          Mark today&apos;s target
        </button>
        <button
          type="button"
          className="action-button"
          onClick={() => {
            const result = updatePlan(plan.id, { dailyAyahTarget: nextDailyTarget });
            onStatusChange(result.message);
          }}
        >
          Recalculate plan
        </button>
        {!isActive ? (
          <button
            type="button"
            className="action-button"
            onClick={() => {
              const result = onSetActivePlan(plan.id);
              onStatusChange(result.message);
            }}
          >
            Set active
          </button>
        ) : null}
        <button
          type="button"
          className="action-button"
          onClick={() => {
            const result = removePlan(plan.id);
            onStatusChange(result.message);
          }}
        >
          Remove
        </button>
        <Link
          href={
            metrics.todayRange
              ? `/ayah/${metrics.todayRange.start.surahNumber}/${metrics.todayRange.start.ayahNumber}`
              : `/surah/${plan.range.start.surahNumber}`
          }
          className="action-button action-button--link"
        >
          Open in reader
        </Link>
      </div>
    </article>
  );
}
