import { PageHero } from "@/components/page-hero";
import { SectionDeck } from "@/components/section-deck";
import { heroPills, planCards } from "@/lib/site-data";

export default function PlansPage() {
  return (
    <>
      <PageHero
        eyebrow="Plans"
        title="Reading plans that feel steady, editable, and personal"
        description="Plan architecture in QuranKit should support different reading cadences without turning the interface into a rigid scheduler."
        pills={heroPills.plans}
      />
      <SectionDeck
        label="Plan structure"
        title="Cadence, checkpoints, and privacy need to stay visible"
        description="The plan foundation keeps today's reading simple while leaving room for richer workflows later."
        cards={planCards}
      />
    </>
  );
}
