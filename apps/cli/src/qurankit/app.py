from __future__ import annotations

import json
from pathlib import Path
from typing import Annotated, Callable, TypeVar

import typer

from . import __version__
from .backends import (
    AyahRangeResult,
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
from .personal import (
    AyahRange,
    BookmarkEntry,
    NoteEntry,
    PersonalDataError,
    PlanTodayResult,
    ProgressMarkResult,
    ReadingPlan,
    StudyTracker,
    describe_study_store,
    parse_ayah_range,
    select_study_store,
)

app = typer.Typer(
    no_args_is_help=True,
    help=(
        "Respectful Quran lookup, private reading progress, plans, bookmarks, "
        "notes, and exports for QuranKit."
    ),
)
config_app = typer.Typer(
    no_args_is_help=True,
    help=(
        "Manage QuranKit CLI configuration for Quran data backends and private "
        "study-state storage."
    ),
)
progress_app = typer.Typer(
    no_args_is_help=False,
    invoke_without_command=True,
    help="Review or update private reading progress.",
)
bookmark_app = typer.Typer(
    no_args_is_help=False,
    invoke_without_command=True,
    help="Save private bookmarks for ayah references or ranges.",
)
note_app = typer.Typer(
    no_args_is_help=False,
    invoke_without_command=True,
    help="Manage private study notes linked to ayah references or ranges.",
)
plan_app = typer.Typer(
    no_args_is_help=False,
    invoke_without_command=True,
    help="Create and inspect private reading plans.",
)
export_app = typer.Typer(
    no_args_is_help=True,
    help="Export QuranKit CLI data with clear attribution boundaries.",
)

app.add_typer(config_app, name="config")
app.add_typer(progress_app, name="progress")
app.add_typer(bookmark_app, name="bookmark")
app.add_typer(note_app, name="note")
app.add_typer(plan_app, name="plan")
app.add_typer(export_app, name="export")

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
    study_store_kind, study_store_summary = describe_study_store(settings)

    payload = {
        "config_file": str(store.path),
        "mode": settings.mode.value,
        "state_mode": settings.state_mode.value,
        "api_url": settings.api_url,
        "db_path": settings.db_path,
        "state_path": settings.state_path,
        "translation": settings.translation,
        "api_token_configured": settings.api_token is not None,
        "backend_kind": backend.kind,
        "backend_summary": backend.summary,
        "study_store_kind": study_store_kind,
        "study_store_summary": study_store_summary,
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
    typer.echo(f"State mode: {payload['state_mode']}")
    typer.echo(f"API URL: {payload['api_url']}")
    typer.echo(f"DB Path: {payload['db_path']}")
    typer.echo(f"State Path: {payload['state_path']}")
    typer.echo(f"Translation: {payload['translation']}")
    typer.echo(
        "API token: "
        + ("configured" if payload["api_token_configured"] else "not configured")
    )
    typer.echo(f"Active backend: {payload['backend_summary']}")
    typer.echo(f"Personal data: {payload['study_store_summary']}")


@config_app.command("set")
def config_set(
    key: Annotated[
        ConfigField,
        typer.Argument(
            help=(
                "One of: mode, state-mode, api-url, db-path, state-path, "
                "translation, api-token."
            )
        ),
    ],
    value: Annotated[str, typer.Argument(help="Value to persist for that setting.")],
) -> None:
    store = ConfigStore()

    try:
        settings = store.update(key, value)
    except ValueError as exc:
        raise typer.BadParameter(str(exc)) from exc

    backend = select_backend(settings)
    _, study_store_summary = describe_study_store(settings)
    typer.echo(f"Saved {key.value} to {store.path}")
    typer.echo(f"Active backend: {backend.summary}")
    typer.echo(f"Personal data: {study_store_summary}")


@progress_app.callback(invoke_without_command=True)
def progress_root(
    ctx: typer.Context,
    json_output: Annotated[
        bool,
        typer.Option(
            "--json",
            help="Emit machine-readable JSON instead of formatted text.",
        ),
    ] = False,
) -> None:
    if ctx.invoked_subcommand is None:
        _progress_show(json_output=json_output)


@progress_app.command("show")
def progress_show_command(
    json_output: Annotated[
        bool,
        typer.Option(
            "--json",
            help="Emit machine-readable JSON instead of formatted text.",
        ),
    ] = False,
) -> None:
    _progress_show(json_output=json_output)


@progress_app.command("mark")
def progress_mark_command(
    reference_or_range: Annotated[
        str,
        typer.Argument(
            help=(
                "Ayah reference or range, for example 2:255, 2:255-257, or "
                "2:255-3:5."
            )
        ),
    ],
    json_output: Annotated[
        bool,
        typer.Option(
            "--json",
            help="Emit machine-readable JSON instead of formatted text.",
        ),
    ] = False,
) -> None:
    reading_range = _parse_reading_range(reference_or_range)
    settings = _load_settings()
    _, tracker = _load_tracker(settings)
    backend = select_backend(settings)
    _invoke(lambda: _validate_reading_range(backend, reading_range))
    result = _invoke(lambda: tracker.mark_progress(reading_range))
    _emit_result(
        {
            **result.to_dict(),
            "storage": _study_storage_payload(settings, tracker),
        },
        _render_progress_mark_text(result, tracker.description),
        json_output,
    )


@bookmark_app.callback(invoke_without_command=True)
def bookmark_root(
    ctx: typer.Context,
    json_output: Annotated[
        bool,
        typer.Option(
            "--json",
            help="Emit machine-readable JSON instead of formatted text.",
        ),
    ] = False,
) -> None:
    if ctx.invoked_subcommand is None:
        _bookmark_list(json_output=json_output)


@bookmark_app.command("list")
def bookmark_list_command(
    json_output: Annotated[
        bool,
        typer.Option(
            "--json",
            help="Emit machine-readable JSON instead of formatted text.",
        ),
    ] = False,
) -> None:
    _bookmark_list(json_output=json_output)


@bookmark_app.command("add")
def bookmark_add_command(
    reference_or_range: Annotated[
        str,
        typer.Argument(
            help=(
                "Ayah reference or range, for example 1:1, 2:255-257, or "
                "2:255-3:5."
            )
        ),
    ],
    label: Annotated[
        str | None,
        typer.Option(
            "--label",
            help="Optional private label to help recognize the bookmark later.",
        ),
    ] = None,
    json_output: Annotated[
        bool,
        typer.Option(
            "--json",
            help="Emit machine-readable JSON instead of formatted text.",
        ),
    ] = False,
) -> None:
    reading_range = _parse_reading_range(reference_or_range)
    settings = _load_settings()
    _, tracker = _load_tracker(settings)
    backend = select_backend(settings)
    _invoke(lambda: _validate_reading_range(backend, reading_range))
    bookmark = _invoke(lambda: tracker.add_bookmark(reading_range, label=label))
    _emit_result(
        {
            "bookmark": bookmark.to_dict(),
            "storage": _study_storage_payload(settings, tracker),
        },
        _render_bookmark_added_text(bookmark, tracker.description),
        json_output,
    )


@bookmark_app.command("remove")
def bookmark_remove_command(
    entry_id: Annotated[str, typer.Argument(help="Saved bookmark identifier.")],
    json_output: Annotated[
        bool,
        typer.Option(
            "--json",
            help="Emit machine-readable JSON instead of formatted text.",
        ),
    ] = False,
) -> None:
    settings, tracker = _load_tracker()
    removed = _invoke(lambda: tracker.remove_bookmark(entry_id))
    _emit_result(
        {
            "bookmark": removed.to_dict(),
            "removed": True,
            "storage": _study_storage_payload(settings, tracker),
        },
        _render_removed_text(
            "bookmark",
            removed.id,
            removed.reading_range.label,
            tracker.description,
        ),
        json_output,
    )


@note_app.callback(invoke_without_command=True)
def note_root(
    ctx: typer.Context,
    reference: Annotated[
        str | None,
        typer.Option(
            "--reference",
            help="Limit notes to a specific ayah reference or range.",
        ),
    ] = None,
    json_output: Annotated[
        bool,
        typer.Option(
            "--json",
            help="Emit machine-readable JSON instead of formatted text.",
        ),
    ] = False,
) -> None:
    if ctx.invoked_subcommand is None:
        _note_list(reference_or_range=reference, json_output=json_output)


@note_app.command("list")
def note_list_command(
    reference: Annotated[
        str | None,
        typer.Option(
            "--reference",
            help="Limit notes to a specific ayah reference or range.",
        ),
    ] = None,
    json_output: Annotated[
        bool,
        typer.Option(
            "--json",
            help="Emit machine-readable JSON instead of formatted text.",
        ),
    ] = False,
) -> None:
    _note_list(reference_or_range=reference, json_output=json_output)


@note_app.command("add")
def note_add_command(
    reference_or_range: Annotated[
        str,
        typer.Argument(
            help=(
                "Ayah reference or range, for example 1:1, 2:255-257, or "
                "2:255-3:5."
            )
        ),
    ],
    body_parts: Annotated[
        list[str],
        typer.Argument(help="Private note body."),
    ],
    json_output: Annotated[
        bool,
        typer.Option(
            "--json",
            help="Emit machine-readable JSON instead of formatted text.",
        ),
    ] = False,
) -> None:
    reading_range = _parse_reading_range(reference_or_range)
    body = _join_text_parts(body_parts, field_name="Note body")
    settings = _load_settings()
    _, tracker = _load_tracker(settings)
    backend = select_backend(settings)
    _invoke(lambda: _validate_reading_range(backend, reading_range))
    note = _invoke(lambda: tracker.add_note(reading_range, body=body))
    _emit_result(
        {
            "note": note.to_dict(),
            "storage": _study_storage_payload(settings, tracker),
        },
        _render_note_added_text(note, tracker.description),
        json_output,
    )


@note_app.command("remove")
def note_remove_command(
    entry_id: Annotated[str, typer.Argument(help="Saved note identifier.")],
    json_output: Annotated[
        bool,
        typer.Option(
            "--json",
            help="Emit machine-readable JSON instead of formatted text.",
        ),
    ] = False,
) -> None:
    settings, tracker = _load_tracker()
    removed = _invoke(lambda: tracker.remove_note(entry_id))
    _emit_result(
        {
            "note": removed.to_dict(),
            "removed": True,
            "storage": _study_storage_payload(settings, tracker),
        },
        _render_removed_text(
            "note",
            removed.id,
            removed.reading_range.label,
            tracker.description,
        ),
        json_output,
    )


@plan_app.callback(invoke_without_command=True)
def plan_root(
    ctx: typer.Context,
    json_output: Annotated[
        bool,
        typer.Option(
            "--json",
            help="Emit machine-readable JSON instead of formatted text.",
        ),
    ] = False,
) -> None:
    if ctx.invoked_subcommand is None:
        _plan_list(json_output=json_output)


@plan_app.command("list")
def plan_list_command(
    json_output: Annotated[
        bool,
        typer.Option(
            "--json",
            help="Emit machine-readable JSON instead of formatted text.",
        ),
    ] = False,
) -> None:
    _plan_list(json_output=json_output)


@plan_app.command("create")
def plan_create_command(
    name: Annotated[str, typer.Argument(help="Private reading plan name.")],
    reference_or_range: Annotated[
        str,
        typer.Argument(
            help=(
                "Ayah reference or range, for example 1:1-1:7 or 2:255-3:5."
            )
        ),
    ],
    daily_ayah_target: Annotated[
        int,
        typer.Option(
            "--daily-ayahs",
            "--daily",
            min=1,
            help="How many ayahs to assign each day.",
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
    reading_range = _parse_reading_range(reference_or_range)
    settings = _load_settings()
    _, tracker = _load_tracker(settings)
    backend = select_backend(settings)
    _invoke(lambda: _validate_reading_range(backend, reading_range))
    plan = _invoke(
        lambda: tracker.create_plan(
            name=name,
            reading_range=reading_range,
            daily_ayah_target=daily_ayah_target,
        )
    )
    _emit_result(
        {
            "plan": plan.to_dict(),
            "storage": _study_storage_payload(settings, tracker),
        },
        _render_plan_created_text(plan, tracker.description),
        json_output,
    )


@plan_app.command("today")
def plan_today_command(
    plan_selector: Annotated[
        str | None,
        typer.Option(
            "--plan",
            help="Plan id or exact plan name. Required when multiple plans exist.",
        ),
    ] = None,
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
    settings = _load_settings()
    _, tracker = _load_tracker(settings)
    backend = select_backend(settings)
    result = _invoke(
        lambda: tracker.today(
            backend=backend,
            plan_selector=plan_selector,
            translation_identifier=_resolve_translation_identifier(
                settings,
                translation,
                no_translation,
            ),
        )
    )
    _emit_result(
        {
            **result.to_dict(),
            "storage": _study_storage_payload(settings, tracker),
        },
        _render_plan_today_text(result, tracker.description),
        json_output,
    )


@export_app.command("progress")
def export_progress_command(
    output: Annotated[
        Path | None,
        typer.Option(
            "--output",
            "-o",
            help="Write the export to a file instead of stdout.",
        ),
    ] = None,
) -> None:
    settings, tracker = _load_tracker()
    state = _invoke(lambda: tracker.load_state())
    payload = {
        "storage": _study_storage_payload(settings, tracker),
        "progress": state.progress.to_dict() if state.progress is not None else None,
        "plans": [plan.to_dict() for plan in state.plans],
    }
    _emit_export(
        _serialize_json(payload),
        output=output,
        success_message="Exported progress data.",
    )


@export_app.command("bookmarks")
def export_bookmarks_command(
    output: Annotated[
        Path | None,
        typer.Option(
            "--output",
            "-o",
            help="Write the export to a file instead of stdout.",
        ),
    ] = None,
) -> None:
    settings, tracker = _load_tracker()
    bookmarks = _invoke(lambda: tracker.list_bookmarks())
    payload = {
        "storage": _study_storage_payload(settings, tracker),
        "count": len(bookmarks),
        "bookmarks": [bookmark.to_dict() for bookmark in bookmarks],
    }
    _emit_export(
        _serialize_json(payload),
        output=output,
        success_message="Exported bookmarks.",
    )


@export_app.command("surah")
def export_surah_command(
    surah_number: Annotated[
        int,
        typer.Argument(help="Surah number to export.", min=1, max=114),
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
            help="Show Arabic text only for this export.",
        ),
    ] = False,
    output_format: Annotated[
        str,
        typer.Option(
            "--format",
            "-f",
            help="Choose text or json output.",
            case_sensitive=False,
        ),
    ] = "json",
    output: Annotated[
        Path | None,
        typer.Option(
            "--output",
            "-o",
            help="Write the export to a file instead of stdout.",
        ),
    ] = None,
) -> None:
    settings, backend = _load_backend()
    result = _invoke(
        lambda: backend.get_surah(
            surah_number,
            _resolve_translation_identifier(settings, translation, no_translation),
        )
    )
    normalized_format = _normalize_output_format(output_format)
    if normalized_format == "json":
        content = _serialize_json(result.to_dict())
    else:
        content = _render_surah_text(result)
    _emit_export(
        content,
        output=output,
        success_message=f"Exported surah {surah_number}.",
    )


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
    result = _invoke(
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
    result = _invoke(
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
    result = _invoke(
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
    result = _invoke(
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
    query = _join_text_parts(query_parts, field_name="Search query")
    settings, backend = _load_backend()
    result = _invoke(
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
    query = _join_text_parts(query_parts, field_name="Search query")
    settings, backend = _load_backend()
    result = _invoke(
        lambda: backend.semantic_search(
            query,
            _resolve_translation_identifier(settings, translation, no_translation),
            limit,
        )
    )
    _emit_result(result.to_dict(), _render_semantic_search_text(result), json_output)


def _progress_show(*, json_output: bool) -> None:
    settings, tracker = _load_tracker()
    state = _invoke(lambda: tracker.load_state())
    payload = {
        "storage": _study_storage_payload(settings, tracker),
        "progress": state.progress.to_dict() if state.progress is not None else None,
        "bookmark_count": len(state.bookmarks),
        "note_count": len(state.notes),
        "plan_count": len(state.plans),
    }
    _emit_result(payload, _render_progress_text(state, tracker.description), json_output)


def _bookmark_list(*, json_output: bool) -> None:
    settings, tracker = _load_tracker()
    bookmarks = _invoke(lambda: tracker.list_bookmarks())
    payload = {
        "storage": _study_storage_payload(settings, tracker),
        "count": len(bookmarks),
        "bookmarks": [bookmark.to_dict() for bookmark in bookmarks],
    }
    _emit_result(
        payload,
        _render_bookmarks_text(bookmarks, tracker.description),
        json_output,
    )


def _note_list(*, reference_or_range: str | None, json_output: bool) -> None:
    settings, tracker = _load_tracker()
    reading_range = (
        _parse_reading_range(reference_or_range)
        if reference_or_range is not None
        else None
    )
    notes = _invoke(lambda: tracker.list_notes(reading_range))
    payload = {
        "storage": _study_storage_payload(settings, tracker),
        "count": len(notes),
        "filter": reading_range.to_dict() if reading_range is not None else None,
        "notes": [note.to_dict() for note in notes],
    }
    _emit_result(
        payload,
        _render_notes_text(
            notes,
            tracker.description,
            filter_label=reading_range.label if reading_range is not None else None,
        ),
        json_output,
    )


def _plan_list(*, json_output: bool) -> None:
    settings, tracker = _load_tracker()
    plans = _invoke(lambda: tracker.list_plans())
    payload = {
        "storage": _study_storage_payload(settings, tracker),
        "count": len(plans),
        "plans": [plan.to_dict() for plan in plans],
    }
    _emit_result(
        payload,
        _render_plan_list_text(plans, tracker.description),
        json_output,
    )


def _parse_ayah_reference(value: str) -> AyahReference:
    normalized = value.strip()
    surah_text, separator, ayah_text = normalized.partition(":")
    if separator != ":" or not surah_text.isdigit() or not ayah_text.isdigit():
        raise typer.BadParameter(
            "Ayah reference must look like SURAH:AYAH, for example 2:255."
        )

    surah_number = int(surah_text)
    ayah_number = int(ayah_text)
    if surah_number < 1 or ayah_number < 1:
        raise typer.BadParameter("Ayah reference numbers must both be positive.")

    return AyahReference(surah_number=surah_number, ayah_number=ayah_number)


def _parse_reading_range(value: str | None) -> AyahRange:
    if value is None:
        raise typer.BadParameter("A reference or ayah range is required.")

    try:
        return parse_ayah_range(value)
    except PersonalDataError as exc:
        raise typer.BadParameter(str(exc)) from exc


def _join_text_parts(parts: list[str], *, field_name: str) -> str:
    normalized = " ".join(part for part in parts if part.strip())
    if not normalized:
        raise typer.BadParameter(f"{field_name} cannot be empty.")

    return normalized


def _load_settings() -> Settings:
    store = ConfigStore()
    try:
        return store.load()
    except ValueError as exc:
        _exit_with_error(str(exc))


def _load_backend(settings: Settings | None = None) -> tuple[Settings, QuranBackend]:
    resolved_settings = settings or _load_settings()
    return resolved_settings, select_backend(resolved_settings)


def _load_tracker(settings: Settings | None = None) -> tuple[Settings, StudyTracker]:
    resolved_settings = settings or _load_settings()
    try:
        tracker = StudyTracker(select_study_store(resolved_settings))
    except PersonalDataError as exc:
        _exit_with_error(str(exc))

    return resolved_settings, tracker


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


def _validate_reading_range(backend: QuranBackend, reading_range: AyahRange) -> None:
    backend.get_range(reading_range.start, reading_range.end, None)


def _invoke(action: Callable[[], ResultT]) -> ResultT:
    try:
        return action()
    except (BackendValidationError, QuranKitBackendError, PersonalDataError) as exc:
        _exit_with_error(str(exc))


def _emit_result(payload: object, text: str, json_output: bool) -> None:
    if json_output:
        typer.echo(_serialize_json(payload))
        return

    typer.echo(text)


def _emit_export(content: str, *, output: Path | None, success_message: str) -> None:
    if output is None:
        typer.echo(content)
        return

    output.parent.mkdir(parents=True, exist_ok=True)
    if content.endswith("\n"):
        output.write_text(content, encoding="utf-8")
    else:
        output.write_text(content + "\n", encoding="utf-8")
    typer.echo(f"{success_message} Wrote {output}.")


def _serialize_json(payload: object) -> str:
    return json.dumps(payload, ensure_ascii=False, indent=2)


def _normalize_output_format(value: str) -> str:
    normalized = value.strip().lower()
    if normalized not in {"json", "text"}:
        raise typer.BadParameter("--format must be either text or json")
    return normalized


def _study_storage_payload(settings: Settings, tracker: StudyTracker) -> dict[str, object]:
    return {
        "mode": settings.state_mode.value,
        "summary": tracker.description,
        "private_by_default": True,
    }


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
    title = (
        "Random ayah"
        if result.selection_kind == "random"
        else f"Ayah {result.ayah.reference}"
    )
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


def _render_progress_text(state: object, store_description: str) -> str:
    progress = getattr(state, "progress", None)
    bookmarks = getattr(state, "bookmarks", ())
    notes = getattr(state, "notes", ())
    plans = getattr(state, "plans", ())

    lines = [
        "Reading progress",
        f"Storage: {store_description}",
        "Privacy: private by default.",
    ]
    if progress is None:
        lines.append("No reading progress has been marked yet.")
    else:
        lines.append(f"Latest checkpoint: {progress.reading_range.label}")
        lines.append(f"Updated: {progress.updated_at}")

    lines.append(f"Bookmarks: {len(bookmarks)}")
    lines.append(f"Notes: {len(notes)}")
    lines.append(f"Plans: {len(plans)}")
    return "\n".join(lines)


def _render_progress_mark_text(
    result: ProgressMarkResult, store_description: str
) -> str:
    lines = [
        f"Updated reading progress to {result.progress.reading_range.label}",
        f"Updated: {result.progress.updated_at}",
        f"Storage: {store_description}",
        "Privacy: private by default.",
    ]
    if result.updated_plan_names:
        lines.append("Updated plans: " + ", ".join(result.updated_plan_names))
    return "\n".join(lines)


def _render_bookmarks_text(
    bookmarks: tuple[BookmarkEntry, ...], store_description: str
) -> str:
    lines = [
        "Bookmarks",
        f"Storage: {store_description}",
        "Privacy: private by default.",
    ]
    if not bookmarks:
        lines.append("No bookmarks saved.")
        return "\n".join(lines)

    lines.append(f"Saved: {len(bookmarks)}")
    lines.append("")
    for index, bookmark in enumerate(bookmarks):
        lines.append(f"{bookmark.id} • {bookmark.reading_range.label}")
        if bookmark.label:
            lines.append(f"Label: {bookmark.label}")
        lines.append(f"Created: {bookmark.created_at}")
        if index < len(bookmarks) - 1:
            lines.append("")
    return "\n".join(lines)


def _render_bookmark_added_text(
    bookmark: BookmarkEntry, store_description: str
) -> str:
    lines = [
        f"Saved bookmark {bookmark.id}",
        f"Range: {bookmark.reading_range.label}",
        f"Storage: {store_description}",
        "Privacy: private by default.",
    ]
    if bookmark.label:
        lines.append(f"Label: {bookmark.label}")
    return "\n".join(lines)


def _render_notes_text(
    notes: tuple[NoteEntry, ...],
    store_description: str,
    *,
    filter_label: str | None,
) -> str:
    lines = [
        "Notes",
        f"Storage: {store_description}",
        "Privacy: private by default.",
    ]
    if filter_label:
        lines.append(f"Filter: {filter_label}")
    if not notes:
        lines.append("No notes saved.")
        return "\n".join(lines)

    lines.append(f"Saved: {len(notes)}")
    lines.append("")
    for index, note in enumerate(notes):
        lines.append(f"{note.id} • {note.reading_range.label}")
        lines.append(note.body)
        lines.append(f"Updated: {note.updated_at}")
        if index < len(notes) - 1:
            lines.append("")
    return "\n".join(lines)


def _render_note_added_text(note: NoteEntry, store_description: str) -> str:
    return "\n".join(
        [
            f"Saved note {note.id}",
            f"Range: {note.reading_range.label}",
            f"Storage: {store_description}",
            "Privacy: private by default.",
        ]
    )


def _render_removed_text(
    kind: str,
    entry_id: str,
    range_label: str,
    store_description: str,
) -> str:
    return "\n".join(
        [
            f"Removed {kind} {entry_id}",
            f"Range: {range_label}",
            f"Storage: {store_description}",
            "Privacy: private by default.",
        ]
    )


def _render_plan_list_text(
    plans: tuple[ReadingPlan, ...], store_description: str
) -> str:
    lines = [
        "Reading plans",
        f"Storage: {store_description}",
        "Privacy: private by default.",
    ]
    if not plans:
        lines.append("No reading plans saved.")
        return "\n".join(lines)

    lines.append(f"Saved: {len(plans)}")
    lines.append("")
    for index, plan in enumerate(plans):
        lines.append(f"{plan.id} • {plan.name}")
        lines.append(f"Range: {plan.reading_range.label}")
        lines.append(f"Daily target: {plan.daily_ayah_target} ayahs")
        if plan.completed_through is not None:
            lines.append(f"Completed through: {plan.completed_through.text}")
        else:
            lines.append("Completed through: not started")
        if index < len(plans) - 1:
            lines.append("")
    return "\n".join(lines)


def _render_plan_created_text(
    plan: ReadingPlan, store_description: str
) -> str:
    return "\n".join(
        [
            f"Created reading plan {plan.name}",
            f"Plan id: {plan.id}",
            f"Range: {plan.reading_range.label}",
            f"Daily target: {plan.daily_ayah_target} ayahs",
            f"Storage: {store_description}",
            "Privacy: private by default.",
        ]
    )


def _render_plan_today_text(
    result: PlanTodayResult, store_description: str
) -> str:
    lines = [
        f"Plan today: {result.plan.name}",
        f"Plan id: {result.plan.id}",
        f"Plan range: {result.plan.reading_range.label}",
        f"Daily target: {result.plan.daily_ayah_target} ayahs",
        f"Progress: {result.completed_ayahs} of {result.total_ayahs} ayahs completed",
        f"Storage: {store_description}",
        "Privacy: private by default.",
    ]

    if result.completed or result.today_range is None:
        lines.append("Status: Complete")
        return "\n".join(lines)

    remaining_after_today = max(
        result.remaining_ayahs - len(result.today_range.ayahs),
        0,
    )
    lines.append(f"Today's range: {result.today_range.start_reference} to {result.today_range.end_reference}")
    lines.append(f"Ayahs today: {len(result.today_range.ayahs)}")
    lines.append(f"Remaining after today: {remaining_after_today}")
    lines.append("")

    for index, ayah in enumerate(result.today_range.ayahs):
        lines.extend(_render_ayah_block(ayah, include_surah_name=True))
        if index < len(result.today_range.ayahs) - 1:
            lines.append("")

    lines.append("")
    lines.extend(_render_attribution_lines(result.today_range.translation_attribution))
    return "\n".join(lines)


def _render_ayah_block(
    ayah: AyahSelection | SurahResult | object,
    *,
    include_surah_name: bool,
) -> list[str]:
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
