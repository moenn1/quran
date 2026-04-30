import {
  getBundledAyahContext,
  getBundledAyahNeighbors,
  getBundledSurah,
  getBundledSurahs,
} from "@/lib/reader-data";

describe("reader data", () => {
  it("ships a bundled sample with both Meccan and Medinan surahs", () => {
    const revelationPlaces = new Set(
      getBundledSurahs().map((surah) => surah.revelationPlace),
    );

    expect(revelationPlaces).toEqual(new Set(["makkah", "madinah"]));
    expect(getBundledSurah(112)?.ayahs).toHaveLength(4);
  });

  it("builds ayah context windows and cross-surah neighbors", () => {
    expect(getBundledAyahContext(112, 2).map((ayah) => ayah.reference)).toEqual([
      "112:1",
      "112:2",
      "112:3",
    ]);

    const neighbors = getBundledAyahNeighbors(110, 3);

    expect(neighbors.previous?.ayah.reference).toBe("110:2");
    expect(neighbors.next?.ayah.reference).toBe("112:1");
  });
});
