# DOCSTATE.md — papadam documentation

_Last updated: 2026-03-12. Overwrite this file each loop; do not append._

---

## Status: GREEN

| Doc | Status | Notes |
|---|---|---|
| `README.md` | ✓ updated | Added service worker to feature table, ADMIN_PASSWORD to quickstart |
| `SETUP.md` | ✓ rewritten | Full deployment guide with SEED_ vars, smoke test, upgrade steps |
| `DEVELOPMENT.md` | ✓ updated | seed_prod group "Instance" → "Community", SEED_ env var table |
| `ARCHITECTURE.md` | ✓ updated | Phase 3 complete, service worker shipped, reply threading resolved, test count 189 |
| `STATE.md` | ✓ updated | Fresh metrics, resolved debt items, last session summary |
| `api/README.md` | ✓ current | |
| `ui/README.md` | ✓ updated | service-worker.js in build output, Workbox in tech stack |
| `deploy/README.md` | ✓ updated | seed_prod section, ADMIN_PASSWORD in required env vars |
| `crdt/README.md` | ✓ current | |
| `transcribe/README.md` | ✓ current | |
| `docs/docs/index.md` | ✓ current | |
| `docs/docs/howtouse/authentication.md` | ✓ current | |
| `docs/docs/howtouse/dashboard.md` | ✓ current | |
| `docs/docs/howtouse/groups.md` | ✓ current | |
| `docs/docs/howtouse/uploadmedia.md` | ✓ current | |
| `docs/docs/howtouse/annotate.md` | ✓ current | |
| `docs/docs/howtouse/search.md` | ✓ updated | Media/Annotations toggle, global annotations page, removed "filter by media type" from not-available |
| `docs/docs/howtouse/exhibits.md` | ✓ current | |
| `docs/docs/admin/create_admin_user.md` | ✓ current | |
| `docs/docs/admin/settings.md` | ✓ updated | Offline-first mode no longer "coming soon" |
| `docs/mkdocs.yml` | ✓ current | |

_No separate ROADMAP.md — the roadmap lives in the Roadmap section of ARCHITECTURE.md._

---

## Delta (this round)

### Rewritten docs (1)

- `SETUP.md`: Was raw CLI output from a conversation. Rewritten as a proper step-by-step deployment guide with env var tables, smoke test checklist, optional profiles, and upgrade instructions.

### Updated docs (8)

- `README.md`: Service worker added to feature comparison table; ADMIN_PASSWORD added to quickstart minimum required vars
- `DEVELOPMENT.md`: Production seed section updated — group default "Instance" → "Community"; added SEED_ env var table
- `ARCHITECTURE.md`: Phase 3 marked complete (service worker shipped); reply threading tech debt resolved; Phase 5 deferred list updated (service worker removed); Vitest count 155 → 189
- `STATE.md`: Full metrics refresh; 3 resolved debt items removed; 3 new known issues added; last session summary
- `ui/README.md`: `service-worker.js` added to build output listing; Workbox added to tech stack table
- `deploy/README.md`: `ADMIN_PASSWORD` added to required env vars; seed_prod section added with SEED_ var docs
- `docs/docs/howtouse/search.md`: Media/Annotations toggle documented; global annotations page section added; "filter by media type" removed from not-available list
- `docs/docs/admin/settings.md`: Offline-first mode description updated from "coming in a future release" to shipped feature

---

## Gaps

None.

---

## TODO(loop)

| Item | Notes |
|---|---|
| Screenshots | All docs have `<!-- TODO(loop) -->` for screenshots. Current images are from upstream papad Vue UI and do not match papadam. Requires running instance to recapture. |
| `player_controls.show_waveform` | Phase 5. Marked "coming in a future release" in settings.md. |
| Exhibit publish endpoint | Phase 5. `GET /api/v1/exhibit/{uuid}/publish/` not implemented. |
| Exhibit block drag reorder | Phase 5. ▲/▼ buttons are live; drag is future. Doc describes buttons only. |
| Icon / voice profile rendering | Phase 5. CSS vars wired; profile-specific UIs pending. Not mentioned in user docs yet (no feature to document). |
| Archive picker: remaining filters | Phase 5. Tags, date range, author, transcript filters not yet built. |
| `nav_annotations` i18n key | Missing from message catalog — causes svelte-check error in NavBar.svelte |
