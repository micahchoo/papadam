# Production Deployment

## Prerequisites

- A server with Docker and Docker Compose v2
- A domain pointed at the server (for automatic HTTPS via Caddy)
- OR an existing reverse proxy (Nginx Proxy Manager) on the server

---

## 1. Clone and configure

```bash
git clone <your-repo-url> papadam && cd papadam
```

Build the SPA:

```bash
cd ui && npm install && npm run build && cd ..
```

Create the environment file:

```bash
cd deploy
cp service_config.env.sample service_config.env
```

Edit `service_config.env` — fill in all values marked `REQUIRED`:

| Variable | How to generate |
|---|---|
| `DJANGO_SECRET_KEY` | `python3 -c "import secrets; print(secrets.token_hex(50))"` |
| `POSTGRES_PASSWORD` | Choose a strong password (also used in `DB_URL`) |
| `MINIO_ROOT_USER` | MinIO admin username |
| `MINIO_ROOT_PASSWORD` | MinIO admin password (min 8 chars) |
| `CRDT_SERVER_TOKEN` | `python3 -c "import secrets; print(secrets.token_hex(32))"` |
| `PUBLIC_API_URL` | Public HTTPS URL, e.g. `https://papad.example.org` |
| `PUBLIC_CRDT_URL` | WebSocket URL, e.g. `wss://papad.example.org/ws` |
| `ADMIN_PASSWORD` | Password for the admin user |
| `DOMAIN` | Your domain (Caddy profile only) |

### Community branding (optional)

Set these to customise the initial group created by `seed_prod`:

| Variable | Default | Description |
|---|---|---|
| `SEED_GROUP_NAME` | `Community` | Group name |
| `SEED_GROUP_LANGUAGE` | `en` | BCP 47 language tag (e.g. `kn`, `hi`, `ta`) |
| `SEED_BRAND_NAME` | same as group name | Shown in the navigation masthead |
| `SEED_BRAND_PRIMARY` | `#1e3a5f` | Primary brand colour |
| `SEED_BRAND_ACCENT` | `#d97706` | Accent colour |

---

## 2. Start the stack

**With standalone Caddy HTTPS (no existing reverse proxy):**

```bash
docker compose --profile webserver --profile minio --profile backup up -d
```

**With existing Nginx Proxy Manager:**

```bash
docker compose --profile minio --profile backup up -d
```

Then configure NPM — see [deploy/README.md](./deploy/README.md) for the nginx location blocks.

---

## 3. Wait for healthchecks

```bash
docker compose ps
```

All services should show `healthy`. This typically takes 30–60 seconds on first start.

---

## 4. Seed production data

```bash
docker compose exec api python manage.py seed_prod
```

This creates the admin user and initial group with UIConfig. Re-running is safe (idempotent).

---

## 5. Verify

```bash
# HTTPS working
curl -I https://YOUR_DOMAIN/healthcheck/
# Expected: HTTP/2 200

# Config endpoint
curl https://YOUR_DOMAIN/config.json
# Expected: {"API_URL": "https://...", "CRDT_URL": "wss://..."}
```

---

## 6. Smoke test

1. Log in as admin
2. Upload media → wait for HLS transcode → play back
3. Create an annotation → reply to it → verify 3-level threading
4. Open a second tab → verify CRDT sync between tabs
5. Kill the API container (`docker kill papadam-api`) → verify it restarts within 30s

---

## 7. Backup test

```bash
docker compose exec backup /backup.sh
```

Verify a backup file was created in the backup volume.

---

## Optional profiles

```bash
# With Whisper transcription (auto-generates VTT captions)
docker compose --profile minio --profile transcribe up -d

# With daily automated backups
docker compose --profile minio --profile backup up -d

# All optional services
docker compose --profile minio --profile transcribe --profile backup --profile docs up -d
```

---

## Upgrades

```bash
git pull
cd ui && npm install && npm run build && cd ../deploy
docker compose --profile minio up -d --build
docker compose exec api python manage.py migrate
```
