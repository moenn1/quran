export function SemanticDisclaimer() {
  return (
    <section className="semantic-notice" aria-labelledby="semantic-notice-title">
      <p className="section-label">Semantic search guidance</p>
      <h2 id="semantic-notice-title" className="section-title">
        Similarity-based results are exploratory, not interpretive.
      </h2>
      <p className="section-description">
        QuranKit&apos;s semantic search is intended to help readers discover
        related passages by similarity signals. It must never be presented as
        tafsir, fatwa, or a religious ruling.
      </p>
      <ul className="semantic-notice__list">
        <li>Keep the similarity disclaimer visible near the query and results.</li>
        <li>Send readers into the full ayah context before they act on a match.</li>
        <li>Use clear, modest language instead of confidence-heavy claims.</li>
      </ul>
    </section>
  );
}
