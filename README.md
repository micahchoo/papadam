# papadam

Participatory Archive for Participatory Action — a community media annotation,
media-to-media dialogue, and exhibit platform for low-connectivity, low-literacy communities.

Hard fork of [PLASMA/papad](https://gitlab.com/servelots/papad) by [Janastu/Servelots](https://janastu.org).

---

## Get started

| I want to...                  | Guide                                                                            |
| ----------------------------- | -------------------------------------------------------------------------------- |
| Deploy papadam on a server    | [SETUP.md](./SETUP.md) — step-by-step Docker deployment with Nginx Proxy Manager |
| Run papadam on my own machine | [DEVELOPMENT.md](./DEVELOPMENT.md) — local dev with hot-reload                   |
| Understand the architecture   | [ARCHITECTURE.md](./ARCHITECTURE.md) — system design, constraints, roadmap       |

---

## What papadam adds over papad

| Feature                                                             | papad | papadam    |
| ------------------------------------------------------------------- | ----- | ---------- |
| Text annotations on media                                           | ✓     | ✓          |
| Image annotations pinned to video/audio segments                    | —     | ✓          |
| Audio/video reply annotations                                       | —     | ✓          |
| Threaded annotation replies (media-to-media dialogue)               | —     | ✓          |
| CRDT collaborative + offline annotation                             | —     | ✓          |
| Exhibit builder with full-archive picker                            | —     | ✓          |
| UIConfig per-group UI customisation (icon/voice/standard profiles)  | —     | ✓          |
| Whisper auto-transcription                                          | —     | ✓ optional |
| Automatic HTTPS (Caddy)                                             | —     | ✓          |
| Architecture enforced by linter (import-linter + eslint-boundaries) | —     | ✓          |
| 80% test coverage gate in CI                                        | —     | ✓          |
| Automated MinIO bucket init                                         | —     | ✓          |
| Automated daily backups                                             | —     | ✓ optional |

---

## Forks

| Directory     | Forked from                                                                     | Original license |
| ------------- | ------------------------------------------------------------------------------- | ---------------- |
| `api/`        | [papad-api](https://gitlab.com/servelots/papad/papad-api)                       | AGPLv3           |
| `ui/`         | [custom-ui-papad](https://github.com/Aruvu-collab/custom-ui-papad) `custom-ui/` | AGPLv3           |
| `deploy/`     | [papad-docker](https://gitlab.com/servelots/papad/papad-docker)                 | AGPLv3           |
| `docs/`       | [papad-docs](https://gitlab.com/servelots/papad/papad-docs)                     | CC-BY-SA 4.0     |
| `crdt/`       | new                                                                             | AGPLv3           |
| `transcribe/` | new                                                                             | AGPLv3           |

---

## Services

| Service | Stack | Notes |
|---|---|---|
| `api/` | Python 3.12 · Django 4.2 · DRF · PostgreSQL 16 · ARQ · Redis | [api/README.md](./api/README.md) |
| `ui/` | SvelteKit 2 · Svelte 5 · TypeScript · HLS.js · Y.js · Paraglide | — |
| `crdt/` | Node.js · TypeScript · y-websocket · Redis pub/sub | [crdt/README.md](./crdt/README.md) |
| `transcribe/` | Python · Whisper · ARQ | [transcribe/README.md](./transcribe/README.md) · optional profile |
| `deploy/` | nginx · Caddy (optional) · PostgreSQL 16 · Redis 7 · MinIO | — |
| `docs/` | MkDocs | — |

---

## Quickstart

```bash
# 1. Build the SPA
cd ui && npm install && npm run build && cd ..

# 2. Create env file
cp deploy/service_config.env.sample deploy/service_config.env
# edit — minimum required: DJANGO_SECRET_KEY, POSTGRES_PASSWORD, MINIO_ROOT_USER,
#         MINIO_ROOT_PASSWORD, CRDT_SERVER_TOKEN, PUBLIC_API_URL, PUBLIC_CRDT_URL

cd deploy

# With Nginx Proxy Manager (existing nginx on nginx_network):
docker compose --profile minio up -d

# Standalone HTTPS via Caddy (no existing nginx — also set DOMAIN in env file):
docker compose --profile webserver --profile minio up -d
```

With Whisper transcription and daily backups:

```bash
docker compose --profile minio --profile transcribe --profile backup up -d
```

---

## Development

### Backend (api/)

```bash
cd api
python -m venv .venv && source .venv/bin/activate
pip install -r requirements/requirements-dev.txt

# Run tests
pytest

# Lint (style + security + architecture contracts)
ruff check .
mypy papadapi/
lint-imports          # enforces dependency direction between Django apps
bandit -r papadapi/

# All checks at once (also run by pre-commit)
pre-commit run --all-files
```

### Frontend (ui/)

```bash
cd ui
npm install

npm run dev           # dev server
npm run check         # svelte-check + TypeScript
npm run lint          # ESLint (includes architecture boundary enforcement)
npm test              # Vitest unit tests
npm run test:e2e      # Playwright end-to-end tests
npm run test:all      # unit + e2e
```

### CRDT server (crdt/)

```bash
cd crdt
npm install
npm run dev
```

---

## Architecture

See [ARCHITECTURE.md](./ARCHITECTURE.md) for the full system design:

- Opinionated backend constraints
- CRDT layer (Y.js document schema, persistence bridge, offline flow)
- Media-to-media annotation model (image/audio/video replies, threaded dialogue)
- Exhibit builder (data model, archive picker, API)
- UIConfig customisation system (icon/voice/standard/high-contrast profiles)
- Linting as architecture (import-linter contracts + eslint-boundaries)
- Infrastructure (Caddy, Docker Compose profiles, automated MinIO init, backups)
- Roadmap (5 phases)

---

## License

AGPLv3 — see [LICENSE](./LICENSE).
Documentation: CC-BY-SA 4.0.
