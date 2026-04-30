type PageHeroProps = {
  eyebrow: string;
  title: string;
  description: string;
  pills?: readonly string[];
};

export function PageHero({
  eyebrow,
  title,
  description,
  pills = [],
}: PageHeroProps) {
  return (
    <section className="page-hero flex flex-col gap-5 md:gap-6">
      <p className="section-label">{eyebrow}</p>
      <h1 className="page-hero__title">{title}</h1>
      <p className="page-hero__description">{description}</p>
      {pills.length > 0 ? (
        <ul
          className="pill-list flex flex-wrap gap-2"
          aria-label={`${eyebrow} highlights`}
        >
          {pills.map((pill) => (
            <li key={pill} className="pill">
              {pill}
            </li>
          ))}
        </ul>
      ) : null}
    </section>
  );
}
