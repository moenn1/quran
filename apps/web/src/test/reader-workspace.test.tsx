import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { vi } from "vitest";

import { ReaderWorkspace } from "@/components/reader-workspace";
import { StudyStateProvider } from "@/components/study-state-provider";
import { bundledReaderAttribution, getBundledSurah } from "@/lib/reader-data";

describe("ReaderWorkspace", () => {
  it("supports translation visibility, view controls, and attributed copy", async () => {
    const surah = getBundledSurah(112);
    const writeText = vi.fn().mockResolvedValue(undefined);

    Object.defineProperty(window.navigator, "clipboard", {
      configurable: true,
      value: { writeText },
    });

    if (!surah) {
      throw new Error("Expected bundled surah sample.");
    }

    window.localStorage.clear();

    const { container } = render(
      <StudyStateProvider>
        <ReaderWorkspace
          surah={surah}
          ayahs={surah.ayahs}
          navigationLabel="Surah reader"
        />
      </StudyStateProvider>,
    );

    expect(screen.getByText("Allah, the Eternal Refuge.")).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "Hide translation" }));

    expect(
      screen.queryByText("Allah, the Eternal Refuge."),
    ).not.toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "Show translation" }));
    fireEvent.click(screen.getByRole("button", { name: "Translation focus" }));
    fireEvent.click(screen.getByRole("button", { name: "Majlis" }));

    const workspace = container.querySelector(".reader-layout");

    expect(workspace).toHaveAttribute("data-text-view", "translation");
    expect(workspace).toHaveAttribute("data-arabic-scale", "majlis");

    fireEvent.click(screen.getAllByRole("button", { name: "Copy ayah" })[0]);

    await waitFor(() => expect(writeText).toHaveBeenCalledTimes(1));
    expect(writeText.mock.calls[0][0]).toContain("112:1");
    expect(writeText.mock.calls[0][0]).toContain(
      bundledReaderAttribution.arabic,
    );
    expect(writeText.mock.calls[0][0]).toContain(
      bundledReaderAttribution.translation,
    );
  });
});
