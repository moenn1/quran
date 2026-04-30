import { fireEvent, screen } from "@testing-library/react";

import { ProgressExperience } from "@/components/progress-experience";
import { renderWithStudyState } from "@/test/test-study-utils";

describe("ProgressExperience", () => {
  it("saves a checkpoint and updates bundled progress totals", () => {
    renderWithStudyState(<ProgressExperience />);

    expect(screen.getByText("0 of 47 ayahs")).toBeInTheDocument();

    fireEvent.change(screen.getByLabelText("Checkpoint start"), {
      target: { value: "112:1" },
    });
    fireEvent.change(screen.getByLabelText("Checkpoint end"), {
      target: { value: "112:2" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Save checkpoint" }));

    expect(
      screen.getByText("112:1-2 saved as the latest private checkpoint."),
    ).toBeInTheDocument();
    expect(screen.getByText("2 of 47 ayahs")).toBeInTheDocument();
  });
});
