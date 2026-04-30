"use client";

import { useState } from "react";
import type { CSSProperties } from "react";

import Link from "next/link";

import { useStudyState } from "@/components/study-state-provider";
import { cn } from "@/lib/cn";
import {
  bundledReaderAttribution,
  formatPageRange,
  formatRevelationPlace,
  type BundledAyah,
  type BundledSurah,
} from "@/lib/reader-data";
import { hasBookmarkForReference } from "@/lib/study-data";

type TextView = "balanced" | "arabic" | "translation";
type ArabicScale = "standard" | "large" | "majlis";
type TranslationScale = "compact" | "standard" | "roomy";

type ReaderWorkspaceProps = {
  surah: BundledSurah;
  ayahs: readonly BundledAyah[];
  focusReference?: string;
  navigationLabel: string;
};

type AyahActionBarProps = {
  surahNumber: number;
  ayah: BundledAyah;
  translationVisible: boolean;
};

const arabicScaleVars: Record<ArabicScale, string> = {
  standard: "clamp(2rem, 4.8vw, 2.9rem)",
  large: "clamp(2.35rem, 5.6vw, 3.35rem)",
  majlis: "clamp(2.7rem, 6.3vw, 3.8rem)",
};

const translationScaleVars: Record<TranslationScale, string> = {
  compact: "0.98rem",
  standard: "1.05rem",
  roomy: "1.16rem",
};

export function ReaderWorkspace({
  surah,
  ayahs,
  focusReference,
  navigationLabel,
}: ReaderWorkspaceProps) {
  const { setReaderPreferences, snapshot } = useStudyState();
  const [translationVisible, setTranslationVisible] = useState(
    snapshot.preferences.translationVisible,
  );
  const [textView, setTextView] = useState<TextView>(snapshot.preferences.textView);
  const [arabicScale, setArabicScale] = useState<ArabicScale>(
    snapshot.preferences.arabicScale,
  );
  const [translationScale, setTranslationScale] = useState<TranslationScale>(
    snapshot.preferences.translationScale,
  );

  const style = {
    "--reader-arabic-size": arabicScaleVars[arabicScale],
    "--reader-translation-size": translationScaleVars[translationScale],
  } as CSSProperties;

  return (
    <div
      className="reader-layout"
      data-text-view={textView}
      data-arabic-scale={arabicScale}
      data-translation-scale={translationScale}
      style={style}
    >
      <section className="reader-panel reader-panel--spacious">
        <div className="reader-panel__header">
          <div>
            <p className="section-label">{navigationLabel}</p>
            <h2 className="section-title">
              {surah.nameEnglish} reader sample
            </h2>
          </div>
          <div className="reader-panel__meta">
            <span>{surah.nameTranslation}</span>
            <span>{formatRevelationPlace(surah.revelationPlace)}</span>
            <span>{surah.ayahCount} ayahs</span>
            <span>{formatPageRange(surah.pages)}</span>
          </div>
        </div>
        <ol className="ayah-list ayah-list--reader">
          {ayahs.map((ayah) => {
            const isFocused = ayah.reference === focusReference;

            return (
              <li key={ayah.reference}>
                <article
                  id={`ayah-${ayah.ayahNumber}`}
                  className={cn("ayah-card ayah-card--reader", isFocused && "ayah-card--focus")}
                >
                  <div className="ayah-card__topline">
                    <div className="ayah-card__heading">
                      <span className="ayah-card__number">
                        Ayah {ayah.ayahNumber}
                      </span>
                      <Link
                        href={`/ayah/${surah.number}/${ayah.ayahNumber}`}
                        className="ayah-card__reference"
                      >
                        {ayah.reference}
                      </Link>
                    </div>
                    {isFocused ? (
                      <span className="ayah-card__focus-tag">Focused ayah</span>
                    ) : null}
                  </div>
                  {textView === "translation" && translationVisible ? (
                    <p className="ayah-card__translation ayah-card__translation--reader ayah-card__translation--lead">
                      {ayah.translationText}
                    </p>
                  ) : null}
                  <p
                    className={cn(
                      "ayah-card__arabic ayah-card__arabic--reader",
                      textView === "arabic" && "ayah-card__arabic--lead",
                    )}
                    dir="rtl"
                    lang="ar"
                  >
                    {ayah.arabicText}
                  </p>
                  {textView !== "translation" && translationVisible ? (
                    <p className="ayah-card__translation ayah-card__translation--reader">
                      {ayah.translationText}
                    </p>
                  ) : null}
                  <AyahActionBar
                    surahNumber={surah.number}
                    ayah={ayah}
                    translationVisible={translationVisible}
                  />
                </article>
              </li>
            );
          })}
        </ol>
      </section>
      <aside className="reader-panel reader-panel--support">
        <div className="reader-control-group">
          <span className="reader-control-label">Translation</span>
          <button
            type="button"
            className={cn(
              "reader-toggle",
              translationVisible && "reader-toggle--selected",
            )}
            aria-pressed={translationVisible}
            onClick={() => {
              const nextValue = !translationVisible;
              setTranslationVisible(nextValue);
              setReaderPreferences({ translationVisible: nextValue });
            }}
          >
            {translationVisible ? "Hide translation" : "Show translation"}
          </button>
        </div>
        <div className="reader-control-group">
          <span className="reader-control-label">Text view</span>
          <div className="segmented-control" role="group" aria-label="Text view">
            {[
              ["balanced", "Balanced"],
              ["arabic", "Arabic focus"],
              ["translation", "Translation focus"],
            ].map(([value, label]) => {
              const selected = textView === value;

              return (
                <button
                  key={value}
                  type="button"
                  className={cn(
                    "segmented-control__button",
                    selected && "segmented-control__button--selected",
                  )}
                  aria-pressed={selected}
                  onClick={() => {
                    const nextValue = value as TextView;
                    setTextView(nextValue);
                    setReaderPreferences({ textView: nextValue });
                  }}
                >
                  {label}
                </button>
              );
            })}
          </div>
        </div>
        <div className="reader-control-group">
          <span className="reader-control-label">Arabic size</span>
          <div className="segmented-control" role="group" aria-label="Arabic text size">
            {[
              ["standard", "Standard"],
              ["large", "Large"],
              ["majlis", "Majlis"],
            ].map(([value, label]) => {
              const selected = arabicScale === value;

              return (
                <button
                  key={value}
                  type="button"
                  className={cn(
                    "segmented-control__button",
                    selected && "segmented-control__button--selected",
                  )}
                  aria-pressed={selected}
                  onClick={() => {
                    const nextValue = value as ArabicScale;
                    setArabicScale(nextValue);
                    setReaderPreferences({ arabicScale: nextValue });
                  }}
                >
                  {label}
                </button>
              );
            })}
          </div>
        </div>
        <div className="reader-control-group">
          <span className="reader-control-label">Translation size</span>
          <div
            className="segmented-control"
            role="group"
            aria-label="Translation text size"
          >
            {[
              ["compact", "Compact"],
              ["standard", "Standard"],
              ["roomy", "Roomy"],
            ].map(([value, label]) => {
              const selected = translationScale === value;

              return (
                <button
                  key={value}
                  type="button"
                  className={cn(
                    "segmented-control__button",
                    selected && "segmented-control__button--selected",
                  )}
                  aria-pressed={selected}
                  disabled={!translationVisible}
                  onClick={() => {
                    const nextValue = value as TranslationScale;
                    setTranslationScale(nextValue);
                    setReaderPreferences({ translationScale: nextValue });
                  }}
                >
                  {label}
                </button>
              );
            })}
          </div>
        </div>
        <div className="reader-inline-links">
          <Link href="/bookmarks" className="reader-link">
            Bookmarks stay private
          </Link>
          <Link href="/notes" className="reader-link reader-link--muted">
            Notes stay local-first
          </Link>
          <Link href="/settings" className="reader-link reader-link--muted">
            Adjust reader settings
          </Link>
        </div>
        <p className="reader-status reader-status--compact">
          Bookmark and read-marker actions in this preview are private by
          default and scoped to the local reader surface.
        </p>
        <div className="reader-attribution">
          <p className="attribution">{bundledReaderAttribution.arabic}</p>
          <p className="attribution">{bundledReaderAttribution.translation}</p>
          <p className="reader-preview__note">{bundledReaderAttribution.note}</p>
        </div>
      </aside>
    </div>
  );
}

function AyahActionBar({
  surahNumber,
  ayah,
  translationVisible,
}: AyahActionBarProps) {
  const { clearProgress, markProgress, snapshot, toggleBookmark } = useStudyState();
  const [status, setStatus] = useState("");
  const bookmarked = hasBookmarkForReference(snapshot, ayah.reference);
  const read =
    snapshot.state.progress?.range.start.surahNumber === surahNumber &&
    snapshot.state.progress.range.start.ayahNumber === ayah.ayahNumber &&
    snapshot.state.progress.range.end.surahNumber === surahNumber &&
    snapshot.state.progress.range.end.ayahNumber === ayah.ayahNumber;

  async function copyAyah() {
    const text = [
      ayah.reference,
      ayah.arabicText,
      translationVisible ? ayah.translationText : null,
      bundledReaderAttribution.arabic,
      translationVisible ? bundledReaderAttribution.translation : null,
    ]
      .filter(Boolean)
      .join("\n\n");

    if (!navigator.clipboard?.writeText) {
      setStatus(`Clipboard is unavailable for ${ayah.reference}.`);
      return;
    }

    try {
      await navigator.clipboard.writeText(text);
      setStatus(`Copied ${ayah.reference} with attribution.`);
    } catch {
      setStatus(`Unable to copy ${ayah.reference} right now.`);
    }
  }

  return (
    <div className="ayah-actions">
      <div className="ayah-actions__row">
        <button
          type="button"
          className={cn("action-button", bookmarked && "action-button--selected")}
          aria-pressed={bookmarked}
          onClick={() => {
            const result = toggleBookmark({ reference: ayah.reference });
            setStatus(result.message);
          }}
        >
          {bookmarked ? "Bookmarked" : "Bookmark"}
        </button>
        <Link
          href={`/notes?reference=${encodeURIComponent(ayah.reference)}`}
          className="action-button action-button--link"
        >
          Private note
        </Link>
        <button
          type="button"
          className={cn("action-button", read && "action-button--selected")}
          aria-pressed={read}
          onClick={() => {
            const result = read
              ? clearProgress()
              : markProgress({
                  startReference: ayah.reference,
                  source: "reader_action",
                });
            setStatus(result.message);
          }}
        >
          {read ? "Checkpoint saved" : "Mark read"}
        </button>
        <button type="button" className="action-button" onClick={() => void copyAyah()}>
          Copy ayah
        </button>
      </div>
      <p className="ayah-actions__status" aria-live="polite">
        {status || "Study actions remain private by default."}
      </p>
    </div>
  );
}
