import type { Metadata } from "next";

import Link from "next/link";
import { notFound } from "next/navigation";

import { ReaderWorkspace } from "@/components/reader-workspace";
import {
  formatRevelationPlace,
  getBundledAyah,
  getBundledAyahContext,
  getBundledAyahNeighbors,
  getBundledSurahs,
} from "@/lib/reader-data";

type AyahPageProps = {
  params: Promise<{
    surah: string;
    ayah: string;
  }>;
};

export async function generateStaticParams() {
  return getBundledSurahs().flatMap((surah) =>
    surah.ayahs.map((ayah) => ({
      surah: surah.number.toString(),
      ayah: ayah.ayahNumber.toString(),
    })),
  );
}

export async function generateMetadata({
  params,
}: AyahPageProps): Promise<Metadata> {
  const { surah, ayah } = await params;
  const result = getBundledAyah(Number(surah), Number(ayah));

  return {
    title: result ? `Ayah ${result.ayah.reference}` : "Ayah Detail",
    description: result
      ? `Read ayah ${result.ayah.reference} in context with translation toggles, font controls, and private study actions.`
      : "Read a bundled QuranKit ayah sample in context.",
  };
}

export default async function AyahPage({ params }: AyahPageProps) {
  const { surah, ayah } = await params;
  const surahNumber = Number(surah);
  const ayahNumber = Number(ayah);
  const result = getBundledAyah(surahNumber, ayahNumber);

  if (!result) {
    notFound();
  }

  const { surah: currentSurah, ayah: currentAyah } = result;
  const contextAyahs = getBundledAyahContext(surahNumber, ayahNumber);
  const { previous, next } = getBundledAyahNeighbors(surahNumber, ayahNumber);

  return (
    <>
      <section className="page-hero reader-route-hero">
        <Link href={`/surah/${currentSurah.number}`} className="reader-route-backlink">
          Return to full surah
        </Link>
        <p className="section-label">Ayah detail</p>
        <div className="reader-route-header">
          <div className="reader-route-header__copy">
            <h1 className="page-hero__title">Ayah {currentAyah.reference}</h1>
            <p className="page-hero__description">
              Open one ayah with its immediate context, then adjust translation
              visibility, text emphasis, and font sizing without losing the
              verse reference or attribution.
            </p>
          </div>
          <div className="reader-route-header__stack">
            <p className="reader-route-header__arabic" dir="rtl" lang="ar">
              {currentSurah.nameArabic}
            </p>
            <p className="reader-route-header__meta">
              {currentSurah.nameEnglish} · {formatRevelationPlace(currentSurah.revelationPlace)}
            </p>
          </div>
        </div>
        <ul className="pill-list" aria-label={`${currentAyah.reference} context`}>
          <li className="pill">Context window</li>
          <li className="pill">{currentSurah.nameTranslation}</li>
          <li className="pill">{currentAyah.reference}</li>
          <li className="pill">Private study actions</li>
        </ul>
      </section>
      <ReaderWorkspace
        surah={currentSurah}
        ayahs={contextAyahs}
        focusReference={currentAyah.reference}
        navigationLabel="Ayah detail"
      />
      <nav className="route-pager" aria-label="Ayah navigation">
        {previous ? (
          <Link
            href={`/ayah/${previous.surah.number}/${previous.ayah.ayahNumber}`}
            className="route-pager__link"
          >
            <span className="route-pager__eyebrow">Previous ayah</span>
            <strong>{previous.ayah.reference}</strong>
            <span>{previous.surah.nameEnglish}</span>
          </Link>
        ) : (
          <div className="route-pager__link route-pager__link--static">
            <span className="route-pager__eyebrow">Previous ayah</span>
            <strong>Beginning of bundled sample</strong>
            <span>Return to explore for another route</span>
          </div>
        )}
        {next ? (
          <Link
            href={`/ayah/${next.surah.number}/${next.ayah.ayahNumber}`}
            className="route-pager__link"
          >
            <span className="route-pager__eyebrow">Next ayah</span>
            <strong>{next.ayah.reference}</strong>
            <span>{next.surah.nameEnglish}</span>
          </Link>
        ) : (
          <div className="route-pager__link route-pager__link--static">
            <span className="route-pager__eyebrow">Next ayah</span>
            <strong>End of bundled sample</strong>
            <span>Browse again from explore</span>
          </div>
        )}
      </nav>
    </>
  );
}
