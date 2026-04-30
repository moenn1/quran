import { render, screen } from "@testing-library/react";

import { AppProviders } from "@/components/app-providers";
import { RuntimeFoundation } from "@/components/runtime-foundation";

describe("RuntimeFoundation", () => {
  it("surfaces query and api setup in the home experience", async () => {
    render(
      <AppProviders>
        <RuntimeFoundation />
      </AppProviders>,
    );

    expect(
      await screen.findByRole("heading", {
        name: /Query caching and the API client are ready for live Quran data/i,
      }),
    ).toBeInTheDocument();
    expect(screen.getByText("TanStack Query ready")).toBeInTheDocument();
    expect(screen.getByText("http://localhost:8000")).toBeInTheDocument();
    expect(
      screen.getByText(
        /Local-first for progress, bookmarks, notes, and reading plans\./,
      ),
    ).toBeInTheDocument();
  });
});
