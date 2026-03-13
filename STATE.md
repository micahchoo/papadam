# papadam — State Dashboard

_Ephemeral metrics snapshot. Updated after every session. For accumulated knowledge (decisions, patterns, conventions), run `mulch prime`._

## Current Metrics

| Check | Result |
|-------|--------|
| `svelte-check` | **1 error** (625 files) — pre-existing `nav_annotations` i18n key missing in NavBar |
| `eslint` | **0 errors, 0 warnings** |
| `vitest run` | **189/189 passed** (6 component test files fail to load — pre-existing vi.mock hoisting) |
| `pytest` | **165/165 passed** (161 prior + 4 new seed_prod tests) |
| `ruff` | **0 violations** |
| `mypy` | **0 errors** (13/13 apps strict) |
| `lint-imports` | **10/10 contracts kept** |
| `npm run build` | **exit 0** — includes `service-worker.js` (17KB) |

## Known Debt

<!-- Only permanent constraints that affect every session. Not session history. -->

- `transcribe_media` worker not covered by pytest (separate process, no test setup)
- `data-voice` attribute set but unconsumed (Phase 5)
- 6 component test files fail to load (vi.mock hoisting issue) — tests within them pass if file loads
- Pre-existing `nav_annotations` i18n key missing (NavBar.svelte:34) — needs message catalog entry
- Annotations route uses placeholder group ID in media links (backend doesn't return group ID on annotations)
- Google Fonts loaded via CSS @import (consider self-hosting for production)

## Last Session

_Overwrite this section each session with: what changed, what was completed, any new gaps._

Launch readiness Tasks 4a–5 completed (Tasks 1–3 were prior session):

- **Task 4a:** SPA shell precache — Workbox `precacheAndRoute` for all build output + static files
- **Task 4b:** Runtime cache — stale-while-revalidate for media (200 LRU, 7d), network-first for API (100 LRU, 1d)
- **Task 4c:** Offline upload queue — Background Sync for POST to annotate/archive, queue status UI in UploadMediaModal, 5 unit tests
- **Task 4d:** Auth token resilience — dual-write JWT to IndexedDB, SW refreshes token before replay, AUTH_EXPIRED message → login redirect, 4 unit tests
- **Task 5:** seed_prod env vars — SEED_GROUP_NAME/LANGUAGE/BRAND_NAME/PRIMARY/ACCENT, default group renamed "Instance" → "Community", update_or_create for UIConfig, 4 backend tests
- Deployment hardening: restart policies verified, SEED_ vars added to env sample
