import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { vi } from "vitest";

import { SemanticSearchExperience } from "@/components/semantic-search-experience";
import { StudyStateProvider } from "@/components/study-state-provider";
import { getBundledSurahs } from "@/lib/reader-data";

describe("SemanticSearchExperience", () => {
  it("supports filters, optional scores, and private study actions", async () => {
    const writeText = vi.fn().mockResolvedValue(undefined);

    Object.defineProperty(window.navigator, "clipboard", {
      configurable: true,
      value: { writeText },
    });

    window.localStorage.clear();

    render(
      <StudyStateProvider>
        <SemanticSearchExperience surahs={getBundledSurahs()} />
      </StudyStateProvider>,
    );

    fireEvent.click(
      screen.getByRole("checkbox", {
        name: /Show similarity scores for this preview/i,
      }),
    );
    fireEvent.change(screen.getByRole("searchbox"), {
      target: { value: "evil" },
    });
    fireEvent.change(screen.getByLabelText("Result limit"), {
      target: { value: "3" },
    });
    fireEvent.change(screen.getByLabelText("Surah filter"), {
      target: { value: "113" },
    });

    expect(
      screen.getByText("Showing 3 related passages from the bundled sample. Scores are approximate preview cues only."),
    ).toBeInTheDocument();
    expect(screen.getAllByText(/Score /)).toHaveLength(3);

    fireEvent.click(screen.getAllByRole("button", { name: "Bookmark" })[0]);
    fireEvent.click(screen.getAllByRole("button", { name: "Add to plan" })[0]);
    fireEvent.click(screen.getAllByRole("button", { name: "Copy result" })[0]);

    await waitFor(() => expect(writeText).toHaveBeenCalledTimes(1));
    expect(writeText.mock.calls[0][0]).toMatch(/113:\d/);
    expect(writeText.mock.calls[0][0]).toContain("Arabic text sample");
    expect(screen.getByRole("button", { name: "Bookmarked" })).toBeInTheDocument();
  });
});
