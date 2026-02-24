# STATE.md — papadam

_Last updated: 2026-02-24. Overwrite this file each loop; do not append._

---

## Status: GREEN

| Check | Result |
|---|---|
| `ruff check api/` | 0 errors |
| `mypy` (new files) | 0 errors |
| `lint-imports` | 10/10 contracts kept |
| `django check` | 0 errors, 1 silenced warning (static dir missing — dev-only) |
| `svelte-check` | 0 errors, 0 warnings (581 files) |
| `eslint` | 0 errors, 0 warnings |
| `pytest papadapi/annotate/` | 23/23 passed |
| `pytest papadapi/` (full) | 87/87 passed |
| `seed_dev` | runs clean — admin/admin, demo/demo, Demo Community, 6 tags |

---

## Delta (this session — round 9)

### Backend: legacy users tests deleted + users/test/ rectified

- `papadapi/users/test/test_serializers.py` — deleted: referenced `CreateUserSerializer` (removed Phase 1a) and `user-list`/`user-detail` URL names (never registered)
- `papadapi/users/test/test_views.py` — deleted: same issues + used DRF `Token` auth which was replaced by simplejwt

### Backend: 4 media_relation tests added

- `test_create_reply_404_for_unknown_parent` — POST reply to non-existent annotation → 404
- `test_create_reply_defaults_to_text_type` — no annotation_type → stored as "text"
- `test_create_reply_inherits_media_reference_id` — reply inherits parent's media_reference_id
- `test_create_reply_sets_created_by` — reply.created_by == authenticated user

### Backend: 3 pre-existing bugs fixed

- `exhibit/serializers.py ExhibitWriteSerializer`: added `uuid` as read_only field — create response now includes uuid (test `test_exhibit_create` was failing with `assert "uuid" in resp.data`)
- `exhibit/views.py`: merged `add_block` + `list_blocks` into single `blocks` action (`methods=["get", "post"]`, `url_path="blocks"`) — two `@action` decorators with same `url_path` caused DRF to route only the first to the URL, giving GET → 405 (`test_list_blocks` was failing)
- `crdt/views.py CrdtServerTokenAuthentication`: added `authenticate_header()` returning `'Bearer realm="api"'` — DRF was downgrading 401 to 403 when the first authenticator had no `authenticate_header` method (`test_crdt_requires_auth` was failing)

### Backend: permissions + ruff fixes

- `annotate/permissions.py IsAnnotateCreateOrReadOnly.has_permission()`: use `_to_uuid()` helper for the `MediaStore.objects.get()` call — handles URL-format `media_reference_id` without `ValidationError`; wrap in `try/except MediaStore.DoesNotExist`; return `True` for SAFE_METHODS on unknown IDs (matches pre-existing `"annotate"` sentinel behaviour)
- `pyproject.toml`: added `ANN101` to global `ignore` — rule is deprecated in ruff 0.6.9 (type checkers infer `self` automatically; will be removed in future ruff)
- `common/migrations/0013_uiconfig.py`: fixed I001 import order
- `annotate/tests/test_signals.py`: fixed 2 E501 lines (extract `texts` variable; split long kwarg line)

### Frontend: AnnotationViewer delete UX fixed

- `AnnotationViewer.svelte`: added `onAnnotationDeleted?: (id: number) => void` to Props; `deleteAnno()` now calls `onAnnotationDeleted?.(annotation.id)` instead of `window.history.back()`
- `groups/[id]/media/[slug]/+page.svelte`: added `handleAnnotationDeleted(id)` function (filters annotation from `annotations` state); passes `onAnnotationDeleted={handleAnnotationDeleted}` to `<AnnotationViewer>` — the `{#key annotations}` block re-renders on array change

---

## Gaps

None.

---

## Known technical debt / TODO(loop)

| Item | Rounds | Notes |
|---|---|---|
| ARQ transcoding for `annotation_audio` / `annotation_video` | 3 | Fields exist, view saves files, no ARQ convert task. Phase 5. |
| `[data-profile]` icon/voice rendering | 1→5 | Phase 5 design work first. |
| `[data-voice]` TTS / voice UI | 1→5 | Phase 5. |
| `UIConfig.offline_first` service worker | 1→5 | Phase 5. |
| `player_controls.show_waveform` | 4→5 | Phase 5. |
| `player_controls.show_transcript` | 4→5 | Phase 5. |
| `player_controls.default_quality` | 4→5 | Phase 5. |
| Tailwind brand color opacity variants | 1 | Phase 5 if needed. |
| `staticfiles.W004` static dir missing | — | Pre-existing. Dev-only warning. |
| `IsAnnotateCreateOrReadOnly.has_permission()` path-based archive lookup | — | Extracts archive ID from URL path last segment; fragile for nested routes. Pre-existing. |
| Full test coverage < 80% (global) | — | Legacy apps (archive, common views, importexport) untested. Coverage gate only enforced per annotate/ for now. |
