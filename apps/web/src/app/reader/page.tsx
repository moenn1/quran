import { PageHero } from "@/components/page-hero";
import { ReaderPreview } from "@/components/reader-preview";
import { SectionDeck } from "@/components/section-deck";
import { heroPills, readerExperienceCards } from "@/lib/site-data";

export default function ReaderPage() {
  return (
    <>
      <PageHero
        eyebrow="Reader"
        title="A respectful reader surface with Quran text as the visual center"
        description="The reader architecture favors steady reading, strong Arabic typography, quiet metadata, and visible source attribution on the page itself."
        pills={heroPills.reader}
      />
      <ReaderPreview />
      <SectionDeck
        label="Reader architecture"
        title="Build the reader around hierarchy, rhythm, and trust"
        description="These patterns define how QuranKit should treat the ayah surface once remote and local data modes are connected."
        cards={readerExperienceCards}
      />
    </>
  );
}
