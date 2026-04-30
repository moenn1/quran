import { ExactSearchExperience } from "@/components/exact-search-experience";
import { PageHero } from "@/components/page-hero";
import { getBundledSurahs } from "@/lib/reader-data";
import { heroPills } from "@/lib/site-data";

export default function SearchPage() {
  return (
    <>
      <PageHero
        eyebrow="Exact search"
        title="Search the text precisely without blurring what matched"
        description="Exact search remains a distinct experience inside QuranKit so readers can move from a query into context with transparent filters and predictable results."
        pills={heroPills.search}
      />
      <ExactSearchExperience surahs={getBundledSurahs()} />
    </>
  );
}
