"use client";

import { useDeferredValue, useState } from "react";
import type { ReactNode } from "react";

import Link from "next/link";

import { cn } from "@/lib/cn";
import {
  bundledReaderAttribution,
  type BundledAyah,
  type BundledSurah,
  type RevelationPlace,
} from "@/lib/reader-data";
import {
  exactSearchScopeOptions,
  getBundledJuzOptions,
  getBundledSurahOptions,
  runExactSearch,
  type ExactSearchScope,
} from "@/lib/search-data";

type ExactSearchExperienceProps = {
  surahs: readonly BundledSurah[];
};

export function ExactSearchExperience({ surahs }: ExactSearchExperienceProps) {
  const [query, setQuery] = useState("truth");
  const [scope, setScope] = useState<ExactSearchScope>("all");
  const [surahFilter, setSurahFilter] = useState<number | "all">("all");
  const [revelationFilter, setRevelationFilter] =
    useState<RevelationPlace | "all">("all");

  const deferredQuery = useDeferredValue(query);
  const results = runExactSearch({
    surahs,
    query: deferredQuery,
    scope,
    surahFilter,
    revelationFilter,
  });
  const surahOptions = getBundledSurahOptions(surahs);
  const juzOptions = getBundledJuzOptions(surahs);
  const trimmedQuery = deferredQuery.trim();

  return (
    <div className="reader-layout">
      <section className="reader-panel reader-panel--spacious">
        <div className="section-copy max-w-3xl">
          <p className="section-label">Search interface</p>
          <h2 className="section-title">
            Filters stay visible so every exact match remains explainable
          </h2>
          <p className="section-description">
            Search the bundled sample by Arabic text, translation, or metadata,
            then move into ayah context without silently switching to
            similarity-based retrieval.
          </p>
        </div>

        <div className="reader-control-panel">
          <div className="search-filter-grid">
            <label className="reader-control-group search-filter-grid__wide">
              <span className="reader-control-label">Exact query</span>
              <input
                type="search"
                value={query}
                onChange={(event) => setQuery(event.target.value)}
                className="reader-search-input"
                placeholder="Try truth, الرحیم, 98:5, or Medinan"
              />
            </label>

            <div className="reader-control-group search-filter-grid__wide">
              <span className="reader-control-label">Search scope</span>
              <div className="segmented-control" role="group" aria-label="Exact search scope">
                {exactSearchScopeOptions.map((option) => {
                  const selected = scope === option.value;

                  return (
                    <button
                      key={option.value}
                      type="button"
                      className={cn(
                        "segmented-control__button",
                        selected && "segmented-control__button--selected",
                      )}
                      aria-pressed={selected}
                      onClick={() => setScope(option.value)}
                    >
                      {option.label}
                    </button>
                  );
                })}
              </div>
            </div>

            <label className="reader-control-group">
              <span className="reader-control-label">Revelation place</span>
              <select
                value={revelationFilter}
                onChange={(event) =>
                  setRevelationFilter(event.target.value as RevelationPlace | "all")
                }
                className="reader-select-input"
                aria-label="Revelation place"
              >
                <option value="all">All sample revelations</option>
                <option value="makkah">Meccan sample surahs</option>
                <option value="madinah">Medinan sample surahs</option>
              </select>
            </label>

            <label className="reader-control-group">
              <span className="reader-control-label">Surah</span>
              <select
                value={surahFilter}
                onChange={(event) =>
                  setSurahFilter(
                    event.target.value === "all" ? "all" : Number(event.target.value),
                  )
                }
                className="reader-select-input"
                aria-label="Surah"
              >
                <option value="all">All bundled sample surahs</option>
                {surahOptions.map((option) => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </select>
            </label>
          </div>
        </div>

        <p className="reader-status" aria-live="polite">
          {trimmedQuery.length === 0
            ? "Enter an Arabic phrase, English phrase, reference, or surah name to run an exact search."
            : `Showing ${results.length} exact ${results.length === 1 ? "match" : "matches"} from the bundled sample.`}
        </p>

        {results.length > 0 ? (
          <ol className="search-result-list">
            {results.map((result) => (
              <li key={result.ayah.reference}>
                <article className="search-result">
                  <div className="search-result__header">
                    <div className="search-result__copy">
                      <div className="search-result__eyebrow-row">
                        <span className="surah-chip">{result.ayah.reference}</span>
                        {result.matchedIn.map((item) => (
                          <span key={item} className="search-match-chip">
                            {item}
                          </span>
                        ))}
                      </div>
                      <h3 className="search-result__title">
                        {result.surah.nameEnglish}
                      </h3>
                      <p className="search-result__meta">
                        {result.surah.nameTranslation} · {result.revelationLabel} · Juz{" "}
                        {result.juz}
                      </p>
                    </div>
                    <p
                      className="search-result__arabic"
                      dir="rtl"
                      lang="ar"
                    >
                      {renderHighlightedText(result.ayah.arabicText, trimmedQuery)}
                    </p>
                  </div>

                  <p className="search-result__translation">
                    {renderHighlightedText(result.ayah.translationText, trimmedQuery)}
                  </p>

                  <div className="search-context">
                    <p className="section-label">Result context</p>
                    <div className="search-context__grid">
                      <ContextBlock
                        label="Context before"
                        ayah={result.contextBefore}
                        query={trimmedQuery}
                      />
                      <ContextBlock
                        label="Context after"
                        ayah={result.contextAfter}
                        query={trimmedQuery}
                      />
                    </div>
                  </div>

                  <div className="reader-inline-links">
                    <Link
                      href={`/ayah/${result.surah.number}/${result.ayah.ayahNumber}`}
                      className="reader-link"
                    >
                      Open ayah detail
                    </Link>
                    <Link
                      href={`/surah/${result.surah.number}`}
                      className="reader-link reader-link--muted"
                    >
                      Read surrounding surah
                    </Link>
                    <Link
                      href={`/notes?reference=${encodeURIComponent(result.ayah.reference)}`}
                      className="reader-link reader-link--muted"
                    >
                      Private note
                    </Link>
                  </div>
                </article>
              </li>
            ))}
          </ol>
        ) : trimmedQuery.length > 0 ? (
          <div className="reader-empty-state">
            <h3 className="surface-card__title">No exact match in the bundled sample</h3>
            <p className="surface-card__description">
              Adjust the revelation, surah, or scope filters, or try a more
              direct phrase from the Arabic text, translation, or surah
              metadata.
            </p>
          </div>
        ) : null}
      </section>

      <aside className="reader-panel reader-panel--support">
        <p className="section-label">Search guardrails</p>
        <h2 className="surface-card__title">
          Exact search stays lexical and moves straight into reader context
        </h2>
        <p className="surface-card__description">
          Filters are visible before the results list so QuranKit does not
          collapse exact lookup into a vague ranking mode. Context stays one
          action away from every match.
        </p>
        <ul className="surface-card__list">
          <li>Scope remains explicit: Arabic text, translation, metadata, or all.</li>
          <li>Result cards include previous and next bundled ayah context when available.</li>
          <li>Bookmarks, notes, and study actions remain private by default.</li>
        </ul>
        <div className="reader-attribution">
          <p className="attribution">{bundledReaderAttribution.arabic}</p>
          <p className="attribution">{bundledReaderAttribution.translation}</p>
          <p className="reader-preview__note">{bundledReaderAttribution.note}</p>
        </div>
        <div className="search-support-summary">
          <p className="section-label">Bundled sample coverage</p>
          <ul className="surface-card__list">
            {juzOptions.map((option) => (
              <li key={option.value}>{option.label} is available in the current search sample.</li>
            ))}
          </ul>
        </div>
      </aside>
    </div>
  );
}

type ContextBlockProps = {
  label: string;
  ayah: BundledAyah | null;
  query: string;
};

function ContextBlock({ label, ayah, query }: ContextBlockProps) {
  return (
    <div className="search-context__item">
      <p className="search-context__label">{label}</p>
      {ayah ? (
        <>
          <p className="search-context__reference">{ayah.reference}</p>
          <p className="search-context__translation">
            {renderHighlightedText(ayah.translationText, query)}
          </p>
        </>
      ) : (
        <p className="search-context__translation">
          No additional bundled context on this side of the result.
        </p>
      )}
    </div>
  );
}

function renderHighlightedText(text: string, query: string): ReactNode {
  const trimmedQuery = query.trim();
  if (trimmedQuery.length === 0) {
    return text;
  }

  const normalizedText = text.toLowerCase();
  const normalizedQuery = trimmedQuery.toLowerCase();
  const parts: ReactNode[] = [];
  let cursor = 0;

  while (cursor < text.length) {
    const matchIndex = normalizedText.indexOf(normalizedQuery, cursor);

    if (matchIndex === -1) {
      parts.push(text.slice(cursor));
      break;
    }

    if (matchIndex > cursor) {
      parts.push(text.slice(cursor, matchIndex));
    }

    parts.push(
      <mark key={`${text}-${matchIndex}`}>
        {text.slice(matchIndex, matchIndex + trimmedQuery.length)}
      </mark>,
    );

    cursor = matchIndex + trimmedQuery.length;
  }

  return parts;
}
