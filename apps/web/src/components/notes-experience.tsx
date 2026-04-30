"use client";

import { useState } from "react";

import Link from "next/link";
import { useSearchParams } from "next/navigation";

import { useStudyState } from "@/components/study-state-provider";
import {
  formatStudyDateTime,
  getAyahPreview,
  getBookmarkForReference,
  getBundledReferenceOptions,
  parseReferenceLabel,
  type StudyNote,
} from "@/lib/study-data";

const referenceOptions = getBundledReferenceOptions();

export function NotesExperience() {
  const searchParams = useSearchParams();
  const requestedReference = searchParams.get("reference");
  const prefilledReference =
    requestedReference && parseReferenceLabel(requestedReference)
      ? requestedReference
      : null;
  const { saveNote, snapshot } = useStudyState();
  const [selectedReference, setSelectedReference] = useState<string>(
    prefilledReference ?? referenceOptions[0]?.value ?? "1:1",
  );
  const [body, setBody] = useState("");
  const [editingId, setEditingId] = useState<string | null>(null);
  const [query, setQuery] = useState("");
  const [status, setStatus] = useState(
    "Private notes are stored in this browser and remain outside public search or profile surfaces.",
  );
  const effectiveReference =
    !editingId && body.trim().length === 0 && prefilledReference
      ? prefilledReference
      : selectedReference;

  const normalizedQuery = query.trim().toLowerCase();
  const filteredNotes = snapshot.state.notes.filter((note) => {
    if (!normalizedQuery) {
      return true;
    }

    const preview = getAyahPreview(note.range.start);
    const searchable = [
      note.range.label,
      note.body,
      preview?.surah.nameEnglish ?? "",
      preview?.surah.nameArabic ?? "",
      preview?.surah.nameTranslation ?? "",
    ]
      .join(" ")
      .toLowerCase();

    return searchable.includes(normalizedQuery);
  });

  function handleSaveNote(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
      const result = saveNote({
        id: editingId ?? undefined,
        reference: effectiveReference,
        body,
      });

    setStatus(result.message);

    if (result.ok) {
      setBody("");
      setEditingId(null);
    }
  }

  function handleStartEdit(note: StudyNote) {
    setEditingId(note.id);
    setSelectedReference(note.range.label);
    setBody(note.body);
    setStatus(`Editing the private note linked to ${note.range.label}.`);
  }

  return (
    <div className="reader-layout">
      <section className="reader-panel reader-panel--spacious">
        <div className="section-copy max-w-3xl">
          <p className="section-label">Private notes</p>
          <h2 className="section-title">
            Keep reflections linked to references, not to social features
          </h2>
          <p className="section-description">
            Notes are plainspoken and reference-aware. They stay separate from
            semantic-search claims, public commentary, or anything that could be
            mistaken for tafsir or religious rulings.
          </p>
        </div>

        <form className="reader-control-panel" onSubmit={handleSaveNote}>
          <div className="search-filter-grid">
            <label className="reader-control-group">
              <span className="reader-control-label">Reference</span>
              <select
                value={effectiveReference}
                onChange={(event) => setSelectedReference(event.target.value)}
                className="reader-select-input"
                aria-label="Note reference"
              >
                {referenceOptions.map((option) => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </select>
            </label>
            <label className="reader-control-group search-filter-grid__wide">
              <span className="reader-control-label">Find existing notes</span>
              <input
                type="search"
                value={query}
                onChange={(event) => setQuery(event.target.value)}
                className="reader-search-input"
                placeholder="Search note text, reference, or surah name"
              />
            </label>
            <label className="reader-control-group search-filter-grid__wide">
              <span className="reader-control-label">
                {editingId ? "Edit note body" : "New note body"}
              </span>
              <textarea
                value={body}
                onChange={(event) => setBody(event.target.value)}
                className="reader-textarea"
                rows={6}
                placeholder="Keep the note plain and private."
              />
            </label>
          </div>
          {prefilledReference && !editingId && body.trim().length === 0 ? (
            <p className="reader-status reader-status--compact">
              {prefilledReference} was prefilled from the reader or search flow.
            </p>
          ) : null}
          <div className="study-form-actions">
            <button type="submit" className="action-button action-button--selected">
              {editingId ? "Update note" : "Save note"}
            </button>
            {(editingId || body) && (
              <button
                type="button"
                className="action-button"
                onClick={() => {
                  setEditingId(null);
                  setBody("");
                  setStatus("The note composer was reset.");
                }}
              >
                Reset composer
              </button>
            )}
          </div>
        </form>

        <p className="reader-status" aria-live="polite">
          {status}
        </p>

        {filteredNotes.length > 0 ? (
          <div className="study-card-list">
            {filteredNotes.map((note) => (
              <NoteCard
                key={note.id}
                note={note}
                onEdit={handleStartEdit}
                onStatusChange={setStatus}
              />
            ))}
          </div>
        ) : (
          <div className="reader-empty-state">
            <h3 className="surface-card__title">No private note yet</h3>
            <p className="surface-card__description">
              Start with a reference above, or open this page from the reader or
              exact-search results so the composer is prefilled with the ayah you
              want to keep in view.
            </p>
          </div>
        )}
      </section>

      <aside className="reader-panel reader-panel--support">
        <p className="section-label">Note boundaries</p>
        <h2 className="surface-card__title">
          The note surface stays personal, local-first, and reference-aware
        </h2>
        <p className="surface-card__description">
          Notes are anchored to explicit references so they remain readable later.
          They are not shared, ranked, or treated as scholarly output.
        </p>
        <ul className="surface-card__list">
          <li>Reader and search routes can prefill the composer with a specific ayah reference.</li>
          <li>Bookmarks and notes remain connected but distinct; either can exist without the other.</li>
          <li>Exports are intentional and live in settings so the privacy boundary stays explicit.</li>
        </ul>
        <div className="reader-inline-links">
          <Link href="/bookmarks" className="reader-link">
            Review bookmarks
          </Link>
          <Link href="/settings" className="reader-link reader-link--muted">
            Review exports
          </Link>
        </div>
      </aside>
    </div>
  );
}

type NoteCardProps = {
  note: StudyNote;
  onEdit: (note: StudyNote) => void;
  onStatusChange: (message: string) => void;
};

function NoteCard({ note, onEdit, onStatusChange }: NoteCardProps) {
  const { deleteNote, snapshot } = useStudyState();
  const preview = getAyahPreview(note.range.start);
  const linkedBookmark = getBookmarkForReference(snapshot, note.range.label);

  return (
    <article className="surface-card">
      <div className="study-card-header">
        <div>
          <div className="study-tag-row">
            <span className="surah-chip">{note.range.label}</span>
            {preview ? (
              <span className="search-match-chip">{preview.surah.nameEnglish}</span>
            ) : null}
            {linkedBookmark ? (
              <span className="study-tag study-tag--accent">Bookmarked</span>
            ) : null}
          </div>
          <h3 className="surface-card__title">
            {preview ? `${preview.surah.number} · ${preview.surah.nameTranslation}` : "Private note"}
          </h3>
          <p className="surface-card__description">
            Updated {formatStudyDateTime(note.updatedAt)}
          </p>
        </div>
      </div>

      <p className="study-note-body">{note.body}</p>

      <div className="study-plan-summary">
        <p className="study-plan-summary__item">
          <strong>Open reference</strong>
          <span>{note.range.label}</span>
        </p>
        <p className="study-plan-summary__item">
          <strong>Saved</strong>
          <span>{formatStudyDateTime(note.createdAt)}</span>
        </p>
      </div>

      <div className="study-form-actions">
        <button type="button" className="action-button" onClick={() => onEdit(note)}>
          Edit note
        </button>
        {preview ? (
          <Link
            href={`/ayah/${preview.surah.number}/${preview.ayah.ayahNumber}`}
            className="action-button action-button--link"
          >
            Open ayah detail
          </Link>
        ) : null}
        <button
          type="button"
          className="action-button"
          onClick={() => {
            const result = deleteNote(note.id);
            onStatusChange(result.message);
          }}
        >
          Delete
        </button>
      </div>
    </article>
  );
}
