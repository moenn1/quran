import type { Metadata } from "next";
import type { ReactNode } from "react";

import "@/app/globals.css";

import { AppShell } from "@/components/app-shell";

export const metadata: Metadata = {
  title: {
    default: "QuranKit",
    template: "%s | QuranKit",
  },
  description:
    "Arabic-inspired Quran reading, exact search, semantic discovery, and private study tools.",
};

type RootLayoutProps = {
  children: ReactNode;
};

export default function RootLayout({ children }: RootLayoutProps) {
  return (
    <html lang="en">
      <body>
        <AppShell>{children}</AppShell>
      </body>
    </html>
  );
}
