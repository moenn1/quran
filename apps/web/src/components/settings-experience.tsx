"use client";

import { useState } from "react";

import Link from "next/link";

import { useStudyState } from "@/components/study-state-provider";
import { bundledReaderAttribution } from "@/lib/reader-data";
import {
  buildStudyExportPayload,
  STUDY_REMOTE_ENDPOINTS,
  STUDY_STORAGE_KEY,
} from "@/lib/study-data";

export function SettingsExperience() {
  const { clearStudyData, setReaderPreferences, snapshot } = useStudyState();
  const [exportPreview, setExportPreview] = useState("");
  const [exportFilename, setExportFilename] = useState("qurankit-study-state.json");
  const [status, setStatus] = useState(
    "Reader defaults, export previews, and storage information stay private in this browser until you choose otherwise.",
  );
  const [armedForClear, setArmedForClear] = useState(false);

  function updatePreference(
    patch: Parameters<typeof setReaderPreferences>[0],
    message?: string,
  ) {
    const result = setReaderPreferences(patch);
    setStatus(message ?? result.message);
  }

  function previewExport(scope: "full" | "progress" | "bookmarks" | "notes") {
    const payload = buildStudyExportPayload(snapshot, scope);
    setExportPreview(JSON.stringify(payload, null, 2));
    setExportFilename(`qurankit-${scope}.json`);
    setStatus(`Prepared the ${scope} export preview locally.`);
  }

  async function copyExportPreview() {
    if (!exportPreview) {
      setStatus("Prepare an export preview before copying it.");
      return;
    }

    if (!navigator.clipboard?.writeText) {
      setStatus("Clipboard access is unavailable in this browser.");
      return;
    }

    try {
      await navigator.clipboard.writeText(exportPreview);
      setStatus(`Copied ${exportFilename} to the clipboard.`);
    } catch {
      setStatus("Unable to copy the export preview right now.");
    }
  }

  function downloadExportPreview() {
    if (!exportPreview) {
      setStatus("Prepare an export preview before downloading it.");
      return;
    }

    const blob = new Blob([exportPreview], { type: "application/json" });
    const url = window.URL.createObjectURL(blob);
    const anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = exportFilename;
    anchor.click();
    window.URL.revokeObjectURL(url);
    setStatus(`Downloaded ${exportFilename}.`);
  }

  return (
    <div className="reader-layout">
      <section className="reader-panel reader-panel--spacious">
        <div className="section-copy max-w-3xl">
          <p className="section-label">Reader settings</p>
          <h2 className="section-title">
            Reader defaults, source clarity, and export boundaries stay visible
          </h2>
          <p className="section-description">
            Settings in QuranKit focus on what materially affects reading:
            translation visibility, text emphasis, preferred sizing, storage
            clarity, and deliberate exports.
          </p>
        </div>

        <div className="card-grid">
          <article className="surface-card surface-card--warm">
            <p className="section-label">Translation display</p>
            <h3 className="surface-card__title">
              {snapshot.preferences.translationVisible ? "Translation shown" : "Arabic only"}
            </h3>
            <div className="segmented-control" role="group" aria-label="Translation display">
              <button
                type="button"
                className={`segmented-control__button${snapshot.preferences.translationVisible ? " segmented-control__button--selected" : ""}`}
                aria-pressed={snapshot.preferences.translationVisible}
                onClick={() =>
                  updatePreference(
                    { translationVisible: true },
                    "Translation previews will stay visible in the reader and bookmark cards.",
                  )
                }
              >
                Show translation
              </button>
              <button
                type="button"
                className={`segmented-control__button${!snapshot.preferences.translationVisible ? " segmented-control__button--selected" : ""}`}
                aria-pressed={!snapshot.preferences.translationVisible}
                onClick={() =>
                  updatePreference(
                    { translationVisible: false },
                    "The reader will default to Arabic-only previews until you change it back.",
                  )
                }
              >
                Arabic only
              </button>
            </div>
          </article>

          <article className="surface-card">
            <p className="section-label">Text view</p>
            <h3 className="surface-card__title">
              {snapshot.preferences.textView === "balanced"
                ? "Balanced"
                : snapshot.preferences.textView === "arabic"
                  ? "Arabic focus"
                  : "Translation focus"}
            </h3>
            <div className="segmented-control" role="group" aria-label="Reader text view">
              {[
                ["balanced", "Balanced"],
                ["arabic", "Arabic focus"],
                ["translation", "Translation focus"],
              ].map(([value, label]) => {
                const selected = snapshot.preferences.textView === value;

                return (
                  <button
                    key={value}
                    type="button"
                    className={`segmented-control__button${selected ? " segmented-control__button--selected" : ""}`}
                    aria-pressed={selected}
                    onClick={() =>
                      updatePreference(
                        { textView: value as typeof snapshot.preferences.textView },
                        `${label} is now the default reader emphasis.`,
                      )
                    }
                  >
                    {label}
                  </button>
                );
              })}
            </div>
          </article>

          <article className="surface-card">
            <p className="section-label">Arabic size</p>
            <h3 className="surface-card__title">{snapshot.preferences.arabicScale}</h3>
            <div className="segmented-control" role="group" aria-label="Arabic size">
              {[
                ["standard", "Standard"],
                ["large", "Large"],
                ["majlis", "Majlis"],
              ].map(([value, label]) => {
                const selected = snapshot.preferences.arabicScale === value;

                return (
                  <button
                    key={value}
                    type="button"
                    className={`segmented-control__button${selected ? " segmented-control__button--selected" : ""}`}
                    aria-pressed={selected}
                    onClick={() =>
                      updatePreference(
                        { arabicScale: value as typeof snapshot.preferences.arabicScale },
                        `${label} Arabic sizing is now the default reader scale.`,
                      )
                    }
                  >
                    {label}
                  </button>
                );
              })}
            </div>
          </article>

          <article className="surface-card">
            <p className="section-label">Translation size</p>
            <h3 className="surface-card__title">{snapshot.preferences.translationScale}</h3>
            <div className="segmented-control" role="group" aria-label="Translation size">
              {[
                ["compact", "Compact"],
                ["standard", "Standard"],
                ["roomy", "Roomy"],
              ].map(([value, label]) => {
                const selected = snapshot.preferences.translationScale === value;

                return (
                  <button
                    key={value}
                    type="button"
                    className={`segmented-control__button${selected ? " segmented-control__button--selected" : ""}`}
                    aria-pressed={selected}
                    onClick={() =>
                      updatePreference(
                        {
                          translationScale:
                            value as typeof snapshot.preferences.translationScale,
                        },
                        `${label} translation sizing is now the default reader scale.`,
                      )
                    }
                    disabled={!snapshot.preferences.translationVisible}
                  >
                    {label}
                  </button>
                );
              })}
            </div>
          </article>
        </div>

        <div className="card-grid">
          <article className="surface-card surface-card--accent">
            <p className="section-label">Motion preference</p>
            <h3 className="surface-card__title">
              {snapshot.preferences.reducedMotion ? "Reduced motion" : "Standard motion"}
            </h3>
            <p className="surface-card__description">
              Reduced motion disables interface transitions in the current shell
              so the reading surface stays calm.
            </p>
            <div className="study-form-actions">
              <button
                type="button"
                className={`action-button${!snapshot.preferences.reducedMotion ? " action-button--selected" : ""}`}
                onClick={() =>
                  updatePreference(
                    { reducedMotion: false },
                    "Standard motion is now the default for this browser.",
                  )
                }
              >
                Standard motion
              </button>
              <button
                type="button"
                className={`action-button${snapshot.preferences.reducedMotion ? " action-button--selected" : ""}`}
                onClick={() =>
                  updatePreference(
                    { reducedMotion: true },
                    "Reduced motion is now enabled for this browser.",
                  )
                }
              >
                Reduce motion
              </button>
            </div>
          </article>

          <article className="surface-card">
            <p className="section-label">Source attribution</p>
            <h3 className="surface-card__title">Visible on every text surface</h3>
            <ul className="surface-card__list">
              <li>{bundledReaderAttribution.arabic}</li>
              <li>{bundledReaderAttribution.translation}</li>
              <li>Arabic-only display hides translations visually but does not remove source clarity from the broader settings surface.</li>
            </ul>
          </article>
        </div>

        <div className="card-grid">
          <article className="surface-card">
            <p className="section-label">Storage mode</p>
            <h3 className="surface-card__title">Local-first browser storage</h3>
            <p className="surface-card__description">
              The current web UI stores progress, bookmarks, notes, plans, and
              reader defaults locally under `{STUDY_STORAGE_KEY}`.
            </p>
            <ul className="surface-card__list">
              {STUDY_REMOTE_ENDPOINTS.map((endpoint) => (
                <li key={endpoint}>
                  Remote sync contract preview: <code>{endpoint}</code>
                </li>
              ))}
              <li>Authenticated sync is not wired into this web slice yet, so changing settings does not send data to a server.</li>
            </ul>
          </article>

          <article className="surface-card surface-card--warm">
            <p className="section-label">Export preview</p>
            <h3 className="surface-card__title">Deliberate JSON exports only</h3>
            <div className="study-form-actions">
              <button type="button" className="action-button" onClick={() => previewExport("full")}>
                Full study state
              </button>
              <button
                type="button"
                className="action-button"
                onClick={() => previewExport("progress")}
              >
                Progress only
              </button>
              <button
                type="button"
                className="action-button"
                onClick={() => previewExport("bookmarks")}
              >
                Bookmarks only
              </button>
              <button type="button" className="action-button" onClick={() => previewExport("notes")}>
                Notes only
              </button>
            </div>
            {exportPreview ? (
              <>
                <pre className="study-json-preview">{exportPreview}</pre>
                <div className="study-form-actions">
                  <button type="button" className="action-button" onClick={() => void copyExportPreview()}>
                    Copy JSON
                  </button>
                  <button type="button" className="action-button" onClick={downloadExportPreview}>
                    Download JSON
                  </button>
                </div>
              </>
            ) : (
              <p className="surface-card__description">
                Prepare an export preview first so the JSON boundary is visible
                before anything leaves the browser.
              </p>
            )}
          </article>
        </div>

        <div className="study-danger-zone">
          <div>
            <p className="section-label">Clear local data</p>
            <h3 className="surface-card__title">Keep destructive actions deliberate</h3>
            <p className="surface-card__description">
              Clearing local study data removes browser-stored progress,
              bookmarks, notes, plans, and reader defaults on this device.
            </p>
          </div>
          <label className="search-checkbox-row">
            <input
              type="checkbox"
              checked={armedForClear}
              onChange={(event) => setArmedForClear(event.target.checked)}
            />
            <span>I understand this clears private local study data on this browser.</span>
          </label>
          <div className="study-form-actions">
            <button
              type="button"
              className="action-button"
              disabled={!armedForClear}
              onClick={() => {
                const result = clearStudyData();
                setStatus(result.message);
                setExportPreview("");
                setArmedForClear(false);
              }}
            >
              Clear local study data
            </button>
          </div>
        </div>

        <p className="reader-status" aria-live="polite">
          {status}
        </p>
      </section>

      <aside className="reader-panel reader-panel--support">
        <p className="section-label">Settings links</p>
        <h2 className="surface-card__title">
          Reader defaults apply across the local study workflow
        </h2>
        <p className="surface-card__description">
          Translation visibility and text sizing affect the routed reader and the
          bookmark previews built from the same bundled sample. Progress, plan,
          and note state stay local unless exported intentionally.
        </p>
        <div className="reader-inline-links">
          <Link href="/progress" className="reader-link">
            Review progress
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
