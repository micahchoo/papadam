# STATE.md — papadam

_Last updated: 2026-02-24. Overwrite this file each loop; do not append._

---

## Status: GREEN

| Check | Result |
|---|---|
| `svelte-check` | 0 errors, 0 warnings (582 files) |
| `eslint` | 0 errors, 0 warnings |
| `vitest run` | 84/85 passed (1 pre-existing config caching flake — not caused by this round) |
| `pytest` | 118/118 passed |
| `ruff` | 0 violations (pre-existing manage-prod.py issues unchanged) |
| `lint-imports` | 10/10 contracts kept |

---

## Delta (this session — round 15: Whisper transcript display)

### Backend

- `papadapi/common/storage.py` — NEW: extracted shared MinIO helpers (`minio_client`, `extract_minio_domain`) — 3rd consumer triggered the extraction (TODO from round 1)
- `papadapi/archive/tasks.py` — import helpers from `common/storage`; remove duplicated `_minio_client` / `_extract_domain`
- `papadapi/annotate/tasks.py` — same; remove duplicated MinIO helpers
- `papadapi/archive/models.py` — add `transcript_vtt_url = URLField(blank=True, default='')`
- `papadapi/archive/migrations/0023_mediastore_transcript_vtt_url.py` — migration
- `papadapi/archive/serializers.py` — add `transcript_vtt_url` to fields
- `papadapi/archive/views.py` — add `MediaStoreTranscriptView` (`POST /api/v1/archive/<uuid>/transcript/` with `X-Internal-Key` auth); add structlog + default_storage imports
- `papadapi/config/common.py` — add `INTERNAL_SERVICE_KEY = env.str("INTERNAL_SERVICE_KEY", "")`
- `papadapi/config/test.py` — add `INTERNAL_SERVICE_KEY = ""` stub
- `papadapi/urls.py` — register `api/v1/archive/<uuid>/transcript/` endpoint
- `papadapi/archive/tests.py` — fix patches to use `minio_client`/`extract_minio_domain`; add 5 new `MediaStoreTranscriptView` tests
- `papadapi/annotate/tests/test_tasks.py` — fix Minio patches to use `minio_client`/`extract_minio_domain`

### Transcribe worker

- `transcribe/worker.py` — implement `transcribe_media(ctx, media_uuid)`:
  - Download media from upload URL via httpx stream
  - Run `whisper.load_model(_WHISPER_MODEL).transcribe()`
  - Convert segments to WebVTT via `_segments_to_vtt()`
  - POST VTT to `/api/v1/archive/<uuid>/transcript/` with `X-Internal-Key`
  - Registered in `WorkerSettings.functions = [transcribe_media]`

### Frontend

- `ui/src/lib/api.ts` — add `transcript_vtt_url: string` to `MediaStore` interface
- `ui/src/lib/stores.ts` — add `showTranscript` derived store from `uiConfig.player_controls.show_transcript`
- `ui/src/lib/components/MediaPlayer.svelte` — add `transcriptUrl?: string` prop; wire `<track kind="captions">` element; `default` attribute set when URL present
- `ui/src/routes/groups/[id]/media/[slug]/+page.svelte` — pass `transcriptUrl` to `MediaPlayer`; add transcript panel controlled by `$showTranscript` UIConfig flag; `loadTranscript()` + `parseVtt()` helpers; lazy-loaded on "Show transcript" button click
- `ui/src/lib/stores.test.ts` — add `transcript_vtt_url: ''` to `MOCK_MEDIA` fixture

---

## Gaps

- Pre-existing Vitest flake: `config.test.ts > loadConfig > is cached` — fetch called 2× instead of 1 due to `api.ts` module init calling `resolveBaseUrl()` on `vi.resetModules()` re-import. Not introduced this round.
- Pre-existing unhandled rejection in `api.test.ts`: `Cannot set properties of undefined (setting 'baseURL')` — `http.defaults` undefined in Vitest environment. Not introduced this round.
- `transcribe_media` worker function is not yet covered by backend tests (transcribe app is separate process with no pytest setup)

---

## Known technical debt / TODO(loop)

| Item | Rounds | Notes |
|---|---|------|
| Raw annotation files not deleted from MinIO after HLS transcode | 1 | TODO(loop) in `annotate/tasks.py`. |
| Pre-existing Vitest config cache flake | 1 | `config.test.ts` — fix requires isolating `api.ts` module init in tests. |
| `[data-profile]` icon/voice rendering | 1→5 | Phase 5. |
| `[data-voice]` TTS / voice UI | 1→5 | Phase 5. |
| `UIConfig.offline_first` service worker | 1→5 | Phase 5. |
| `player_controls.show_waveform` | 4→5 | Phase 5. |
| `player_controls.default_quality` | 4→5 | Phase 5. |
| Tailwind brand color opacity variants | 1 | Phase 5 if needed. |
| `staticfiles.W004` static dir missing | — | Pre-existing. Dev-only warning. |
| ExhibitBlock UUID referential integrity | — | Phase 5. |
| Exhibit publish endpoint | — | Phase 5. |
| Exhibit block drag/keyboard reorder | — | Phase 5. |
