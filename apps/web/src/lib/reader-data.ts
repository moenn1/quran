export type RevelationPlace = "makkah" | "madinah";

export type BundledAyah = {
  reference: string;
  ayahNumber: number;
  arabicText: string;
  translationText: string;
};

export type BundledSurah = {
  number: number;
  nameEnglish: string;
  nameArabic: string;
  nameTranslation: string;
  revelationPlace: RevelationPlace;
  ayahCount: number;
  pages: readonly [number, number];
  ayahs: readonly BundledAyah[];
};

export const bundledReaderAttribution = {
  label: "Bundled reader sample",
  arabic:
    "Arabic text sample: Quran.com API, Uthmani script, bundled for the routed reader preview.",
  translation:
    "English translation sample: Saheeh International via AlQuran.Cloud.",
  note:
    "This routed sample keeps Quran text and translation attribution visible while QuranKit's broader validated reading corpus is being wired into the web app.",
} as const;

export const bundledSurahs = [
  {
    number: 1,
    nameEnglish: "Al-Fatihah",
    nameArabic: "الفاتحة",
    nameTranslation: "The Opener",
    revelationPlace: "makkah",
    ayahCount: 7,
    pages: [1, 1] as const,
    ayahs: [
      {
        reference: "1:1",
        ayahNumber: 1,
        arabicText: "بِسْمِ ٱللَّهِ ٱلرَّحْمَـٰنِ ٱلرَّحِيمِ",
        translationText:
          "In the name of Allah, the Entirely Merciful, the Especially Merciful.",
      },
      {
        reference: "1:2",
        ayahNumber: 2,
        arabicText: "ٱلْحَمْدُ لِلَّهِ رَبِّ ٱلْعَـٰلَمِينَ",
        translationText:
          "Praise is due to Allah, Lord of the worlds.",
      },
      {
        reference: "1:3",
        ayahNumber: 3,
        arabicText: "ٱلرَّحْمَـٰنِ ٱلرَّحِيمِ",
        translationText:
          "The Entirely Merciful, the Especially Merciful,",
      },
      {
        reference: "1:4",
        ayahNumber: 4,
        arabicText: "مَـٰلِكِ يَوْمِ ٱلدِّينِ",
        translationText: "Sovereign of the Day of Recompense.",
      },
      {
        reference: "1:5",
        ayahNumber: 5,
        arabicText: "إِيَّاكَ نَعْبُدُ وَإِيَّاكَ نَسْتَعِينُ",
        translationText:
          "It is You we worship and You we ask for help.",
      },
      {
        reference: "1:6",
        ayahNumber: 6,
        arabicText: "ٱهْدِنَا ٱلصِّرَٰطَ ٱلْمُسْتَقِيمَ",
        translationText: "Guide us to the straight path -",
      },
      {
        reference: "1:7",
        ayahNumber: 7,
        arabicText:
          "صِرَٰطَ ٱلَّذِينَ أَنْعَمْتَ عَلَيْهِمْ غَيْرِ ٱلْمَغْضُوبِ عَلَيْهِمْ وَلَا ٱلضَّآلِّينَ",
        translationText:
          "The path of those upon whom You have bestowed favor, not of those who have earned anger or of those who are astray.",
      },
    ],
  },
  {
    number: 98,
    nameEnglish: "Al-Bayyinah",
    nameArabic: "البينة",
    nameTranslation: "The Clear Proof",
    revelationPlace: "madinah",
    ayahCount: 8,
    pages: [598, 599] as const,
    ayahs: [
      {
        reference: "98:1",
        ayahNumber: 1,
        arabicText:
          "لَمْ يَكُنِ ٱلَّذِينَ كَفَرُوا۟ مِنْ أَهْلِ ٱلْكِتَـٰبِ وَٱلْمُشْرِكِينَ مُنفَكِّينَ حَتَّىٰ تَأْتِيَهُمُ ٱلْبَيِّنَةُ",
        translationText:
          "Those who disbelieved among the People of the Scripture and the polytheists were not to be parted until there came to them clear evidence -",
      },
      {
        reference: "98:2",
        ayahNumber: 2,
        arabicText: "رَسُولٌ مِّنَ ٱللَّهِ يَتْلُوا۟ صُحُفًا مُّطَهَّرَةً",
        translationText:
          "A Messenger from Allah, reciting purified scriptures,",
      },
      {
        reference: "98:3",
        ayahNumber: 3,
        arabicText: "فِيهَا كُتُبٌ قَيِّمَةٌ",
        translationText:
          "Within which are correct writings.",
      },
      {
        reference: "98:4",
        ayahNumber: 4,
        arabicText:
          "وَمَا تَفَرَّقَ ٱلَّذِينَ أُوتُوا۟ ٱلْكِتَـٰبَ إِلَّا مِنۢ بَعْدِ مَا جَآءَتْهُمُ ٱلْبَيِّنَةُ",
        translationText:
          "Nor did those who were given the Scripture become divided until after there had come to them clear evidence.",
      },
      {
        reference: "98:5",
        ayahNumber: 5,
        arabicText:
          "وَمَآ أُمِرُوٓا۟ إِلَّا لِيَعْبُدُوا۟ ٱللَّهَ مُخْلِصِينَ لَهُ ٱلدِّينَ حُنَفَآءَ وَيُقِيمُوا۟ ٱلصَّلَوٰةَ وَيُؤْتُوا۟ ٱلزَّكَوٰةَ ۚ وَذَٰلِكَ دِينُ ٱلْقَيِّمَةِ",
        translationText:
          "And they were not commanded except to worship Allah, sincere to Him in religion, inclining to truth, and to establish prayer and to give zakah. And that is the correct religion.",
      },
      {
        reference: "98:6",
        ayahNumber: 6,
        arabicText:
          "إِنَّ ٱلَّذِينَ كَفَرُوا۟ مِنْ أَهْلِ ٱلْكِتَـٰبِ وَٱلْمُشْرِكِينَ فِى نَارِ جَهَنَّمَ خَـٰلِدِينَ فِيهَآ ۚ أُو۟لَـٰٓئِكَ هُمْ شَرُّ ٱلْبَرِيَّةِ",
        translationText:
          "Indeed, they who disbelieved among the People of the Scripture and the polytheists will be in the fire of Hell, abiding eternally therein. Those are the worst of creatures.",
      },
      {
        reference: "98:7",
        ayahNumber: 7,
        arabicText:
          "إِنَّ ٱلَّذِينَ ءَامَنُوا۟ وَعَمِلُوا۟ ٱلصَّـٰلِحَـٰتِ أُو۟لَـٰٓئِكَ هُمْ خَيْرُ ٱلْبَرِيَّةِ",
        translationText:
          "Indeed, they who have believed and done righteous deeds - those are the best of creatures.",
      },
      {
        reference: "98:8",
        ayahNumber: 8,
        arabicText:
          "جَزَآؤُهُمْ عِندَ رَبِّهِمْ جَنَّـٰتُ عَدْنٍ تَجْرِى مِن تَحْتِهَا ٱلْأَنْهَـٰرُ خَـٰلِدِينَ فِيهَآ أَبَدًا ۖ رَّضِىَ ٱللَّهُ عَنْهُمْ وَرَضُوا۟ عَنْهُ ۚ ذَٰلِكَ لِمَنْ خَشِىَ رَبَّهُۥ",
        translationText:
          "Their reward with their Lord will be gardens of perpetual residence beneath which rivers flow, wherein they will abide forever, Allah being pleased with them and they with Him. That is for whoever has feared his Lord.",
      },
    ],
  },
  {
    number: 99,
    nameEnglish: "Az-Zalzalah",
    nameArabic: "الزلزلة",
    nameTranslation: "The Earthquake",
    revelationPlace: "madinah",
    ayahCount: 8,
    pages: [599, 599] as const,
    ayahs: [
      {
        reference: "99:1",
        ayahNumber: 1,
        arabicText: "إِذَا زُلْزِلَتِ ٱلْأَرْضُ زِلْزَالَهَا",
        translationText:
          "When the earth is shaken with its final earthquake",
      },
      {
        reference: "99:2",
        ayahNumber: 2,
        arabicText: "وَأَخْرَجَتِ ٱلْأَرْضُ أَثْقَالَهَا",
        translationText:
          "And the earth discharges its burdens",
      },
      {
        reference: "99:3",
        ayahNumber: 3,
        arabicText: "وَقَالَ ٱلْإِنسَـٰنُ مَا لَهَا",
        translationText:
          'And man says, "What is wrong with it?" -',
      },
      {
        reference: "99:4",
        ayahNumber: 4,
        arabicText: "يَوْمَئِذٍ تُحَدِّثُ أَخْبَارَهَا",
        translationText:
          "That Day, it will report its news",
      },
      {
        reference: "99:5",
        ayahNumber: 5,
        arabicText: "بِأَنَّ رَبَّكَ أَوْحَىٰ لَهَا",
        translationText:
          "Because your Lord has inspired it.",
      },
      {
        reference: "99:6",
        ayahNumber: 6,
        arabicText:
          "يَوْمَئِذٍ يَصْدُرُ ٱلنَّاسُ أَشْتَاتًا لِّيُرَوْا۟ أَعْمَـٰلَهُمْ",
        translationText:
          "That Day, the people will depart separated into categories to be shown the result of their deeds.",
      },
      {
        reference: "99:7",
        ayahNumber: 7,
        arabicText: "فَمَن يَعْمَلْ مِثْقَالَ ذَرَّةٍ خَيْرًا يَرَهُۥ",
        translationText:
          "So whoever does an atom's weight of good will see it,",
      },
      {
        reference: "99:8",
        ayahNumber: 8,
        arabicText: "وَمَن يَعْمَلْ مِثْقَالَ ذَرَّةٍ شَرًّا يَرَهُۥ",
        translationText:
          "And whoever does an atom's weight of evil will see it.",
      },
    ],
  },
  {
    number: 103,
    nameEnglish: "Al-'Asr",
    nameArabic: "العصر",
    nameTranslation: "The Declining Day",
    revelationPlace: "makkah",
    ayahCount: 3,
    pages: [601, 601] as const,
    ayahs: [
      {
        reference: "103:1",
        ayahNumber: 1,
        arabicText: "وَٱلْعَصْرِ",
        translationText: "By time,",
      },
      {
        reference: "103:2",
        ayahNumber: 2,
        arabicText: "إِنَّ ٱلْإِنسَـٰنَ لَفِى خُسْرٍ",
        translationText:
          "Indeed, mankind is in loss,",
      },
      {
        reference: "103:3",
        ayahNumber: 3,
        arabicText:
          "إِلَّا ٱلَّذِينَ ءَامَنُوا۟ وَعَمِلُوا۟ ٱلصَّـٰلِحَـٰتِ وَتَوَاصَوْا۟ بِٱلْحَقِّ وَتَوَاصَوْا۟ بِٱلصَّبْرِ",
        translationText:
          "Except for those who have believed and done righteous deeds and advised each other to truth and advised each other to patience.",
      },
    ],
  },
  {
    number: 108,
    nameEnglish: "Al-Kawthar",
    nameArabic: "الكوثر",
    nameTranslation: "The Abundance",
    revelationPlace: "makkah",
    ayahCount: 3,
    pages: [602, 602] as const,
    ayahs: [
      {
        reference: "108:1",
        ayahNumber: 1,
        arabicText: "إِنَّآ أَعْطَيْنَـٰكَ ٱلْكَوْثَرَ",
        translationText:
          "Indeed, We have granted you al-Kawthar.",
      },
      {
        reference: "108:2",
        ayahNumber: 2,
        arabicText: "فَصَلِّ لِرَبِّكَ وَٱنْحَرْ",
        translationText:
          "So pray to your Lord and offer sacrifice to Him alone.",
      },
      {
        reference: "108:3",
        ayahNumber: 3,
        arabicText: "إِنَّ شَانِئَكَ هُوَ ٱلْأَبْتَرُ",
        translationText:
          "Indeed, your enemy is the one cut off.",
      },
    ],
  },
  {
    number: 110,
    nameEnglish: "An-Nasr",
    nameArabic: "النصر",
    nameTranslation: "The Divine Support",
    revelationPlace: "madinah",
    ayahCount: 3,
    pages: [603, 603] as const,
    ayahs: [
      {
        reference: "110:1",
        ayahNumber: 1,
        arabicText: "إِذَا جَآءَ نَصْرُ ٱللَّهِ وَٱلْفَتْحُ",
        translationText:
          "When the victory of Allah has come and the conquest,",
      },
      {
        reference: "110:2",
        ayahNumber: 2,
        arabicText:
          "وَرَأَيْتَ ٱلنَّاسَ يَدْخُلُونَ فِى دِينِ ٱللَّهِ أَفْوَاجًا",
        translationText:
          "And you see the people entering into the religion of Allah in multitudes,",
      },
      {
        reference: "110:3",
        ayahNumber: 3,
        arabicText:
          "فَسَبِّحْ بِحَمْدِ رَبِّكَ وَٱسْتَغْفِرْهُ ۚ إِنَّهُۥ كَانَ تَوَّابًۢا",
        translationText:
          "Then exalt Him with praise of your Lord and ask forgiveness of Him. Indeed, He is ever Accepting of Repentance.",
      },
    ],
  },
  {
    number: 112,
    nameEnglish: "Al-Ikhlas",
    nameArabic: "الإخلاص",
    nameTranslation: "The Sincerity",
    revelationPlace: "makkah",
    ayahCount: 4,
    pages: [604, 604] as const,
    ayahs: [
      {
        reference: "112:1",
        ayahNumber: 1,
        arabicText: "قُلْ هُوَ ٱللَّهُ أَحَدٌ",
        translationText:
          'Say, "He is Allah, Who is One,',
      },
      {
        reference: "112:2",
        ayahNumber: 2,
        arabicText: "ٱللَّهُ ٱلصَّمَدُ",
        translationText:
          "Allah, the Eternal Refuge.",
      },
      {
        reference: "112:3",
        ayahNumber: 3,
        arabicText: "لَمْ يَلِدْ وَلَمْ يُولَدْ",
        translationText:
          "He neither begets nor is born,",
      },
      {
        reference: "112:4",
        ayahNumber: 4,
        arabicText: "وَلَمْ يَكُن لَّهُۥ كُفُوًا أَحَدٌۢ",
        translationText:
          'Nor is there to Him any equivalent."',
      },
    ],
  },
  {
    number: 113,
    nameEnglish: "Al-Falaq",
    nameArabic: "الفلق",
    nameTranslation: "The Daybreak",
    revelationPlace: "makkah",
    ayahCount: 5,
    pages: [604, 604] as const,
    ayahs: [
      {
        reference: "113:1",
        ayahNumber: 1,
        arabicText: "قُلْ أَعُوذُ بِرَبِّ ٱلْفَلَقِ",
        translationText:
          'Say, "I seek refuge in the Lord of daybreak',
      },
      {
        reference: "113:2",
        ayahNumber: 2,
        arabicText: "مِن شَرِّ مَا خَلَقَ",
        translationText:
          "From the evil of that which He created",
      },
      {
        reference: "113:3",
        ayahNumber: 3,
        arabicText: "وَمِن شَرِّ غَاسِقٍ إِذَا وَقَبَ",
        translationText:
          "And from the evil of darkness when it settles",
      },
      {
        reference: "113:4",
        ayahNumber: 4,
        arabicText: "وَمِن شَرِّ ٱلنَّفَّـٰثَـٰتِ فِى ٱلْعُقَدِ",
        translationText:
          "And from the evil of the blowers in knots",
      },
      {
        reference: "113:5",
        ayahNumber: 5,
        arabicText: "وَمِن شَرِّ حَاسِدٍ إِذَا حَسَدَ",
        translationText:
          'And from the evil of an envier when he envies."',
      },
    ],
  },
  {
    number: 114,
    nameEnglish: "An-Nas",
    nameArabic: "الناس",
    nameTranslation: "Mankind",
    revelationPlace: "makkah",
    ayahCount: 6,
    pages: [604, 604] as const,
    ayahs: [
      {
        reference: "114:1",
        ayahNumber: 1,
        arabicText: "قُلْ أَعُوذُ بِرَبِّ ٱلنَّاسِ",
        translationText:
          'Say, "I seek refuge in the Lord of mankind,',
      },
      {
        reference: "114:2",
        ayahNumber: 2,
        arabicText: "مَلِكِ ٱلنَّاسِ",
        translationText:
          "The Sovereign of mankind,",
      },
      {
        reference: "114:3",
        ayahNumber: 3,
        arabicText: "إِلَـٰهِ ٱلنَّاسِ",
        translationText:
          "The God of mankind,",
      },
      {
        reference: "114:4",
        ayahNumber: 4,
        arabicText: "مِن شَرِّ ٱلْوَسْوَاسِ ٱلْخَنَّاسِ",
        translationText:
          "From the evil of the retreating whisperer -",
      },
      {
        reference: "114:5",
        ayahNumber: 5,
        arabicText: "ٱلَّذِى يُوَسْوِسُ فِى صُدُورِ ٱلنَّاسِ",
        translationText:
          "Who whispers evil into the breasts of mankind -",
      },
      {
        reference: "114:6",
        ayahNumber: 6,
        arabicText: "مِنَ ٱلْجِنَّةِ وَٱلنَّاسِ",
        translationText:
          'From among the jinn and mankind."',
      },
    ],
  },
] as const satisfies readonly BundledSurah[];

const flattenedAyahs = bundledSurahs.flatMap((surah) =>
  surah.ayahs.map((ayah) => ({
    surah,
    ayah,
  })),
);

export function getBundledSurahs() {
  return bundledSurahs;
}

export function getBundledSurah(number: number) {
  return bundledSurahs.find((surah) => surah.number === number) ?? null;
}

export function getBundledAyah(surahNumber: number, ayahNumber: number) {
  const surah = getBundledSurah(surahNumber);
  if (!surah) {
    return null;
  }

  const ayah = surah.ayahs.find((item) => item.ayahNumber === ayahNumber) ?? null;
  if (!ayah) {
    return null;
  }

  return {
    surah,
    ayah,
  };
}

export function getBundledAyahContext(surahNumber: number, ayahNumber: number) {
  const surah = getBundledSurah(surahNumber);
  if (!surah) {
    return [] as const;
  }

  const focusIndex = surah.ayahs.findIndex((ayah) => ayah.ayahNumber === ayahNumber);
  if (focusIndex === -1) {
    return [] as const;
  }

  return surah.ayahs.slice(
    Math.max(0, focusIndex - 1),
    Math.min(surah.ayahs.length, focusIndex + 2),
  );
}

export function getBundledSurahNeighbors(number: number) {
  const index = bundledSurahs.findIndex((surah) => surah.number === number);

  return {
    previous: index > 0 ? bundledSurahs[index - 1] : null,
    next: index >= 0 && index < bundledSurahs.length - 1 ? bundledSurahs[index + 1] : null,
  };
}

export function getBundledAyahNeighbors(surahNumber: number, ayahNumber: number) {
  const index = flattenedAyahs.findIndex(
    (entry) =>
      entry.surah.number === surahNumber && entry.ayah.ayahNumber === ayahNumber,
  );

  return {
    previous: index > 0 ? flattenedAyahs[index - 1] : null,
    next:
      index >= 0 && index < flattenedAyahs.length - 1
        ? flattenedAyahs[index + 1]
        : null,
  };
}

export function formatRevelationPlace(place: RevelationPlace) {
  return place === "makkah" ? "Meccan" : "Medinan";
}

export function formatPageRange(pages: readonly [number, number]) {
  const [start, end] = pages;
  return start === end ? `Page ${start}` : `Pages ${start}-${end}`;
}
