import type { ContentCard } from "@/lib/site-data";

import { SectionCard } from "@/components/section-card";

type SectionDeckProps = {
  label: string;
  title: string;
  description: string;
  cards: ContentCard[];
};

export function SectionDeck({
  label,
  title,
  description,
  cards,
}: SectionDeckProps) {
  return (
    <section className="section-block">
      <div className="section-copy">
        <p className="section-label">{label}</p>
        <h2 className="section-title">{title}</h2>
        <p className="section-description">{description}</p>
      </div>
      <div className="card-grid">
        {cards.map((card) => (
          <SectionCard key={card.title} {...card} />
        ))}
      </div>
    </section>
  );
}
