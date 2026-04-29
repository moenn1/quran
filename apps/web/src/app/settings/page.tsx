import { PageHero } from "@/components/page-hero";
import { SectionDeck } from "@/components/section-deck";
import { heroPills, settingsCards } from "@/lib/site-data";

export default function SettingsPage() {
  return (
    <>
      <PageHero
        eyebrow="Settings"
        title="Settings that clarify reading preferences, sources, and storage mode"
        description="The settings foundation keeps reader adjustments, translation attribution, and privacy-sensitive storage choices understandable."
        pills={heroPills.settings}
      />
      <SectionDeck
        label="Preference model"
        title="Make the important decisions easy to inspect and change"
        description="Reader presentation, translation choices, and data storage should be explicit throughout the settings experience."
        cards={settingsCards}
      />
    </>
  );
}
