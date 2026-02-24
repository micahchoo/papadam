# DOCSTATE.md — papadam documentation

_Last updated: 2026-02-24. Overwrite this file each loop; do not append._

---

## Status: GREEN

| Doc | Status | Notes |
|---|---|---|
| `docs/docs/index.md` | ✓ current | |
| `docs/docs/howtouse/authentication.md` | ✓ current | |
| `docs/docs/howtouse/dashboard.md` | ✓ current | |
| `docs/docs/howtouse/groups.md` | ✓ current | Added Settings reference this round |
| `docs/docs/howtouse/uploadmedia.md` | ✓ current | |
| `docs/docs/howtouse/annotate.md` | ✓ current | Covers all 5 annotation types, CRDT, threaded replies |
| `docs/docs/howtouse/search.md` | ✓ current | |
| `docs/docs/howtouse/exhibits.md` | ✓ NEW | Written this round |
| `docs/docs/admin/create_admin_user.md` | ✓ current | |
| `docs/docs/admin/settings.md` | ✓ NEW | Written this round |
| `docs/mkdocs.yml` | ✓ current | Nav updated to include Exhibits + Settings |
| `README.md` | ✓ current | |
| `SETUP.md` | ✓ current | |
| `DEVELOPMENT.md` | ✓ current | Test SQLite claim is accurate (test.py settings; prod-only constraint is separate) |
| `ARCHITECTURE.md` | ✓ current | |

---

## Delta (this round)

### New docs

- `docs/docs/howtouse/exhibits.md` — how to create/edit/view exhibits; block types;
  create prerequisite (collection must be selected); correct error messages from source
- `docs/docs/admin/settings.md` — all UIConfig settings; field-by-field reference;
  Phase 5 placeholders called out as "coming in a future release"

### Updated docs

- `docs/docs/howtouse/groups.md` — added "Customising the workspace" section linking to admin/settings
- `docs/mkdocs.yml` — added `Exhibits` to How to Use nav; added `Customising the workspace` to Instance Admin nav

---

## Gaps

None.

---

## TODO(loop)

| Item | Notes |
|---|---|
| Block removal button not in exhibit editor UI | `handleDeleteBlock` defined in `edit/+page.svelte` but not wired to any button in the block list template. API and function exist — Phase 5 UI work. Doc correctly omits it. |
| Exhibit block manual reorder | Phase 5. No drag/keyboard UI yet. Doc correctly omits it. |
| Show waveform / show transcript settings | Phase 5. Marked "coming in a future release" in settings.md. |
| Offline-first toggle | Phase 5. Marked "coming in a future release" in settings.md. |
