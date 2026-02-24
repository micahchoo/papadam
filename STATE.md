# STATE.md — papadam

_Last updated: 2026-02-24. Overwrite this file each loop; do not append._

---

## Status: GREEN

| Check | Result |
|---|---|
| `ruff check papadapi/annotate/` | 0 errors |
| `mypy papadapi/annotate/` | 0 errors (pre-existing errors in queue.py unchanged) |
| `lint-imports` | 10/10 contracts kept |
| `svelte-check` | 0 errors, 0 warnings (582 files) |
| `eslint` (new/modified files) | 0 errors |
| `pytest papadapi/annotate/` | 31/31 passed |
| `pytest papadapi/` (full) | 113/113 passed |

---

## Delta (this session — round 13)

### Backend: annotation HLS transcode pipeline

- `annotate/tasks.py`: New ARQ tasks `transcode_annotation_audio` and `transcode_annotation_video`
  - Probe bitrate/resolution via ffprobe, transcode to HLS with ffmpeg, upload to MinIO, overwrite field `.name` to manifest path
  - On ffmpeg failure: field NOT updated — raw file remains playable natively
  - MinIO helpers duplicated from `archive/tasks.py` (YAGNI — `# TODO(loop):` to extract when 3rd consumer appears)
- `annotate/views.py`: `AnnotationCreateSet.create()` enqueues `transcode_annotation_audio`/`transcode_annotation_video` after `m.save()` when audio/video file present
- `annotate/tests/test_tasks.py`: 5 new async tests (audio: 3, video: 2) — all import at top, ruff-clean
- `annotate/tests/test_create_update.py`: 3 new enqueue tests (audio, video, text-no-op) — all import at top, ruff-clean
- `worker.py`: `transcode_annotation_audio` and `transcode_annotation_video` registered in `WorkerSettings.functions`

### Frontend: HLS-capable annotation media player

- `ui/src/lib/components/primitives/AnnotationMedia.svelte`: New primitive — `<audio>`/`<video>` with HLS.js init, same pattern as `MediaPlayer.svelte`
- `ui/src/lib/components/AnnotationViewer.svelte`: Replaced bare `<audio>`/`<video>` elements with `<AnnotationMedia>` for HLS support

### Docs

- `ARCHITECTURE.md` Phase 3 checklist: audio/video reply upload items marked `[x]`

---

## Gaps

None.

---

## Known technical debt / TODO(loop)

| Item | Rounds | Notes |
|---|---|---|
| Raw annotation files not deleted from MinIO after HLS transcode | 1 | TODO(loop) in `annotate/tasks.py`. No bucket cost concern yet. |
| MinIO helpers duplicated in `annotate/tasks.py` | 1 | TODO(loop) to extract when a 3rd consumer appears. |
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
