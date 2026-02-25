# CLAUDE.md

> Confirm which sections below apply before writing any code.

## Loop (mandatory)

ORIENT → BUILD → TEST → RECTIFY → SYNC. No skipping.

- **ORIENT**: Read STATE.md (metrics). Run `mulch prime` (domain knowledge) — or `mulch prime --files <paths>` when scoped to specific files. Read ARCHITECTURE.md/ROADMAP.md on phase transitions or gaps.
- **BUILD**: Implement.
- **TEST**: Write/update tests.
- **RECTIFY**: Lint, type-check, fix.
- **SYNC**: Overwrite STATE.md metrics (run all checks, record numbers). Run `mulch learn` to see what changed, then `mulch record <domain>` for any new convention, pattern, failure, or decision discovered during the session. Update ROADMAP/ARCHITECTURE only on structural changes.
- **Exit**: zero gaps, clean types, green tests, no pending migrations.

## Types

No `any` without `// TYPE_DEBT: <reason>`. Single source of truth. Narrow first. Schema changes → typed reversible tested migrations first. Unresolvable → `// TODO(loop):`.

## Tests

Encode contracts, not implementations.

- **Stub check**: trivial stub passes → test is too weak.
- **No magic literals**: assert relationships, not hardcoded values.
- **≥1 adversarial case per file**: empty, max, malformed, concurrent.
- **Names = spec**: `rejects negative quantities` not `test_3`.
- **Don't test compiler guarantees.**

## Lint

Bug fix → can a **project-wide** rule prevent this **category** everywhere? Yes → add it now. Prefer structural rules. `TODO(loop)` at 3+ rounds → escalate.

## Docs (when applicable)

One task per doc: does → how → expect → troubleshoot. User's words. Walk it as a new user. Changed in app → changed in docs same round. Delete docs that restate types.

## UI (when applicable)

**Wiring**: Trace render → data source. Wire types end-to-end. Lint for: missing props, unhandled loading/error, stale subscriptions.

**Shadow**: Walk every user-facing flow through the code as a first-time user. Don't suggest fixes — report what the user experiences.

- For each flow: what renders first → what can the user do → trace handler → state → re-render → what if they do nothing → what if they do it wrong.
- Happy path first, then sad, then weird (back button, refresh, double-click, slow network). Branch on roles/flags → walk each.
- Flag: DEAD END (no obvious action) · SILENT FAIL (error caught, not shown) · NO FEEDBACK (state changes invisibly) · ASSUMPTION (jargon, unlabelled inputs) · RACE (stale data, flash states) · NAV TRAP (loses state) · HIDDEN REQ (validation only on submit).
- Every claim → file:line. Every flag → can a test or lint rule catch it permanently? Add it.
- Report per flow in STATE.md: entry, steps, issues with category and location.

**UI tests**: Assert user-visible outcomes only. Never DOM structure, CSS classes, or component internals.