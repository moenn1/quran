from __future__ import annotations

import re
from collections.abc import Iterable, Iterator
from io import TextIOWrapper
from pathlib import Path
from typing import Any
from zipfile import ZipFile


INSERT_RE = re.compile(r"^INSERT INTO `([^`]+)` \(([^)]+)\) VALUES$")
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
                values.append(_coerce_sql_value(raw))
            token = []
            continue

        token.append(ch)

    raw = "".join(token).strip()
    if raw:
        values.append(_coerce_sql_value(raw))

    return values


def _coerce_sql_value(raw: str) -> Any:
    if raw == "NULL":
        return None
    if INT_RE.match(raw):
        return int(raw)
    return raw


def iter_sql_table_rows(
    lines: Iterable[str],
    *,
    tables: set[str] | None = None,
) -> Iterator[tuple[str, dict[str, Any]]]:
    current_table: str | None = None
    current_columns: list[str] | None = None

    for raw_line in lines:
        line = raw_line.rstrip("\n")

        insert_match = INSERT_RE.match(line)
        if insert_match:
            table_name = insert_match.group(1)
            if tables is not None and table_name not in tables:
                current_table = "__skip__"
                current_columns = None
                continue

            current_table = table_name
            current_columns = [
                column.strip().strip("`")
                for column in insert_match.group(2).split(",")
            ]
            continue

        if current_table == "__skip__":
            if line.endswith(";"):
                current_table = None
            continue

        if current_table and line.startswith("("):
            row = dict(zip(current_columns or [], parse_sql_tuple(line)))
            yield current_table, row
            if line.endswith(";"):
                current_table = None
                current_columns = None
            continue

        if current_table and line.endswith(";"):
            current_table = None
            current_columns = None


def iter_zip_sql_table_rows(
    archive_path: Path,
    *,
    sql_entry_name: str,
    tables: set[str] | None = None,
) -> Iterator[tuple[str, dict[str, Any]]]:
    with ZipFile(archive_path) as archive:
        with archive.open(sql_entry_name) as handle:
            with TextIOWrapper(handle, encoding="utf-8", errors="replace") as text_handle:
                yield from iter_sql_table_rows(text_handle, tables=tables)


def read_dump_metadata(archive_path: Path, *, sql_entry_name: str) -> dict[str, str]:
    metadata: dict[str, str] = {}
    tool_name: str | None = None
    tool_version: str | None = None

    with ZipFile(archive_path) as archive:
        with archive.open(sql_entry_name) as handle:
            with TextIOWrapper(handle, encoding="utf-8", errors="replace") as text_handle:
                for raw_line in text_handle:
                    line = raw_line.rstrip("\n")
                    if line.startswith("CREATE TABLE "):
                        break
                    if line.startswith("-- phpMyAdmin SQL Dump"):
                        tool_name = "phpMyAdmin"
                    elif line.startswith("-- version "):
                        tool_version = line.split("-- version ", 1)[1].strip()
                    elif line.startswith("-- Generation Time:"):
                        metadata["generation_time"] = line.split(":", 1)[1].strip()
                    elif line.startswith("-- Server version:"):
                        metadata["server_version"] = line.split(":", 1)[1].strip()
                    elif line.startswith("-- PHP Version:"):
                        metadata["php_version"] = line.split(":", 1)[1].strip()
                    elif line.startswith("-- Database:"):
                        metadata["database_name"] = line.split("`", 2)[1]

    if tool_name and tool_version:
        metadata["dump_export_tool"] = f"{tool_name} {tool_version}"
    elif tool_name:
        metadata["dump_export_tool"] = tool_name

    return metadata
