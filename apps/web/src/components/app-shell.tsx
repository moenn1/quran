import type { ReactNode } from "react";

import Link from "next/link";

import { SiteNavigation } from "@/components/site-navigation";

type AppShellProps = {
  children: ReactNode;
};

export function AppShell({ children }: AppShellProps) {
  return (
    <>
      <a href="#main-content" className="skip-link">
        Skip to content
      </a>
      <div className="app-shell">
        <div className="shell-frame">
          <header className="shell-header">
            <div className="shell-header__top">
              <div className="brand-block">
                <span className="brand-block__eyebrow">Frontend foundation</span>
                <Link href="/" className="brand-block__title">
                  QuranKit
                </Link>
                <p className="brand-block__copy">
                  Arabic-inspired reading, exact search, and private study tools
                  with clear attribution and careful guardrails.
                </p>
              </div>
              <div className="seal" aria-hidden="true">
                <span />
                <span />
                <span />
              </div>
            </div>
            <SiteNavigation />
          </header>
          <main id="main-content" className="page-stack">
            {children}
          </main>
          <footer className="site-footer">
            <p>
              QuranKit is a personal project for respectful study and
              development. It is not a source of tafsir, fatwa, or religious
              rulings.
            </p>
            <p>
              Progress, bookmarks, and notes are private by default. If
              something is wrong Islamically, contact the maintainer so it can
              be corrected.
            </p>
          </footer>
        </div>
      </div>
    </>
  );
}
