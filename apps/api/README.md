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

Run the backend tests from the repository root with:

```bash
./scripts/run-backend-tests.sh
```
