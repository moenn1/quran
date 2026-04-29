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
- a source metadata seed module for the evaluated upstream snapshot

Run the backend tests from the repository root with:

```bash
./scripts/run-backend-tests.sh
```

Run the initial database bootstrap from the repository root with:

```bash
./scripts/run-db-migrations.sh
./scripts/seed-source-metadata.sh
```

If `QURANKIT_DATABASE_URL` is not set, these scripts use `apps/api/.data/qurankit.db`.
