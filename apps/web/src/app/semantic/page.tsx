import { PageHero } from "@/components/page-hero";
import { SemanticSearchExperience } from "@/components/semantic-search-experience";
import { SemanticDisclaimer } from "@/components/semantic-disclaimer";
import { getBundledSurahs } from "@/lib/reader-data";
import { heroPills } from "@/lib/site-data";

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
      <SemanticSearchExperience surahs={getBundledSurahs()} />
    </>
  );
}
