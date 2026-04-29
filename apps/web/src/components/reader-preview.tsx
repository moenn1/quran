import { sampleSurahPreview } from "@/lib/site-data";

export function ReaderPreview() {
  return (
    <section className="reader-preview">
      <div className="reader-preview__header">
        <div>
          <p className="section-label">{sampleSurahPreview.label}</p>
          <h2 className="section-title">{sampleSurahPreview.heading}</h2>
        </div>
        <p className="reader-preview__description">
          {sampleSurahPreview.description}
        </p>
      </div>
      <div className="reader-preview__surah">
        <div>
          <span className="surah-chip">Surah</span>
          <h3 className="reader-preview__surah-title">
            {sampleSurahPreview.surahNameEnglish}
          </h3>
        </div>
        <p
          className="reader-preview__surah-arabic"
          dir="rtl"
          lang="ar"
        >
          {sampleSurahPreview.surahNameArabic}
        </p>
        <p className="reader-preview__surah-meta">
          {sampleSurahPreview.revelationType}
        </p>
      </div>
      <ol className="ayah-list">
        {sampleSurahPreview.ayahs.map((ayah) => (
          <li key={ayah.number} className="ayah-card">
            <span className="ayah-card__number">Ayah {ayah.number}</span>
            <p className="ayah-card__arabic" dir="rtl" lang="ar">
              {ayah.arabic}
            </p>
            <p className="ayah-card__translation">{ayah.translation}</p>
          </li>
        ))}
      </ol>
      <div className="reader-preview__footer">
        <p className="attribution">{sampleSurahPreview.arabicAttribution}</p>
        <p className="attribution">
          {sampleSurahPreview.translationAttribution}
        </p>
        <p className="reader-preview__note">{sampleSurahPreview.sourceNote}</p>
      </div>
    </section>
  );
}
