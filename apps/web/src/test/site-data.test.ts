import { homeFeatureCards, navigationItems } from "@/lib/site-data";

describe("site data", () => {
  it("defines the primary web architecture routes", () => {
    expect(navigationItems.map((item) => item.href)).toEqual([
      "/",
      "/reader",
      "/search",
      "/semantic",
      "/progress",
      "/plans",
      "/bookmarks",
      "/notes",
      "/settings",
    ]);
  });

  it("keeps semantic search clearly labeled from the browse surface", () => {
    const semanticCard = homeFeatureCards.find(
      (card) => card.href === "/semantic",
    );

    expect(semanticCard).toBeDefined();
    expect(semanticCard?.title).toBe("Semantic Search");
    expect(semanticCard?.description).toMatch(/Similarity-based search/);
  });
});
