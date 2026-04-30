from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class HighlightSpan:
    excerpt: str
    match_start: int
    match_end: int


def clean_search_query(value: str) -> str:
    normalized = " ".join(value.split())
    if not normalized:
        raise ValueError("Query cannot be empty.")
    return normalized


def normalize_search_text(value: str | None) -> str:
    if not value:
        return ""
    return value.lstrip("\ufeff").strip().lower()


def build_highlight(text: str, query: str, *, window: int = 36) -> HighlightSpan | None:
    needle = normalize_search_text(query)
    if not needle:
        return None

    haystack = text.lower()
    match_start = haystack.find(needle)
    if match_start < 0:
        return None

    match_end = match_start + len(needle)
    excerpt_start = max(0, match_start - window)
    excerpt_end = min(len(text), match_end + window)
    excerpt = text[excerpt_start:excerpt_end]
    if excerpt_start > 0:
        excerpt = f"...{excerpt}"
    if excerpt_end < len(text):
        excerpt = f"{excerpt}..."

    return HighlightSpan(
        excerpt=excerpt,
        match_start=match_start,
        match_end=match_end,
    )
