import { PageHero } from "@/components/page-hero";
import { SectionDeck } from "@/components/section-deck";
import { exactSearchCards, heroPills } from "@/lib/site-data";

export default function SearchPage() {
  return (
    <>
      <PageHero
        eyebrow="Exact search"
        title="Search the text precisely without blurring what matched"
        description="Exact search remains a distinct experience inside QuranKit so readers can move from a query into context with transparent filters and predictable results."
        pills={heroPills.search}
      />
      <SectionDeck
        label="Search structure"
        title="Exact search should stay explainable from query to result"
        description="Keyword, phrase, and translation queries must remain clearly scoped instead of dissolving into generic ranking."
        cards={exactSearchCards}
      />
    </>
  );
}
