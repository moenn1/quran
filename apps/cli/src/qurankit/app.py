from __future__ import annotations

import json
from typing import Annotated, Callable, TypeVar

import typer

from . import __version__
from .backends import (
    AyahReference,
    AyahSelection,
    BackendValidationError,
    ExactSearchHit,
    ExactSearchResult,
    JuzResult,
    LocalSQLiteBackend,
    QuranBackend,
    QuranKitBackendError,
    SemanticSearchHit,
    SemanticSearchResult,
    SurahResult,
    select_backend,
)
from .config import ConfigField, ConfigStore, Settings

app = typer.Typer(
    no_args_is_help=True,
    help=(
        "Respectful Quran lookup, exact search, and textual-similarity search "
        "for QuranKit."
    ),
)
config_app = typer.Typer(
    no_args_is_help=True,
    help="Manage QuranKit CLI configuration for remote API or local SQLite usage.",
)
app.add_typer(config_app, name="config")

ResultT = TypeVar("ResultT")


def _version_callback(value: bool) -> None:
    if value:
        typer.echo(__version__)
        raise typer.Exit()


@app.callback()
def root(
    version: Annotated[
        bool,
        typer.Option(
            "--version",
            help="Show the installed QuranKit CLI version and exit.",
            callback=_version_callback,
            is_eager=True,
        ),
    ] = False,
) -> None:
    """Respectful command-line access to QuranKit."""


def _settings_payload(store: ConfigStore) -> dict[str, object]:
    settings = store.load()
    backend = select_backend(settings)

    payload = {
        "config_file": str(store.path),
        "mode": settings.mode.value,
        "api_url": settings.api_url,
        "db_path": settings.db_path,
        "translation": settings.translation,
        "backend_kind": backend.kind,
        "backend_summary": backend.summary,
    }

    if isinstance(backend, LocalSQLiteBackend):
        payload["db_exists"] = backend.db_path.exists()

    return payload


@config_app.command("show")
def config_show(
    output_format: Annotated[
        str,
        typer.Option(
            "--format",
            "-f",
            help="Choose text or json output.",
            case_sensitive=False,
        ),
    ] = "text",
) -> None:
    store = ConfigStore()
    payload = _settings_payload(store)
    normalized = output_format.strip().lower()

    if normalized == "json":
        typer.echo(json.dumps(payload, indent=2, sort_keys=True))
        return

    if normalized != "text":
        raise typer.BadParameter("--format must be either text or json")

    typer.echo(f"Config file: {payload['config_file']}")
    typer.echo(f"Mode: {payload['mode']}")
    typer.echo(f"API URL: {payload['api_url']}")
    typer.echo(f"DB Path: {payload['db_path']}")
    typer.echo(f"Translation: {payload['translation']}")
    typer.echo(f"Active backend: {payload['backend_summary']}")


@config_app.command("set")
def config_set(
    key: Annotated[
        ConfigField,
        typer.Argument(help="One of: mode, api-url, db-path, translation."),
    ],
    value: Annotated[str, typer.Argument(help="Value to persist for that setting.")],
) -> None:
    store = ConfigStore()

    try:
        settings = store.update(key, value)
    except ValueError as exc:
        raise typer.BadParameter(str(exc)) from exc

    backend = select_backend(settings)
    typer.echo(f"Saved {key.value} to {store.path}")
    typer.echo(f"Active backend: {backend.summary}")


@app.command("surah")
def surah_command(
    surah_number: Annotated[
        int,
        typer.Argument(help="Surah number to load.", min=1, max=114),
    ],
    translation: Annotated[
        str | None,
        typer.Option(
            "--translation",
            help="Override the configured translation or text edition identifier.",
        ),
    ] = None,
    no_translation: Annotated[
        bool,
        typer.Option(
            "--no-translation",
            help="Show Arabic text only for this command.",
        ),
    ] = False,
    json_output: Annotated[
        bool,
        typer.Option(
            "--json",
            help="Emit machine-readable JSON instead of formatted text.",
        ),
    ] = False,
) -> None:
    settings, backend = _load_backend()
    result = _invoke_backend(
        lambda: backend.get_surah(
            surah_number,
            _resolve_translation_identifier(settings, translation, no_translation),
        )
    )
    _emit_result(result.to_dict(), _render_surah_text(result), json_output)


@app.command("ayah")
def ayah_command(
    reference: Annotated[
        str,
        typer.Argument(help="Ayah reference in SURAH:AYAH form, for example 2:255."),
    ],
    translation: Annotated[
        str | None,
        typer.Option(
            "--translation",
            help="Override the configured translation or text edition identifier.",
        ),
    ] = None,
    no_translation: Annotated[
        bool,
        typer.Option(
            "--no-translation",
            help="Show Arabic text only for this command.",
        ),
    ] = False,
    json_output: Annotated[
        bool,
        typer.Option(
            "--json",
            help="Emit machine-readable JSON instead of formatted text.",
        ),
    ] = False,
) -> None:
    ayah_reference = _parse_ayah_reference(reference)
    settings, backend = _load_backend()
    result = _invoke_backend(
        lambda: backend.get_ayah(
            ayah_reference,
            _resolve_translation_identifier(settings, translation, no_translation),
        )
    )
    _emit_result(result.to_dict(), _render_ayah_selection_text(result), json_output)


@app.command("juz")
def juz_command(
    juz_number: Annotated[
        int,
        typer.Argument(help="Juz number to load.", min=1, max=30),
    ],
    translation: Annotated[
        str | None,
        typer.Option(
            "--translation",
            help="Override the configured translation or text edition identifier.",
        ),
    ] = None,
    no_translation: Annotated[
        bool,
        typer.Option(
            "--no-translation",
            help="Show Arabic text only for this command.",
        ),
    ] = False,
    json_output: Annotated[
        bool,
        typer.Option(
            "--json",
            help="Emit machine-readable JSON instead of formatted text.",
        ),
    ] = False,
) -> None:
    settings, backend = _load_backend()
    result = _invoke_backend(
        lambda: backend.get_juz(
            juz_number,
            _resolve_translation_identifier(settings, translation, no_translation),
        )
    )
    _emit_result(result.to_dict(), _render_juz_text(result), json_output)


@app.command("random")
def random_command(
    translation: Annotated[
        str | None,
        typer.Option(
            "--translation",
            help="Override the configured translation or text edition identifier.",
        ),
    ] = None,
    no_translation: Annotated[
        bool,
        typer.Option(
            "--no-translation",
            help="Show Arabic text only for this command.",
        ),
    ] = False,
    json_output: Annotated[
        bool,
        typer.Option(
            "--json",
            help="Emit machine-readable JSON instead of formatted text.",
        ),
    ] = False,
) -> None:
    settings, backend = _load_backend()
    result = _invoke_backend(
        lambda: backend.get_random_ayah(
            _resolve_translation_identifier(settings, translation, no_translation)
        )
    )
    _emit_result(result.to_dict(), _render_ayah_selection_text(result), json_output)


@app.command("search")
def search_command(
    query_parts: Annotated[
        list[str],
        typer.Argument(help="Words or phrase to search exactly."),
    ],
    translation: Annotated[
        str | None,
        typer.Option(
            "--translation",
            help="Override the configured translation or text edition identifier.",
        ),
    ] = None,
    no_translation: Annotated[
        bool,
        typer.Option(
            "--no-translation",
            help="Search Arabic text only for this command.",
        ),
    ] = False,
    limit: Annotated[
        int,
        typer.Option(
            "--limit",
            min=1,
            max=25,
            help="Maximum number of exact matches to return.",
        ),
    ] = 5,
    json_output: Annotated[
        bool,
        typer.Option(
            "--json",
            help="Emit machine-readable JSON instead of formatted text.",
        ),
    ] = False,
) -> None:
    query = _join_query_parts(query_parts)
    settings, backend = _load_backend()
    result = _invoke_backend(
        lambda: backend.search(
            query,
            _resolve_translation_identifier(settings, translation, no_translation),
            limit,
        )
    )
    _emit_result(result.to_dict(), _render_exact_search_text(result), json_output)


@app.command("semantic")
def semantic_command(
    query_parts: Annotated[
        list[str],
        typer.Argument(help="Words or phrase used to find related passages."),
    ],
    translation: Annotated[
        str | None,
        typer.Option(
            "--translation",
            help="Override the configured translation or text edition identifier.",
        ),
    ] = None,
    no_translation: Annotated[
        bool,
        typer.Option(
            "--no-translation",
            help="Search Arabic text only for this command.",
        ),
    ] = False,
    limit: Annotated[
        int,
        typer.Option(
            "--limit",
            min=1,
            max=25,
            help="Maximum number of related passages to return.",
        ),
    ] = 5,
    json_output: Annotated[
        bool,
        typer.Option(
            "--json",
            help="Emit machine-readable JSON instead of formatted text.",
        ),
    ] = False,
) -> None:
    query = _join_query_parts(query_parts)
    settings, backend = _load_backend()
    result = _invoke_backend(
        lambda: backend.semantic_search(
            query,
            _resolve_translation_identifier(settings, translation, no_translation),
            limit,
        )
    )
    _emit_result(result.to_dict(), _render_semantic_search_text(result), json_output)


def _parse_ayah_reference(value: str) -> AyahReference:
    normalized = value.strip()
    surah_text, separator, ayah_text = normalized.partition(":")
    if separator != ":" or not surah_text.isdigit() or not ayah_text.isdigit():
        raise typer.BadParameter("Ayah reference must look like SURAH:AYAH, for example 2:255.")

    surah_number = int(surah_text)
    ayah_number = int(ayah_text)
    if surah_number < 1 or ayah_number < 1:
        raise typer.BadParameter("Ayah reference numbers must both be positive.")

    return AyahReference(surah_number=surah_number, ayah_number=ayah_number)


def _join_query_parts(parts: list[str]) -> str:
    normalized = " ".join(part for part in parts if part.strip())
    if not normalized:
        raise typer.BadParameter("Search query cannot be empty.")

    return normalized


def _load_backend() -> tuple[Settings, QuranBackend]:
    store = ConfigStore()
    try:
        settings = store.load()
    except ValueError as exc:
        _exit_with_error(str(exc))

    return settings, select_backend(settings)


def _resolve_translation_identifier(
    settings: Settings, override: str | None, no_translation: bool
) -> str | None:
    if no_translation:
        return None

    if override is None:
        return settings.translation

    normalized = override.strip()
    if not normalized:
        raise typer.BadParameter("--translation cannot be empty")

    return normalized


def _invoke_backend(action: Callable[[], ResultT]) -> ResultT:
    try:
        return action()
    except (BackendValidationError, QuranKitBackendError) as exc:
        _exit_with_error(str(exc))


def _emit_result(payload: dict[str, object], text: str, json_output: bool) -> None:
    if json_output:
        typer.echo(json.dumps(payload, ensure_ascii=False, indent=2))
        return

    typer.echo(text)


def _render_surah_text(result: SurahResult) -> str:
    lines = [
        f"Surah {result.surah_number}: {result.name_english}",
        f"Arabic name: {result.name_arabic}",
    ]
    if result.name_translation:
        lines.append(f"Translated name: {result.name_translation}")
    if result.revelation_type:
        lines.append(f"Revelation: {result.revelation_type}")
    lines.append(f"Ayahs: {len(result.ayahs)}")
    lines.append("")

    for index, ayah in enumerate(result.ayahs):
        lines.extend(_render_ayah_block(ayah, include_surah_name=False))
        if index < len(result.ayahs) - 1:
            lines.append("")

    lines.append("")
    lines.extend(_render_attribution_lines(result.translation_attribution))
    return "\n".join(lines)


def _render_ayah_selection_text(result: AyahSelection) -> str:
    title = "Random ayah" if result.selection_kind == "random" else f"Ayah {result.ayah.reference}"
    lines = [title]
    lines.append(
        f"Surah: {result.ayah.surah_name_english} ({result.ayah.surah_name_arabic})"
    )
    if result.ayah.surah_name_translation:
        lines.append(f"Translated name: {result.ayah.surah_name_translation}")
    if result.ayah.revelation_type:
        lines.append(f"Revelation: {result.ayah.revelation_type}")
    lines.append("")
    lines.extend(_render_ayah_block(result.ayah, include_surah_name=False))
    lines.append("")
    lines.extend(_render_attribution_lines(result.translation_attribution))
    return "\n".join(lines)


def _render_juz_text(result: JuzResult) -> str:
    lines = [
        f"Juz {result.juz_number}",
        f"Range: {result.start_reference} to {result.end_reference}",
        f"Ayahs: {len(result.ayahs)}",
        "",
    ]

    for index, ayah in enumerate(result.ayahs):
        lines.extend(_render_ayah_block(ayah, include_surah_name=True))
        if index < len(result.ayahs) - 1:
            lines.append("")

    lines.append("")
    lines.extend(_render_attribution_lines(result.translation_attribution))
    return "\n".join(lines)


def _render_exact_search_text(result: ExactSearchResult) -> str:
    lines = [f'Exact matches for "{result.query}"']
    if result.results:
        lines.append(f"Results: {len(result.results)}")
    else:
        lines.append("No exact matches found.")
        return "\n".join(lines)

    lines.append(
        "Searched fields: "
        + ", ".join(_display_search_field(field) for field in result.searched_fields)
    )
    lines.append("")

    for index, hit in enumerate(result.results):
        lines.extend(_render_exact_hit(hit))
        if index < len(result.results) - 1:
            lines.append("")

    lines.append("")
    lines.extend(_render_attribution_lines(result.translation_attribution))
    return "\n".join(lines)


def _render_semantic_search_text(result: SemanticSearchResult) -> str:
    lines = [
        f'Related passages by textual similarity for "{result.query}"',
        result.disclaimer,
    ]
    if result.results:
        lines.append(f"Results: {len(result.results)}")
    else:
        lines.append("No related passages were found.")
        return "\n".join(lines)

    lines.append("")
    for index, hit in enumerate(result.results):
        lines.extend(_render_semantic_hit(hit))
        if index < len(result.results) - 1:
            lines.append("")

    lines.append("")
    lines.extend(_render_attribution_lines(result.translation_attribution))
    return "\n".join(lines)


def _render_ayah_block(ayah: AyahSelection | SurahResult | object, *, include_surah_name: bool) -> list[str]:
    if not hasattr(ayah, "reference"):
        return []

    lines: list[str] = []
    if include_surah_name:
        lines.append(f"{ayah.reference} • {ayah.surah_name_english}")
    else:
        lines.append(ayah.reference)
    lines.append(ayah.arabic_text)
    if ayah.translation_text:
        lines.append(ayah.translation_text)

    metadata: list[str] = []
    if ayah.page_number is not None:
        metadata.append(f"Page {ayah.page_number}")
    if ayah.juz_number is not None:
        metadata.append(f"Juz {ayah.juz_number}")
    if ayah.hizb_number is not None:
        metadata.append(f"Hizb slot {ayah.hizb_number}")
    if ayah.sajda:
        metadata.append("Sajda")
    if metadata:
        lines.append(" | ".join(metadata))

    return lines


def _render_exact_hit(hit: ExactSearchHit) -> list[str]:
    lines = _render_ayah_block(hit.ayah, include_surah_name=True)
    lines.append(
        "Matched in: "
        + ", ".join(_display_search_field(field) for field in hit.match_sources)
    )
    return lines


def _render_semantic_hit(hit: SemanticSearchHit) -> list[str]:
    lines = _render_ayah_block(hit.ayah, include_surah_name=True)
    lines.append(f"Similarity score: {hit.similarity_score:.3f}")
    lines.append(f"Why it was included: {hit.reason}")
    return lines


def _render_attribution_lines(translation: object | None) -> list[str]:
    lines = [
        "Arabic source: AbdullahGhanem/quran-database "
        "(snapshot f6c4c805f22b0432677d79aafc12139b915e1a0d)"
    ]
    if translation is not None and hasattr(translation, "display_name"):
        label = "Translation"
        if getattr(translation, "label", "translation") == "edition":
            label = "Edition"
        lines.append(
            f"{label}: {translation.display_name} ({translation.identifier})"
        )
    return lines


def _display_search_field(value: str) -> str:
    if value == "arabic_text":
        return "Arabic text"
    if value == "translation":
        return "Selected translation"
    return value.replace("_", " ")


def _exit_with_error(message: str) -> None:
    typer.echo(f"Error: {message}", err=True)
    raise typer.Exit(code=1)


def main() -> None:
    app()
