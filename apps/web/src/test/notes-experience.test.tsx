import { fireEvent, screen } from "@testing-library/react";
import { vi } from "vitest";

import { NotesExperience } from "@/components/notes-experience";
import { renderWithStudyState } from "@/test/test-study-utils";

vi.mock("next/navigation", () => ({
  useSearchParams: () => new URLSearchParams("reference=112:1"),
}));

describe("NotesExperience", () => {
  it("prefills references and supports creating and updating notes", () => {
    renderWithStudyState(<NotesExperience />);

    expect(
      screen.getByText("112:1 was prefilled from the reader or search flow."),
    ).toBeInTheDocument();

    fireEvent.change(screen.getByLabelText("New note body"), {
      target: { value: "Reflect on sincerity." },
    });
    fireEvent.click(screen.getByRole("button", { name: "Save note" }));

    expect(screen.getByText("112:1 saved in private notes.")).toBeInTheDocument();
    expect(screen.getByText("Reflect on sincerity.")).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "Edit note" }));
    fireEvent.change(screen.getByLabelText("Edit note body"), {
      target: { value: "Reflect on sincerity and refuge." },
    });
    fireEvent.click(screen.getByRole("button", { name: "Update note" }));

    expect(
      screen.getByText("Reflect on sincerity and refuge."),
    ).toBeInTheDocument();
  });
});
