# STATE.md — papadam

_Last updated: 2026-02-24. Overwrite this file each loop; do not append._

---

## Status: GREEN

| Check | Result |
|---|---|
| `svelte-check` | 0 errors, 0 warnings (582 files) |
| `eslint` | 0 errors, 0 warnings |
| `vitest run` | 85/85 passed |
| `pytest` | 124/124 passed |
| `ruff` | 0 violations |
| `lint-imports` | 10/10 contracts kept |

---

## Delta (this session — rounds 16–17)

### Round 16: bug & lint squash

- `archive/views.py` — move `log` below imports (E402 x9); remove unused `# noqa: ANN001` (RUF100)
- `annotate/tests/test_tasks.py` — wrap long `patch()` lines (E501 x2)
- `manage.py` + `manage-prod.py` — `-> None`, `# noqa: F401`, `raise ... from exc` (ANN201, PGH004, B904)
- `wait_for_postgres.py` — annotate `pg_isready()` + wrap long log (ANN, E501)
- `ui/src/lib/api.ts` — lazy `ensureBaseUrl()` in interceptor (was eager module-init); fixes Vitest config-cache flake
- `common/storage.py` — add `delete_minio_object()`; annotate/tasks.py deletes raw files after HLS transcode
- `annotate/tests/test_tasks.py` — 2 new raw-file-deletion tests

### Round 17: mediaType filter + exhibit picker upgrade

**Backend:**
- `archive/views.py` — `mediaType` query param (`audio|video|image`) via `file_extension__startswith` filter in `MediaStoreCreateSet.get_queryset`; `frozenset[str]` typed; unknown values silently ignored
- `archive/tests.py` — 4 new TDD tests (audio, video, unknown, absent)

**Frontend:**
- `api.ts` — add `mediaType?: 'audio' | 'video' | 'image'` to `archive.list` params
- `exhibits/[uuid]/edit/+page.svelte` — replace static 100-item `groupMedia` with paginated server-side-filtered picker: `loadPickerMedia(reset)` with type filter (`<select>`), search (`<input>`), "Load more" pagination
- `api.test.ts` — add `defaults: { baseURL: '' }` to mockHttp (defensive; prevents future `Cannot set properties of undefined` if interceptor is invoked)

**Docs:**
- `ARCHITECTURE.md` — Phase 3: `[x] Whisper transcript`; Phase 4: `[x] Archive picker: mediaType + search + pagination`

---

## Gaps

- `_fetch_job_status` coroutine-never-awaited RuntimeWarning in pytest — pre-existing, non-fatal
- `transcribe_media` worker function not covered by backend tests (separate process, no pytest setup)

---

## Known technical debt / TODO(loop)

| Item | Rounds | Notes |
|---|---|------|
| Archive picker: remaining filters (tags, date, author, transcript) | — | Phase 5. |
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
