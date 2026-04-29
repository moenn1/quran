# QuranKit CLI

QuranKit now includes an initial Typer-based CLI scaffold in `apps/cli` under the Python package name `qurankit`.

The current implementation focuses on configuration and backend selection so later reading, search, progress, and export commands can share one stable foundation.

## Install For Local Development

```bash
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -e 'apps/cli[dev]'
```

The editable install exposes the `qurankit` command and the pytest dependencies used by `./scripts/run-cli-tests.sh`.

The repository test entry point prefers `.venv/bin/python` when it exists so local CLI verification and GitHub Actions both run against an explicitly prepared Python environment.

## Current Commands

- `qurankit config show`
- `qurankit config show --format json`
- `qurankit config set mode remote`
- `qurankit config set mode local`
- `qurankit config set api-url http://localhost:8000`
- `qurankit config set db-path ~/.local/share/qurankit/qurankit.sqlite3`
- `qurankit config set translation en.sahih`

## Configuration Storage

- Config file path: `~/.config/qurankit/config.json`
- Local data path default: `~/.local/share/qurankit/qurankit.sqlite3`
- Config home override: `QURANKIT_CONFIG_HOME`
- Data home override: `QURANKIT_DATA_HOME`
- Direct config file override: `QURANKIT_CONFIG_FILE`

`config show` prints the effective settings together with the currently selected backend summary.

## Backend Modes

- `remote`: use a QuranKit HTTP API base URL, defaulting to `http://localhost:8000`
- `local`: use a local SQLite file path for future offline reading and search flows

The local SQLite mode is intentionally described as a storage/backend choice only at this stage. The CLI does not yet ship the surah, ayah, search, progress, or export commands that will consume that database.

## Religious Safety And Privacy

- Show source and translation attribution whenever Quran text or translations are added to command output.
- Keep bookmarks, notes, and reading progress private by default when those commands land.
- Describe semantic search as textual similarity only, never as tafsir, fatwa, or religious ruling.
