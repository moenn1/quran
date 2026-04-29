import { PageHero } from "@/components/page-hero";
import { SectionDeck } from "@/components/section-deck";
import { heroPills, noteCards } from "@/lib/site-data";

export default function NotesPage() {
  return (
    <>
      <PageHero
        eyebrow="Notes"
        title="Private study notes linked to verses, not social features"
        description="The notes architecture treats reflections as personal study material, with clear references and explicit export boundaries."
        pills={heroPills.notes}
      />
      <SectionDeck
        label="Notes workflow"
        title="Keep the note surface plain, private, and reference-aware"
        description="Notes should feel like a personal study margin attached to the reader rather than a chat stream or feed."
        cards={noteCards}
      />
    </>
  );
}
