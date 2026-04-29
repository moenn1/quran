import { PageHero } from "@/components/page-hero";
import { SectionDeck } from "@/components/section-deck";
import { bookmarkCards, heroPills } from "@/lib/site-data";

export default function BookmarksPage() {
  return (
    <>
      <PageHero
        eyebrow="Bookmarks"
        title="Bookmarks that preserve context without adding clutter"
        description="Bookmark flows should make it easy to return to important ayat while keeping the interface private, quiet, and source-aware."
        pills={heroPills.bookmarks}
      />
      <SectionDeck
        label="Bookmark design"
        title="Returning to saved ayat should feel immediate and contextual"
        description="The bookmark architecture keeps references light, readable, and connected back to the main reader."
        cards={bookmarkCards}
      />
    </>
  );
}
