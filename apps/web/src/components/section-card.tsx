import Link from "next/link";

import { cn } from "@/lib/cn";
import type { ContentCard } from "@/lib/site-data";

const toneClassNames = {
  neutral: "surface-card--neutral",
  accent: "surface-card--accent",
  warm: "surface-card--warm",
} as const;

export function SectionCard({
  title,
  description,
  items,
  footer,
  href,
  linkLabel,
  tone = "neutral",
}: ContentCard) {
  return (
    <article className={cn("surface-card", toneClassNames[tone])}>
      <div className="surface-card__body">
        <h3 className="surface-card__title">{title}</h3>
        <p className="surface-card__description">{description}</p>
        {items ? (
          <ul className="surface-card__list">
            {items.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
        ) : null}
      </div>
      {footer ? <p className="surface-card__footer">{footer}</p> : null}
      {href ? (
        <Link href={href} className="surface-card__link">
          {linkLabel ?? "Open page"}
        </Link>
      ) : null}
    </article>
  );
}
