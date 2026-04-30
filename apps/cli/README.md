# QuranKit CLI

Typer-based command-line interface for QuranKit.

The CLI now supports Quran lookup, exact search, similarity-based discovery, private progress tracking, reading plans, bookmarks, notes, and export workflows in both remote API mode and local SQLite mode.

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
- `qurankit config set mode local`
- `qurankit config set state-mode local`
- `qurankit config set state-path ~/.local/share/qurankit/study-state.json`
- `qurankit config set api-token YOUR_TOKEN`
- `qurankit surah 1`
- `qurankit ayah 2:255`
- `qurankit juz 30`
- `qurankit random`
- `qurankit search mercy --limit 5`
- `qurankit semantic guide path --limit 5`
- `qurankit progress`
- `qurankit progress mark 2:255-257`
- `qurankit bookmark add 2:255 --label "Evening review"`
- `qurankit note add 2:255 "Reflect on trust in Allah"`
- `qurankit plan create "Week 1" 1:1-1:7 --daily 2`
- `qurankit plan today --plan "Week 1"`
- `qurankit export progress`
- `qurankit export bookmarks`
- `qurankit export surah 1 --format text --output surah-1.txt`
- Add `--json` to lookup, search, progress, bookmark, note, and plan commands for machine-readable output.
- Add `--translation IDENTIFIER` to override the configured translation.
- Add `--no-translation` to render Arabic text only for that command.

## Backend And State Modes

- `mode=remote`: calls versioned QuranKit HTTP endpoints for surahs, ayahs, juzs, random ayahs, exact search, and semantic similarity search.
- `mode=local`: reads directly from a SQLite file with upstream-style `surahs`, `ayahs`, `editions`, and `ayah_edition` tables.
- `state-mode=local`: saves private progress, plans, bookmarks, and notes to a local JSON file. This is the default.
- `state-mode=remote`: uses authenticated `GET` and `PUT` requests to `/api/v1/me/study` and the configured API token. The database-backed `apps/api` service now implements that document contract; the bootstrap Docker service used by smoke checks still does not.

When translation output is enabled in local mode, the SQLite database must include `editions` metadata and the matching `ayah_edition` rows for the selected identifier.

## Output And Safety Rules

- Quran text is shown exactly as stored in the selected backend.
- Text output includes Quran source attribution and selected translation attribution whenever Quran text is displayed.
- Exact search stays separate from semantic search in both copy and command naming.
- Semantic results are labeled as related passages by textual similarity only. They are not tafsir, fatwa, or religious rulings.
- Progress, bookmarks, notes, and plans remain private by default whether the Quran text backend is local or remote.

## Development Coverage

`./scripts/run-cli-tests.sh` runs the CLI pytest suite against config handling, backend selection, local SQLite queries, private study-state behavior, remote auth expectations, and Typer command output.

`./scripts/smoke-cli.sh` exercises `qurankit --version`, `qurankit config show --format json`, and isolated `config set` persistence through the installed console entrypoint.
