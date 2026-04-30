from __future__ import annotations

from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

from qurankit_api.data.pipeline import ValidationExpectations


SAMPLE_SQL = """-- phpMyAdmin SQL Dump
-- version 4.7.7
-- Generation Time: Apr 29, 2026 at 10:00 PM
-- Server version: 5.7.22
-- PHP Version: 7.1.18

-- Database: `quran`
--

CREATE TABLE `ayahs` (
  `id` int(10) UNSIGNED NOT NULL,
  `number` int(11) NOT NULL,
  `text` text COLLATE utf8mb4_unicode_ci NOT NULL,
  `number_in_surah` int(11) NOT NULL,
  `page` int(11) NOT NULL,
  `surah_id` int(11) NOT NULL,
  `hizb_id` int(11) NOT NULL,
  `juz_id` int(11) NOT NULL,
  `sajda` tinyint(1) NOT NULL,
  `created_at` timestamp NULL DEFAULT NULL,
  `updated_at` timestamp NULL DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `ayah_edition` (
  `id` int(10) UNSIGNED NOT NULL,
  `ayah_id` int(10) UNSIGNED NOT NULL,
  `edition_id` int(10) UNSIGNED NOT NULL,
  `data` text COLLATE utf8mb4_unicode_ci NOT NULL,
  `is_audio` tinyint(1) NOT NULL,
  `created_at` timestamp NULL DEFAULT NULL,
  `updated_at` timestamp NULL DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `editions` (
  `id` int(10) UNSIGNED NOT NULL,
  `identifier` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `language` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `name` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `englishName` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `format` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `type` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `created_at` timestamp NULL DEFAULT NULL,
  `updated_at` timestamp NULL DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `surahs` (
  `id` int(10) UNSIGNED NOT NULL,
  `number` int(11) NOT NULL,
  `name_ar` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `name_en` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `name_en_translation` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `type` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `created_at` timestamp NULL DEFAULT NULL,
  `updated_at` timestamp NULL DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

INSERT INTO `surahs` (`id`, `number`, `name_ar`, `name_en`, `name_en_translation`, `type`, `created_at`, `updated_at`) VALUES
(1, 1, 'سورة الفاتحة', 'Al-Faatiha', 'The Opening', 'Meccan', NULL, NULL),
(2, 2, 'سورة البقرة', 'Al-Baqara', 'The Cow', 'Medinan', NULL, NULL);

INSERT INTO `ayahs` (`id`, `number`, `text`, `number_in_surah`, `page`, `surah_id`, `hizb_id`, `juz_id`, `sajda`, `created_at`, `updated_at`) VALUES
(1, 1, '﻿بِسْمِ ٱللَّهِ', 1, 1, 1, 1, 1, 0, NULL, NULL),
(2, 2, 'بِسْمِ ٱللَّهِ الٓمٓ', 1, 2, 2, 4, 1, 0, NULL, NULL),
(3, 3, 'ذَٰلِكَ ٱلْكِتَٰبُ', 2, 2, 2, 4, 1, 1, NULL, NULL);

INSERT INTO `editions` (`id`, `identifier`, `language`, `name`, `englishName`, `format`, `type`, `created_at`, `updated_at`) VALUES
(1, 'en.sahih', 'en', 'Sahih', 'Saheeh International', 'text', 'translation', NULL, NULL),
(2, 'quran-simple', 'ar', 'Simple', 'Simple', 'text', 'quran', NULL, NULL);

INSERT INTO `ayah_edition` (`id`, `ayah_id`, `edition_id`, `data`, `is_audio`, `created_at`, `updated_at`) VALUES
(1, 1, 1, 'In the name of Allah', 0, NULL, NULL),
(2, 2, 1, 'Alif Lam Mim', 0, NULL, NULL),
(3, 3, 1, 'That is the Book', 0, NULL, NULL),
(4, 1, 2, 'بِسْمِ ٱللَّهِ', 0, NULL, NULL),
(5, 2, 2, 'بِسْمِ ٱللَّهِ الٓمٓ', 0, NULL, NULL),
(6, 3, 2, 'ذَٰلِكَ ٱلْكِتَٰبُ', 0, NULL, NULL);
"""

SAMPLE_EXPECTATIONS = ValidationExpectations(
    surah_count=2,
    ayah_count=3,
    page_range=(1, 2),
    juz_range=(1, 1),
    hizb_range=(1, 1),
    rub_el_hizb_range=(1, 4),
)


def write_sample_zip(path: Path) -> Path:
    with ZipFile(path, "w", compression=ZIP_DEFLATED) as archive:
        archive.writestr("quran.sql", SAMPLE_SQL)
    return path
