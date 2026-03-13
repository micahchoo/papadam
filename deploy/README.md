# papadam/deploy

Docker Compose stack for papadam.
Fork of [papad-docker](https://gitlab.com/servelots/papad/papad-docker).

---

## Prerequisites

- Docker + Docker Compose v2
- The `ui/build/` directory must exist — run `npm run build` in `ui/` first
- An existing reverse proxy on `nginx_network` (Nginx Proxy Manager recommended), **OR** use the `webserver` profile for standalone Caddy HTTPS

---

## Quickstart

```bash
# 0. Build the SPA (required before first deploy)
cd ../ui && npm install && npm run build && cd ../deploy

# 1. Create env file
cp service_config.env.sample service_config.env
nano service_config.env   # fill in all REQUIRED values

# 2. Ensure the external proxy network exists (NPM creates this automatically;
#    create it manually if using Caddy or a different nginx setup)
docker network create nginx_network 2>/dev/null || true

# 3. Start the stack (NPM / existing nginx setup)
docker compose --profile minio up -d

# 4. Start with standalone Caddy HTTPS (no existing nginx)
docker compose --profile webserver --profile minio up -d
```

---

## Environment file

Copy `service_config.env.sample` to `service_config.env`. Never commit it.

Minimum required values:

| Variable | Description |
|---|---|
| `DJANGO_SECRET_KEY` | Generate: `python -c "import secrets; print(secrets.token_hex(50))"` |
| `POSTGRES_PASSWORD` | Also used in `DB_URL` |
| `MINIO_ROOT_USER` | MinIO admin username |
| `MINIO_ROOT_PASSWORD` | MinIO admin password (min 8 chars) |
| `CRDT_SERVER_TOKEN` | Service-account JWT for CRDT persistence. Generate: `python -c "import secrets; print(secrets.token_hex(32))"` |
| `PUBLIC_API_URL` | Public HTTPS URL for the API, e.g. `https://papad.example.org` |
| `PUBLIC_CRDT_URL` | Public WebSocket URL, e.g. `wss://papad.example.org/ws` |
| `ADMIN_PASSWORD` | Password for the admin user created by `seed_prod` |
| `DOMAIN` | Your domain (Caddy `webserver` profile only) |

---

## Services

| Service | Image | Profile | Notes |
|---|---|---|---|
| `postgres` | postgres:16-alpine | always | healthcheck: pg_isready |
| `redis` | redis:7-alpine | always | AOF persistence |
| `minio` | quay.io/minio/minio | `minio` | healthcheck: /minio/health/live |
| `minio-init` | quay.io/minio/mc | `minio` | auto-creates `papadam` bucket with public policy, then exits |
| `api` | build: ../api | always | Django; healthcheck: /healthcheck/ |
| `bg-app` | build: ../api | always | ARQ background worker |
| `crdt` | build: ../crdt | always | y-websocket CRDT server; healthcheck: /health |
| `ui` | nginx:stable-alpine | always | serves `ui/build/` static SPA |
| `caddy` | caddy:2-alpine | `webserver` | automatic HTTPS (Let's Encrypt) |
| `transcribe` | build: ../transcribe | `transcribe` | Whisper STT worker, 2GB RAM limit |
| `docs` | build: ../docs | `docs` | MkDocs documentation site |
| `backup` | postgres-backup-local | `backup` | daily pg dumps, 7d + 4w + 6m retention |

---

## Networks

The compose file uses two networks:

- `default` — internal only (postgres, redis, api, bg-app, crdt communicate here)
- `nginx_network` — external, shared with your reverse proxy (NPM or other nginx)

`api`, `crdt`, and `ui` join `nginx_network` so the reverse proxy can reach them by container name:
- `papadam-api:8000`
- `papadam-crdt:1234`
- `papadam-ui:80`

The external `nginx_network` must already exist. If using Nginx Proxy Manager, it creates this network automatically.

---

## Nginx Proxy Manager setup

Create one proxy host for your domain with:

- **Backend**: `papadam-ui`, port `80`
- **SSL**: Let's Encrypt or existing cert
- **Advanced** custom nginx config:

```nginx
location /api/ {
    proxy_pass http://papadam-api:8000;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
}
location /auth/ {
    proxy_pass http://papadam-api:8000;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
}
location /nimda/ {
    proxy_pass http://papadam-api:8000;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
}
location /config.json {
    proxy_pass http://papadam-api:8000;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
}
location /healthcheck/ {
    proxy_pass http://papadam-api:8000;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
}
location /ws/ {
    proxy_pass http://papadam-crdt:1234/;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
    proxy_set_header Host $host;
    proxy_read_timeout 86400;
}
```

All other paths fall through to `papadam-ui:80` (SPA with `try_files` → `index.html`).

---

## Seed production data

```bash
docker compose exec api python manage.py seed_prod
```

Creates an admin superuser and a **Community** group with UIConfig. Idempotent — safe to re-run.

Optional `SEED_` env vars in `service_config.env` customise the initial group:
`SEED_GROUP_NAME`, `SEED_GROUP_LANGUAGE`, `SEED_BRAND_NAME`, `SEED_BRAND_PRIMARY`, `SEED_BRAND_ACCENT`.

### Manual admin creation (alternative)

```bash
docker exec -it papadam-api python manage-prod.py createsuperuser
```

Admin site: `https://your-domain/nimda/`

---

## Verify deployment

```bash
curl https://your-domain/healthcheck/
# → {"status": "ok"}

curl https://your-domain/config.json
# → {"API_URL": "https://your-domain", "CRDT_URL": "wss://your-domain/ws"}
```

---

## Optional profiles

```bash
# With Whisper transcription
docker compose --profile minio --profile transcribe up -d

# With automated daily backups
docker compose --profile minio --profile backup up -d

# All optional services
docker compose --profile minio --profile transcribe --profile backup --profile docs up -d
```

---

## Upgrades

```bash
docker compose pull
docker compose --profile minio up -d --build
```
