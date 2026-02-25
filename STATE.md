# papadam — State Dashboard

_Ephemeral metrics snapshot. Updated after every session. For accumulated knowledge (decisions, patterns, conventions), run `mulch prime`._

## Current Metrics

| Check | Result |
|-------|--------|
| `svelte-check` | **0 errors, 0 warnings** (585 files) |
| `eslint` | **0 errors, 0 warnings** |
| `vitest run` | **155/155 passed** |
| `pytest` | **161/161 passed** |
| `ruff` | **0 violations** |
| `mypy` | **0 errors** (13/13 apps strict) |
| `lint-imports` | **10/10 contracts kept** |

## Known Debt

<!-- Only permanent constraints that affect every session. Not session history. -->

- `transcribe_media` worker not covered by pytest (separate process, no test setup)
- Annotation create view bypasses serializer input validation — invalid `annotation_type` values stored without rejection
- Reply threading limited to 1 level in frontend (backend allows arbitrary nesting)
- `data-voice` attribute set but unconsumed (Phase 5)
- 32 UI shadow walk flags remain (mostly Phase 5 scope) — breakdown in mulch: `mulch search "shadow walk"`

## Last Session

_Overwrite this section each session with: what changed, what was completed, any new gaps._

Set up hybrid mulch + STATE.md knowledge management system. Migrated accumulated project knowledge from bloated STATE.md (383 lines) into 28 structured mulch records across 6 domains (architecture, django-api, sveltekit-ui, infrastructure, testing, roadmap). Updated CLAUDE.md loop with mulch prime/learn/record steps.
