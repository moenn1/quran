import { render, screen } from "@testing-library/react";

import { ReaderPreview } from "@/components/reader-preview";

describe("ReaderPreview", () => {
  it("renders Quran text with attribution and rtl support", () => {
    render(<ReaderPreview />);

    const ayah = screen.getByText("بِسْمِ ٱللَّهِ ٱلرَّحْمَٰنِ ٱلرَّحِيمِ");

    expect(ayah).toHaveAttribute("dir", "rtl");
    expect(screen.getByText("Al-Faatiha")).toBeInTheDocument();
    expect(
      screen.getByText("In the name of Allah, the Beneficent, the Merciful."),
    ).toBeInTheDocument();
    expect(
      screen.getByText(/Arabic text sample: AlQuran\.Cloud, Uthmani edition\./),
    ).toBeInTheDocument();
    expect(
      screen.getByText(/Mohammed Marmaduke William Pickthall/),
    ).toBeInTheDocument();
  });
});
