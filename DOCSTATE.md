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
| `docs/docs/howtouse/exhibits.md` | ✓ updated | Media picker description now matches Phase 4 UI (type filter + search + paginated select + Load more) |
| `docs/docs/admin/create_admin_user.md` | ✓ current | |
| `docs/docs/admin/settings.md` | ✓ updated | Removed "coming in a future release" from Show transcript (shipped Round 15) |
| `docs/mkdocs.yml` | ✓ updated | site_name → papadam; site_description → papadam documentation; stale upstream repo_url removed |
| `README.md` | ✓ current | |
| `SETUP.md` | ✓ current | |
| `DEVELOPMENT.md` | ✓ current | |
| `ARCHITECTURE.md` | ✓ updated | Vitest count 83→85; archive picker filter list corrected to match reality; Phase 5 consolidates all deferred items |

_No separate ROADMAP.md — the roadmap lives in the Roadmap section of ARCHITECTURE.md._

---

## Delta (this round)

### Updated docs

- `docs/docs/admin/settings.md`: Show transcript — removed "(coming in a future release)"; feature shipped in Round 15

---

## Gaps

None.

---

## TODO(loop)

| Item | Notes |
|---|---|
| `player_controls.show_waveform` | Phase 5. Marked "coming in a future release" in settings.md. |
| `UIConfig.offline_first` service worker | Phase 5. Marked "coming in a future release" in settings.md. |
| Exhibit publish endpoint | Phase 5. `GET /api/v1/exhibit/{uuid}/publish/` not implemented. |
| Exhibit block drag reorder | Phase 5. ▲/▼ buttons are live; drag is future. Doc describes buttons only. |
| Icon / voice profile rendering | Phase 5. CSS vars wired; profile-specific UIs pending. Not mentioned in user docs yet (no feature to document). |
| Archive picker: remaining filters | Phase 5. Tags, date range, author, transcript filters not yet built. |
