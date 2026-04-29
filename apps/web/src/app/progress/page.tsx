import { PageHero } from "@/components/page-hero";
import { SectionDeck } from "@/components/section-deck";
import { heroPills, progressCards } from "@/lib/site-data";

export default function ProgressPage() {
  return (
    <>
      <PageHero
        eyebrow="Progress"
        title="Track reading progress privately, with calm cues instead of noisy metrics"
        description="Progress in QuranKit is meant to help a reader resume and reflect, not turn study into a leaderboard or public profile."
        pills={heroPills.progress}
      />
      <SectionDeck
        label="Progress architecture"
        title="Local-first tracking with restrained visibility"
        description="These patterns define how resume markers, milestones, and related study tools should behave before remote sync is added."
        cards={progressCards}
      />
    </>
  );
}
