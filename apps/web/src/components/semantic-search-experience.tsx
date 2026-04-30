"use client";

import { useDeferredValue, useState } from "react";

import Link from "next/link";

import { useStudyState } from "@/components/study-state-provider";
import { cn } from "@/lib/cn";
import { bundledReaderAttribution, type BundledSurah } from "@/lib/reader-data";
import { hasBookmarkForReference } from "@/lib/study-data";
import {
  getBundledJuzOptions,
  getBundledSurahOptions,
  runSemanticSearch,
  semanticScopeOptions,
  semanticTranslationOptions,
  type SemanticScope,
  type SemanticSearchResult,
  type SemanticTranslationMode,
} from "@/lib/search-data";

type SemanticSearchExperienceProps = {
  surahs: readonly BundledSurah[];
};

export function SemanticSearchExperience({
  surahs,
}: SemanticSearchExperienceProps) {
  const [query, setQuery] = useState("refuge");
  const [scope, setScope] = useState<SemanticScope>("all");
  const [translationMode, setTranslationMode] =
    useState<SemanticTranslationMode>("saheeh");
  const [limit, setLimit] = useState(4);
  const [surahFilter, setSurahFilter] = useState<number | "all">("all");
  const [juzFilter, setJuzFilter] = useState<number | "all">(30);
  const [showScores, setShowScores] = useState(false);

  const deferredQuery = useDeferredValue(query);
  const results = runSemanticSearch({
    surahs,
    query: deferredQuery,
    scope,
    surahFilter,
    juzFilter,
    limit,
  });
  const surahOptions = getBundledSurahOptions(surahs);
  const juzOptions = getBundledJuzOptions(surahs);
  const trimmedQuery = deferredQuery.trim();

  return (
    <div className="reader-layout">
      <section className="reader-panel reader-panel--spacious">
        <div className="section-copy max-w-3xl">
          <p className="section-label">Similarity workflow</p>
          <h2 className="section-title">
            Related passages stay exploratory, filtered, and easy to verify
          </h2>
          <p className="section-description">
            This semantic preview uses bundled similarity cues so readers can
            compare related passages while still checking the Quran text and the
            reader route directly.
          </p>
        </div>

        <div className="reader-control-panel">
          <div className="search-filter-grid">
            <label className="reader-control-group search-filter-grid__wide">
              <span className="reader-control-label">Similarity query</span>
              <input
                type="search"
                value={query}
                onChange={(event) => setQuery(event.target.value)}
                className="reader-search-input"
                placeholder="Try refuge, mercy, patience, or forgiveness"
              />
            </label>

            <label className="reader-control-group">
              <span className="reader-control-label">Scope</span>
              <select
                value={scope}
                onChange={(event) => setScope(event.target.value as SemanticScope)}
                className="reader-select-input"
                aria-label="Scope"
              >
                {semanticScopeOptions.map((option) => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </select>
            </label>

            <label className="reader-control-group">
              <span className="reader-control-label">Translation</span>
              <select
                value={translationMode}
                onChange={(event) =>
                  setTranslationMode(event.target.value as SemanticTranslationMode)
                }
                className="reader-select-input"
                aria-label="Translation"
              >
                {semanticTranslationOptions.map((option) => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </select>
            </label>

            <label className="reader-control-group">
              <span className="reader-control-label">Result limit</span>
              <select
                value={limit}
                onChange={(event) => setLimit(Number(event.target.value))}
                className="reader-select-input"
                aria-label="Result limit"
              >
                {[3, 4, 6, 8].map((value) => (
                  <option key={value} value={value}>
                    {value} passages
                  </option>
                ))}
              </select>
            </label>

            <label className="reader-control-group">
              <span className="reader-control-label">Surah filter</span>
              <select
                value={surahFilter}
                onChange={(event) =>
                  setSurahFilter(
                    event.target.value === "all" ? "all" : Number(event.target.value),
                  )
                }
                className="reader-select-input"
                aria-label="Surah filter"
              >
                <option value="all">All bundled sample surahs</option>
                {surahOptions.map((option) => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </select>
            </label>

            <label className="reader-control-group">
              <span className="reader-control-label">Juz filter</span>
              <select
                value={juzFilter}
                onChange={(event) =>
                  setJuzFilter(
                    event.target.value === "all" ? "all" : Number(event.target.value),
                  )
                }
                className="reader-select-input"
                aria-label="Juz filter"
              >
                <option value="all">All bundled juz samples</option>
                {juzOptions.map((option) => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </select>
            </label>
          </div>

          <label className="search-checkbox-row">
            <input
              type="checkbox"
              checked={showScores}
              onChange={(event) => setShowScores(event.target.checked)}
            />
            <span>Show similarity scores for this preview</span>
          </label>
        </div>

        <p className="reader-status" aria-live="polite">
          {trimmedQuery.length === 0
            ? "Enter a cue to compare related passages in the bundled similarity preview."
            : `Showing ${results.length} related ${results.length === 1 ? "passage" : "passages"} from the bundled sample.${showScores ? " Scores are approximate preview cues only." : ""}`}
        </p>

        {results.length > 0 ? (
          <ol className="search-result-list">
            {results.map((result) => (
              <li key={result.ayah.reference}>
                <SemanticResultCard
                  result={result}
                  showScores={showScores}
                  translationMode={translationMode}
                />
              </li>
            ))}
          </ol>
        ) : trimmedQuery.length > 0 ? (
          <div className="reader-empty-state">
            <h3 className="surface-card__title">No related bundled passage yet</h3>
            <p className="surface-card__description">
              Broaden the scope, raise the limit, or loosen the surah and juz
              filters. This preview uses textual similarity cues only and does
              not infer interpretation.
            </p>
          </div>
        ) : null}
      </section>

      <aside className="reader-panel reader-panel--support">
        <p className="section-label">Similarity guardrails</p>
        <h2 className="surface-card__title">
          Scores stay optional and every result stays connected to verification
        </h2>
        <p className="surface-card__description">
          Similarity scores are hidden by default, and the action set remains
          grounded in private study tasks: bookmark, add to plan, copy with
          attribution, and open the reader.
        </p>
        <ul className="surface-card__list">
          <li>Similarity is presented as a retrieval cue, not tafsir or a ruling.</li>
          <li>Surah and juz filters stay available before the result list.</li>
          <li>Reader links remain one action away from every related passage.</li>
        </ul>
        <div className="reader-attribution">
          <p className="attribution">{bundledReaderAttribution.arabic}</p>
          {translationMode === "saheeh" ? (
            <p className="attribution">{bundledReaderAttribution.translation}</p>
          ) : null}
          <p className="reader-preview__note">
            This preview groups passages by textual similarity cues in the
            bundled sample. Verify the text directly in the reader.
          </p>
        </div>
        <div className="reader-inline-links">
          <Link href="/reader" className="reader-link">
            Return to the reader
          </Link>
          <Link href="/plans" className="reader-link reader-link--muted">
            Review reading plans
          </Link>
          <Link href="/bookmarks" className="reader-link reader-link--muted">
            Private bookmarks
          </Link>
        </div>
      </aside>
    </div>
  );
}

type SemanticResultCardProps = {
  result: SemanticSearchResult;
  showScores: boolean;
  translationMode: SemanticTranslationMode;
};

function SemanticResultCard({
  result,
  showScores,
  translationMode,
}: SemanticResultCardProps) {
  const { snapshot, toggleBookmark } = useStudyState();
  const bookmarked = hasBookmarkForReference(snapshot, result.ayah.reference);
  const [planned, setPlanned] = useState(false);
  const [status, setStatus] = useState("Study actions remain private by default.");

  async function copyResult() {
    const text = [
      result.ayah.reference,
      result.ayah.arabicText,
      translationMode === "saheeh" ? result.ayah.translationText : null,
      bundledReaderAttribution.arabic,
      translationMode === "saheeh" ? bundledReaderAttribution.translation : null,
    ]
      .filter(Boolean)
      .join("\n\n");

    if (!navigator.clipboard?.writeText) {
      setStatus(`Clipboard is unavailable for ${result.ayah.reference}.`);
      return;
    }

    try {
      await navigator.clipboard.writeText(text);
      setStatus(`Copied ${result.ayah.reference} with attribution.`);
    } catch {
      setStatus(`Unable to copy ${result.ayah.reference} right now.`);
    }
  }

  return (
    <article className="search-result search-result--semantic">
      <div className="search-result__header">
        <div className="search-result__copy">
          <div className="search-result__eyebrow-row">
            <span className="surah-chip">{result.ayah.reference}</span>
            {showScores ? (
              <span className="search-match-chip search-match-chip--accent">
                Score {Math.round(result.score * 100)}%
              </span>
            ) : null}
          </div>
          <h3 className="search-result__title">{result.surah.nameEnglish}</h3>
          <p className="search-result__meta">
            {result.surah.nameTranslation} · {result.revelationLabel} · Juz{" "}
            {result.juz}
          </p>
        </div>
        <p className="search-result__arabic" dir="rtl" lang="ar">
          {result.ayah.arabicText}
        </p>
      </div>

      {translationMode === "saheeh" ? (
        <p className="search-result__translation">{result.ayah.translationText}</p>
      ) : null}

      <div className="search-context">
        <p className="search-context__label">Similarity explanation</p>
        <p className="search-result__reason">{result.explanation}</p>
        <div className="search-result__term-row">
          {result.matchedTerms.map((term) => (
            <span key={term} className="search-match-chip">
              {term}
            </span>
          ))}
        </div>
      </div>

      <div className="ayah-actions">
        <div className="ayah-actions__row">
        <button
          type="button"
          className={cn("action-button", bookmarked && "action-button--selected")}
          aria-pressed={bookmarked}
          onClick={() => {
            const outcome = toggleBookmark({ reference: result.ayah.reference });
            setStatus(outcome.message);
          }}
        >
          {bookmarked ? "Bookmarked" : "Bookmark"}
          </button>
          <button
            type="button"
            className={cn("action-button", planned && "action-button--selected")}
            aria-pressed={planned}
            onClick={() => {
              setPlanned((value) => !value);
              setStatus(
                !planned
                  ? `${result.ayah.reference} added to a private reading plan in this preview.`
                  : `${result.ayah.reference} removed from the private reading plan in this preview.`,
              );
            }}
          >
            {planned ? "Planned" : "Add to plan"}
          </button>
          <button type="button" className="action-button" onClick={() => void copyResult()}>
            Copy result
          </button>
          <Link
            href={`/ayah/${result.surah.number}/${result.ayah.ayahNumber}`}
            className="action-button action-button--link"
          >
            Open in reader
          </Link>
        </div>
        <p className="ayah-actions__status" aria-live="polite">
          {status}
        </p>
      </div>
    </article>
  );
}
