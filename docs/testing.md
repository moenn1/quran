# QuranKit Testing Strategy

The backend scaffold now has a dedicated local test entrypoint:

```bash
./scripts/run-backend-tests.sh
```

The current API test suite covers:

- service metadata at `GET /`
- health reporting at `GET /api/v1/health`
- QuranKit error envelopes for `404`, `405`, and `500` responses
- generated OpenAPI metadata and the published health contract

Future backend issues should extend this foundation with persistence, migration, seed, search, and attribution contract tests as those layers land.
