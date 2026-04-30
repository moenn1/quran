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

The scaffold exposes:

- `GET /`
- `GET /api/v1/health`
- `GET /docs`
- `GET /openapi.json`

It also now includes:

- SQLAlchemy models for Quran text, translation, attribution, personal reading state, and semantic embedding metadata
- Alembic migrations under `apps/api/alembic`
- a locked-source normalization, validation, load, and export pipeline for the evaluated upstream snapshot

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
