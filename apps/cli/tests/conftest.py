from __future__ import annotations

import sqlite3
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"

if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


@pytest.fixture()
def sample_sqlite_db(tmp_path: Path) -> Path:
    db_path = tmp_path / "qurankit.sqlite3"
    conn = sqlite3.connect(db_path)
    try:
        conn.executescript(
            """
            CREATE TABLE surahs (
                id INTEGER PRIMARY KEY,
                number INTEGER NOT NULL,
                name_ar TEXT NOT NULL,
                name_en TEXT NOT NULL,
                name_en_translation TEXT,
                type TEXT,
                created_at TEXT,
                updated_at TEXT
            );

            CREATE TABLE ayahs (
                id INTEGER PRIMARY KEY,
                number INTEGER NOT NULL,
                text TEXT NOT NULL,
                number_in_surah INTEGER NOT NULL,
                page INTEGER NOT NULL,
                surah_id INTEGER NOT NULL,
                hizb_id INTEGER NOT NULL,
                juz_id INTEGER NOT NULL,
                sajda INTEGER NOT NULL DEFAULT 0,
                created_at TEXT,
                updated_at TEXT
            );

            CREATE TABLE editions (
                id INTEGER PRIMARY KEY,
                identifier TEXT NOT NULL,
                language TEXT,
                name TEXT,
                englishName TEXT,
                format TEXT,
                type TEXT,
                created_at TEXT,
                updated_at TEXT
            );

            CREATE TABLE ayah_edition (
                id INTEGER PRIMARY KEY,
                ayah_id INTEGER NOT NULL,
                edition_id INTEGER NOT NULL,
                data TEXT NOT NULL,
                is_audio INTEGER NOT NULL DEFAULT 0,
                created_at TEXT,
                updated_at TEXT
            );
            """
        )

        conn.executemany(
            """
            INSERT INTO surahs (
                id, number, name_ar, name_en, name_en_translation, type, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, NULL, NULL)
            """,
            [
                (1, 1, "ٱلْفَاتِحَةِ", "Al-Fatihah", "The Opening", "Meccan"),
                (2, 2, "ٱلْبَقَرَةِ", "Al-Baqarah", "The Cow", "Medinan"),
                (112, 112, "ٱلْإِخْلَاصِ", "Al-Ikhlas", "Sincerity", "Meccan"),
            ],
        )

        conn.executemany(
            """
            INSERT INTO ayahs (
                id, number, text, number_in_surah, page, surah_id, hizb_id, juz_id, sajda, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, NULL, NULL)
            """,
            [
                (
                    1,
                    1,
                    "بِسْمِ ٱللَّهِ ٱلرَّحْمَٰنِ ٱلرَّحِيمِ",
                    1,
                    1,
                    1,
                    1,
                    1,
                    0,
                ),
                (
                    2,
                    2,
                    "ٱلْحَمْدُ لِلَّهِ رَبِّ ٱلْعَٰلَمِينَ",
                    2,
                    1,
                    1,
                    1,
                    1,
                    0,
                ),
                (
                    3,
                    3,
                    "ٱلرَّحْمَٰنِ ٱلرَّحِيمِ",
                    3,
                    1,
                    1,
                    1,
                    1,
                    0,
                ),
                (
                    4,
                    4,
                    "مَٰلِكِ يَوْمِ ٱلدِّينِ",
                    4,
                    1,
                    1,
                    1,
                    1,
                    0,
                ),
                (
                    5,
                    5,
                    "إِيَّاكَ نَعْبُدُ وَإِيَّاكَ نَسْتَعِينُ",
                    5,
                    1,
                    1,
                    1,
                    1,
                    0,
                ),
                (
                    6,
                    6,
                    "ٱهْدِنَا ٱلصِّرَٰطَ ٱلْمُسْتَقِيمَ",
                    6,
                    1,
                    1,
                    1,
                    1,
                    0,
                ),
                (7, 7, "الٓمٓ", 1, 2, 2, 1, 1, 0),
                (
                    8,
                    8,
                    "ذَٰلِكَ ٱلْكِتَٰبُ لَا رَيْبَ ۛ فِيهِ هُدًى لِّلْمُتَّقِينَ",
                    2,
                    2,
                    2,
                    1,
                    1,
                    0,
                ),
                (9, 9, "قُلْ هُوَ ٱللَّهُ أَحَدٌ", 1, 604, 112, 240, 30, 0),
                (10, 10, "ٱللَّهُ ٱلصَّمَدُ", 2, 604, 112, 240, 30, 0),
            ],
        )

        conn.executemany(
            """
            INSERT INTO editions (
                id, identifier, language, name, englishName, format, type, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, NULL, NULL)
            """,
            [
                (
                    1,
                    "en.sahih",
                    "en",
                    "Saheeh International",
                    "Saheeh International",
                    "text",
                    "translation",
                )
            ],
        )

        conn.executemany(
            """
            INSERT INTO ayah_edition (
                id, ayah_id, edition_id, data, is_audio, created_at, updated_at
            ) VALUES (?, ?, ?, ?, 0, NULL, NULL)
            """,
            [
                (
                    1,
                    1,
                    1,
                    "In the name of Allah, the Entirely Merciful, the Especially Merciful.",
                ),
                (2, 2, 1, "All praise is due to Allah, Lord of the worlds."),
                (3, 3, 1, "The Entirely Merciful, the Especially Merciful."),
                (4, 4, 1, "Master of the Day of Judgment."),
                (5, 5, 1, "It is You we worship and You we ask for help."),
                (6, 6, 1, "Guide us to the straight path."),
                (7, 7, 1, "Alif, Lam, Meem."),
                (
                    8,
                    8,
                    1,
                    "This is the Book about which there is no doubt, a guidance for those conscious of Allah.",
                ),
                (9, 9, 1, "Say, He is Allah, One."),
                (10, 10, 1, "Allah, the Eternal Refuge."),
            ],
        )
        conn.commit()
    finally:
        conn.close()

    return db_path
