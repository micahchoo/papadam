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
| `pytest papadapi/` (full) | 94/94 passed |
| `seed_dev` | runs clean — admin/admin, demo/demo, Demo Community, 6 tags |

---

## Delta (this session — round 11)

### Frontend: settings page — all UIConfig fields now exposed

- `settings/+page.svelte`: Added 9 new state variables (`brandLogoUrl`, `iconSet`, `skipBackward`, `skipForward`, `showWaveform`, `showTranscript`, `defaultQuality`, `allowImages`, `allowAudio`, `allowVideo`, `allowMediaRef`, `timeRangeInput`, `exhibitEnabled`)
- `loadFromStore()` now populates all fields including nested `player_controls`, `annotations_config`, `exhibit_config`
- `save()` PATCH payload now includes all fields: full `player_controls` sub-object (skip_seconds as [backward, forward] tuple), full `annotations_config` sub-object, `exhibit_config`
- Added 3 new fieldsets: **Player** (skip sliders, quality select, waveform/transcript toggles), **Annotations** (time_range_input select, 4 allow_* checkboxes), **Features** (exhibit_config.enabled)
- Added `brand_logo_url` URL input and `icon_set` text input to existing Branding fieldset
- Types: `MediaQuality` and `TimeRangeInput` imported from `$lib/api`; all `$state` calls explicitly typed

### Doc: ARCHITECTURE.md — ExhibitBlock drift corrected

- `ExhibitBlock.block_type`: removed `"text" | "heading" | "divider"` — only `"media" | "annotation"` exist in model + frontend type
- Removed non-existent fields: `media (FK)`, `annotation (FK)`, `text_content`, `start_time`, `end_time`, `display_options` — actual fields are `media_uuid`, `annotation_uuid`, `caption`
- API table: removed `PUT .../blocks/{id}/` (not implemented); removed `GET .../publish/` (not implemented — Phase 5); added `PATCH /api/v1/exhibit/{uuid}/` (exists via UpdateModelMixin)

### Doc: common/serializers.py TODO → TODO(loop)

- Line 109: `# TODO:` → `# TODO(loop):` — marks pre-existing unresolved issue for loop tracking; escalate if survives 3+ rounds

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
| `IsAnnotateCreateOrReadOnly.has_permission()` path-based archive lookup | — | Fragile URL extraction for nested routes. Pre-existing. |
| Full test coverage < 80% (global) | — | Legacy apps (archive, common views, importexport) untested. 80% gate enforced per annotate/ only. |
| ExhibitBlock UUID referential integrity | — | `ExhibitBlockSerializer.validate()` does not verify `media_uuid`/`annotation_uuid` exist. Phase 5. |
| `extra_group_questions` per-group filtering | 1+ | `UpdateGroupSerializer` returns all questions. `# TODO(loop):` in common/serializers.py:109. |
| Exhibit publish endpoint | — | `GET /api/v1/exhibit/{uuid}/publish/` not implemented. Phase 5. |
| Exhibit block drag/keyboard reorder | — | Phase 5. |
| Exhibit archive picker (multi-filter) | — | Phase 5. |
