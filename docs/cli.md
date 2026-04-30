# QuranKit CLI

QuranKit includes a Typer-based CLI in `apps/cli` under the Python package name `qurankit`.

The current CLI covers configuration, Quran lookup, exact search, and textual-similarity search while keeping remote API mode and local SQLite mode behind one consistent command surface.

## Install For Local Development

```bash
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -e 'apps/cli[dev]'
```

The editable install exposes the `qurankit` command and the pytest dependencies used by `./scripts/run-cli-tests.sh`.

`./scripts/smoke-cli.sh` verifies the installed `qurankit` console script itself with a temporary config/data home so release checks cover the packaging path as well as the in-process pytest suite.

## Current Commands

### Configuration

- `qurankit config show`
- `qurankit config show --format json`
- `qurankit config set mode remote`
- `qurankit config set mode local`
- `qurankit config set api-url http://localhost:8000`
- `qurankit config set db-path ~/.local/share/qurankit/qurankit.sqlite3`
- `qurankit config set translation en.sahih`

### Quran Lookup

- `qurankit surah 1`
- `qurankit ayah 2:255`
- `qurankit juz 30`
- `qurankit random`

### Search

- `qurankit search mercy`
- `qurankit search guide path --limit 10`
- `qurankit semantic guide path`
- `qurankit semantic steadfast mercy --limit 8`

### Shared Output Controls

- `--json`: return machine-readable JSON instead of formatted text
- `--translation IDENTIFIER`: override the configured translation or text edition for one command
- `--no-translation`: render or search Arabic text only for one command

## Configuration Storage

- Config file path: `~/.config/qurankit/config.json`
- Local data path default: `~/.local/share/qurankit/qurankit.sqlite3`
- Config home override: `QURANKIT_CONFIG_HOME`
- Data home override: `QURANKIT_DATA_HOME`
- Direct config file override: `QURANKIT_CONFIG_FILE`

`config show` prints the effective settings together with the currently selected backend summary.

## Backend Modes

### Remote API Mode

`remote` mode uses the configured QuranKit HTTP base URL and expects versioned GET endpoints for:

- `/api/v1/surahs/{surahNumber}`
- `/api/v1/ayahs/{surah}:{ayah}`
- `/api/v1/juzs/{juzNumber}`
- `/api/v1/ayahs/random`
- `/api/v1/search/exact?q=...&translation=...&limit=...`
- `/api/v1/search/semantic?q=...&translation=...&limit=...`

Responses should include Quran source attribution and selected translation attribution whenever Quran text is returned.

### Local SQLite Mode

`local` mode reads directly from a SQLite file path.

Minimum tables:

- `surahs`
- `ayahs`

Required when translation output or translation-aware search is enabled:

- `editions`
- `ayah_edition`

If the local file is missing or those tables are absent, the CLI exits with a useful setup error instead of silently creating an empty database.

## Output Conventions

- `surah`, `ayah`, `juz`, and `random` show Arabic text first and translation second when enabled.
- `search` reports exact matches only and labels where the query matched, such as Arabic text or the selected translation.
- `semantic` reports related passages by textual similarity and includes an explicit guardrail that the results are not tafsir, fatwa, or religious rulings.
- JSON payloads preserve attribution metadata so downstream scripts do not lose source context.

## Religious Safety And Privacy

- Show Quran text exactly as stored in the selected backend.
- Show source and translation attribution whenever Quran text or translations are returned.
- Keep exact search and semantic search distinct in both command names and output wording.
- Describe semantic search as textual similarity only, never as tafsir, fatwa, or religious ruling.
- Keep bookmarks, notes, and reading progress private by default when those commands land later.
