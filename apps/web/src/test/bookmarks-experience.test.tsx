import { fireEvent, screen } from "@testing-library/react";

import { BookmarksExperience } from "@/components/bookmarks-experience";
import { renderWithStudyState } from "@/test/test-study-utils";

describe("BookmarksExperience", () => {
  it("adds bookmarks and filters them by query", () => {
    renderWithStudyState(<BookmarksExperience />);

    fireEvent.change(screen.getByLabelText("Bookmark reference"), {
      target: { value: "112:1" },
    });
    fireEvent.change(screen.getByPlaceholderText("Revision, evening, or reflection"), {
      target: { value: "Evening" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Save bookmark" }));

    fireEvent.change(screen.getByLabelText("Bookmark reference"), {
      target: { value: "113:1" },
    });
    fireEvent.change(screen.getByPlaceholderText("Revision, evening, or reflection"), {
      target: { value: "Protection" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Save bookmark" }));

    expect(screen.getByText("قُلْ هُوَ ٱللَّهُ أَحَدٌ")).toBeInTheDocument();
    expect(screen.getByText("قُلْ أَعُوذُ بِرَبِّ ٱلْفَلَقِ")).toBeInTheDocument();

    fireEvent.change(screen.getByRole("searchbox"), {
      target: { value: "Protection" },
    });

    expect(screen.queryByText("قُلْ هُوَ ٱللَّهُ أَحَدٌ")).not.toBeInTheDocument();
    expect(screen.getByText("قُلْ أَعُوذُ بِرَبِّ ٱلْفَلَقِ")).toBeInTheDocument();
  });
});
