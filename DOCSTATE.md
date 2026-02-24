# DOCSTATE.md — papadam documentation

_Last updated: 2026-02-24. Overwrite this file each loop; do not append._

---

## Status: GREEN

| Doc | Status | Notes |
|---|---|---|
| `docs/docs/index.md` | ✓ current | |
| `docs/docs/howtouse/authentication.md` | ✓ current | |
| `docs/docs/howtouse/dashboard.md` | ✓ current | |
| `docs/docs/howtouse/groups.md` | ✓ current | |
| `docs/docs/howtouse/uploadmedia.md` | ✓ current | |
| `docs/docs/howtouse/annotate.md` | ✓ current | Audio/video types documented; HLS transcoding is transparent — no doc change needed |
| `docs/docs/howtouse/search.md` | ✓ current | |
| `docs/docs/howtouse/exhibits.md` | ✓ current | |
| `docs/docs/admin/create_admin_user.md` | ✓ current | |
| `docs/docs/admin/settings.md` | ✓ current | |
| `docs/mkdocs.yml` | ✓ current | |
| `README.md` | ✓ current | |
| `SETUP.md` | ✓ current | |
| `DEVELOPMENT.md` | ✓ current | |
| `ARCHITECTURE.md` | ✓ updated | Phase 3 audio/video items marked complete |

---

## Delta (this round)

### Updated docs

- `ARCHITECTURE.md`: Phase 3 checklist — audio/video reply annotation items now `[x]`

---

## Gaps

None.

---

## TODO(loop)

| Item | Notes |
|---|---|
| `player_controls.show_waveform` | Phase 5. Marked "coming in a future release" in settings.md. |
| `player_controls.show_transcript` | Phase 5. Marked "coming in a future release" in settings.md. |
| `UIConfig.offline_first` service worker | Phase 5. Marked "coming in a future release" in settings.md. |
| Exhibit publish endpoint | Phase 5. `GET /api/v1/exhibit/{uuid}/publish/` not implemented. |
| Exhibit block drag reorder | Phase 5. ▲/▼ buttons are live; drag is future. Doc describes buttons only. |
