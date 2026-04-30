# QuranKit API

This package contains the initial FastAPI scaffold for QuranKit.

## Local Development

```bash
cd apps/api
python3 -m venv .venv
. .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
uvicorn qurankit_api.main:app --reload
```

The API now exposes:

- `GET /`
- `GET /api/v1/health`
- `GET /api/v1/surahs`
- `GET /api/v1/surahs/{surah_number}`
- `GET /api/v1/surahs/{surah_number}/ayahs`
- `GET /api/v1/ayahs/{reference}`
- `GET /api/v1/ayahs/random`
- `GET /api/v1/juz/{number}`
- `GET /api/v1/hizb/{number}`
- `GET /api/v1/pages/{number}`
- `GET /api/v1/search/exact`
- `GET /api/v1/search/semantic`
- `GET /docs`
- `GET /openapi.json`

It also now includes:

- SQLAlchemy models for Quran text, translation, attribution, personal reading state, and semantic embedding metadata
- Alembic migrations under `apps/api/alembic`
- a locked-source normalization, validation, load, and export pipeline for the evaluated upstream snapshot
- database-backed browse handlers that read normalized surah and ayah data from the configured QuranKit database
- an exact-search API with field filters, edition filters, pagination, and attribution-aware highlights
- a semantic-search API with similarity-only disclaimer wording, scoped filters, optional scores, context references, and source-preserving attribution

Run the backend tests from the repository root with:

```bash
./scripts/run-backend-tests.sh
```

Validate the locked upstream dump from the repository root with:

```bash
./scripts/run-data-validation.sh
```

Load normalized Quran data into the configured database from the repository root with:

```bash
./scripts/run-db-migrations.sh
./scripts/load-quran-data.sh
```

Build SQLite, JSON, and PostgreSQL seed artifacts with:

```bash
./scripts/build-data-artifacts.sh --output-dir .data/exports
```

If `QURANKIT_DATABASE_URL` is not set, the database scripts use `apps/api/.data/qurankit.db`.
The locked upstream archive cache lives at `apps/api/.data/upstream/quran.sql.zip`.
