import { PageHero } from "@/components/page-hero";
import { SectionDeck } from "@/components/section-deck";
import { SemanticDisclaimer } from "@/components/semantic-disclaimer";
import { heroPills, semanticSearchCards } from "@/lib/site-data";

export default function SemanticPage() {
  return (
    <>
      <PageHero
        eyebrow="Semantic search"
        title="Similarity-based discovery with guardrails built into the interface"
        description="The semantic search page is intentionally framed as exploratory. It can help readers find related passages, but it must never imply interpretation or religious authority."
        pills={heroPills.semantic}
      />
      <SemanticDisclaimer />
      <SectionDeck
        label="Similarity workflow"
        title="Keep semantic search useful without overstating what it knows"
        description="QuranKit should separate retrieval quality from religious meaning, and the page architecture needs to make that obvious."
        cards={semanticSearchCards}
      />
    </>
  );
}
