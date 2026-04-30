import { Suspense } from "react";

import { PageHero } from "@/components/page-hero";
import { NotesExperience } from "@/components/notes-experience";
import { heroPills } from "@/lib/site-data";

export default function NotesPage() {
  return (
    <>
      <PageHero
        eyebrow="Notes"
        title="Private study notes linked to verses, not social features"
        description="The notes surface treats reflections as personal study material, with clear references, plain language, and explicit export boundaries. It stays separate from tafsir, fatwa, or any social commentary layer."
        pills={heroPills.notes}
      />
      <Suspense
        fallback={
          <section className="reader-panel reader-panel--support">
            <p className="section-label">Private notes</p>
            <p className="reader-status">
              Loading the local note composer and linked reference state.
            </p>
          </section>
        }
      >
        <NotesExperience />
      </Suspense>
    </>
  );
}
