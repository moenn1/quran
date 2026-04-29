"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

import { cn } from "@/lib/cn";
import { navigationItems } from "@/lib/site-data";

export function SiteNavigation() {
  const pathname = usePathname();

  return (
    <nav className="nav" aria-label="Primary">
      {navigationItems.map((item) => {
        const active = pathname === item.href;

        return (
          <Link
            key={item.href}
            href={item.href}
            aria-current={active ? "page" : undefined}
            className={cn("nav__link", active && "nav__link--active")}
          >
            {item.label}
          </Link>
        );
      })}
    </nav>
  );
}
