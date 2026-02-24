# papadam/crdt

Y.js WebSocket sync server — real-time collaborative annotation for papadam.

---

## What it does

Every media item in the archive maps to one Y.js document (`media:<uuid>`).
This server:

1. Authenticates connecting browsers via JWT (proxied to Django `/auth/users/me/`)
2. Checks group membership before granting document access
3. Loads the saved Y.js binary state from Django on first connection to a document
4. Receives Y.js updates from all connected clients and fans them out
5. Persists the merged state back to Django (debounced, 2 s after last write)
6. Maintains a Redis connection for future multi-instance awareness fan-out

---

## Environment variables

| Variable | Default | Required | Description |
|---|---|---|---|
| `PORT` | `1234` | no | Port to listen on |
| `CRDT_API_URL` | `http://api:8000` | no | Base URL of the Django API |
| `REDIS_URL` | `redis://redis:6379` | no | Redis URL for pub/sub |
| `CRDT_SERVER_TOKEN` | *(empty)* | **yes in production** | Service-account token used to call the persistence bridge |

If `CRDT_SERVER_TOKEN` is empty the server still runs, but persistence writes are silently
skipped — Y.js state is not saved between restarts.
Redis connection failure is non-fatal: the server starts with a warning and disables multi-instance awareness.

---

## WebSocket URL format

```
ws://host/<mediaUuid>?token=<jwt>&groupId=<groupId>
```

| Parameter | Description |
|---|---|
| `<mediaUuid>` | UUID of the media item in the Django `MediaStore` |
| `token` | The browser's JWT access token |
| `groupId` | UUID of the group this media item belongs to (used for membership check) |

The server returns:
- `400 Bad Request` if any parameter is missing
- `401 Unauthorized` if the JWT is invalid or expired
- `403 Forbidden` if the user is not a member of the group

---

## Persistence bridge

The Django API exposes two endpoints called by the crdt server (not browsers):

```
GET /api/v1/crdt/media/<uuid>/    → binary Y.js state (arraybuffer)
PUT /api/v1/crdt/media/<uuid>/    → save binary Y.js state (application/octet-stream)
```

These require `Authorization: Bearer <CRDT_SERVER_TOKEN>`.
The token is a shared machine-to-machine secret — set identically in both services.

---

## Local development

`make setup` from the monorepo root creates `crdt/.env.local` automatically.
To create it manually:

```bash
cat > crdt/.env.local << 'EOF'
PORT=1234
CRDT_API_URL=http://localhost:8000
REDIS_URL=redis://localhost:6379
CRDT_SERVER_TOKEN=local-crdt-dev-token
EOF
```

Start the server:

```bash
cd crdt
npm install
npm run dev
```

The dev script uses Node 22's `--env-file` flag to load `.env.local`.
**Node 22 is required.** Node 20 supports `--env-file` but not `--watch`; Node 18 supports neither.

If you see `getaddrinfo ENOTFOUND redis`:
- `.env.local` is not being loaded, or `REDIS_URL` is not set in it
- Redis is not running — start it with `docker compose -f deploy/dev.yml up -d redis`

The CRDT server is optional for local development.
Annotations save normally via the REST API if it is not running.

---

## Production (Docker)

The crdt server is included in the default `docker-compose.yml` stack — no profile needed.

```bash
# Check it is healthy
docker compose logs crdt
docker compose exec crdt wget -qO- http://localhost:1234/health
```

Expected output from the health endpoint: `{"status":"ok"}`

The container starts after the `api` container is healthy (dependency in compose).
If the API is slow to start, the crdt server may log `getaddrinfo ENOTFOUND api` briefly — this is expected and resolves once the API is ready.

---

## Health check

```
GET /health → 200 {"status":"ok"}
```

All other HTTP paths return 404. WebSocket upgrade is the primary protocol.

---

## Logging

Structured JSON to stdout. Fields: `ts` (ISO8601), `level`, `msg`, and context extras.
Collected by Docker and forwarded to your log aggregator.

---

## Architecture note

See [`../ARCHITECTURE.md`](../ARCHITECTURE.md#crdt-layer) for the Y.js document schema,
offline flow, and what is/is not CRDT-managed.
