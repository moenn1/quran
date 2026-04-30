"use client";

import { useState } from "react";

import Link from "next/link";

import { cn } from "@/lib/cn";
import {
  bundledReaderAttribution,
  formatPageRange,
  formatRevelationPlace,
  type BundledSurah,
  type RevelationPlace,
} from "@/lib/reader-data";

type ExploreExperienceProps = {
  surahs: readonly BundledSurah[];
};

const revelationFilters = [
  { value: "all", label: "All" },
  { value: "makkah", label: "Meccan" },
  { value: "madinah", label: "Medinan" },
] as const;

export function ExploreExperience({ surahs }: ExploreExperienceProps) {
  const [query, setQuery] = useState("");
  const [revelationFilter, setRevelationFilter] = useState<
    RevelationPlace | "all"
  >("all");

  const normalizedQuery = query.trim().toLowerCase();
  const filteredSurahs = surahs.filter((surah) => {
    const matchesFilter =
      revelationFilter === "all" || surah.revelationPlace === revelationFilter;

    const matchesQuery =
      normalizedQuery.length === 0 ||
      surah.number.toString().includes(normalizedQuery) ||
      surah.nameEnglish.toLowerCase().includes(normalizedQuery) ||
      surah.nameArabic.includes(query.trim()) ||
      surah.nameTranslation.toLowerCase().includes(normalizedQuery) ||
      formatRevelationPlace(surah.revelationPlace)
        .toLowerCase()
        .includes(normalizedQuery);

    return matchesFilter && matchesQuery;
  });

  return (
    <div className="reader-layout reader-layout--single">
      <section className="reader-panel reader-panel--spacious">
        <div className="section-copy max-w-3xl">
          <p className="section-label">Surah filtering</p>
          <h2 className="section-title">
            Search by name, number, or revelation place
          </h2>
          <p className="section-description">
            This explore route ships a small bundled reader sample while the
            wider QuranKit reading corpus is being wired into the web app. The
            browse structure, dynamic routes, and attribution treatment match
            the user-facing reader flow.
          </p>
        </div>
        <div className="reader-control-panel">
          <label className="reader-control-group">
            <span className="reader-control-label">Find a surah</span>
            <input
              type="search"
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              className="reader-search-input"
              placeholder="Try 112, Ikhlas, or Medinan"
            />
          </label>
          <div className="reader-control-group">
            <span className="reader-control-label">Reveal by place</span>
            <div className="segmented-control" role="group" aria-label="Revelation place">
              {revelationFilters.map((option) => {
                const selected = revelationFilter === option.value;

                return (
                  <button
                    key={option.value}
                    type="button"
                    className={cn(
                      "segmented-control__button",
                      selected && "segmented-control__button--selected",
                    )}
                    aria-pressed={selected}
                    onClick={() => setRevelationFilter(option.value)}
                  >
                    {option.label}
                  </button>
                );
              })}
            </div>
          </div>
        </div>
        <p className="reader-status" aria-live="polite">
          Showing {filteredSurahs.length} of {surahs.length} bundled sample surahs.
        </p>
        <div className="surah-grid">
          {filteredSurahs.map((surah) => (
            <article key={surah.number} className="surah-tile">
              <div className="surah-tile__header">
                <div className="surah-tile__copy">
                  <span className="surah-chip">Surah {surah.number}</span>
                  <h3 className="surah-tile__title">{surah.nameEnglish}</h3>
                  <p className="surah-tile__subtitle">{surah.nameTranslation}</p>
                </div>
                <p className="surah-tile__arabic" dir="rtl" lang="ar">
                  {surah.nameArabic}
                </p>
              </div>
              <div className="surah-tile__meta">
                <span>{formatRevelationPlace(surah.revelationPlace)}</span>
                <span>{surah.ayahCount} ayahs</span>
                <span>{formatPageRange(surah.pages)}</span>
              </div>
              <p className="surah-tile__description">
                Open the full bundled sample surah reader or jump directly into
                the first ayah detail route with the same attribution and local
                study controls.
              </p>
              <div className="surah-tile__actions">
                <Link href={`/surah/${surah.number}`} className="reader-link">
                  Read sample surah
                </Link>
                <Link
                  href={`/ayah/${surah.number}/1`}
                  className="reader-link reader-link--muted"
                >
                  Open ayah detail
                </Link>
              </div>
            </article>
          ))}
        </div>
        {filteredSurahs.length === 0 ? (
          <div className="reader-empty-state">
            <h3 className="surface-card__title">No bundled sample match yet</h3>
            <p className="surface-card__description">
              Try an English name, Arabic name, surah number, or a revelation
              filter such as Meccan or Medinan.
            </p>
          </div>
        ) : null}
      </section>
      <aside className="reader-panel reader-panel--support">
        <p className="section-label">{bundledReaderAttribution.label}</p>
        <h2 className="surface-card__title">
          Reader routes keep attribution and privacy cues attached
        </h2>
        <p className="surface-card__description">
          Quran text is never presented without its source line, and the bundled
          reader actions are worded as private study tools rather than social or
          interpretive features.
        </p>
        <ul className="surface-card__list">
          <li>{bundledReaderAttribution.arabic}</li>
          <li>{bundledReaderAttribution.translation}</li>
          <li>Bookmark, read-marker, and note flows stay private by default.</li>
        </ul>
        <p className="reader-status reader-status--compact">
          {bundledReaderAttribution.note}
        </p>
      </aside>
    </div>
  );
}
