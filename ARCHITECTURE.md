# papadam — Architecture

## Principles

**Backend: highly opinionated.** One way to do everything. No configuration drift.
PostgreSQL only. Redis only. ARQ only. structlog only. JWT only. pytest only.
The dependency graph between Django apps is a first-class contract enforced by the linter.
A new contributor has no infrastructure decisions to make.

**Frontend: highly customizable.** The UI is a rendering engine.
It reads a `UIConfig` from the API and assembles itself — layout, language, interaction model,
icon sets, voice mode, player controls. One codebase serves oral communities, researchers,
archivists, and exhibit curators without custom builds or per-community deployments.

---

## Monorepo Layout

```
papadam/
├── api/            Django REST API (fork of papad-api)
├── ui/             SvelteKit PWA   (fork of custom-ui/custom-ui)
├── crdt/           y-websocket CRDT sync server (new)
├── transcribe/     Whisper transcription worker (new)
├── deploy/         Docker Compose stack (fork of papad-docker)
└── docs/           MkDocs documentation (fork of papad-docs)
```

---

## System Diagram

```
╔══════════════════════════════════════════════════════════════════════════╗
║  CLIENT — SvelteKit PWA                                                  ║
║  ┌────────────┐  ┌───────────┐  ┌──────────┐  ┌─────────────────────┐  ║
║  │ UIConfig   │  │ Y.js+IDB  │  │ HLS.js   │  │ Service Worker      │  ║
║  │ profile:   │  │ offline   │  │ adaptive │  │ offline queue       │  ║
║  │ icon/voice │  │ CRDT      │  │ player   │  │ background sync     │  ║
║  └────────────┘  └───────────┘  └──────────┘  └─────────────────────┘  ║
╠══════╤══════════════════════════════════╤═══════════════════════════════╣
║      │  REST / SSE (HTTPS — reverse proxy)  │  WebSocket                ║
╠══════╪══════════════════════════════════╪═══════════════════════════════╣
║      ▼                                  ▼                               ║
║  ┌─────────────────────────┐  ┌──────────────────────────────────────┐  ║
║  │  api/  Django + DRF     │  │  crdt/  y-websocket server           │  ║
║  │                         │  │  · JWT auth on connect               │  ║
║  │  /api/v1/               │  │  · group membership check → api      │  ║
║  │  /auth/ (simplejwt)     │  │  · Y.js doc load/persist             │  ║
║  │  /api/v1/crdt/          │  │  · Redis pub/sub presence fan-out    │  ║
║  │  /api/v1/events/ (SSE)  │  │                                      │  ║
║  │  /api/v1/exhibit/       │  └──────────────────────────────────────┘  ║
║  │  /api/v1/media_relation/│                                            ║
║  │  structlog JSON stdout  │                                            ║
║  └────────────┬────────────┘                                            ║
╠═══════════════╪═════════════════════════════════════════════════════════╣
║  ┌────────────▼──────┐  ┌────────────────┐  ┌────────────────────────┐ ║
║  │  PostgreSQL 16    │  │  Redis 7       │  │  MinIO                 │ ║
║  │  · all relational │  │  · ARQ queue   │  │  · media files         │ ║
║  │  · YDocState blob │  │  · cache       │  │  · HLS streams         │ ║
║  │  · exhibits       │  │  · sessions    │  │  · waveforms           │ ║
║  │  · media relations│  │  · CRDT pubsub │  │  · transcripts (VTT)   │ ║
║  └───────────────────┘  │  · SSE feeds   │  │  · exhibit assets      │ ║
║                         └────────────────┘  │  · reply media files   │ ║
║                                             └────────────────────────┘ ║
╠═════════════════════════════════════════════════════════════════════════╣
║  WORKERS                                                                 ║
║  ┌──────────────────────────────┐  ┌─────────────────────────────────┐  ║
║  │  bg-app  ARQ worker         │  │  transcribe  (optional profile) │  ║
║  │  · ffmpeg HLS transcode     │  │  · Whisper STT → VTT captions   │  ║
║  │  · waveform generation      │  │  · searchable via annotation API│  ║
║  │  · reply media transcode    │  │                                 │  ║
║  │  · import/export tarballs   │  └─────────────────────────────────┘  ║
║  │  · soft-delete cleanup      │                                        ║
║  │  · SSE progress events      │                                        ║
║  └──────────────────────────────┘                                       ║
╚═════════════════════════════════════════════════════════════════════════╝
```

---

## Backend — Opinionated Constraints

These are enforced by the codebase and CI, not configurable:

| Constraint | Enforcement |
|---|---|
| PostgreSQL only | Startup check rejects non-postgres `DB_URL` |
| Redis only for queue | ARQ hardcoded; no Celery/Huey path |
| structlog JSON stdout | No file handlers, no email handlers |
| No `print()` in source | `ruff T20` rule + pre-commit hook — CI fails |
| JWT + refresh tokens | drf-simplejwt; opaque token support removed |
| pytest, 80% coverage gate | CI fails below threshold |
| drf-spectacular schema | `/api/schema/` always current; drives CRDT client types |
| Dependency graph enforced | `import-linter` contracts in `pyproject.toml` — CI fails on violation |
| Type checking | `mypy` with django-stubs — progressively strict |
| Security scanning | `bandit` on every CI run |
| No circular imports | `import-linter` independence contract across all apps |
| No `pages/` app | Deleted; SvelteKit owns all frontend routing |
| No SQLite | Removed from requirements entirely |

### Changes from papad-api

| Removed | Added/Replaced with |
|---|---|
| Huey + tasks.db | ARQ + Redis |
| Djoser | drf-simplejwt |
| `print()` logging | structlog |
| SQLite default | PostgreSQL only |
| `pages/` app | deleted |
| django-nose | pytest + pytest-django + pytest-cov + pytest-xdist |
| opaque tokens | JWT with refresh |
| black + isort + flake8 | ruff (covers all three + security + no-print) |
| pylint | mypy + django-stubs |
| — | drf-spectacular (OpenAPI) |
| — | import-linter (architecture as code) |
| — | bandit (security scanning) |
| — | `crdt/` app (YDocState model + persistence bridge) |
| — | `events/` app (SSE job progress feed) |
| — | `exhibit/` app (exhibit builder) |
| — | `media_relation/` app (media-to-media annotations + threaded replies) |

### What stays identical

All existing models (Archive, Annotation, Group, Tags, ImportExport), serializers,
viewsets, URL patterns, W3C annotation structure, ffmpeg HLS pipeline,
MinIO/S3 layer, group permission system.

---

## Linting as Architecture

The dependency direction between Django apps is a contract, not a convention.
`import-linter` encodes the allowed graph in `pyproject.toml` and fails CI on violation
— the same way a broken test fails CI.

### Allowed dependency graph

```
common  ←────────────────────────────── new code: no imports from other apps
  ↑                                     legacy debt: functions/serializers/views import
  │                                     archive, annotate, users — exempted in contracts
users   ←────────────────────────────── may not import from archive or above
  ↑
archive ←────────────────────────────── may not import from importexport or new apps
  ↑                                     legacy debt: serializers import annotate — exempted
annotate ←───────────────────────────── may not import from importexport or new apps
  ↑              ↑
exhibit          media_relation ───────  may import: common, users, archive, annotate
crdt    ←────────────────────────────── may import: common, archive, annotate
events  ←────────────────────────────── may import: common only
importexport ←───────────────────────── may import: common, users, archive, annotate
queue   ←────────────────────────────── leaf — may not import from any app
```

New apps strictly enforce the graph. Legacy apps (`common`, `archive`) have pre-existing
cross-imports documented as `ignore_imports` in the contracts — these violations must not grow.
Contracts live in `api/pyproject.toml` under `[tool.importlinter]`.

### Frontend architecture (eslint-boundaries)

The module dependency graph in `ui/` is enforced by `eslint-plugin-boundaries`:

```
api.ts       → leaf (no internal imports — pure HTTP client)
events.ts    → api only
crdt.ts      → may import: stores
config.ts    → may import: api
stores.ts    → may import: config, crdt
i18n/        → leaf
primitives/  → leaf (unstyled components, no business logic)
components/  → may import: api, stores, config, events, i18n, primitives
routes/      → may import: everything
```

A component importing from a route, or `api.ts` importing from `stores`, fails the lint step.

---

## CRDT Layer

### Why Y.js

Mature, production-proven (used by Notion, Linear). Has: SvelteKit bindings,
WebSocket sync server, IndexedDB offline persistence, awareness protocol (presence).
No alternatives considered — opinionated choice.

### Document schema

Each `MediaStore` item maps to one Y.js document, keyed by `media:{uuid}`.

```
YDoc  key="media:{uuid}"
│
├── annotations: Y.Map<uuid, Y.Map>
│     Each annotation Y.Map:
│       uuid              string    immutable
│       annotation_text   Y.Text    collaborative — char-level merge
│       media_target      string    "t=22.5,37"  LWW
│       tags              Y.Array   append-only, deduplicated on read
│       annotation_type   string    "text" | "image" | "audio" | "video" | "media_ref"
│       reply_to          string?   uuid of parent annotation (threaded replies)
│       media_ref_uuid    string?   uuid of referenced MediaStore (media-to-media link)
│       created_by        string    immutable user UUID
│       created_at        string    immutable ISO8601
│       is_delete         boolean   server-authoritative
│
├── metadata: Y.Map
│     name                Y.Text    collaborative
│     description         Y.Text    collaborative
│     tags                Y.Array   OR-Set semantics
│
└── awareness  (ephemeral — never persisted)
      user_id             string
      username            string
      color               string    stable per user
      cursor              number    playback position in seconds
```

### Persistence bridge

Django stores two representations per media item:

1. **Normalized** — existing `Annotation` model rows. Used for search, filter, export, API compatibility.
2. **Binary Y.js state** — `YDocState.binary_state` (bytes). Used for CRDT sync and offline recovery.

Written together in a single transaction. If the normalized write fails, the binary state is not written.

### Offline flow

```
User writes annotation offline
  → Y.js applies to local YDoc immediately (IndexedDB persistence)
  → UI shows annotation instantly (optimistic)
User comes online
  → y-websocket reconnects, sends pending update vector
  → Server merges, responds with remote updates
  → Conflicts resolved by CRDT semantics — no data loss
  → Normalized records written to PostgreSQL
```

### What is NOT CRDT (server-authoritative)

- Group membership (requires authorization)
- Media file upload (binary, sequential)
- HLS/Whisper job status (server owns processing pipeline)
- `is_instance_admin_withheld` / `is_instance_group_withheld` (admin-only)
- User accounts

---

## Media-to-Media Annotations

Any annotation can reference another piece of media as its body,
creating a dialogue graph across the archive.

### Annotation types

| type | body | use case |
|---|---|---|
| `text` | RichText (existing) | Standard text annotation |
| `image` | ImageField → MinIO | Visual callout pinned to a video/audio segment |
| `audio` | FileField → MinIO + HLS | Spoken reply to a recording |
| `video` | FileField → MinIO + HLS | Video response to a media item |
| `media_ref` | FK → MediaStore | Link an existing archive item as a reply |

### Image annotations on video

An annotation with `type: "image"` and a time range `t=start,end` pins an image
to a segment of a video or audio file. The player renders the image as an overlay
during playback of that segment.

### Threaded replies

Annotations carry an optional `reply_to` field (FK → Annotation UUID).
This forms a thread tree on any media item:

```
audio story uploaded by community member A
  └── video reply by member B  (t=30,60 of the original)
        └── text reply by member C
        └── image annotation by member D  (pins a photo to that segment)
  └── audio reply by member E  (t=0,20 of the original)
```

All replies are time-anchored to their parent media segment.
New reply types (audio/video) are transcoded by the existing ffmpeg ARQ pipeline.

### API additions to annotate/

```
POST /api/v1/annotate/                    extended: annotation_type, reply_to, media_ref_uuid
GET  /api/v1/annotate/thread/{uuid}/      full reply tree for an annotation
GET  /api/v1/archive/{uuid}/relations/    all media items that reference this one
```

---

## Exhibit Builder

Exhibits are curated, ordered presentations assembled from items across the archive.
Published as standalone public pages — no auth required to view.

### Data model (`exhibit/` Django app)

```
Exhibit
  uuid, title, description
  group (FK → Group)
  created_by (FK → User)
  is_public
  created_at, updated_at

ExhibitBlock  (ordered list within an Exhibit)
  exhibit (FK), order (int)
  block_type: "media" | "annotation"
  media_uuid (UUID, nullable — references MediaStore)
  annotation_uuid (UUID, nullable — references Annotation)
  caption (text, blank)
```

### Archive picker

The exhibit builder UI presents a full-archive picker that filters by:

- Group
- Tags
- Media type (audio / video / image)
- Date range
- Annotation author
- Transcript content (if transcribe worker enabled)
- Free-text search across all metadata

Each picked item becomes an `ExhibitBlock`. Blocks are reorderable by drag or keyboard.
A block can clip a specific time range, play an annotation in context, or display
a media-to-media thread as a visual dialogue.

### API

```
GET    /api/v1/exhibit/
POST   /api/v1/exhibit/
GET    /api/v1/exhibit/{uuid}/
PUT    /api/v1/exhibit/{uuid}/
PATCH  /api/v1/exhibit/{uuid}/
DELETE /api/v1/exhibit/{uuid}/
GET    /api/v1/exhibit/{uuid}/blocks/
POST   /api/v1/exhibit/{uuid}/blocks/
DELETE /api/v1/exhibit/{uuid}/blocks/{id}/
```

---

## Frontend — UIConfig Customisation System

```typescript
// ui/src/lib/api.ts — authoritative; backend mirrors via common.UIConfig model
interface UIConfig {
  profile: 'standard' | 'icon' | 'voice' | 'high-contrast'
  brand_name: string
  brand_logo_url: string
  primary_color: string         // hex, e.g. "#1e3a5f"
  accent_color: string          // hex
  language: string              // BCP 47 — 'kn', 'hi', 'ta', 'en', etc.
  icon_set: string              // 'default' | custom MinIO URL to icon sprite
  font_scale: number            // 1.0 default, 1.4–1.8 for low-vision
  color_scheme: 'default' | 'warm' | 'cool' | 'high-contrast'
  voice_enabled: boolean
  offline_first: boolean
  player_controls: {
    skip_seconds: [number, number]
    show_waveform: boolean
    show_transcript: boolean
    default_quality: 'low' | 'medium' | 'high' | 'auto'
  }
  annotations_config: {
    allow_images: boolean
    allow_audio: boolean         // voice reply annotations
    allow_video: boolean         // video reply annotations
    allow_media_ref: boolean     // link existing archive items as replies
    time_range_input: 'slider' | 'timestamp' | 'tap'
  }
  exhibit_config: {
    enabled: boolean
  }
  updated_at: string | null
}
```

Config is stored per-group in `common.UIConfig` (Django model, OneToOneField → Group).
`group_extra_questions` is legacy — do not add new config keys there.
One running instance serves all profiles. No custom builds. No per-community deployments.

> **Type-safety:** UIConfig `profile` and `color_scheme` are `TextChoices` enums (not raw strings).
> Frontend UIConfig types are derived from backend field names (snake_case throughout).
> Discriminated union approach for profile switching is deferred to Phase 5 work.

### Interaction profiles

| Profile | Description |
|---|---|
| `standard` | Text labels, keyboard nav, desktop-optimised |
| `icon` | Pictogram-first, culturally swappable icon sets, minimal required reading |
| `voice` | Mic always accessible, annotation starts with recording, Whisper auto-transcribes |
| `high-contrast` | WCAG AAA contrast, 1.5× font scale, no colour-only indicators |

### Frontend module boundary rules (eslint-plugin-boundaries)

```
api.ts        leaf — pure HTTP, no internal imports
events.ts     → api only
crdt.ts       → stores only
config.ts     → api only
stores.ts     → config, crdt
i18n/         leaf
primitives/   leaf — unstyled accessible components (bits-ui wrappers)
components/   → api, stores, config, events, i18n, primitives
routes/       → anything in lib/
```

Violations fail `npm run lint` and the CI lint step.

---

## Test Suite

### Backend (api/)

| Tool | Role | Gate |
|---|---|---|
| pytest | test runner | — |
| pytest-django | Django integration | — |
| pytest-cov | coverage | **80% minimum — CI fails below** |
| pytest-xdist | parallel execution | — |
| pytest-randomly | random test order | catches order-dependent tests |
| factory-boy | model fixtures | — |
| responses | HTTP mock | — |
| ruff | style + security + no-print + async + type-checking + pytest + simplify | CI fails on any violation in new code |
| mypy | type checking | CI fails on errors in new apps |
| import-linter | architecture contracts (10 contracts, 0 broken) | **CI fails on dependency violation** |
| bandit | security scanning | CI warns (errors on HIGH severity) |

Run all checks: `pre-commit run --all-files`

### Frontend (ui/)

| Tool | Role | Gate |
|---|---|---|
| Vitest | unit tests | **80% line/function coverage** |
| @testing-library/svelte | component tests | — |
| Playwright | E2E tests | chromium + firefox + Pixel 5 |
| ESLint + typescript-eslint | style + type rules | CI fails on any error |
| eslint-plugin-boundaries | **architecture contracts** | CI fails on boundary violation |
| svelte-check | Svelte + TS type check | CI fails on errors |
| prettier | formatting | CI fails if not formatted |

Run all checks: `npm run lint && npm run check && npm run test:all`

---

## Infrastructure

### Docker Compose services

| Service | Image | Profile | Notes |
|---|---|---|---|
| `postgres` | postgres:16-alpine | always | healthcheck: pg_isready |
| `redis` | redis:7-alpine | always | AOF persistence enabled |
| `minio` | quay.io/minio/minio | `minio` | healthcheck: /minio/health/live |
| `minio-init` | quay.io/minio/mc | `minio` | creates bucket + sets public policy, exits |
| `api` | build: ../api | always | Django; healthcheck: /healthcheck/; container: papadam-api |
| `bg-app` | build: ../api | always | ARQ worker |
| `crdt` | build: ../crdt | always | y-websocket; healthcheck: /health; container: papadam-crdt |
| `ui` | nginx:stable-alpine | always | serves ui/build/ SPA; container: papadam-ui |
| `caddy` | caddy:2-alpine | `webserver` | standalone HTTPS via Let's Encrypt (alternative to NPM) |
| `transcribe` | build: ../transcribe | `transcribe` | 2GB memory limit |
| `docs` | build: ../docs | `docs` | MkDocs |
| `backup` | postgres-backup-local | `backup` | daily, 7-day + 4-week + 6-month retention |

### Reverse proxy

Two supported options:

**Nginx Proxy Manager (recommended for servers with existing nginx):**
`papadam-api`, `papadam-crdt`, and `papadam-ui` join `nginx_network` (external).
NPM routes `/api/`, `/auth/`, `/nimda/`, `/config.json`, `/healthcheck/` → `papadam-api:8000`;
`/ws/` → `papadam-crdt:1234/` (WebSocket, strips prefix); all else → `papadam-ui:80` (SPA fallback).

**Caddy (`--profile webserver`):**
```
{$DOMAIN} {
    reverse_proxy /api/*     api:8000
    reverse_proxy /auth/*    api:8000
    reverse_proxy /nimda/*   api:8000
    reverse_proxy /config.json  api:8000
    reverse_proxy /ws/*      crdt:1234
    root * /srv/ui
    file_server
    try_files {path} /index.html
    encode gzip
}
```
`DOMAIN` is the only required variable. Let's Encrypt cert provisioning is automatic.

### Runtime config injection

Django serves `GET /config.json` → `{"API_URL": "...", "CRDT_URL": "..."}`.
The SPA fetches this on startup (`src/lib/config.ts`). Set `PUBLIC_API_URL` and `PUBLIC_CRDT_URL` in `service_config.env`.
Local dev: set `VITE_API_URL` + `VITE_CRDT_URL` in `ui/.env.local` instead.

---

## Delta from Original Vision

### Divergence from upstream papad (Janastu/Servelots)

The upstream project is a Django 2.x + Vue 2 SPA for W3C-style community annotation over shared media archives.
papadam preserves the data model (Archive, Annotation, Group, Tags, ImportExport), W3C annotation structure,
ffmpeg HLS pipeline, MinIO/S3 layer, and group permission system exactly — then diverges on every other axis.

| Dimension | upstream papad | papadam |
|---|---|---|
| Annotation types | text only | text, image, audio, video, media_ref |
| Collaborative editing | none | Y.js CRDT + y-websocket + IndexedDB offline |
| Threaded replies | none | `reply_to` FK + media-to-media (`media_relation` app) |
| Exhibits | none | Exhibit builder — curated public presentations |
| UI customisation | per-deployment builds | UIConfig per-group — one codebase, no custom builds |
| Transcription | none | Whisper worker (optional Docker profile, VTT captions) |
| Architecture enforcement | none | import-linter (backend) + eslint-boundaries (frontend) |
| Test coverage gate | no gate | 80% pytest + 80% Vitest, enforced in CI |
| Frontend framework | Vue 2 | SvelteKit 2 + Svelte 5, adapter-static PWA |
| Media player | video.js | HLS.js adaptive bitrate |
| Infrastructure | single compose | multi-profile (transcribe, backup, webserver, docs, minio) |

The REST API is backwards-compatible where endpoints overlap.
The tooling replacements (Huey→ARQ, Djoser→simplejwt, black/isort/flake8→ruff, etc.)
are detailed in the Backend Constraints section above.

### Planned vs shipped

| Feature | Plan | Status | Notes |
|---|---|---|---|
| ARQ + Redis | Phase 1 | ✓ | |
| JWT (drf-simplejwt) | Phase 1 | ✓ | |
| import-linter 10 contracts | Phase 1 | ✓ | |
| PostgreSQL-only | Phase 1 | ✓ | |
| Y.js CRDT annotations | Phase 2 | ✓ | |
| HLS.js adaptive player | Phase 2 | ✓ | |
| Exhibit builder | Phase 2 | ✓ (deepened Phase 4) | Archive picker multi-filter deferred → Phase 5 |
| UIConfig per-group | Phase 2 | ✓ (landed Phase 4) | More complex than estimated — slipped one phase |
| Image overlay annotations | Phase 3 | ✓ | |
| Audio/video reply transcode | Phase 3 | ✓ | Full ARQ pipeline |
| Whisper transcription | Phase 3 | ✓ (landed Phase 4) | Optional worker; VTT wired in player |
| Service worker offline queue | Phase 3 | ☐ | Deferred; y-indexeddb covers basic offline |
| WCAG AA audit | Phase 3 | partial | high-contrast CSS profile + modal fixes shipped; full audit pending |
| icon / voice profiles | Phase 4 | partial | CSS vars + UIConfig wired; full rendering → Phase 5 |
| Block drag/keyboard reorder | Phase 4 | ☐ | Phase 5 |
| ActivityPub federation | Phase 5 | ☐ | As planned |
| Decentralised identity (DID) | Phase 5 | ☐ | As planned |

One addition beyond the original plan: **server-authoritative moderation flags**
(`is_instance_admin_withheld`, `is_instance_group_withheld`) — required once CRDT was in scope,
because CRDT semantics must not control moderation state.

---

## Roadmap

### Phase 1 — Foundation (backend hardening) ✓ COMPLETE
- ARQ + Redis replacing Huey + SQLite — `tasks_compat.py` deleted, all tasks async
- structlog throughout `api/`
- PostgreSQL only (remove SQLite path)
- JWT (drf-simplejwt) replacing Djoser
- ruff (E/W/F/I/B/C4/UP/S/T20/RUF/ASYNC/TCH/PT/SIM/DTZ) + mypy + import-linter + bandit wired to CI
- Automated MinIO bucket init (`minio-init` container)
- Healthchecks on all Docker services
- Caddy replacing nginx for HTTPS
- pytest coverage gate at 80%
- 4 new apps: `events/`, `crdt/`, `exhibit/`, `media_relation/`
- Annotation model extended: `annotation_type`, `reply_to`, `media_ref_uuid`
- import-linter: 10 contracts, all passing (legacy violations documented as exemptions)

### Phase 2 — Frontend rebuild ✓ COMPLETE
- Typed API client (`ui/src/lib/api.ts`) — all endpoints covered
- Full page parity: auth (login/register/logout), groups, media detail, upload, exhibit
- HLS.js player (audio + video, adaptive bitrate)
- SSE progress bar for upload/transcode jobs
- Y.js CRDT annotations (collaborative + offline, y-indexeddb persistence)
- Threaded reply display in AnnotationViewer
- Exhibit viewer + basic exhibit editor
- ESLint + svelte-check + eslint-boundaries wired to CI
- Vitest unit tests (83 tests, 97%+ line coverage) + Playwright E2E smoke
- i18n skeleton (Paraglide, English catalog)
- adapter-static SPA build → `ui/build/` served by nginx container

### Phase 3 — Media depth + inclusivity
- [x] Image overlay annotations during video/audio playback
- [x] Audio + video reply annotation upload UI — raw upload + HLS transcode pipeline wired
- [ ] Whisper transcript display in media player
- [ ] Service worker + offline annotation queue + background sync
- [ ] WCAG AA audit + fixes

### Phase 4 — UIConfig wiring + exhibit gating ✓ COMPLETE
- [x] UIConfig model (`common.UIConfig`, OneToOneField → Group) + `/api/v1/uiconfig/` endpoint
- [x] Seed commands (`seed_dev`, `seed_prod`) — idempotent, env-driven
- [x] Frontend UIConfig store + CSS var application on mount
- [x] Settings page (auth-gated UIConfig editor, live CSS preview)
- [x] Derived stores for all sub-features (`exhibitEnabled`, `allowedAnnotationTypes`, `playerSkipSeconds`, `timeRangeInputMode`)
- [x] Exhibit nav link + routes gated by `exhibit_config.enabled`
- [x] Annotation type filter via `annotations_config.allow_*`
- [x] Skip buttons wired to `player_controls.skip_seconds`
- [x] Tap mode for annotation time range (`annotations_config.time_range_input`)
- [x] Image file upload + `media_ref_uuid` input in annotation modal
- [x] `[data-profile]` / `[data-color-scheme]` HTML attributes + high-contrast / warm / cool CSS
- [x] DOMPurify sanitization on `{@html}` in exhibit viewer
- [ ] Full archive picker (multi-filter: tags, type, date, author, transcript) — Phase 5
- [ ] Block drag/keyboard reorder — Phase 5
- [ ] `icon` and `voice` interaction profiles full rendering — Phase 5

### Phase 5 — Exhibit builder depth + federation (future)
- ActivityPub for cross-instance archive sharing
- Import/export in open formats (building on existing tarball system)
- Decentralised identity (DID) for community members
