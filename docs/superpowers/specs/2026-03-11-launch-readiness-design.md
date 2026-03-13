# papadam Launch Readiness — Design Spec

**Date:** 2026-03-11
**Goal:** Deploy papadam to a server for a low-literacy, voice-first community with first-class annotation capability. Standard profile for launch; voice and icon profiles deferred.

---

## Context

papadam is a hard fork of PLASMA/papad — a community media annotation platform. Phases 1-4 are complete: Django 4.2 backend (13 apps, strict mypy, 161 tests), SvelteKit 2 frontend (155 tests), Y.js CRDT sync server, Whisper transcription worker, Docker Compose deployment stack.

All checks green: 0 errors across svelte-check, eslint, vitest, pytest, ruff, mypy, import-linter.

The platform has never been deployed to a real community. This spec covers the work needed to make annotation solid end-to-end and get it in front of users.

---

## Work Items

### 1. Serializer Validation

**Problem:** The annotation create view has validation gaps.
- `reply_to`: silently swallows bad IDs (non-existent, malformed) — sets `None` instead of returning an error.
- `media_ref_uuid`: accepts any string, no existence check, no FK constraint.
- `annotation_type`: validated at the view layer, not the serializer.

**Scope of change:** The `create()` method in `AnnotationCreateSet` currently bypasses the serializer entirely — it reads `request.data` manually, creates objects via `Annotation.objects.create()`, and handles files and `reply_to` inline with `contextlib.suppress`. This is not "move validation" — it is a full rewrite of the create path to go through the serializer.

**Fix:** Rewrite `AnnotationCreateSet.create()` to use `serializer = AnnotationSerializer(data=request.data); serializer.is_valid(raise_exception=True); serializer.save(created_by=request.user)`. Move file handling and tag handling into serializer `create()` override.

Add validation to `AnnotationSerializer`:
- `annotation_type`: `ChoiceField` already exists — verify it rejects invalid values at the serializer level.
- `reply_to`: add `validate_reply_to()` — must reference an existing `Annotation` in the same group. If the parent annotation's `group` is `None`, reject with 400. Bad values return HTTP 400 with a clear message. No silent fallback to `None`.
- `media_ref_uuid`: add `validate_media_ref_uuid()` — keep as `UUIDField` (no FK migration; CRDT layer uses string UUIDs). Query `MediaStore.objects.filter(uuid=value)` and check the user's group membership. Bad values return HTTP 400.

Remove duplicated validation from the view layer once the serializer handles it.

**CRDT persistence path:** The CRDT persistence bridge also writes normalized `Annotation` rows. The same validation constraints (annotation_type, reply_to group scoping, media_ref_uuid existence) must be enforced in the CRDT persistence code. Identify the specific bridge code that writes normalized records and apply the same rules — either by routing through the serializer or by sharing validation logic.

**Tests:**
- Invalid `annotation_type` → 400
- Non-existent `reply_to` → 400 (not silent `None`)
- Malformed `reply_to` (non-numeric) → 400
- `reply_to` pointing to annotation in a different group → 400
- Non-existent `media_ref_uuid` → 400
- `media_ref_uuid` pointing to media in inaccessible group → 400
- Valid `reply_to` and `media_ref_uuid` → 201

---

### 2. Reply Threading

**Problem:** Backend allows arbitrary nesting via `reply_to` FK. Frontend renders only 1 level — replies-to-replies silently vanish (their parent ID doesn't match any root annotation).

**Approach:** Keep the `reply_to` FK (pragmatic papadam extension alongside W3C target structure). The W3C `target` fields (`media_reference_id` + `media_target`) continue to describe what media segment each annotation is about. Threading is carried by `reply_to`. This is not pure W3C but is the correct pragmatic choice — refactoring to pure W3C target-based threading would require data migration and reworking the entire frontend grouping logic with no user-visible benefit.

**Depth constant:** `MAX_REPLY_DEPTH = 2` (0-indexed). This means 3 levels total: root (depth 0), reply (depth 1), reply-to-reply (depth 2). Both backend and frontend reference this constant.

**Backend changes:**
- Add depth validation on create: compute depth by walking the `reply_to` chain (max 3 hops). If the parent annotation is at depth `MAX_REPLY_DEPTH`, reject with HTTP 400.
- Depth computation should be efficient — limit the chain walk to `MAX_REPLY_DEPTH + 1` hops.
- CRDT persistence bridge must enforce the same depth constraint.

**Frontend changes:**
- `AnnotationViewer.svelte`: make `allRepliesFor()` recursive. For each reply, check if it has replies of its own, render with increasing indentation. 3 levels total (depth 0, 1, 2).
- No "Reply" button on annotations at depth 2 (`MAX_REPLY_DEPTH`).
- Replies at all levels show parent context (who they're replying to).

**Tests:**
- Backend: reject annotation at depth 3+
- Backend: allow annotation at depth 0, 1, 2
- Frontend: render 3-level thread correctly
- Frontend: no reply button at max depth

---

### 3. Visual Overhaul — Newspaper Aesthetic + Full API Wiring

**Problem:** The current UI uses a generic card-based layout, and a wiring audit found 17 `api.ts` exports never called from UI code, 2 stores imported but unconsumed, and 4 silent catch blocks. The visual overhaul is the natural place to add the missing UI surfaces so everything ships with the final design language.

**Approach:** Full visual restyling of the standard profile using the frontend-design skill, combined with 6 feature slices that wire every remaining API function into the UI. Each slice ships a complete, newspaper-styled surface. No unstyled intermediate states.

**Design direction:**
- **Typography-driven layout** — strong hierarchy with serif headings, clean sans-serif body, column-based layouts where density warrants it.
- **Media archive as front page** — media items presented like articles: prominent thumbnails, headlines (media name), bylines (uploader), dates.
- **Annotation threads as editorial columns** — annotations alongside media like reader letters or marginalia, not a flat comment list.
- **Exhibit viewer as feature spread** — curated exhibits feel like magazine pages, not slideshows.
- **Ink-on-paper palette** — warm whites, dark greys, minimal color. UIConfig brand colors as accent only (like a newspaper masthead).
- **Dense but readable** — more content per screen, whitespace and typography for separation instead of boxes and borders.

**Constraints:**
- Must still respect UIConfig system (brand colors, font scale, color scheme, high-contrast).
- Must work on mobile (the community uses phones).
- Tailwind CSS — no new CSS framework.

**This item will use the frontend-design skill for detailed mockups and implementation.**

#### Wiring Slice 1 — Dead Export Cleanup

Code-only, no UI change.

- Remove `crdt.loadState`, `crdt.saveState` from `api.ts` — CRDT sync goes through websocket; the REST endpoints are consumed by the CRDT server, not the browser.
- Remove `auth.refresh` from `api.ts` — the 401 interceptor calls `http.post` directly; the named export is dead code.
- Update `api.test.ts` to remove tests for deleted exports.
- Wire `timeRangeInputMode` store in `UploadAnnotationModal.svelte` — branch on `'slider'` / `'timestamp'` / `'tap'` to control time input UI.
- Add `<!-- Phase 5: waveform renderer -->` comment in `MediaPlayer` where `showWaveform` store would gate rendering.

#### Wiring Slice 2 — Reply Fetching + Cross-Media Marginalia

**`mediaRelation.replies`** — wires into `AnnotationViewer.svelte` for 3-level threaded display (complements Chunk 1 threading work).

- On mount: fetch root annotations (`reply_to === null`) via `annotations.byMedia(mediaUuid)`.
- On expand/click of an annotation: call `mediaRelation.replies(uuid)` to lazy-load direct children.
- Recursively fetch one more level for reply-to-replies (depth 3 max). No reply button at max depth.
- Loading state: small inline spinner per thread. Error state: "Couldn't load replies" with retry link.

**`mediaRelation.mediaRefs`** — "See also" section on media detail page (`/groups/[id]/media/[slug]`).

- On mount (after media loads): call `mediaRelation.mediaRefs(mediaUuid)`.
- Desktop: sidebar column styled as newspaper marginalia. Mobile: section below annotations.
- Title: "See also" or "Referenced in".
- Each entry: linked media name, annotation text that created the reference (truncated), navigation link to source media.
- Empty state: section does not render. Error: silent (supplementary content).

#### Wiring Slice 3 — Tag Management + Edit Annotation Modal

**Inline tag chips on `AnnotationViewer`:**

- Each tag as a removable chip ("x" button) → calls `annotations.removeTag(uuid, tagName)`.
- "+" button after last chip opens autocomplete dropdown fed by `tags.list()` (fetched once on first tap, cached for session).
- Selecting a tag calls `annotations.addTag(uuid, tagName)`.
- Optimistic UI: chip appears/disappears immediately, rolls back on API error with brief inline message.
- Add/remove controls auth-gated.

**New `EditAnnotationModal` component:**

- Trigger: pencil icon on each annotation in `AnnotationViewer` (auth-gated).
- On open: calls `annotations.get(uuid)` for fresh state.
- Pre-fills: annotation text, type (read-only — cannot change type), time range (`media_target`), tags.
- Time range input respects `timeRangeInputMode` store (slider / timestamp / tap).
- Submit: `annotations.update(uuid, formData)`.
- On success: update local list, close modal. On error: inline message, don't close.

#### Wiring Slice 4 — Group Management in Settings + Import/Export

**Group management section in `/settings`** (below existing UIConfig form, auth-gated):

- "Collections" heading with list of all groups via `groups.list()`.
- Each row: name, member count, media count, public/private badge.
- Inline "Edit" button → expands form (name, description, is_public toggle) → `groups.update(id, payload)`.
- "Delete" button → confirmation dialog → `groups.delete(id)`.
- "Create collection" form at top → `groups.create(payload)`.
- On success: update list in place. On error: inline message per action.

**Export button on group detail page** (`/groups/[id]`):

- Small "Export" action in page header (auth-gated).
- Calls `importexport.requestExport(groupId)`.
- Inline confirmation: "Export requested — check Settings for status."

**Import/Export request history in `/settings`** (below group management):

- "Import / Export" heading.
- Import: file upload form → `importexport.requestImport(formData)`.
- Request table via `importexport.listRequests()`: request ID, type, status, requested_at, download link (if export complete).
- Auto-refresh: poll every 30 s while any request is not complete.
- Empty state: "No import or export requests yet."

#### Wiring Slice 5 — Global Annotations Route + Enhanced Search

**New `/annotations` route** (newspaper "letters" archive):

- Data: `annotations.list()` with pagination.
- Filters: group (dropdown from `groups.list()`), search text, annotation type, tag.
- Each entry: annotation text (truncated), type badge, tags as chips, author, timestamp, link to source media.
- Pagination: "Load More" (consistent with other list pages).
- Error/loading states: "Failed to load annotations" with retry; spinner on initial load.
- NavBar: add "Annotations" link between "Collections" and "Exhibits" (auth-gated).

**Enhanced `SearchSort` on group detail page:**

- "Media" | "Annotations" toggle — switches search target.
- When "Annotations" active: calls `annotations.list({ group: groupId, search, page })`.
- Results: compact annotation list (text, type badge, link to media detail).
- Default: "Media" tab.

#### Wiring Slice 6 — Silent Failure Fixes

Four silent catch blocks get the same pattern: small inline error message with retry action where content would have been. No toasts, no modals.

| Location | Fix |
|----------|-----|
| `groups/+page.svelte` Load More | "Failed to load more — tap to retry" |
| `groups/[id]/+page.svelte` Load More | Same |
| `exhibits/+page.svelte` Load More | Same |
| `groups/[id]/media/[slug]/+page.svelte` annotation fetch | "Annotations unavailable" with retry |

**Scope — pages/components affected:**
- Media list page (archive front page)
- Media detail page (player + annotation panel + "See also" marginalia)
- Annotation panel (AnnotationViewer, reply threads, inline tag chips, edit trigger)
- Exhibit viewer
- Top navigation / layout shell
- Group selector
- Settings page (group management, import/export sections)
- New: `/annotations` route (global annotation browser)
- New: `EditAnnotationModal` component

**Acceptance criteria:**
- [ ] No hardcoded Tailwind color classes outside brand tokens (wiring-lint passes)
- [ ] Passes mobile viewport test at 375px width (smallest common phone)
- [ ] UIConfig brand colors visible in masthead/header area
- [ ] Typography hierarchy: serif headings, sans-serif body, at least 3 distinct size levels
- [ ] Media list uses column/grid layout, not vertical card stack
- [ ] Annotation panel reads as editorial marginalia, not a comment feed
- [ ] All existing component tests still pass
- [ ] Zero unwired API exports in `api.ts` (every export called from at least one UI file)
- [ ] `timeRangeInputMode` store consumed in annotation time input UI
- [ ] All 4 silent catch blocks replaced with inline error + retry
- [ ] New `EditAnnotationModal` has unit tests
- [ ] Edit annotation modal opens with pre-filled data, submits update, closes on success
- [ ] Reply lazy-loading: expanding a thread fetches and displays child replies
- [ ] "See also" marginalia renders on media detail page when cross-media refs exist
- [ ] Inline tag chips: add and remove tags with optimistic UI updates
- [ ] SearchSort: Media/Annotations toggle switches search target on group detail page
- [ ] `/annotations` route renders and paginates
- [ ] Group CRUD works from `/settings`
- [ ] Import/export request flow works end-to-end

---

### 4. Service Worker — Offline Resilience

**Problem:** Y.js + IndexedDB handles basic offline for CRDT annotations, but:
- Media uploads fail silently when offline.
- The SPA shell isn't cached — no connection = blank page.
- JWT expires while offline — user returns to a logged-out state.

**Approach:** Workbox-based service worker. This is the largest work item — broken into sub-items that can ship incrementally.

**Sub-item 4a: SPA shell precache (ship first — quick win):**
- Precache index.html, JS bundles, CSS, static assets at build time.
- App loads even fully offline.

**Sub-item 4b: Runtime media cache (ship with 4a):**
- Stale-while-revalidate for media assets (HLS segments, thumbnails, images) already fetched.
- Bounded cache size (LRU eviction).

**Sub-item 4c: Offline upload queue (ship after 4a+4b):**
- Failed media uploads (annotation attachments, new media) → IndexedDB queue.
- Service worker retries via Background Sync API on reconnect.
- UI shows queued items with status: pending / syncing / failed.
- Failed items surface a retry/discard option.

**Sub-item 4d: Auth resilience (ship with 4c):**
- Store refresh token accessible to service worker.
- On reconnect, silently refresh JWT before replaying queued requests.
- If refresh token is also expired, surface login prompt — don't silently discard queued uploads.

**Conflict resolution:**
- CRDT annotations: Y.js merge semantics (already handled).
- Media uploads: no conflict (each upload is a new object).
- Metadata edits: CRDT handles this.

**Not included:**
- Offline playback of uncached media (can't cache everything on a phone).
- Peer-to-peer sync between devices.

**Tests:**
- Unit: queue add/retry/discard logic
- Unit: auth token refresh on replay
- E2E: Playwright with simulated offline → go online → verify sync

---

### 5. Deployment Hardening

**Problem:** The Docker Compose stack exists but has never been validated end-to-end from a bare environment.

**Verification checklist:**

- [ ] `seed_prod` creates admin user + first group idempotently — run twice, confirm no errors or duplicates. `seed_prod` reads group name, language, and brand settings from `service_config.env` (or uses sensible defaults). Env vars: `SEED_GROUP_NAME` (default: "Community"), `SEED_GROUP_LANGUAGE` (default: "en"), `SEED_BRAND_NAME` (default: group name), `SEED_BRAND_PRIMARY` (default: "#1e3a5f"), `SEED_BRAND_ACCENT` (default: "#d97706").
- [ ] Full stack comes up from `docker compose --profile webserver --profile minio --profile backup up -d` with only `service_config.env` configured.
- [ ] All healthchecks pass within 60 seconds of startup.
- [ ] Smoke test: upload media → HLS transcode completes (check SSE progress) → annotate with text → reply to annotation → open second browser tab → verify CRDT sync.
- [ ] `restart: unless-stopped` on all services — kill a container, verify it restarts.
- [ ] Backup profile: trigger a backup, wipe postgres volume, restore, verify data is intact.
- [ ] Caddy provisions HTTPS certificate on the target domain.
- [ ] Whisper transcription: upload audio → verify VTT appears and is visible in player.

---

### 6. Deploy

- Provision target server (user's responsibility — this spec doesn't cover infrastructure procurement).
- Clone repo, configure `service_config.env` (secrets, domain, URLs).
- `docker compose --profile webserver --profile minio --profile backup up -d` (add `--profile transcribe` if Whisper is wanted).
- Run `seed_prod` to create admin + first group.
- Verify HTTPS, healthchecks, media upload + transcode + annotation flow.
- Onboard community: create user accounts, upload initial media.

---

## Order of Work

```
1. Serializer validation
2. Reply threading
3. Visual overhaul (newspaper aesthetic + full API wiring)
4. Service worker (offline resilience)
5. Deployment hardening
6. Deploy
```

Items 1-2 are tightly coupled (threading depends on clean validation). Item 3 is independent of 1-2 but should land before deployment — it now includes wiring all remaining API functions into the UI alongside the visual reskin (6 feature slices). Item 4 is independent but the largest piece of work. Item 5 is the final gate before 6.

---

## Out of Scope (Deferred)

- Voice interaction profile
- Icon interaction profile
- Exhibit block drag reorder
- Archive picker advanced filters (tags, date, author, transcript)
- ActivityPub federation
- Decentralised identity (DID)
- Waveform renderer
- WCAG AA full audit
- Monitoring dashboards
- CI/CD pipeline for server
- Multi-tenant / multi-server deployment
