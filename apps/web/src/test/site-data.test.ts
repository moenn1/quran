import { homeFeatureCards, navigationItems } from "@/lib/site-data";

describe("site data", () => {
  it("defines the primary web architecture routes", () => {
    expect(navigationItems.map((item) => item.href)).toEqual([
      "/explore",
      "/search",
      "/semantic",
      "/progress",
      "/plans",
      "/bookmarks",
      "/notes",
      "/settings",
    ]);
  });

  it("keeps the explore route visible from the browse surface", () => {
    const exploreCard = homeFeatureCards.find((card) => card.href === "/explore");

    expect(exploreCard).toBeDefined();
    expect(exploreCard?.title).toBe("Explore");
    expect(exploreCard?.description).toMatch(/routed surah and ayah pages/i);
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
