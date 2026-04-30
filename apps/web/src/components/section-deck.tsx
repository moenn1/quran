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
    <section className="section-block flex flex-col gap-5 md:gap-6">
      <div className="section-copy max-w-3xl">
        <p className="section-label">{label}</p>
        <h2 className="section-title">{title}</h2>
        <p className="section-description">{description}</p>
      </div>
      <div className="card-grid grid gap-4 md:grid-cols-2">
        {cards.map((card) => (
          <SectionCard key={card.title} {...card} />
        ))}
      </div>
    </section>
  );
}
