import { fireEvent, render, screen } from "@testing-library/react";

import { ExploreExperience } from "@/components/explore-experience";
import { getBundledSurahs } from "@/lib/reader-data";

describe("ExploreExperience", () => {
  it("filters bundled surahs by revelation place and search query", () => {
    render(<ExploreExperience surahs={getBundledSurahs()} />);

    expect(screen.getByText("Showing 9 of 9 bundled sample surahs.")).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "Medinan" }));

    expect(screen.getByText("Showing 3 of 9 bundled sample surahs.")).toBeInTheDocument();
    expect(
      screen.getByRole("heading", { name: "Al-Bayyinah" }),
    ).toBeInTheDocument();
    expect(
      screen.queryByRole("heading", { name: "Al-Ikhlas" }),
    ).not.toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "All" }));
    fireEvent.change(screen.getByRole("searchbox"), {
      target: { value: "Ikhlas" },
    });

    expect(
      screen.getByRole("heading", { name: "Al-Ikhlas" }),
    ).toBeInTheDocument();
    expect(
      screen.queryByRole("heading", { name: "Al-Bayyinah" }),
    ).not.toBeInTheDocument();
  });
});
