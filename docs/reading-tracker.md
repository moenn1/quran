# QuranKit Reading Tracker

The reading tracker is QuranKit's private study-state surface for progress, bookmarks, notes, plans, and related exports.

## Scope

The current CLI already supports:

- progress checkpoints
- bookmarks
- notes
- reading plans
- progress and bookmark exports

Those features should remain one coherent private study-state surface whether the data lives in a local JSON file or a future authenticated API.

## Current Web UI

The web app now exposes private study-state routes for:

- `/progress`
- `/plans`
- `/bookmarks`
- `/notes`
- `/settings`

The current web slice uses the bundled reader sample that already powers `/explore`, `/surah/[number]`, and `/ayah/[surah]/[ayah]`.

The web routes currently support:

- manual progress checkpoints
- overall bundled-sample progress by surah and juz
- active-plan targets and plan recalculation
- bookmark search and label filtering
- private note creation and editing
- reader-default controls for translation visibility, text view, type scale, and reduced motion
- deliberate JSON export previews and local-data clearing

## Privacy Rules

- Reading progress, bookmarks, notes, and plans are private by default.
- Public read APIs must never expose another user's study state.
- Private by default does not mean encrypted. Local filesystem protections still matter.
- Sample deployments and docs should not encourage publishing private study-state data.

## Current CLI Commands

```bash
qurankit progress
qurankit progress mark 2:255-257
qurankit bookmark add 2:255 --label "Evening review"
qurankit note add 2:255 "Reflect on trust in Allah"
qurankit plan create "Week 1" 1:1-1:7 --daily 2
qurankit plan today --plan "Week 1"
qurankit export progress --output exports/progress.json
qurankit export bookmarks --output exports/bookmarks.json
```

Private workflow commands validate ayah references and ranges against the configured Quran backend before they are saved.

## Storage Modes

### Local-First State

`state-mode=local` stores study state in a JSON file, by default:

- `~/.local/share/qurankit/study-state.json`

Relevant overrides:

- `QURANKIT_STATE_MODE`
- `QURANKIT_STATE_PATH`
- `QURANKIT_DATA_HOME`

This is the default and the only fully working storage path in the repository today.

### Web Browser Local State

The web app stores private study state in browser local storage under:

- `qurankit.study-state.v1`

That browser-local snapshot currently includes:

- the core study document (`progress`, `bookmarks`, `notes`, `plans`)
- completed-reference history used for progress dashboards
- the active plan id
- reader preferences such as translation visibility and type scale
- a small local activity timeline for private progress summaries

This browser-local model is still private by default. It is not synced to a server in the current web slice.

### Authenticated Remote State Contract

`state-mode=remote` expects one authenticated document endpoint pair:

- `GET /api/v1/me/study`
- `PUT /api/v1/me/study`

The CLI sends `Authorization: Bearer <token>` using `qurankit config set api-token ...` or `QURANKIT_API_TOKEN`.

The current bootstrap Docker API does not implement `/api/v1/me/study` yet. This is a shared contract for future API work, not a promise that the bootstrap stack already syncs private state.

## Study-State Shape

Illustrative payload:

```json
{
  "state": {
    "progress": {
      "range": {
        "start": { "surah_number": 1, "ayah_number": 1 },
        "end": { "surah_number": 1, "ayah_number": 7 },
        "label": "1:1-7"
      },
      "updated_at": "2026-04-30T00:00:00+00:00",
      "source": "manual_mark"
    },
    "bookmarks": [
      {
        "id": "bookmark-id",
        "range": {
          "start": { "surah_number": 2, "ayah_number": 255 },
          "end": { "surah_number": 2, "ayah_number": 255 },
          "label": "2:255"
        },
        "label": "Evening review",
        "created_at": "2026-04-30T00:00:00+00:00"
      }
    ],
    "notes": [
      {
        "id": "note-id",
        "range": {
          "start": { "surah_number": 2, "ayah_number": 255 },
          "end": { "surah_number": 2, "ayah_number": 255 },
          "label": "2:255"
        },
        "body": "Reflect on trust in Allah",
        "created_at": "2026-04-30T00:00:00+00:00",
        "updated_at": "2026-04-30T00:00:00+00:00"
      }
    ],
    "plans": [
      {
        "id": "plan-id",
        "name": "Week 1",
        "range": {
          "start": { "surah_number": 1, "ayah_number": 1 },
          "end": { "surah_number": 1, "ayah_number": 7 },
          "label": "1:1-7"
        },
        "daily_ayah_target": 2,
        "created_at": "2026-04-30T00:00:00+00:00",
        "updated_at": "2026-04-30T00:00:00+00:00",
        "completed_through": null
      }
    ]
  }
}
```

For the remote contract, treat `PUT /api/v1/me/study` as a full document replacement unless and until the API explicitly documents patch semantics.

The current web app keeps its richer local progress metadata in browser storage so it can power streaks, bundled-sample completion summaries, and reader defaults without implying that the authenticated API already supports those fields.

## Self-Hosting Notes

- Keep the study-state store private by default in all container and deployment examples.
- Do not expose study-state routes without authentication.
- Review `.env.example`, `.env.api.example`, and `.env.web.example` when changing privacy wording.
- Keep [docs/self-hosting.md](self-hosting.md), [docs/api.md](api.md), and [docs/cli.md](cli.md) aligned whenever study-state behavior changes.
- Keep [docs/frontend-architecture.md](frontend-architecture.md) aligned when web study-state flows or browser-local persistence change.

## Limitations Before Release

- The repository's working implementation is local-first, single-user JSON storage.
- The web app currently stores its private study state in browser local storage and previews exports locally; it does not implement authenticated sync.
- Local notes, plans, bookmarks, and progress are private by default, but they are not encrypted by the CLI.
- Remote sync is contract-only until the production API is implemented.
- Exported private data should be handled carefully because JSON exports can be copied outside the user's private storage path.
