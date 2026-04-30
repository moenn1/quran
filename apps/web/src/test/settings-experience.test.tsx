import { fireEvent, screen } from "@testing-library/react";

import { SettingsExperience } from "@/components/settings-experience";
import { renderWithStudyState } from "@/test/test-study-utils";

describe("SettingsExperience", () => {
  it("updates reader defaults, previews exports, and clears local data", () => {
    renderWithStudyState(<SettingsExperience />);

    fireEvent.click(screen.getByRole("button", { name: "Arabic only" }));
    expect(
      screen.getByText(
        "The reader will default to Arabic-only previews until you change it back.",
      ),
    ).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "Full study state" }));
    expect(screen.getByText(/"storage_key": "qurankit.study-state.v1"/)).toBeInTheDocument();
    expect(screen.getByText(/"starter-plan"/)).toBeInTheDocument();

    fireEvent.click(screen.getByRole("checkbox"));
    fireEvent.click(screen.getByRole("button", { name: "Clear local study data" }));

    expect(
      screen.getByText("Local study state was cleared from this browser."),
    ).toBeInTheDocument();
  });
});
