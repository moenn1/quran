import { PageHero } from "@/components/page-hero";
import { PlansExperience } from "@/components/plans-experience";
import { heroPills } from "@/lib/site-data";

export default function PlansPage() {
  return (
    <>
      <PageHero
        eyebrow="Plans"
        title="Reading plans that feel steady, editable, and personal"
        description="Reading plans in QuranKit are built to stay steady, editable, and personal. The current web slice keeps them local-first and scoped to the bundled sample until the broader reader corpus is connected."
        pills={heroPills.plans}
      />
      <PlansExperience />
    </>
  );
}
