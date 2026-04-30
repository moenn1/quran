import { fireEvent, render, screen } from "@testing-library/react";

import { ExactSearchExperience } from "@/components/exact-search-experience";
import { getBundledSurahs } from "@/lib/reader-data";

describe("ExactSearchExperience", () => {
  it("supports filters and result context for exact search", () => {
    render(<ExactSearchExperience surahs={getBundledSurahs()} />);

    expect(
      screen.getByText("Showing 2 exact matches from the bundled sample."),
    ).toBeInTheDocument();

    fireEvent.change(screen.getByRole("searchbox"), {
      target: { value: "clear evidence" },
    });
    fireEvent.change(screen.getByLabelText("Revelation place"), {
      target: { value: "makkah" },
    });

    expect(
      screen.getByRole("heading", { name: "No exact match in the bundled sample" }),
    ).toBeInTheDocument();

    fireEvent.change(screen.getByLabelText("Revelation place"), {
      target: { value: "madinah" },
    });

    expect(screen.getAllByRole("heading", { name: "Al-Bayyinah" }).length).toBe(2);
    expect(screen.getAllByText("Context after").length).toBeGreaterThan(0);
    expect(screen.getByText("98:2")).toBeInTheDocument();
  });
});
