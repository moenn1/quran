# QuranKit CLI

QuranKit includes a Typer-based CLI in `apps/cli` under the Python package name `qurankit`.

The current CLI covers configuration, Quran lookup, exact search, textual-similarity search, private reading progress, plans, bookmarks, notes, and attribution-aware exports while keeping remote API mode and local SQLite mode behind one consistent command surface.

## Install For Local Development

```bash
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -e 'apps/cli[dev]'
```

The editable install exposes the `qurankit` command and the pytest dependencies used by `./scripts/run-cli-tests.sh`.

`./scripts/run-cli-tests.sh` and `./scripts/smoke-cli.sh` both prefer `.venv/bin/python` when it exists so CLI pytest coverage and installed-entrypoint smoke checks stay on one Python environment.

`./scripts/smoke-cli.sh` verifies the installed `qurankit` console script itself with a temporary config/data home so release checks cover the packaging path as well as the in-process pytest suite.

## Quick Start

```bash
qurankit config show
qurankit surah 1
qurankit search mercy
qurankit semantic guide path
qurankit progress mark 1:1-7
qurankit plan today
```

The CLI is usable in local-first mode now. Remote API mode is already documented, but it expects a future full QuranKit API contract rather than the current bootstrap container.

## Current Commands

### Configuration

- `qurankit config show`
- `qurankit config show --format json`
- `qurankit config set mode remote`
- `qurankit config set mode local`
- `qurankit config set state-mode local`
- `qurankit config set state-mode remote`
- `qurankit config set api-url http://localhost:8000`
- `qurankit config set db-path ~/.local/share/qurankit/qurankit.sqlite3`
- `qurankit config set state-path ~/.local/share/qurankit/study-state.json`
- `qurankit config set translation en.sahih`
- `qurankit config set api-token YOUR_TOKEN`

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

### Private Study Commands

- `qurankit progress`
- `qurankit progress mark 2:255-257`
- `qurankit bookmark`
- `qurankit bookmark add 2:255 --label "Evening review"`
- `qurankit bookmark remove BOOKMARK_ID`
- `qurankit note`
- `qurankit note add 2:255 "Reflect on trust in Allah"`
- `qurankit note remove NOTE_ID`
- `qurankit plan`
- `qurankit plan create "Week 1" 1:1-1:7 --daily 2`
- `qurankit plan today --plan "Week 1"`

### Export Commands

- `qurankit export progress`
- `qurankit export bookmarks`
- `qurankit export surah 1`
- `qurankit export surah 1 --format text --output surah-1.txt`

### Shared Output Controls

- `--json`: return machine-readable JSON instead of formatted text
- `--translation IDENTIFIER`: override the configured translation or text edition for one command
- `--no-translation`: render or search Arabic text only for one command

## Configuration Storage

- Config file path: `~/.config/qurankit/config.json`
- Local Quran data path default: `~/.local/share/qurankit/qurankit.sqlite3`
- Local study-state path default: `~/.local/share/qurankit/study-state.json`
- Config home override: `QURANKIT_CONFIG_HOME`
- Data home override: `QURANKIT_DATA_HOME`
- Direct config file override: `QURANKIT_CONFIG_FILE`
- Quran backend override: `QURANKIT_MODE`
- Study-state mode override: `QURANKIT_STATE_MODE`
- Quran DB path override: `QURANKIT_DB_PATH`
- Study-state path override: `QURANKIT_STATE_PATH`
- Translation override: `QURANKIT_TRANSLATION`
- Remote study-state token override: `QURANKIT_API_TOKEN`

`config show` prints the effective settings together with the selected Quran backend summary and the active private study-state summary.

## Quran Backend Modes

### Remote API Mode

`mode=remote` uses the configured QuranKit HTTP base URL and expects versioned endpoints for:

- `/api/v1/surahs/{surahNumber}`
- `/api/v1/ayahs/{surah}:{ayah}`
- `/api/v1/juzs/{juzNumber}`
- `/api/v1/ayahs/random`
- `/api/v1/search/exact?q=...&translation=...&limit=...`
- `/api/v1/search/semantic?q=...&translation=...&limit=...`

The CLI also builds ayah-range validation from the surah endpoints so plan and progress ranges can be checked before they are saved.

Responses should include Quran source attribution and selected translation attribution whenever Quran text is returned.

The Docker bootstrap API does not implement this contract yet. It only exposes `/` and `/health` for self-hosting smoke checks, so `mode=remote` currently requires a compatible future QuranKit API deployment or a contract-matching stub.

### Local SQLite Mode

`mode=local` reads directly from a SQLite file path.

Minimum tables:

- `surahs`
- `ayahs`

Required when translation output or translation-aware search is enabled:

- `editions`
- `ayah_edition`

If the local file is missing or those tables are absent, the CLI exits with a useful setup error instead of silently creating an empty database.

## Private Study-State Modes

### Local-First State

`state-mode=local` is the default. Progress, plans, bookmarks, and notes are stored in a private JSON file under the configured study-state path.

This local-first path keeps private reading workflows available even when Quran text is being loaded from the remote API.

### Authenticated Remote State

`state-mode=remote` is optional. When enabled, the CLI expects an authenticated QuranKit study-state endpoint at:

- `GET /api/v1/me/study`
- `PUT /api/v1/me/study`

The CLI sends `Authorization: Bearer <token>` using the configured `api-token` or `QURANKIT_API_TOKEN`.

The database-backed `apps/api` service now provides these authenticated study-state endpoints together with register/login, progress, plan, bookmark, note, session, and export routes. The bootstrap Docker API used by Compose smoke checks still does not expose that private surface.

## Ayah Range Format

Private workflow commands accept:

- A single reference, such as `2:255`
- A same-surah shorthand range, such as `2:255-257`
- A spanning range, such as `2:255-3:5`

Ranges are validated against the configured Quran backend before progress, bookmarks, notes, or plans are saved.

## Output Conventions

- `surah`, `ayah`, `juz`, `random`, and `plan today` show Arabic text first and translation second when enabled.
- `search` reports exact matches only and labels where the query matched, such as Arabic text or the selected translation.
- `semantic` reports related passages by textual similarity and includes an explicit guardrail that the results are not tafsir, fatwa, or religious rulings.
- `progress`, `bookmark`, `note`, and `plan` keep wording plainspoken and explicitly private by default.
- `export surah` preserves Quran source attribution and selected translation attribution in both JSON and text output.
- JSON payloads preserve attribution metadata so downstream scripts do not lose source context.

## Example Workflows

### Local-First Reading and Search

```bash
qurankit config set mode local
qurankit config set db-path ~/qurankit/qurankit.sqlite3
qurankit surah 1
qurankit ayah 2:255
qurankit search mercy --limit 10
```

### Remote API Contract

```bash
qurankit config set mode remote
qurankit config set api-url https://api.example.test
qurankit config set translation en.sahih
qurankit search guide --json
```

Use this only against an API that implements the documented `/api/v1/...` contract in [docs/api.md](api.md).

### Private Study Workflow

```bash
qurankit progress mark 2:255-257
qurankit bookmark add 2:255 --label "Evening review"
qurankit note add 2:255 "Reflect on trust in Allah"
qurankit plan create "Week 1" 1:1-1:7 --daily 2
qurankit plan today --plan "Week 1"
```

### Exports

```bash
qurankit export progress --output exports/progress.json
qurankit export bookmarks --output exports/bookmarks.json
qurankit export surah 1 --format text --output exports/surah-1.txt
```

## JSON Shape Highlights

`qurankit progress --json` returns a storage summary together with progress counts:

```json
{
  "storage": {
    "mode": "local",
    "summary": "Private local study state at /home/user/.local/share/qurankit/study-state.json",
    "private_by_default": true
  },
  "progress": null,
  "bookmark_count": 0,
  "note_count": 0,
  "plan_count": 0
}
```

## Religious Safety And Privacy

- Show Quran text exactly as stored in the selected backend.
- Show source and translation attribution whenever Quran text or translations are returned.
- Keep exact search and semantic search distinct in both command names and output wording.
- Describe semantic search as textual similarity only, never as tafsir, fatwa, or religious ruling.
- Keep bookmarks, notes, and reading progress private by default.

## Limitations and Operational Notes

- `mode=remote` is contract-ready, but the repository's current Docker bootstrap API only proves `/` and `/health`.
- `state-mode=remote` requires an authenticated `/api/v1/me/study` implementation and a valid bearer token.
- `mode=local` expects a prepared SQLite file with `surahs` and `ayahs`, and also `editions` plus `ayah_edition` when translation-aware output is enabled.
- Local private study state is stored as a JSON file under the configured study-state path. Private by default does not mean encrypted, so local filesystem permissions still matter.
- The CLI's local semantic-search baseline currently uses textual-overlap heuristics over Arabic text and the selected translation. Future service implementations may change ranking internals without changing the user-facing disclaimer.

## Related Docs

- [docs/api.md](api.md)
- [docs/semantic-search.md](semantic-search.md)
- [docs/reading-tracker.md](reading-tracker.md)
- [docs/self-hosting.md](self-hosting.md)
