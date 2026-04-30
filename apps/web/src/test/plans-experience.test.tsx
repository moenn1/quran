import { fireEvent, screen, within } from "@testing-library/react";

import { PlansExperience } from "@/components/plans-experience";
import { renderWithStudyState } from "@/test/test-study-utils";

describe("PlansExperience", () => {
  it("creates and recalculates private reading plans", () => {
    renderWithStudyState(<PlansExperience />);

    fireEvent.change(screen.getByLabelText("Plan name"), {
      target: { value: "Weekend finish" },
    });
    fireEvent.change(screen.getByLabelText("Plan start reference"), {
      target: { value: "113:1" },
    });
    fireEvent.change(screen.getByLabelText("Plan end reference"), {
      target: { value: "114:6" },
    });
    fireEvent.change(screen.getByLabelText("Daily target"), {
      target: { value: "2" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Create private plan" }));

    const card = screen
      .getByRole("heading", { name: "Weekend finish" })
      .closest("article");

    expect(card).not.toBeNull();
    if (!card) {
      throw new Error("Expected the new plan card.");
    }

    fireEvent.change(within(card).getByLabelText("Weekend finish daily target"), {
      target: { value: "4" },
    });
    fireEvent.click(within(card).getByRole("button", { name: "Recalculate plan" }));

    expect(
      screen.getByText("Recalculated “Weekend finish” for 4 ayahs per day."),
    ).toBeInTheDocument();
    expect(within(card).getByText("4 ayahs")).toBeInTheDocument();
  });
});
