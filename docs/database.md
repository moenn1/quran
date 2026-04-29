# QuranKit Database Source Evaluation

This document evaluates `AbdullahGhanem/quran-database` as the initial QuranKit upstream source and defines the attribution and normalization plan for downstream use.

## Evaluated Upstream

- Repository: `https://github.com/AbdullahGhanem/quran-database`
- Evaluated commit: `f6c4c805f22b0432677d79aafc12139b915e1a0d`
- Commit date: `2026-03-09`
- Primary data artifact: `quran.sql.zip`
- `quran.sql.zip` SHA-256: `ff9033de414a1a18fe42e241dc81f4528c3b194a1e8304d3ac06c9d5b0d7f155`
- Dump generation metadata inside `quran.sql`: `Jun 07, 2018 at 10:43 AM`, MySQL `5.7.22`, phpMyAdmin `4.7.7`
- Reproducible summary: [docs/upstream/quran-database-summary.json](upstream/quran-database-summary.json)
- Summary generator: [scripts/analyze_upstream_quran_sql.py](../scripts/analyze_upstream_quran_sql.py)

## Repository Inventory

At evaluation time the upstream repository contains:

| Path | Notes |
| --- | --- |
| `README.md` | Project overview, schema description, import instructions, and a short license sentence |
| `quran.sql.zip` | The only data artifact in the repository |
| `screenshots/` | Database screenshots |
| `LICENSE` | Not present |

The upstream README says the project is open source and that the Quran text is in the public domain. That statement is useful for source attribution, but it is not a substitute for a repository-level software license or per-edition redistribution terms.

## Actual SQL Dump Contents

The README schema description is materially inaccurate relative to the dump. The SQL export contains these tables:

| Table | Rows | Notes |
| --- | ---: | --- |
| `surahs` | 114 | Surah metadata only |
| `ayahs` | 6236 | Arabic ayah text plus page, juz, hizb, and sajda columns |
| `editions` | 134 | Translation, tafsir, transliteration, Quran, and audio edition metadata |
| `ayah_edition` | 835624 | One row per ayah per edition |
| `juzs` | 0 | Empty table with only `id` and timestamps |
| `hizbs` | 0 | Empty table with only `id` and timestamps |
| `migrations` | 8 | Laravel app scaffolding |
| `users` | 0 | Laravel app scaffolding |
| `password_resets` | 0 | Laravel app scaffolding |

Important mismatches against the README:

- The README refers to `quran_surahs`, `quran_ayahs`, `quran_ayat_edition`, and `quran_addons`.
- The dump actually uses `surahs`, `ayahs`, and `ayah_edition`.
- There is no `addons` table in the dump.
- `juzs` and `hizbs` already exist in schema form, but both are empty and cannot provide range metadata on their own.

## Coverage Confirmed

The dump is strong enough to bootstrap QuranKit's core read path:

- `surahs` contains 114 rows.
- `ayahs` contains 6236 rows.
- Global ayah IDs and global ayah numbers are sequential from `1` to `6236`.
- `page` values span `1..604`.
- `juz_id` values span `1..30`.
- `hizb_id` values span `1..240`.
- `sajda` is present as a boolean flag on 15 ayahs.
- Every edition currently has exactly `6236` related `ayah_edition` rows, which is a good baseline for translation-integrity validation.

The edition metadata spans:

- 110 text editions
- 24 audio editions
- 100 translation editions
- 10 Quran editions
- 2 tafsir editions
- 2 transliteration editions
- 20 `versebyverse` editions

## Source Behavior And Data Risks

The source is usable, but QuranKit should not ingest it blindly.

### 1. Ayah text segmentation differs from some mainstream corpora

Most first ayah texts for surahs other than `1` and `9` are basmala-prefixed in the source dump. For example:

- `2:1` starts with the basmala and then `الٓمٓ`
- `3:1` starts with the basmala and then `الٓمٓ`
- `27:1` starts with the basmala and then `طسٓ`
- `9:1` does not include the basmala
- `95:1` and `97:1` use a basmala-like prefix spelled `بِّسْمِ` instead of the standard `بِسْمِ`

QuranKit must preserve the source text exactly in its raw ingestion layer and explicitly document this upstream segmentation behavior and text anomaly.

### 2. The first ayah contains a UTF-8 BOM

Surah `1:1` begins with a UTF-8 byte order mark in the SQL dump. That is an encoding artifact, not Quran content, but it is still present in the source bytes. QuranKit should:

- retain a checksum and source snapshot for auditability
- treat BOM handling as an explicit ingestion rule with tests
- avoid silent or ad hoc string cleanup

### 3. `hizb_id` looks like quarter-hizb granularity

The `ayahs.hizb_id` range is `1..240`, while the `hizbs` table is empty. That strongly suggests the field represents quarter-hizb slots rather than a populated 60-row hizb dimension. QuranKit should normalize this into explicit fields such as `hizb_number` and `rub_el_hizb_number` instead of copying the upstream name blindly.

### 4. Translation and audio rights are not documented

The `editions` table carries identifiers and display names, but there is no per-edition license, attribution URL, copyright notice, or redistribution permission in the dump. This is the largest downstream risk.

QuranKit should not assume that all translations or audio assets are safe to redistribute just because they exist in the upstream dump.

### 5. The SQL dump is much older than the repository activity

The upstream repository has recent commits, but the SQL dump itself still identifies as a phpMyAdmin export from `2018-06-07`. QuranKit should treat the dump as a fixed snapshot, not as proof of recent data maintenance.

## Attribution Requirements For QuranKit

Every relevant data path in QuranKit should preserve source and edition attribution.

Minimum attribution requirements:

- store the upstream repository URL
- store the exact upstream commit SHA used for ingestion
- store the retrieved filename and SHA-256 checksum
- store the dump generation metadata when available
- store the upstream edition identifier for every imported edition
- store edition language, name, English name, format, and type
- expose source attribution in API responses for Quran text and editions
- block editions from public API exposure until their attribution and reuse posture have been reviewed

Recommended normalized attribution model:

| Table | Purpose |
| --- | --- |
| `source_releases` | One row per upstream snapshot with repo URL, commit SHA, checksum, retrieved timestamp, and notes |
| `source_files` | Optional per-file records for `quran.sql.zip` and any derived artifacts |
| `editions` | QuranKit edition catalog with upstream identifier and display attribution |
| `edition_attributions` | Optional normalized attribution, rights notes, URLs, and review status |

## QuranKit Normalization Plan

The first implementation should separate raw ingestion from normalized serving tables.

### Stage 1. Raw source capture

- Download the upstream repository at a locked commit.
- Record the repository URL, commit SHA, retrieval date, and `quran.sql.zip` checksum.
- Preserve the raw dump outside application tables for auditability.

### Stage 2. Raw relational import

- Import `surahs`, `ayahs`, `editions`, and `ayah_edition` into raw staging tables.
- Keep column names close to upstream names in staging so diffs are easy to audit.
- Store raw text exactly as sourced in staging.

### Stage 3. QuranKit normalized schema

Normalize the staging data into QuranKit-owned tables:

| QuranKit table | Notes |
| --- | --- |
| `surahs` | Canonical surah metadata |
| `ayahs` | Canonical ayah rows with `surah_id`, `ayah_number`, `global_ayah_number`, `page_number`, `juz_number`, `hizb_slot`, `sajda` |
| `ayah_texts` | Text-bearing rows keyed by ayah and edition |
| `editions` | Edition catalog with type, format, attribution fields, and review status |
| `source_releases` | Locked provenance records for every import |

Normalization rules:

- preserve the upstream Arabic text exactly in the raw layer
- derive QuranKit keys such as `surah_number:ayah_number` and `global_ayah_number`
- derive explicit QuranKit naming for `hizb_slot` or `rub_el_hizb` instead of copying the ambiguous upstream name
- keep tafsir, translation, transliteration, Quran text, and audio editions distinct
- do not expose private user features from source data because none exist in this upstream

## Validation Plan

QuranKit should enforce the following validations during import and in test coverage:

- 114 surahs exist
- 6236 ayat exist
- global ayah numbers are sequential with no gaps
- `number_in_surah` is sequential within each surah
- `page_number` spans `1..604`
- `juz_number` spans `1..30`
- `hizb_slot` spans the expected normalized range
- every imported edition has one row per ayah unless intentionally excluded
- every public-serving row carries source attribution
- BOM handling, if any, is explicit and tested

## Recommendation

`AbdullahGhanem/quran-database` is acceptable as an initial QuranKit bootstrap source for raw Quran text, edition catalog metadata, and baseline translations. It is not sufficient on its own for final public-serving attribution or rights confidence.

Proceed with this source only if QuranKit:

- locks imports to specific upstream commits
- keeps raw source provenance
- treats translation and audio editions as separately reviewable assets
- documents the basmala segmentation behavior
- normalizes hizb metadata carefully instead of trusting the empty upstream tables
