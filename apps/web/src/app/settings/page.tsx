import { PageHero } from "@/components/page-hero";
import { SettingsExperience } from "@/components/settings-experience";
import { heroPills } from "@/lib/site-data";

export default function SettingsPage() {
  return (
    <>
      <PageHero
        eyebrow="Settings"
        title="Settings that clarify reading preferences, sources, and storage mode"
        description="Settings in QuranKit keep reader adjustments, translation attribution, export boundaries, and local-first storage choices understandable without burying the privacy tradeoffs."
        pills={heroPills.settings}
      />
      <SettingsExperience />
    </>
  );
}
