# DOCSTATE.md — papadam documentation

_Last updated: 2026-02-24. Overwrite this file each loop; do not append._

---

## Status: GREEN

| Doc | Status | Notes |
|---|---|---|
| `docs/docs/index.md` | ✓ current | |
| `docs/docs/howtouse/authentication.md` | ✓ rewritten | Matched to actual SvelteKit UI: "Register" link, Collections redirect, screenshots removed |
| `docs/docs/howtouse/dashboard.md` | ✓ rewritten | Was "Home page" describing groups list. Now "Collections" describing the actual `/groups` page + landing page |
| `docs/docs/howtouse/groups.md` | ✓ rewritten | Removed non-existent group creation UI, group settings, add-users; group management is admin-only via `/nimda/` |
| `docs/docs/howtouse/uploadmedia.md` | ✓ rewritten | Added image upload; Description marked required; button text corrected (Upload Media / Submit) |
| `docs/docs/howtouse/annotate.md` | ✓ rewritten | Removed false waveform claim for audio; matched to actual native audio controls + skip buttons |
| `docs/docs/howtouse/search.md` | ✓ rewritten | Was describing upstream papad search (description, group, annotation, tag sidebar). Now matches actual SearchSort: name, tags, sort |
| `docs/docs/howtouse/exhibits.md` | ✓ current | Updated previous round |
| `docs/docs/admin/create_admin_user.md` | ✓ updated | Fixed typo "intentional" → "intentionally"; removed false "email displayed to users" claim |
| `docs/docs/admin/settings.md` | ✓ updated | show_transcript: removed "coming in a future release" (feature is shipped — derived store + UI wired) |
| `docs/mkdocs.yml` | ✓ updated | Nav: Dashboard → Collections; Upload Audio/Video → Upload Media; Search → Search and Sort |
| `README.md` | ✓ current | |
| `SETUP.md` | ✓ current | |
| `DEVELOPMENT.md` | ✓ current | |
| `ARCHITECTURE.md` | ✓ updated | show_transcript removed from Phase 5 deferred list (feature is shipped) |

_No separate ROADMAP.md — the roadmap lives in the Roadmap section of ARCHITECTURE.md._

---

## Delta (this round)

### Rewritten docs (6)

- `authentication.md`: "Create new account" → "Register"; post-login goes to "Collections" not "main page"; screenshots removed (upstream papad Vue UI)
- `dashboard.md`: renamed from "Home page" to "Collections"; describes actual `/groups` page (flat group card grid) + landing page; removed phantom "Your groups" / "Other public groups" sections
- `groups.md`: removed group creation form, group settings table, and add-users section (none exist in frontend); these are admin-only via `/nimda/`; kept "Customising the workspace" section (correct, links to settings.md)
- `uploadmedia.md`: "audio and video" → "audio, video, and image"; Description marked required (was optional); "Upload" → "Upload Media" / "Submit"; added image format list; described processing states (Queued → Converting → Complete)
- `annotate.md`: removed "The media player shows the waveform" from audio section (no waveform exists; show_waveform is Phase 5); described actual native audio controls + skip buttons
- `search.md`: removed description search, group search, annotation content search, and tag sidebar (none exist in papadam SearchSort); documented actual: name search, tag search (comma-separated), 4 sort options; added "What is not available yet" section

### Updated docs (3)

- `create_admin_user.md`: typo fix; email claim corrected
- `settings.md`: show_transcript "coming in a future release" removed (feature shipped)
- `mkdocs.yml`: nav labels matched to doc content (Dashboard → Collections, Upload Audio/Video → Upload Media, Search → Search and Sort)
- `ARCHITECTURE.md`: show_transcript removed from Phase 5 deferred list

---

## Gaps

None.

---

## TODO(loop)

| Item | Notes |
|---|---|
| Screenshots | All docs have `<!-- TODO(loop) -->` for screenshots. Current images are from upstream papad Vue UI and do not match papadam. Requires running instance to recapture. |
| `player_controls.show_waveform` | Phase 5. Marked "coming in a future release" in settings.md. |
| `UIConfig.offline_first` service worker | Phase 5. Marked "coming in a future release" in settings.md. |
| Exhibit publish endpoint | Phase 5. `GET /api/v1/exhibit/{uuid}/publish/` not implemented. |
| Exhibit block drag reorder | Phase 5. ▲/▼ buttons are live; drag is future. Doc describes buttons only. |
| Icon / voice profile rendering | Phase 5. CSS vars wired; profile-specific UIs pending. Not mentioned in user docs yet (no feature to document). |
| Archive picker: remaining filters | Phase 5. Tags, date range, author, transcript filters not yet built. |
| In-group media type filter | Not in SearchSort. Exists in exhibit picker but not in group archive view. |
