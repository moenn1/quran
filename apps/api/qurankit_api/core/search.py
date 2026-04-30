from __future__ import annotations

from dataclasses import dataclass
from difflib import SequenceMatcher


DEFAULT_SEMANTIC_THRESHOLD = 0.12
MIN_SEMANTIC_SCORE = 0.08


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


def tokenize_search_text(value: str) -> set[str]:
    tokens: set[str] = set()
    current: list[str] = []

    for char in value.casefold():
        if char.isalnum() or char == "_":
            current.append(char)
            continue

        if current:
            tokens.add("".join(current))
            current = []

    if current:
        tokens.add("".join(current))

    return {token for token in tokens if token}


def related_terms(query_tokens: set[str], text_tokens: set[str]) -> tuple[str, ...]:
    terms: list[str] = []
    for query_token in sorted(query_tokens):
        for text_token in text_tokens:
            if query_token == text_token:
                terms.append(query_token)
                break

            if query_token in text_token or text_token in query_token:
                terms.append(query_token)
                break

            if len(query_token) >= 4 and len(text_token) >= 4:
                ratio = SequenceMatcher(None, query_token, text_token).ratio()
                if ratio >= 0.8:
                    terms.append(query_token)
                    break

    return tuple(terms[:3])


def semantic_similarity(query: str, *texts: str | None) -> tuple[float, str]:
    searchable_text = " ".join(part for part in texts if part).strip()
    if not searchable_text:
        return 0.0, ""

    query_tokens = tokenize_search_text(query)
    text_tokens = tokenize_search_text(searchable_text)
    matched_terms = related_terms(query_tokens, text_tokens)
    ratio = SequenceMatcher(None, query.casefold(), searchable_text.casefold()).ratio()

    token_coverage = len(matched_terms) / len(query_tokens) if query_tokens else 0.0
    union_count = len(query_tokens | text_tokens) or 1
    lexical_overlap = len(matched_terms) / union_count
    score = round((token_coverage * 0.7) + (lexical_overlap * 0.2) + (ratio * 0.1), 3)

    if score < MIN_SEMANTIC_SCORE:
        return 0.0, ""

    if matched_terms:
        reason = "Shared terms in the selected text: " + ", ".join(matched_terms) + "."
    else:
        reason = "Closest textual overlap in the selected text."

    return score, reason


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
