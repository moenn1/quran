from __future__ import annotations

import json
import sqlite3
from collections.abc import Callable, Mapping, Sequence
from contextlib import closing
from dataclasses import dataclass, field
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any, Protocol
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from .config import BackendMode, Settings

ARABIC_SOURCE_REPOSITORY = "AbdullahGhanem/quran-database"
ARABIC_SOURCE_SNAPSHOT = "f6c4c805f22b0432677d79aafc12139b915e1a0d"
ARABIC_SOURCE_NOTE = (
    "Arabic Quran text is shown exactly as stored in the configured QuranKit backend."
)
SEMANTIC_DISCLAIMER = (
    "Related passages are ranked by textual similarity only. They are not tafsir, "
    "fatwa, or religious rulings."
)

SQLiteRow = sqlite3.Row
UrlOpenFn = Callable[..., Any]


class QuranKitBackendError(RuntimeError):
    """Base error for backend and transport failures."""


class BackendConfigurationError(QuranKitBackendError):
    """Raised when the configured backend cannot be used as configured."""


class BackendNotFoundError(QuranKitBackendError):
    """Raised when a requested Quran reference or translation does not exist."""


class BackendRequestError(QuranKitBackendError):
    """Raised when a remote backend request fails."""


class BackendValidationError(QuranKitBackendError):
    """Raised when a query or argument is invalid for backend execution."""


@dataclass(frozen=True)
class ArabicSourceAttribution:
    repository: str = ARABIC_SOURCE_REPOSITORY
    snapshot: str = ARABIC_SOURCE_SNAPSHOT
    note: str = ARABIC_SOURCE_NOTE

    def to_dict(self) -> dict[str, str]:
        return {
            "repository": self.repository,
            "snapshot": self.snapshot,
            "note": self.note,
        }

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any] | None) -> ArabicSourceAttribution:
        if payload is None:
            return cls()

        return cls(
            repository=str(
                payload.get(
                    "repository",
                    payload.get("source_name", ARABIC_SOURCE_REPOSITORY),
                )
            ),
            snapshot=str(
                payload.get(
                    "snapshot",
                    payload.get("upstream_commit_sha", ARABIC_SOURCE_SNAPSHOT),
                )
            ),
            note=str(payload.get("note", ARABIC_SOURCE_NOTE)),
        )


@dataclass(frozen=True)
class TranslationAttribution:
    identifier: str
    language: str | None = None
    name: str | None = None
    english_name: str | None = None
    edition_type: str | None = None
    format: str | None = None

    @property
    def display_name(self) -> str:
        return self.english_name or self.name or self.identifier

    @property
    def label(self) -> str:
        if self.edition_type and self.edition_type != "translation":
            return "edition"

        return "translation"

    def to_dict(self) -> dict[str, str | None]:
        return {
            "identifier": self.identifier,
            "language": self.language,
            "name": self.name,
            "english_name": self.english_name,
            "edition_type": self.edition_type,
            "format": self.format,
        }

    @classmethod
    def from_dict(
        cls, payload: Mapping[str, Any] | None
    ) -> TranslationAttribution | None:
        if payload is None:
            return None

        identifier = payload.get("identifier", payload.get("upstream_identifier"))
        if identifier is None:
            return None

        return cls(
            identifier=str(identifier),
            language=_optional_string(
                payload.get("language", payload.get("language_code"))
            ),
            name=_optional_string(
                payload.get("name", payload.get("translation_name"))
            ),
            english_name=_optional_string(
                payload.get("english_name", payload.get("englishName"))
            ),
            edition_type=_optional_string(
                payload.get("edition_type", payload.get("type"))
            ),
            format=_optional_string(payload.get("format")),
        )


@dataclass(frozen=True)
class AyahReference:
    surah_number: int
    ayah_number: int

    @property
    def text(self) -> str:
        return f"{self.surah_number}:{self.ayah_number}"


@dataclass(frozen=True)
class AyahRecord:
    surah_number: int
    ayah_number: int
    surah_name_arabic: str
    surah_name_english: str
    surah_name_translation: str | None
    revelation_type: str | None
    arabic_text: str
    translation_text: str | None
    page_number: int | None
    juz_number: int | None
    hizb_number: int | None
    sajda: bool = False

    @property
    def reference(self) -> str:
        return f"{self.surah_number}:{self.ayah_number}"

    def to_dict(self) -> dict[str, Any]:
        return {
            "reference": self.reference,
            "surah_number": self.surah_number,
            "ayah_number": self.ayah_number,
            "surah_name_arabic": self.surah_name_arabic,
            "surah_name_english": self.surah_name_english,
            "surah_name_translation": self.surah_name_translation,
            "revelation_type": self.revelation_type,
            "arabic_text": self.arabic_text,
            "translation_text": self.translation_text,
            "page_number": self.page_number,
            "juz_number": self.juz_number,
            "hizb_number": self.hizb_number,
            "sajda": self.sajda,
        }

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> AyahRecord:
        surah_payload = _mapping_value(payload, "surah") or {}

        return cls(
            surah_number=int(
                payload.get("surah_number", surah_payload.get("surah_number"))
            ),
            ayah_number=int(payload["ayah_number"]),
            surah_name_arabic=str(
                payload.get(
                    "surah_name_arabic",
                    payload.get(
                        "surah_name_ar",
                        surah_payload.get("arabic_name", ""),
                    ),
                )
            ),
            surah_name_english=str(
                payload.get(
                    "surah_name_english",
                    payload.get(
                        "surah_name_en",
                        surah_payload.get("english_name", ""),
                    ),
                )
            ),
            surah_name_translation=_optional_string(
                payload.get(
                    "surah_name_translation",
                    payload.get(
                        "surah_name_en_translation",
                        surah_payload.get("english_name_translation"),
                    ),
                )
            ),
            revelation_type=_optional_string(
                payload.get(
                    "revelation_type",
                    payload.get("type", surah_payload.get("revelation_type")),
                )
            ),
            arabic_text=str(payload.get("arabic_text", payload.get("text", ""))),
            translation_text=_optional_string(
                payload.get("translation_text", payload.get("translation"))
            ),
            page_number=_optional_int(payload.get("page_number", payload.get("page"))),
            juz_number=_optional_int(payload.get("juz_number", payload.get("juz"))),
            hizb_number=_optional_int(
                payload.get("hizb_number", payload.get("hizb"))
            ),
            sajda=bool(payload.get("sajda", False)),
        )


@dataclass(frozen=True)
class AyahSelection:
    ayah: AyahRecord
    arabic_source: ArabicSourceAttribution = field(
        default_factory=ArabicSourceAttribution
    )
    translation_attribution: TranslationAttribution | None = None
    selection_kind: str = "ayah"

    def to_dict(self) -> dict[str, Any]:
        return {
            "selection_kind": self.selection_kind,
            "ayah": self.ayah.to_dict(),
            "arabic_source": self.arabic_source.to_dict(),
            "translation_attribution": (
                self.translation_attribution.to_dict()
                if self.translation_attribution is not None
                else None
            ),
        }

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> AyahSelection:
        ayah_payload = _unwrap_mapping(payload, "ayah")
        return cls(
            ayah=AyahRecord.from_dict(ayah_payload),
            arabic_source=ArabicSourceAttribution.from_dict(
                _mapping_value(payload, "arabic_source")
                or _mapping_value(payload, "source")
                or _mapping_value(ayah_payload, "source")
            ),
            translation_attribution=TranslationAttribution.from_dict(
                _mapping_value(payload, "translation_attribution")
                or _mapping_value(ayah_payload, "translation_attribution")
            ),
            selection_kind=str(payload.get("selection_kind", "ayah")),
        )


@dataclass(frozen=True)
class AyahRangeResult:
    start_reference: str
    end_reference: str
    ayahs: tuple[AyahRecord, ...]
    arabic_source: ArabicSourceAttribution = field(
        default_factory=ArabicSourceAttribution
    )
    translation_attribution: TranslationAttribution | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "start_reference": self.start_reference,
            "end_reference": self.end_reference,
            "ayah_count": len(self.ayahs),
            "ayahs": [ayah.to_dict() for ayah in self.ayahs],
            "arabic_source": self.arabic_source.to_dict(),
            "translation_attribution": (
                self.translation_attribution.to_dict()
                if self.translation_attribution is not None
                else None
            ),
        }

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> AyahRangeResult:
        range_payload = _unwrap_mapping(payload, "range")
        return cls(
            start_reference=str(range_payload["start_reference"]),
            end_reference=str(range_payload["end_reference"]),
            ayahs=tuple(
                AyahRecord.from_dict(item)
                for item in range_payload.get("ayahs", [])
                if isinstance(item, Mapping)
            ),
            arabic_source=ArabicSourceAttribution.from_dict(
                _mapping_value(range_payload, "arabic_source")
                or _mapping_value(payload, "arabic_source")
            ),
            translation_attribution=TranslationAttribution.from_dict(
                _mapping_value(range_payload, "translation_attribution")
                or _mapping_value(payload, "translation_attribution")
            ),
        )


@dataclass(frozen=True)
class SurahResult:
    surah_number: int
    name_arabic: str
    name_english: str
    name_translation: str | None
    revelation_type: str | None
    ayahs: tuple[AyahRecord, ...]
    arabic_source: ArabicSourceAttribution = field(
        default_factory=ArabicSourceAttribution
    )
    translation_attribution: TranslationAttribution | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "surah_number": self.surah_number,
            "name_arabic": self.name_arabic,
            "name_english": self.name_english,
            "name_translation": self.name_translation,
            "revelation_type": self.revelation_type,
            "ayah_count": len(self.ayahs),
            "ayahs": [ayah.to_dict() for ayah in self.ayahs],
            "arabic_source": self.arabic_source.to_dict(),
            "translation_attribution": (
                self.translation_attribution.to_dict()
                if self.translation_attribution is not None
                else None
            ),
        }

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> SurahResult:
        surah_payload = _unwrap_mapping(payload, "surah")
        item_payloads = (
            surah_payload.get("ayahs")
            if isinstance(surah_payload.get("ayahs"), list)
            else payload.get("items", [])
        )
        translation_payload = _mapping_value(payload, "translation_attribution")
        if translation_payload is None:
            for item in item_payloads:
                if isinstance(item, Mapping):
                    translation_payload = _mapping_value(item, "translation_attribution")
                    if translation_payload is not None:
                        break

        arabic_source_payload = (
            _mapping_value(payload, "arabic_source")
            or _mapping_value(surah_payload, "source")
        )
        if arabic_source_payload is None:
            for item in item_payloads:
                if isinstance(item, Mapping):
                    arabic_source_payload = _mapping_value(item, "source")
                    if arabic_source_payload is not None:
                        break

        return cls(
            surah_number=int(surah_payload["surah_number"]),
            name_arabic=str(
                surah_payload.get(
                    "name_arabic",
                    surah_payload.get("name_ar", surah_payload.get("arabic_name", "")),
                )
            ),
            name_english=str(
                surah_payload.get(
                    "name_english",
                    surah_payload.get("name_en", surah_payload.get("english_name", "")),
                )
            ),
            name_translation=_optional_string(
                surah_payload.get(
                    "name_translation",
                    surah_payload.get(
                        "name_en_translation",
                        surah_payload.get("english_name_translation"),
                    ),
                )
            ),
            revelation_type=_optional_string(
                surah_payload.get("revelation_type", surah_payload.get("type"))
            ),
            ayahs=tuple(
                AyahRecord.from_dict(item)
                for item in item_payloads
                if isinstance(item, Mapping)
            ),
            arabic_source=ArabicSourceAttribution.from_dict(
                arabic_source_payload
            ),
            translation_attribution=TranslationAttribution.from_dict(
                translation_payload
            ),
        )


@dataclass(frozen=True)
class JuzResult:
    juz_number: int
    start_reference: str
    end_reference: str
    ayahs: tuple[AyahRecord, ...]
    arabic_source: ArabicSourceAttribution = field(
        default_factory=ArabicSourceAttribution
    )
    translation_attribution: TranslationAttribution | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "juz_number": self.juz_number,
            "start_reference": self.start_reference,
            "end_reference": self.end_reference,
            "ayah_count": len(self.ayahs),
            "ayahs": [ayah.to_dict() for ayah in self.ayahs],
            "arabic_source": self.arabic_source.to_dict(),
            "translation_attribution": (
                self.translation_attribution.to_dict()
                if self.translation_attribution is not None
                else None
            ),
        }

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> JuzResult:
        juz_payload = _unwrap_mapping(payload, "juz")
        item_payloads = (
            juz_payload.get("ayahs")
            if isinstance(juz_payload.get("ayahs"), list)
            else payload.get("items", [])
        )
        ayahs = tuple(
            AyahRecord.from_dict(item)
            for item in item_payloads
            if isinstance(item, Mapping)
        )
        translation_payload = _mapping_value(payload, "translation_attribution")
        if translation_payload is None:
            for item in item_payloads:
                if isinstance(item, Mapping):
                    translation_payload = _mapping_value(item, "translation_attribution")
                    if translation_payload is not None:
                        break

        arabic_source_payload = _mapping_value(payload, "arabic_source")
        if arabic_source_payload is None:
            for item in item_payloads:
                if isinstance(item, Mapping):
                    arabic_source_payload = _mapping_value(item, "source")
                    if arabic_source_payload is not None:
                        break

        return cls(
            juz_number=int(juz_payload["juz_number"]),
            start_reference=str(
                juz_payload.get(
                    "start_reference",
                    ayahs[0].reference if ayahs else "",
                )
            ),
            end_reference=str(
                juz_payload.get(
                    "end_reference",
                    ayahs[-1].reference if ayahs else "",
                )
            ),
            ayahs=ayahs,
            arabic_source=ArabicSourceAttribution.from_dict(
                arabic_source_payload
            ),
            translation_attribution=TranslationAttribution.from_dict(
                translation_payload
            ),
        )


@dataclass(frozen=True)
class ExactSearchHit:
    ayah: AyahRecord
    match_sources: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "ayah": self.ayah.to_dict(),
            "match_sources": list(self.match_sources),
        }

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> ExactSearchHit:
        return cls(
            ayah=AyahRecord.from_dict(_unwrap_mapping(payload, "ayah")),
            match_sources=tuple(str(item) for item in payload.get("match_sources", [])),
        )


@dataclass(frozen=True)
class ExactSearchResult:
    query: str
    results: tuple[ExactSearchHit, ...]
    searched_fields: tuple[str, ...]
    arabic_source: ArabicSourceAttribution = field(
        default_factory=ArabicSourceAttribution
    )
    translation_attribution: TranslationAttribution | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "query": self.query,
            "match_type": "exact",
            "count": len(self.results),
            "searched_fields": list(self.searched_fields),
            "results": [result.to_dict() for result in self.results],
            "arabic_source": self.arabic_source.to_dict(),
            "translation_attribution": (
                self.translation_attribution.to_dict()
                if self.translation_attribution is not None
                else None
            ),
        }

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> ExactSearchResult:
        search_payload = _unwrap_mapping(payload, "search")
        return cls(
            query=str(search_payload.get("query", "")),
            results=tuple(
                ExactSearchHit.from_dict(item)
                for item in search_payload.get("results", [])
                if isinstance(item, Mapping)
            ),
            searched_fields=tuple(
                str(item) for item in search_payload.get("searched_fields", [])
            ),
            arabic_source=ArabicSourceAttribution.from_dict(
                _mapping_value(search_payload, "arabic_source")
                or _mapping_value(payload, "arabic_source")
            ),
            translation_attribution=TranslationAttribution.from_dict(
                _mapping_value(search_payload, "translation_attribution")
                or _mapping_value(payload, "translation_attribution")
            ),
        )


@dataclass(frozen=True)
class SemanticSearchHit:
    ayah: AyahRecord
    similarity_score: float
    reason: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "ayah": self.ayah.to_dict(),
            "similarity_score": self.similarity_score,
            "reason": self.reason,
        }

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> SemanticSearchHit:
        return cls(
            ayah=AyahRecord.from_dict(_unwrap_mapping(payload, "ayah")),
            similarity_score=float(payload.get("similarity_score", 0.0)),
            reason=str(payload.get("reason", "")),
        )


@dataclass(frozen=True)
class SemanticSearchResult:
    query: str
    results: tuple[SemanticSearchHit, ...]
    arabic_source: ArabicSourceAttribution = field(
        default_factory=ArabicSourceAttribution
    )
    translation_attribution: TranslationAttribution | None = None
    disclaimer: str = SEMANTIC_DISCLAIMER

    def to_dict(self) -> dict[str, Any]:
        return {
            "query": self.query,
            "match_type": "semantic_similarity",
            "count": len(self.results),
            "disclaimer": self.disclaimer,
            "results": [result.to_dict() for result in self.results],
            "arabic_source": self.arabic_source.to_dict(),
            "translation_attribution": (
                self.translation_attribution.to_dict()
                if self.translation_attribution is not None
                else None
            ),
        }

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> SemanticSearchResult:
        search_payload = _unwrap_mapping(payload, "semantic")
        return cls(
            query=str(search_payload.get("query", "")),
            results=tuple(
                SemanticSearchHit.from_dict(item)
                for item in search_payload.get("results", [])
                if isinstance(item, Mapping)
            ),
            arabic_source=ArabicSourceAttribution.from_dict(
                _mapping_value(search_payload, "arabic_source")
                or _mapping_value(payload, "arabic_source")
            ),
            translation_attribution=TranslationAttribution.from_dict(
                _mapping_value(search_payload, "translation_attribution")
                or _mapping_value(payload, "translation_attribution")
            ),
            disclaimer=str(search_payload.get("disclaimer", SEMANTIC_DISCLAIMER)),
        )


class QuranBackend(Protocol):
    kind: str
    summary: str

    def get_range(
        self,
        start_reference: AyahReference,
        end_reference: AyahReference,
        translation_identifier: str | None,
    ) -> AyahRangeResult: ...

    def get_surah(
        self, surah_number: int, translation_identifier: str | None
    ) -> SurahResult: ...

    def get_ayah(
        self, reference: AyahReference, translation_identifier: str | None
    ) -> AyahSelection: ...

    def get_juz(
        self, juz_number: int, translation_identifier: str | None
    ) -> JuzResult: ...

    def get_random_ayah(self, translation_identifier: str | None) -> AyahSelection: ...

    def search(
        self, query: str, translation_identifier: str | None, limit: int
    ) -> ExactSearchResult: ...

    def semantic_search(
        self, query: str, translation_identifier: str | None, limit: int
    ) -> SemanticSearchResult: ...


@dataclass(frozen=True)
class RemoteBackend:
    api_url: str
    timeout_seconds: float = 10.0
    opener: UrlOpenFn | None = None

    @property
    def kind(self) -> str:
        return "remote"

    @property
    def summary(self) -> str:
        return f"Remote API at {self.api_url}"

    def get_surah(
        self, surah_number: int, translation_identifier: str | None
    ) -> SurahResult:
        payload = self._request_json(
            f"/api/v1/surahs/{surah_number}/ayahs",
            {"translation": translation_identifier},
        )
        return SurahResult.from_dict(payload)

    def get_range(
        self,
        start_reference: AyahReference,
        end_reference: AyahReference,
        translation_identifier: str | None,
    ) -> AyahRangeResult:
        if _reference_key(end_reference) < _reference_key(start_reference):
            raise BackendValidationError(
                "Ayah ranges must end at or after their start reference."
            )

        ayahs: list[AyahRecord] = []
        translation_attribution: TranslationAttribution | None = None

        for surah_number in range(
            start_reference.surah_number,
            end_reference.surah_number + 1,
        ):
            surah = self.get_surah(surah_number, translation_identifier)
            if translation_attribution is None:
                translation_attribution = surah.translation_attribution

            start_ayah = 1
            end_ayah: int | None = None
            if surah_number == start_reference.surah_number:
                start_ayah = start_reference.ayah_number
            if surah_number == end_reference.surah_number:
                end_ayah = end_reference.ayah_number

            selected = [
                ayah
                for ayah in surah.ayahs
                if ayah.ayah_number >= start_ayah
                and (end_ayah is None or ayah.ayah_number <= end_ayah)
            ]
            ayahs.extend(selected)

        if not ayahs:
            raise BackendNotFoundError(
                f"Ayah range {start_reference.text}-{end_reference.text} was not "
                "found in the remote QuranKit API."
            )

        if ayahs[0].reference != start_reference.text or ayahs[-1].reference != end_reference.text:
            raise BackendNotFoundError(
                f"Ayah range {start_reference.text}-{end_reference.text} could not "
                "be resolved exactly from the remote QuranKit API."
            )

        return AyahRangeResult(
            start_reference=ayahs[0].reference,
            end_reference=ayahs[-1].reference,
            ayahs=tuple(ayahs),
            translation_attribution=translation_attribution,
        )

    def get_ayah(
        self, reference: AyahReference, translation_identifier: str | None
    ) -> AyahSelection:
        payload = self._request_json(
            f"/api/v1/ayahs/{reference.text}",
            {"translation": translation_identifier},
        )
        return AyahSelection.from_dict(payload)

    def get_juz(
        self, juz_number: int, translation_identifier: str | None
    ) -> JuzResult:
        payload = self._request_json(
            f"/api/v1/juz/{juz_number}",
            {"translation": translation_identifier},
        )
        return JuzResult.from_dict(payload)

    def get_random_ayah(self, translation_identifier: str | None) -> AyahSelection:
        payload = self._request_json(
            "/api/v1/ayahs/random",
            {"translation": translation_identifier},
        )
        result = AyahSelection.from_dict(payload)
        return AyahSelection(
            ayah=result.ayah,
            arabic_source=result.arabic_source,
            translation_attribution=result.translation_attribution,
            selection_kind="random",
        )

    def search(
        self, query: str, translation_identifier: str | None, limit: int
    ) -> ExactSearchResult:
        payload = self._request_json(
            "/api/v1/search/exact",
            {"q": query, "translation": translation_identifier, "limit": limit},
        )
        return ExactSearchResult.from_dict(payload)

    def semantic_search(
        self, query: str, translation_identifier: str | None, limit: int
    ) -> SemanticSearchResult:
        payload = self._request_json(
            "/api/v1/search/semantic",
            {"q": query, "translation": translation_identifier, "limit": limit},
        )
        return SemanticSearchResult.from_dict(payload)

    def _request_json(
        self, path: str, params: Mapping[str, Any] | None = None
    ) -> Mapping[str, Any]:
        query_string = ""
        if params:
            query_string = urlencode(
                {key: value for key, value in params.items() if value is not None}
            )

        url = f"{self.api_url.rstrip('/')}{path}"
        if query_string:
            url = f"{url}?{query_string}"

        request = Request(
            url,
            headers={
                "Accept": "application/json",
                "User-Agent": "qurankit-cli/0.1.0",
            },
        )
        opener = self.opener or urlopen

        try:
            with opener(request, timeout=self.timeout_seconds) as response:
                body = response.read().decode("utf-8")
        except HTTPError as exc:
            if exc.code == 404:
                raise BackendNotFoundError(
                    f"Remote API resource not found at {url}."
                ) from exc

            detail = exc.read().decode("utf-8", errors="replace").strip()
            message = f"Remote API request failed with HTTP {exc.code} at {url}."
            if detail:
                message = f"{message} {detail}"
            raise BackendRequestError(message) from exc
        except URLError as exc:
            raise BackendRequestError(
                f"Could not reach the QuranKit API at {self.api_url}: {exc.reason}"
            ) from exc

        try:
            payload = json.loads(body)
        except json.JSONDecodeError as exc:
            raise BackendRequestError(
                f"Remote API at {self.api_url} returned invalid JSON."
            ) from exc

        if not isinstance(payload, Mapping):
            raise BackendRequestError(
                f"Remote API at {self.api_url} returned an unexpected payload."
            )

        return payload


@dataclass(frozen=True)
class LocalSQLiteBackend:
    db_path: Path

    @property
    def kind(self) -> str:
        return "local"

    @property
    def summary(self) -> str:
        if self.db_path.exists():
            return f"Local SQLite database at {self.db_path}"

        return f"Local SQLite database at {self.db_path} (file not found yet)"

    def get_surah(
        self, surah_number: int, translation_identifier: str | None
    ) -> SurahResult:
        with closing(self._connect(include_translation=translation_identifier is not None)) as conn:
            translation_id, translation_attribution = self._translation_context(
                conn, translation_identifier
            )
            ayahs = tuple(
                self._fetch_ayahs(
                    conn,
                    "s.number = ?",
                    (surah_number,),
                    translation_id,
                )
            )
            if not ayahs:
                raise BackendNotFoundError(f"Surah {surah_number} was not found.")

            first = ayahs[0]
            return SurahResult(
                surah_number=surah_number,
                name_arabic=first.surah_name_arabic,
                name_english=first.surah_name_english,
                name_translation=first.surah_name_translation,
                revelation_type=first.revelation_type,
                ayahs=ayahs,
                translation_attribution=translation_attribution,
            )

    def get_range(
        self,
        start_reference: AyahReference,
        end_reference: AyahReference,
        translation_identifier: str | None,
    ) -> AyahRangeResult:
        if _reference_key(end_reference) < _reference_key(start_reference):
            raise BackendValidationError(
                "Ayah ranges must end at or after their start reference."
            )

        where_clause = """
            (
                s.number > ?
                OR (s.number = ? AND a.number_in_surah >= ?)
            )
            AND (
                s.number < ?
                OR (s.number = ? AND a.number_in_surah <= ?)
            )
        """

        with closing(self._connect(include_translation=translation_identifier is not None)) as conn:
            translation_id, translation_attribution = self._translation_context(
                conn, translation_identifier
            )
            ayahs = tuple(
                self._fetch_ayahs(
                    conn,
                    where_clause,
                    (
                        start_reference.surah_number,
                        start_reference.surah_number,
                        start_reference.ayah_number,
                        end_reference.surah_number,
                        end_reference.surah_number,
                        end_reference.ayah_number,
                    ),
                    translation_id,
                )
            )

        if not ayahs:
            raise BackendNotFoundError(
                f"Ayah range {start_reference.text}-{end_reference.text} was not "
                f"found in the local SQLite database at {self.db_path}."
            )

        if ayahs[0].reference != start_reference.text or ayahs[-1].reference != end_reference.text:
            raise BackendNotFoundError(
                f"Ayah range {start_reference.text}-{end_reference.text} could not "
                f"be resolved exactly from the local SQLite database at {self.db_path}."
            )

        return AyahRangeResult(
            start_reference=ayahs[0].reference,
            end_reference=ayahs[-1].reference,
            ayahs=ayahs,
            translation_attribution=translation_attribution,
        )

    def get_ayah(
        self, reference: AyahReference, translation_identifier: str | None
    ) -> AyahSelection:
        with closing(self._connect(include_translation=translation_identifier is not None)) as conn:
            translation_id, translation_attribution = self._translation_context(
                conn, translation_identifier
            )
            ayahs = self._fetch_ayahs(
                conn,
                "s.number = ? AND a.number_in_surah = ?",
                (reference.surah_number, reference.ayah_number),
                translation_id,
            )
            if not ayahs:
                raise BackendNotFoundError(
                    f"Ayah {reference.text} was not found in the local SQLite database."
                )

            return AyahSelection(
                ayah=ayahs[0],
                translation_attribution=translation_attribution,
            )

    def get_juz(
        self, juz_number: int, translation_identifier: str | None
    ) -> JuzResult:
        with closing(self._connect(include_translation=translation_identifier is not None)) as conn:
            translation_id, translation_attribution = self._translation_context(
                conn, translation_identifier
            )
            ayahs = tuple(
                self._fetch_ayahs(
                    conn,
                    "a.juz_id = ?",
                    (juz_number,),
                    translation_id,
                )
            )
            if not ayahs:
                raise BackendNotFoundError(
                    f"Juz {juz_number} was not found in the local SQLite database."
                )

            return JuzResult(
                juz_number=juz_number,
                start_reference=ayahs[0].reference,
                end_reference=ayahs[-1].reference,
                ayahs=ayahs,
                translation_attribution=translation_attribution,
            )

    def get_random_ayah(self, translation_identifier: str | None) -> AyahSelection:
        with closing(self._connect(include_translation=translation_identifier is not None)) as conn:
            translation_id, translation_attribution = self._translation_context(
                conn, translation_identifier
            )
            rows = self._query_ayah_rows(
                conn,
                "",
                (),
                translation_id,
                order_by="RANDOM()",
                limit=1,
            )
            if not rows:
                raise BackendNotFoundError(
                    "No ayahs were found in the local SQLite database."
                )

            return AyahSelection(
                ayah=self._row_to_ayah(rows[0]),
                translation_attribution=translation_attribution,
                selection_kind="random",
            )

    def search(
        self, query: str, translation_identifier: str | None, limit: int
    ) -> ExactSearchResult:
        normalized_query = _normalize_query(query)

        with closing(self._connect(include_translation=translation_identifier is not None)) as conn:
            translation_id, translation_attribution = self._translation_context(
                conn, translation_identifier
            )
            rows = self._query_search_rows(conn, normalized_query, translation_id, limit)
            results = tuple(
                ExactSearchHit(
                    ayah=self._row_to_ayah(row),
                    match_sources=self._match_sources(
                        normalized_query,
                        row["arabic_text"],
                        row["translation_text"],
                    ),
                )
                for row in rows
            )

        searched_fields = ("arabic_text",)
        if translation_identifier is not None:
            searched_fields = ("arabic_text", "translation")

        return ExactSearchResult(
            query=normalized_query,
            results=results,
            searched_fields=searched_fields,
            translation_attribution=translation_attribution,
        )

    def semantic_search(
        self, query: str, translation_identifier: str | None, limit: int
    ) -> SemanticSearchResult:
        normalized_query = _normalize_query(query)

        with closing(self._connect(include_translation=translation_identifier is not None)) as conn:
            translation_id, translation_attribution = self._translation_context(
                conn, translation_identifier
            )
            rows = self._query_ayah_rows(
                conn,
                "",
                (),
                translation_id,
                order_by="s.number, a.number_in_surah",
                limit=None,
            )

        scored_hits: list[SemanticSearchHit] = []
        for row in rows:
            ayah = self._row_to_ayah(row)
            score, reason = _semantic_similarity(
                normalized_query,
                ayah.arabic_text,
                ayah.translation_text,
            )
            if score <= 0:
                continue

            scored_hits.append(
                SemanticSearchHit(
                    ayah=ayah,
                    similarity_score=score,
                    reason=reason,
                )
            )

        scored_hits.sort(
            key=lambda item: (
                -item.similarity_score,
                item.ayah.surah_number,
                item.ayah.ayah_number,
            )
        )

        return SemanticSearchResult(
            query=normalized_query,
            results=tuple(scored_hits[:limit]),
            translation_attribution=translation_attribution,
        )

    def _connect(self, *, include_translation: bool) -> sqlite3.Connection:
        if not self.db_path.exists() or not self.db_path.is_file():
            raise BackendConfigurationError(
                f"Local SQLite database not found at {self.db_path}. "
                "Set a valid path with `qurankit config set db-path ...` or switch "
                "to remote mode with `qurankit config set mode remote`."
            )

        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        self._ensure_required_tables(conn, include_translation=include_translation)
        return conn

    def _ensure_required_tables(
        self, conn: sqlite3.Connection, *, include_translation: bool
    ) -> None:
        rows = conn.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table'"
        ).fetchall()
        tables = {str(row[0]) for row in rows}
        required = {"surahs", "ayahs"}
        if include_translation:
            required |= {"editions", "ayah_edition"}

        missing = sorted(required - tables)
        if missing:
            missing_names = ", ".join(missing)
            raise BackendConfigurationError(
                f"Local SQLite database at {self.db_path} is missing required "
                f"tables: {missing_names}."
            )

    def _translation_context(
        self, conn: sqlite3.Connection, identifier: str | None
    ) -> tuple[int | None, TranslationAttribution | None]:
        if identifier is None:
            return None, None

        row = conn.execute(
            """
            SELECT id, identifier, language, name, englishName, type, format
            FROM editions
            WHERE identifier = ?
            LIMIT 1
            """,
            (identifier,),
        ).fetchone()
        if row is None:
            raise BackendNotFoundError(
                f"Translation or text edition '{identifier}' was not found in the "
                f"local SQLite database at {self.db_path}."
            )

        return int(row["id"]), TranslationAttribution(
            identifier=str(row["identifier"]),
            language=_optional_string(row["language"]),
            name=_optional_string(row["name"]),
            english_name=_optional_string(row["englishName"]),
            edition_type=_optional_string(row["type"]),
            format=_optional_string(row["format"]),
        )

    def _fetch_ayahs(
        self,
        conn: sqlite3.Connection,
        where_clause: str,
        params: Sequence[Any],
        translation_id: int | None,
    ) -> list[AyahRecord]:
        rows = self._query_ayah_rows(
            conn,
            where_clause,
            params,
            translation_id,
            order_by="s.number, a.number_in_surah",
            limit=None,
        )
        return [self._row_to_ayah(row) for row in rows]

    def _query_ayah_rows(
        self,
        conn: sqlite3.Connection,
        where_clause: str,
        params: Sequence[Any],
        translation_id: int | None,
        *,
        order_by: str,
        limit: int | None,
    ) -> list[SQLiteRow]:
        translation_join = ""
        translation_select = "NULL AS translation_text"
        bindings: list[Any] = []

        if translation_id is not None:
            translation_join = (
                "LEFT JOIN ayah_edition ae ON ae.ayah_id = a.id AND ae.edition_id = ?"
            )
            translation_select = "ae.data AS translation_text"
            bindings.append(translation_id)

        query = f"""
            SELECT
                s.number AS surah_number,
                s.name_ar AS surah_name_arabic,
                s.name_en AS surah_name_english,
                s.name_en_translation AS surah_name_translation,
                s.type AS revelation_type,
                a.number_in_surah AS ayah_number,
                a.text AS arabic_text,
                a.page AS page_number,
                a.juz_id AS juz_number,
                a.hizb_id AS hizb_number,
                a.sajda AS sajda,
                {translation_select}
            FROM ayahs a
            JOIN surahs s ON s.id = a.surah_id
            {translation_join}
        """

        if where_clause:
            query = f"{query} WHERE {where_clause}"

        query = f"{query} ORDER BY {order_by}"
        if limit is not None:
            query = f"{query} LIMIT ?"

        bindings.extend(params)
        if limit is not None:
            bindings.append(limit)

        rows = conn.execute(query, bindings).fetchall()
        return [row for row in rows if isinstance(row, sqlite3.Row)]

    def _query_search_rows(
        self,
        conn: sqlite3.Connection,
        query: str,
        translation_id: int | None,
        limit: int,
    ) -> list[SQLiteRow]:
        translation_join = ""
        translation_select = "NULL AS translation_text"
        translation_condition = ""
        bindings: list[Any] = []

        if translation_id is not None:
            translation_join = (
                "LEFT JOIN ayah_edition ae ON ae.ayah_id = a.id AND ae.edition_id = ?"
            )
            translation_select = "ae.data AS translation_text"
            translation_condition = " OR ae.data LIKE ?"
            bindings.append(translation_id)

        like_pattern = f"%{query}%"
        query_text = f"""
            SELECT
                s.number AS surah_number,
                s.name_ar AS surah_name_arabic,
                s.name_en AS surah_name_english,
                s.name_en_translation AS surah_name_translation,
                s.type AS revelation_type,
                a.number_in_surah AS ayah_number,
                a.text AS arabic_text,
                a.page AS page_number,
                a.juz_id AS juz_number,
                a.hizb_id AS hizb_number,
                a.sajda AS sajda,
                {translation_select}
            FROM ayahs a
            JOIN surahs s ON s.id = a.surah_id
            {translation_join}
            WHERE a.text LIKE ?{translation_condition}
            ORDER BY s.number, a.number_in_surah
            LIMIT ?
        """

        bindings.append(like_pattern)
        if translation_id is not None:
            bindings.append(like_pattern)
        bindings.append(limit)

        rows = conn.execute(query_text, bindings).fetchall()
        return [row for row in rows if isinstance(row, sqlite3.Row)]

    def _row_to_ayah(self, row: SQLiteRow) -> AyahRecord:
        return AyahRecord(
            surah_number=int(row["surah_number"]),
            ayah_number=int(row["ayah_number"]),
            surah_name_arabic=str(row["surah_name_arabic"]),
            surah_name_english=str(row["surah_name_english"]),
            surah_name_translation=_optional_string(row["surah_name_translation"]),
            revelation_type=_optional_string(row["revelation_type"]),
            arabic_text=str(row["arabic_text"]),
            translation_text=_optional_string(row["translation_text"]),
            page_number=_optional_int(row["page_number"]),
            juz_number=_optional_int(row["juz_number"]),
            hizb_number=_optional_int(row["hizb_number"]),
            sajda=bool(row["sajda"]),
        )

    def _match_sources(
        self, query: str, arabic_text: str, translation_text: str | None
    ) -> tuple[str, ...]:
        normalized_query = query.casefold()
        matches: list[str] = []
        if normalized_query in arabic_text.casefold():
            matches.append("arabic_text")
        if translation_text and normalized_query in translation_text.casefold():
            matches.append("translation")
        return tuple(matches)


Backend = RemoteBackend | LocalSQLiteBackend


def select_backend(settings: Settings) -> Backend:
    if settings.mode is BackendMode.LOCAL:
        return LocalSQLiteBackend(Path(settings.db_path))

    return RemoteBackend(settings.api_url)


def _optional_int(value: Any) -> int | None:
    if value is None or value == "":
        return None

    return int(value)


def _optional_string(value: Any) -> str | None:
    if value is None:
        return None

    text = str(value).strip()
    if not text:
        return None

    return text


def _unwrap_mapping(payload: Mapping[str, Any], key: str) -> Mapping[str, Any]:
    nested = payload.get(key)
    if isinstance(nested, Mapping):
        return nested

    return payload


def _mapping_value(payload: Mapping[str, Any], key: str) -> Mapping[str, Any] | None:
    nested = payload.get(key)
    if isinstance(nested, Mapping):
        return nested

    return None


def _normalize_query(query: str) -> str:
    normalized = " ".join(query.split())
    if not normalized:
        raise BackendValidationError("Query cannot be empty.")

    return normalized


def _reference_key(reference: AyahReference) -> tuple[int, int]:
    return (reference.surah_number, reference.ayah_number)


def _tokenize(text: str) -> set[str]:
    tokens: set[str] = set()
    current: list[str] = []

    for char in text.casefold():
        if char.isalnum() or char == "_":
            current.append(char)
            continue

        if current:
            tokens.add("".join(current))
            current = []

    if current:
        tokens.add("".join(current))

    return {token for token in tokens if token}


def _related_terms(query_tokens: set[str], text_tokens: set[str]) -> tuple[str, ...]:
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


def _semantic_similarity(
    query: str, arabic_text: str, translation_text: str | None
) -> tuple[float, str]:
    searchable_parts = [arabic_text]
    if translation_text:
        searchable_parts.append(translation_text)

    searchable_text = " ".join(part for part in searchable_parts if part).strip()
    query_tokens = _tokenize(query)
    text_tokens = _tokenize(searchable_text)
    related_terms = _related_terms(query_tokens, text_tokens)
    ratio = SequenceMatcher(None, query.casefold(), searchable_text.casefold()).ratio()

    if query_tokens:
        token_coverage = len(related_terms) / len(query_tokens)
    else:
        token_coverage = 0.0

    union_count = len(query_tokens | text_tokens) or 1
    lexical_overlap = len(related_terms) / union_count
    score = round((token_coverage * 0.7) + (lexical_overlap * 0.2) + (ratio * 0.1), 3)

    if not related_terms and score < 0.08:
        return 0.0, ""

    if score < 0.12:
        return 0.0, ""

    if related_terms:
        reason = (
            "Shared terms in the selected text: " + ", ".join(related_terms) + "."
        )
    else:
        reason = "Closest textual overlap in the selected text."

    return score, reason
