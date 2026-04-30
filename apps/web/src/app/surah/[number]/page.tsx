import type { Metadata } from "next";

import Link from "next/link";
import { notFound } from "next/navigation";

import { ReaderWorkspace } from "@/components/reader-workspace";
import {
  formatPageRange,
  formatRevelationPlace,
  getBundledSurah,
  getBundledSurahNeighbors,
  getBundledSurahs,
} from "@/lib/reader-data";

type SurahPageProps = {
  params: Promise<{
    number: string;
  }>;
};

export async function generateStaticParams() {
  return getBundledSurahs().map((surah) => ({
    number: surah.number.toString(),
  }));
}

export async function generateMetadata({
  params,
}: SurahPageProps): Promise<Metadata> {
  const { number } = await params;
  const surah = getBundledSurah(Number(number));

  return {
    title: surah ? `${surah.nameEnglish} Reader` : "Surah Reader",
    description: surah
      ? `Read Surah ${surah.number} with Arabic text, translation controls, and private-by-default study actions.`
      : "Read a bundled QuranKit surah sample.",
  };
}

export default async function SurahPage({ params }: SurahPageProps) {
  const { number } = await params;
  const surahNumber = Number(number);
  const surah = getBundledSurah(surahNumber);

  if (!surah) {
    notFound();
  }

  const { previous, next } = getBundledSurahNeighbors(surahNumber);

  return (
    <>
      <section className="page-hero reader-route-hero">
        <Link href="/explore" className="reader-route-backlink">
          Return to explore
        </Link>
        <p className="section-label">Surah {surah.number}</p>
        <div className="reader-route-header">
          <div className="reader-route-header__copy">
            <h1 className="page-hero__title">{surah.nameEnglish}</h1>
            <p className="page-hero__description">
              {surah.nameTranslation} with Arabic-first reading, translation
              toggles, font controls, and private study actions kept close to
              the ayah surface.
            </p>
          </div>
          <p className="reader-route-header__arabic" dir="rtl" lang="ar">
            {surah.nameArabic}
          </p>
        </div>
        <ul className="pill-list" aria-label={`${surah.nameEnglish} metadata`}>
          <li className="pill">{formatRevelationPlace(surah.revelationPlace)}</li>
          <li className="pill">{surah.ayahCount} ayahs</li>
          <li className="pill">{formatPageRange(surah.pages)}</li>
          <li className="pill">Bundled reader sample</li>
        </ul>
      </section>
      <ReaderWorkspace
        surah={surah}
        ayahs={surah.ayahs}
        navigationLabel="Surah reader"
      />
      <nav className="route-pager" aria-label="Sample surah navigation">
        {previous ? (
          <Link href={`/surah/${previous.number}`} className="route-pager__link">
            <span className="route-pager__eyebrow">Previous sample surah</span>
            <strong>{previous.nameEnglish}</strong>
            <span>{previous.number}</span>
          </Link>
        ) : (
          <div className="route-pager__link route-pager__link--static">
            <span className="route-pager__eyebrow">Previous sample surah</span>
            <strong>Beginning of bundled sample</strong>
            <span>Start from Al-Fatihah</span>
          </div>
        )}
        {next ? (
          <Link href={`/surah/${next.number}`} className="route-pager__link">
            <span className="route-pager__eyebrow">Next sample surah</span>
            <strong>{next.nameEnglish}</strong>
            <span>{next.number}</span>
          </Link>
        ) : (
          <div className="route-pager__link route-pager__link--static">
            <span className="route-pager__eyebrow">Next sample surah</span>
            <strong>End of bundled sample</strong>
            <span>Browse again from explore</span>
          </div>
        )}
      </nav>
    </>
  );
}
