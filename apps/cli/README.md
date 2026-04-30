# QuranKit CLI

Typer-based command-line interface for QuranKit.

The CLI now supports Quran lookup, exact search, and similarity-based discovery in both remote API mode and local SQLite mode.

It builds on the earlier foundation for configuration storage for remote API and local SQLite modes, including the initial `config show` and `config set` commands.

## Install For Local Development

```bash
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -e 'apps/cli[dev]'
```

The editable install exposes the `qurankit` command and the pytest dependencies used by `./scripts/run-cli-tests.sh`.

`./scripts/smoke-cli.sh` verifies the installed `qurankit` console script itself with a temporary config/data home so release checks cover the packaging path as well as the pytest suite.

## Current Commands

- `qurankit config show`
- `qurankit config show --format json`
- `qurankit config set mode remote`
- `qurankit config set mode local`
- `qurankit config set api-url http://localhost:8000`
- `qurankit config set db-path ~/.local/share/qurankit/qurankit.sqlite3`
- `qurankit config set translation en.sahih`
- `qurankit surah 1`
- `qurankit ayah 2:255`
- `qurankit juz 30`
- `qurankit random`
- `qurankit search mercy --limit 5`
- `qurankit semantic guide path --limit 5`
- Add `--json` to any lookup or search command for machine-readable output.
- Add `--translation IDENTIFIER` to override the configured translation.
- Add `--no-translation` to render Arabic text only for that command.

## Backend Modes

- `remote`: calls versioned QuranKit HTTP endpoints for surahs, ayahs, juzs, random ayahs, exact search, and semantic similarity search.
- `local`: reads directly from a SQLite file with upstream-style `surahs`, `ayahs`, `editions`, and `ayah_edition` tables.

When translation output is enabled in local mode, the SQLite database must include `editions` metadata and the matching `ayah_edition` rows for the selected identifier.

## Output And Safety Rules

- Quran text is shown exactly as stored in the selected backend.
- Text output includes Quran source attribution and selected translation attribution whenever Quran text is displayed.
- Exact search stays separate from semantic search in both copy and command naming.
- Semantic results are labeled as related passages by textual similarity only. They are not tafsir, fatwa, or religious rulings.

## Development Coverage

`./scripts/run-cli-tests.sh` runs the CLI pytest suite against config handling, backend selection, local SQLite queries, remote API mode, and Typer command output.

`./scripts/smoke-cli.sh` exercises `qurankit --version`, `qurankit config show --format json`, and isolated `config set` persistence through the installed console entrypoint.
