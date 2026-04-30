# QuranKit Testing Strategy

The backend scaffold now has a dedicated local test entrypoint:

```bash
./scripts/run-backend-tests.sh
```

The data pipeline also has dedicated validation and artifact smoke paths:

```bash
./scripts/run-data-validation.sh
./scripts/build-data-artifacts.sh --output-dir .data/exports
```

The current API test suite covers:

- service metadata at `GET /`
- health reporting at `GET /api/v1/health`
- QuranKit error envelopes for `404`, `405`, and `500` responses
- generated OpenAPI metadata and the published health contract
- Alembic migration application against a temporary SQLite database
- ORM-level constraint checks for ayah metadata ranges, translation review gating, privacy defaults, and semantic embedding targeting rules
- Source metadata seed idempotency for the evaluated upstream snapshot
- Locked-source validation, normalized load, and export coverage using a zipped SQL fixture

The current validation workflow checks the real upstream artifact for:

- 114 surahs
- 6236 ayahs
- sequential global ayah numbering
- sequential ayah numbering inside each surah
- expected page, juz, hizb, and rub el hizb ranges
- complete per-edition ayah coverage

Future backend issues should extend this foundation with API handlers, search contracts, and richer attribution assertions as those layers land.
