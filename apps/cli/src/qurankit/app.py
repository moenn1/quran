from __future__ import annotations

import json
from typing import Annotated

import typer

from . import __version__
from .backends import LocalSQLiteBackend, select_backend
from .config import ConfigField, ConfigStore

app = typer.Typer(
    no_args_is_help=True,
    help="QuranKit command-line interface.",
)
config_app = typer.Typer(
    no_args_is_help=True,
    help="Manage QuranKit CLI configuration for remote API or local SQLite usage.",
)
app.add_typer(config_app, name="config")


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


def main() -> None:
    app()
