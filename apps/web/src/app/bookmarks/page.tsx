import { PageHero } from "@/components/page-hero";
import { BookmarksExperience } from "@/components/bookmarks-experience";
import { heroPills } from "@/lib/site-data";

export default function BookmarksPage() {
  return (
    <>
      <PageHero
        eyebrow="Bookmarks"
        title="Bookmarks that preserve context without adding clutter"
        description="Bookmark flows should make it easy to return to important ayat while keeping the interface private, quiet, and source-aware. The current web slice uses the bundled reader sample and keeps attribution attached to every text preview."
        pills={heroPills.bookmarks}
      />
      <BookmarksExperience />
    </>
  );
}
