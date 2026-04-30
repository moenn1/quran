import { ExploreExperience } from "@/components/explore-experience";
import { PageHero } from "@/components/page-hero";
import { getBundledSurahs } from "@/lib/reader-data";
import { heroPills } from "@/lib/site-data";

export default function ExplorePage() {
  return (
    <>
      <PageHero
        eyebrow="Explore"
        title="Browse routed surah samples with calm filtering and direct reader access"
        description="The explore route makes the QuranKit browse flow tangible: filter bundled surahs, open a surah reader, or move straight into an ayah detail page with attribution and private study actions kept in view."
        pills={heroPills.explore}
      />
      <ExploreExperience surahs={getBundledSurahs()} />
    </>
  );
}
