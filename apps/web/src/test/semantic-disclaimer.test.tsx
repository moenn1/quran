import { render, screen } from "@testing-library/react";

import { SemanticDisclaimer } from "@/components/semantic-disclaimer";

describe("SemanticDisclaimer", () => {
  it("explains semantic search as similarity-based rather than interpretive", () => {
    render(<SemanticDisclaimer />);

    expect(
      screen.getByRole("heading", {
        name: /Similarity-based results are exploratory, not interpretive\./,
      }),
    ).toBeInTheDocument();
    expect(
      screen.getByText(/It must never be presented as tafsir, fatwa/),
    ).toBeInTheDocument();
    expect(
      screen.getByText(
        /Keep the similarity disclaimer visible near the query and results\./,
      ),
    ).toBeInTheDocument();
  });
});
