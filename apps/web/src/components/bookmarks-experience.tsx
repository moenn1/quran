"use client";

import { useState } from "react";

import Link from "next/link";

import { useStudyState } from "@/components/study-state-provider";
import { bundledReaderAttribution } from "@/lib/reader-data";
import {
  formatStudyDateTime,
  getAyahPreview,
  getBundledReferenceOptions,
  type StudyBookmark,
} from "@/lib/study-data";

const referenceOptions = getBundledReferenceOptions();

export function BookmarksExperience() {
  const { saveBookmark, snapshot } = useStudyState();
  const [reference, setReference] = useState<string>(
    referenceOptions[0]?.value ?? "1:1",
  );
  const [label, setLabel] = useState("");
  const [query, setQuery] = useState("");
  const [labelFilter, setLabelFilter] = useState("all");
  const [status, setStatus] = useState(
    "Bookmarks stay in local browser storage unless you intentionally export them.",
  );

  const labelOptions = Array.from(
    new Set(
      snapshot.state.bookmarks
        .map((bookmark) => bookmark.label)
        .filter((value): value is string => Boolean(value)),
    ),
  ).sort((left, right) => left.localeCompare(right));

  const normalizedQuery = query.trim().toLowerCase();
  const filteredBookmarks = snapshot.state.bookmarks.filter((bookmark) => {
    const preview = getAyahPreview(bookmark.range.start);
    const matchesLabel = labelFilter === "all" || bookmark.label === labelFilter;

    if (!matchesLabel) {
      return false;
    }

    if (!normalizedQuery) {
      return true;
    }

    const searchable = [
      bookmark.range.label,
      bookmark.label ?? "",
      preview?.surah.nameEnglish ?? "",
      preview?.surah.nameArabic ?? "",
      preview?.surah.nameTranslation ?? "",
      preview?.ayah.translationText ?? "",
    ]
      .join(" ")
      .toLowerCase();

    return searchable.includes(normalizedQuery);
  });

  function handleAddBookmark(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const result = saveBookmark({
      reference,
      label,
    });

    setStatus(result.message);

    if (result.ok) {
      setLabel("");
    }
  }

  return (
    <div className="reader-layout">
      <section className="reader-panel reader-panel--spacious">
        <div className="section-copy max-w-3xl">
          <p className="section-label">Private bookmarks</p>
          <h2 className="section-title">
            Save ayahs with enough context to return without friction
          </h2>
          <p className="section-description">
            Bookmarks in QuranKit are private by default. This page makes them
            searchable and filterable while keeping the Quran text and
            translation attribution close to every preview.
          </p>
        </div>

        <form className="reader-control-panel" onSubmit={handleAddBookmark}>
          <div className="search-filter-grid">
            <label className="reader-control-group">
              <span className="reader-control-label">Reference</span>
              <select
                value={reference}
                onChange={(event) => setReference(event.target.value)}
                className="reader-select-input"
                aria-label="Bookmark reference"
              >
                {referenceOptions.map((option) => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </select>
            </label>
            <label className="reader-control-group">
              <span className="reader-control-label">Optional label</span>
              <input
                type="text"
                value={label}
                onChange={(event) => setLabel(event.target.value)}
                className="reader-search-input"
                placeholder="Revision, evening, or reflection"
              />
            </label>
            <label className="reader-control-group search-filter-grid__wide">
              <span className="reader-control-label">Find saved bookmarks</span>
              <input
                type="search"
                value={query}
                onChange={(event) => setQuery(event.target.value)}
                className="reader-search-input"
                placeholder="Search by reference, label, surah, or translation"
              />
            </label>
            <label className="reader-control-group">
              <span className="reader-control-label">Label filter</span>
              <select
                value={labelFilter}
                onChange={(event) => setLabelFilter(event.target.value)}
                className="reader-select-input"
                aria-label="Bookmark label filter"
              >
                <option value="all">All labels</option>
                {labelOptions.map((option) => (
                  <option key={option} value={option}>
                    {option}
                  </option>
                ))}
              </select>
            </label>
          </div>
          <div className="study-form-actions">
            <button type="submit" className="action-button action-button--selected">
              Save bookmark
            </button>
          </div>
        </form>

        <p className="reader-status" aria-live="polite">
          {status}
        </p>

        {filteredBookmarks.length > 0 ? (
          <div className="study-card-list">
            {filteredBookmarks.map((bookmark) => (
              <BookmarkCard
                key={bookmark.id}
                bookmark={bookmark}
                translationVisible={snapshot.preferences.translationVisible}
                onStatusChange={setStatus}
              />
            ))}
          </div>
        ) : (
          <div className="reader-empty-state">
            <h3 className="surface-card__title">No bookmark matches yet</h3>
            <p className="surface-card__description">
              Save a bundled sample ayah above, or bookmark from the reader and
              search pages so it appears here with its local context.
            </p>
          </div>
        )}
      </section>

      <aside className="reader-panel reader-panel--support">
        <p className="section-label">Attribution and privacy</p>
        <h2 className="surface-card__title">
          Bookmark previews keep source lines attached to the visible Quran text
        </h2>
        <p className="surface-card__description">
          Bookmark previews are designed to help you remember why an ayah mattered
          without turning the page into a feed or a public collection.
        </p>
        <ul className="surface-card__list">
          <li>{bundledReaderAttribution.arabic}</li>
          {snapshot.preferences.translationVisible ? (
            <li>{bundledReaderAttribution.translation}</li>
          ) : null}
          <li>Bookmark labels are optional and stay private in this browser until you export them intentionally.</li>
        </ul>
        <div className="reader-inline-links">
          <Link href="/settings" className="reader-link">
            Review export settings
          </Link>
          <Link href="/notes" className="reader-link reader-link--muted">
            Open private notes
          </Link>
        </div>
      </aside>
    </div>
  );
}

type BookmarkCardProps = {
  bookmark: StudyBookmark;
  translationVisible: boolean;
  onStatusChange: (message: string) => void;
};

function BookmarkCard({
  bookmark,
  translationVisible,
  onStatusChange,
}: BookmarkCardProps) {
  const { removeBookmark } = useStudyState();
  const preview = getAyahPreview(bookmark.range.start);

  if (!preview) {
    return null;
  }

  return (
    <article className="ayah-card ayah-card--reader">
      <div className="ayah-card__topline">
        <div className="ayah-card__heading">
          <span className="ayah-card__number">{bookmark.range.label}</span>
          <span className="search-match-chip">{preview.surah.nameEnglish}</span>
          {bookmark.label ? (
            <span className="search-match-chip search-match-chip--accent">
              {bookmark.label}
            </span>
          ) : null}
        </div>
        <span className="study-note-meta">
          Saved {formatStudyDateTime(bookmark.createdAt)}
        </span>
      </div>

      <p className="ayah-card__arabic ayah-card__arabic--reader" dir="rtl" lang="ar">
        {preview.ayah.arabicText}
      </p>
      {translationVisible ? (
        <p className="ayah-card__translation ayah-card__translation--reader">
          {preview.ayah.translationText}
        </p>
      ) : null}

      <div className="study-plan-summary">
        <p className="study-plan-summary__item">
          <strong>Surah</strong>
          <span>
            {preview.surah.number} · {preview.surah.nameTranslation}
          </span>
        </p>
        <p className="study-plan-summary__item">
          <strong>Juz</strong>
          <span>Juz {preview.juz}</span>
        </p>
      </div>

      <div className="study-form-actions">
        <Link
          href={`/ayah/${preview.surah.number}/${preview.ayah.ayahNumber}`}
          className="action-button action-button--link"
        >
          Open ayah detail
        </Link>
        <Link
          href={`/notes?reference=${encodeURIComponent(bookmark.range.label)}`}
          className="action-button action-button--link"
        >
          Add private note
        </Link>
        <button
          type="button"
          className="action-button"
          onClick={() => {
            const result = removeBookmark(bookmark.id);
            onStatusChange(result.message);
          }}
        >
          Remove
        </button>
      </div>
    </article>
  );
}
