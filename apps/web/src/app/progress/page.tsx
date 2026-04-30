import { PageHero } from "@/components/page-hero";
import { ProgressExperience } from "@/components/progress-experience";
import { heroPills } from "@/lib/site-data";

export default function ProgressPage() {
  return (
    <>
      <PageHero
        eyebrow="Progress"
        title="Track reading progress privately, with calm cues instead of noisy metrics"
        description="Progress in QuranKit is meant to help a reader resume and reflect, not turn study into a leaderboard or public profile. The current web slice keeps these tools local-first on the bundled reader sample."
        pills={heroPills.progress}
      />
      <ProgressExperience />
    </>
  );
}
