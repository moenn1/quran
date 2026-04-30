import { PageHero } from "@/components/page-hero";
import { ReaderPreview } from "@/components/reader-preview";
import { RuntimeFoundation } from "@/components/runtime-foundation";
import { SectionDeck } from "@/components/section-deck";
import { SemanticDisclaimer } from "@/components/semantic-disclaimer";
import {
  architecturePillars,
  heroPills,
  homeFeatureCards,
} from "@/lib/site-data";

export default function HomePage() {
  return (
    <>
      <PageHero
        eyebrow="UI Direction"
        title="Arabic-inspired reading shaped around clarity, attribution, and calm focus"
        description="This first web slice establishes the QuranKit visual language, page architecture, and guardrails for search, progress, plans, bookmarks, notes, and settings."
        pills={heroPills.home}
      />
      <SectionDeck
        label="Browse foundation"
        title="A route map that reflects QuranKit's core study flows"
        description="The landing page works as a browse surface for the major reader and study experiences, keeping the architecture legible before data integration lands."
        cards={homeFeatureCards}
      />
      <RuntimeFoundation />
      <ReaderPreview />
      <SemanticDisclaimer />
      <SectionDeck
        label="Architecture pillars"
        title="Frontend decisions encoded directly into the foundation"
        description="The theme, layout, and page boundaries below define how the web app should feel as more reader and search functionality is added."
        cards={architecturePillars}
      />
    </>
  );
}
