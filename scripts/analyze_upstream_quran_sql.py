from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from pathlib import Path
from typing import Any

CREATE_TABLE_RE = re.compile(r"^CREATE TABLE `([^`]+)` \($")
INSERT_RE = re.compile(r"^INSERT INTO `([^`]+)` \(([^)]+)\) VALUES$")
COLUMN_RE = re.compile(r"^  `([^`]+)` ")
INT_RE = re.compile(r"^-?\d+$")


def parse_sql_tuple(row_line: str) -> list[Any]:
    line = row_line.strip()
    if not line.startswith("("):
        raise ValueError(f"Expected tuple row, got: {row_line[:40]!r}")

    if line.endswith(","):
        line = line[:-1]
    if line.endswith(";"):
        line = line[:-1]
    if not line.endswith(")"):
        raise ValueError(f"Unexpected tuple ending: {row_line[-40:]!r}")

    values: list[Any] = []
    token: list[str] = []
    in_string = False
    escape = False

    for ch in line[1:-1]:
        if in_string:
            if escape:
                token.append(ch)
                escape = False
            elif ch == "\\":
                escape = True
            elif ch == "'":
                values.append("".join(token))
                token = []
                in_string = False
            else:
                token.append(ch)
            continue

        if ch == "'":
            token = []
            in_string = True
            continue

        if ch == ",":
            raw = "".join(token).strip()
            if raw:
                if raw == "NULL":
                    values.append(None)
                elif INT_RE.match(raw):
                    values.append(int(raw))
                else:
                    values.append(raw)
            token = []
            continue

        token.append(ch)

    raw = "".join(token).strip()
    if raw:
        if raw == "NULL":
            values.append(None)
        elif INT_RE.match(raw):
            values.append(int(raw))
        else:
            values.append(raw)

    return values


def _normalized_text(value: str | None) -> str:
    if not value:
        return ""
    return value.lstrip("\ufeff").strip()


def summarize_sql_dump(sql_path: Path) -> dict[str, Any]:
    create_columns: dict[str, list[str]] = {}
    row_counts: Counter[str] = Counter()
    current_create: str | None = None
    current_table: str | None = None
    current_columns: list[str] | None = None

    metadata: dict[str, Any] = {
        "path": str(sql_path),
        "bytes": sql_path.stat().st_size,
    }
    surahs: dict[int, dict[str, Any]] = {}
    editions: dict[int, dict[str, Any]] = {}
    ayah_count_by_surah: Counter[int] = Counter()
    ayah_edition_count_by_edition: Counter[int] = Counter()
    first_ayah_text_by_surah: dict[int, str] = {}
    last_number_in_surah_by_surah: dict[int, int] = {}
    number_in_surah_issues: list[dict[str, Any]] = []

    last_ayah_id = 0
    last_global_number = 0
    sequence_issues: list[dict[str, Any]] = []
    page_min: int | None = None
    page_max: int | None = None
    juz_min: int | None = None
    juz_max: int | None = None
    hizb_min: int | None = None
    hizb_max: int | None = None
    sajda_count = 0

    with sql_path.open("r", encoding="utf-8", errors="replace") as handle:
        for raw_line in handle:
            line = raw_line.rstrip("\n")

            if "generation_time" not in metadata and line.startswith("-- Generation Time:"):
                metadata["generation_time"] = line.split(":", 1)[1].strip()
            elif "server_version" not in metadata and line.startswith("-- Server version:"):
                metadata["server_version"] = line.split(":", 1)[1].strip()
            elif "php_version" not in metadata and line.startswith("-- PHP Version:"):
                metadata["php_version"] = line.split(":", 1)[1].strip()
            elif "database_name" not in metadata and line.startswith("-- Database:"):
                metadata["database_name"] = line.split("`", 2)[1]

            if current_create:
                if line.startswith(") ENGINE="):
                    current_create = None
                    continue

                column_match = COLUMN_RE.match(line)
                if column_match:
                    create_columns[current_create].append(column_match.group(1))
                continue

            create_match = CREATE_TABLE_RE.match(line)
            if create_match:
                current_create = create_match.group(1)
                create_columns[current_create] = []
                continue

            insert_match = INSERT_RE.match(line)
            if insert_match:
                current_table = insert_match.group(1)
                current_columns = [
                    column.strip().strip("`")
                    for column in insert_match.group(2).split(",")
                ]
                continue

            if current_table and line.startswith("("):
                row_counts[current_table] += 1
                row = dict(zip(current_columns or [], parse_sql_tuple(line)))

                if current_table == "surahs":
                    surahs[int(row["id"])] = row
                elif current_table == "editions":
                    editions[int(row["id"])] = row
                elif current_table == "ayahs":
                    surah_id = int(row["surah_id"])
                    ayah_count_by_surah[surah_id] += 1
                    first_ayah_text_by_surah.setdefault(surah_id, str(row["text"]))

                    expected_ayah_id = last_ayah_id + 1
                    if int(row["id"]) != expected_ayah_id:
                        sequence_issues.append(
                            {
                                "type": "ayah_id_gap",
                                "expected": expected_ayah_id,
                                "actual": int(row["id"]),
                            }
                        )

                    expected_global_number = last_global_number + 1
                    if int(row["number"]) != expected_global_number:
                        sequence_issues.append(
                            {
                                "type": "global_ayah_number_gap",
                                "expected": expected_global_number,
                                "actual": int(row["number"]),
                            }
                        )

                    if int(row["id"]) != int(row["number"]):
                        sequence_issues.append(
                            {
                                "type": "ayah_id_number_mismatch",
                                "ayah_id": int(row["id"]),
                                "global_number": int(row["number"]),
                            }
                        )

                    expected_number_in_surah = last_number_in_surah_by_surah.get(surah_id, 0) + 1
                    if int(row["number_in_surah"]) != expected_number_in_surah:
                        number_in_surah_issues.append(
                            {
                                "surah_id": surah_id,
                                "expected": expected_number_in_surah,
                                "actual": int(row["number_in_surah"]),
                            }
                        )

                    last_ayah_id = int(row["id"])
                    last_global_number = int(row["number"])
                    last_number_in_surah_by_surah[surah_id] = int(row["number_in_surah"])

                    page = int(row["page"])
                    juz_id = int(row["juz_id"])
                    hizb_id = int(row["hizb_id"])
                    page_min = page if page_min is None else min(page_min, page)
                    page_max = page if page_max is None else max(page_max, page)
                    juz_min = juz_id if juz_min is None else min(juz_min, juz_id)
                    juz_max = juz_id if juz_max is None else max(juz_max, juz_id)
                    hizb_min = hizb_id if hizb_min is None else min(hizb_min, hizb_id)
                    hizb_max = hizb_id if hizb_max is None else max(hizb_max, hizb_id)
                    if int(row["sajda"]) == 1:
                        sajda_count += 1
                elif current_table == "ayah_edition":
                    ayah_edition_count_by_edition[int(row["edition_id"])] += 1

                if line.endswith(";"):
                    current_table = None
                    current_columns = None
                continue

            if current_table and line.endswith(";"):
                current_table = None
                current_columns = None

    ayah_count = row_counts.get("ayahs", 0)
    basmala_prefixed_surahs: list[int] = []
    basmala_variant_surahs: list[dict[str, Any]] = []
    for surah_id, text in sorted(first_ayah_text_by_surah.items()):
        if surah_id in (1, 9):
            continue

        normalized = _normalized_text(text)
        if normalized.startswith("بِسْمِ"):
            basmala_prefixed_surahs.append(surah_id)
        elif "سْمِ ٱللَّهِ ٱلرَّحْمَٰنِ ٱلرَّحِيمِ" in normalized:
            basmala_variant_surahs.append(
                {
                    "surah_id": surah_id,
                    "text": normalized,
                }
            )

    edition_languages = Counter(
        str(edition.get("language", "unknown")) for edition in editions.values()
    )
    edition_formats = Counter(
        str(edition.get("format", "unknown")) for edition in editions.values()
    )
    edition_types = Counter(
        str(edition.get("type", "unknown")) for edition in editions.values()
    )

    complete_editions = []
    incomplete_editions = []
    for edition_id, edition in sorted(editions.items()):
        edition_summary = {
            "edition_id": edition_id,
            "identifier": edition.get("identifier"),
            "language": edition.get("language"),
            "format": edition.get("format"),
            "type": edition.get("type"),
            "ayah_rows": ayah_edition_count_by_edition.get(edition_id, 0),
        }
        if edition_summary["ayah_rows"] == ayah_count:
            complete_editions.append(edition_summary)
        else:
            incomplete_editions.append(edition_summary)

    notes: list[str] = []
    if "addons" not in create_columns:
        notes.append(
            "The SQL dump does not include the README's claimed addons table; the README schema names do not match the actual export."
        )
    if row_counts.get("juzs", 0) == 0 and ayah_count:
        notes.append(
            "Ayah rows carry juz_id values, but the juzs table is empty and cannot provide standalone range metadata."
        )
    if row_counts.get("hizbs", 0) == 0 and ayah_count:
        notes.append(
            "Ayah rows carry hizb_id values, but the hizbs table is empty and cannot provide standalone range metadata."
        )
    if hizb_max and hizb_max > 60:
        notes.append(
            "The hizb_id range reaches 240, which suggests quarter-hizb granularity rather than a populated 60-row hizb table."
        )
    if first_ayah_text_by_surah.get(1, "").startswith("\ufeff"):
        notes.append(
            "Surah 1 ayah 1 starts with a UTF-8 BOM character, so ingestion should preserve the raw source while handling the encoding marker explicitly."
        )
    if basmala_prefixed_surahs or basmala_variant_surahs:
        notes.append(
            "Most first-ayah texts for surahs other than 1 and 9 are basmala-prefixed in the source dump, and a small number use a basmala-like variant, so QuranKit should treat that segmentation and spelling behavior as upstream data, not a local transformation."
        )
    if incomplete_editions:
        notes.append("One or more editions are missing ayah_edition rows.")
    else:
        notes.append(
            "Every edition currently has one ayah_edition row per ayah, which is a strong baseline for translation-integrity validation."
        )

    tables = {
        table_name: {
            "columns": columns,
            "rows": row_counts.get(table_name, 0),
        }
        for table_name, columns in create_columns.items()
    }

    return {
        "source_dump": metadata,
        "tables": tables,
        "content_counts": {
            "surahs": row_counts.get("surahs", 0),
            "ayahs": ayah_count,
            "editions": row_counts.get("editions", 0),
            "ayah_edition": row_counts.get("ayah_edition", 0),
        },
        "ranges": {
            "page": [page_min, page_max],
            "juz_id": [juz_min, juz_max],
            "hizb_id": [hizb_min, hizb_max],
            "sajda_count": sajda_count,
        },
        "checks": {
            "surah_count_matches_ayah_coverage": row_counts.get("surahs", 0)
            == len(ayah_count_by_surah),
            "global_ayah_ids_sequential": not any(
                issue["type"] == "ayah_id_gap" for issue in sequence_issues
            ),
            "global_ayah_numbers_sequential": not any(
                issue["type"] in {"global_ayah_number_gap", "ayah_id_number_mismatch"}
                for issue in sequence_issues
            ),
            "number_in_surah_sequential": not number_in_surah_issues,
            "edition_coverage_complete": not incomplete_editions,
            "utf8_bom_on_first_ayah": first_ayah_text_by_surah.get(1, "").startswith(
                "\ufeff"
            ),
            "basmala_prefixed_first_ayahs_excluding_1_9": {
                "count": len(basmala_prefixed_surahs),
                "sample_surah_ids": basmala_prefixed_surahs[:12],
            },
            "variant_basmala_like_first_ayahs_excluding_1_9": {
                "count": len(basmala_variant_surahs),
                "sample": basmala_variant_surahs[:6],
            },
            "empty_juzs_table": row_counts.get("juzs", 0) == 0,
            "empty_hizbs_table": row_counts.get("hizbs", 0) == 0,
        },
        "editions": {
            "by_language": dict(sorted(edition_languages.items())),
            "by_format": dict(sorted(edition_formats.items())),
            "by_type": dict(sorted(edition_types.items())),
            "complete_edition_count": len(complete_editions),
            "incomplete_editions": incomplete_editions[:25],
            "sample": complete_editions[:12],
        },
        "surah_samples": {
            str(surah_id): _normalized_text(first_ayah_text_by_surah.get(surah_id))
            for surah_id in (1, 2, 3, 9, 27, 114)
            if surah_id in first_ayah_text_by_surah
        },
        "notes": notes,
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Summarize an upstream quran.sql MySQL dump for QuranKit."
    )
    parser.add_argument("sql_path", type=Path, help="Path to the extracted quran.sql file.")
    parser.add_argument(
        "--output",
        type=Path,
        help="Optional path to write the JSON summary.",
    )
    args = parser.parse_args()

    summary = summarize_sql_dump(args.sql_path)
    payload = json.dumps(summary, ensure_ascii=False, indent=2)

    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(f"{payload}\n", encoding="utf-8")
        return

    print(payload)


if __name__ == "__main__":
    main()
