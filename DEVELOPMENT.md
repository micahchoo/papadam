# Local Development

## Quickstart (two commands)

Install Docker, Python 3.12, and Node.js 22, then:

```bash
# 1. Set everything up + seed dev data (run once after cloning)
make setup

# 2. Start all servers
make dev
```

Open http://localhost:5173.

`make setup` starts the database, creates the Python venv, installs all
dependencies, runs migrations, creates config files, and seeds dev data.
`make dev` starts the API, UI, and CRDT servers together — Ctrl-C stops all three.

---

## Seed data

### Development

`make setup` runs `seed_dev` automatically. To re-run manually:

```bash
make seed
```

This creates (idempotent — safe to run multiple times):

| Account | Password | Role |
|---------|----------|------|
| `admin` | `admin` | superuser |
| `demo` | `demo` | regular user, member of Demo Community |

Also creates the **Demo Community** group with a UIConfig and 6 tags:
`interview`, `music`, `documentary`, `oral-history`, `archive`, `field-recording`.

> **Security:** `admin/admin` is intentionally insecure. Change the password
> before exposing the API to any network.

### Production

```bash
ADMIN_PASSWORD=<secret> make seed-prod
# or with a custom username:
ADMIN_USERNAME=myuser ADMIN_PASSWORD=<secret> make seed-prod
```

Creates an admin superuser and a **Community** group with a default UIConfig.
The password is **not** reset if the user already exists (re-runs are safe).

Optional `SEED_` env vars customise the initial group:

| Variable | Default | Description |
|---|---|---|
| `SEED_GROUP_NAME` | `Community` | Group name |
| `SEED_GROUP_LANGUAGE` | `en` | BCP 47 language tag |
| `SEED_BRAND_NAME` | same as group name | Shown in masthead |
| `SEED_BRAND_PRIMARY` | `#1e3a5f` | Primary brand colour |
| `SEED_BRAND_ACCENT` | `#d97706` | Accent colour |

---

## What you need

| Tool    | Version  | Install                             |
| ------- | -------- | ----------------------------------- |
| Docker  | 24+      | https://docs.docker.com/get-docker/ |
| Python  | 3.12     | https://python.org/downloads/       |
| Node.js | 22 (LTS) | https://nodejs.org                  |
| git     | any      | https://git-scm.com                 |

---

## Step 1: Get the code

```bash
git clone <your-repo-url> papadam
cd papadam
```

---

## Step 2: Start the data services

These are the database, cache, and file storage — run in Docker so you don't
need to install them. They stay running in the background.

```bash
docker compose -f deploy/dev.yml up -d
```

Wait about 10 seconds, then verify they are running:

```bash
docker compose -f deploy/dev.yml ps
```

All three services (postgres, redis, minio) should show as `running`.

The MinIO console is at http://localhost:9001 — log in with `minioadmin` / `minioadmin`
if you need to inspect uploaded files.

---

## Step 3: Set up the API (Django)

Open a terminal in the `api/` directory. All commands below run from there.

```bash
cd api
```

### 3a: Create the Python environment

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Your prompt should now show `(.venv)`.

Install dependencies:

```bash
pip install -r requirements/requirements-dev.txt
```

This takes a few minutes the first time.

### 3b: Configure

Copy the pre-filled local dev config:

```bash
cp service_config.dev.env.sample service_config.env
```

This file points Django at the data services started in Step 2.
You do not need to edit anything for basic development.

### 3c: Run database migrations

```bash
DJANGO_SETTINGS_MODULE=papadapi.config.local python manage.py migrate
```

Expected output: a list of migrations applied, ending with no errors.

### 3d: Seed dev data

```bash
DJANGO_SETTINGS_MODULE=papadapi.config.local python manage.py seed_dev
```

This creates `admin/admin` (superuser) and `demo/demo` (regular user), the
Demo Community group, a UIConfig, and 6 starter tags. See the
[Seed data](#seed-data) section for details.

Pick any username and password — this is just for local dev.

### 3e: Start the API server

```bash
DJANGO_SETTINGS_MODULE=papadapi.config.local python manage.py runserver
```

The API is now running at http://localhost:8000

Verify it works: http://localhost:8000/healthcheck/
Expected response: `{"status": "ok"}`

The server reloads automatically when you edit Python files.

---

## Step 4: Set up the web interface (SvelteKit)

Open a **new terminal** and go to the `ui/` directory:

```bash
cd ui
npm install
```

Create the local config file:

```bash
cp .env.example .env.local
```

`.env.local` already points to `http://localhost:8000` and `ws://localhost:1234`.
No edits needed.

Start the dev server:

```bash
npm run dev
```

The UI is now running at http://localhost:5173

Open it in your browser. It hot-reloads when you edit Svelte files.

---

## Step 5: Set up the CRDT server (optional)

The CRDT server enables real-time collaborative annotation.
You can skip this step if you don't need live collaboration in development —
the UI works without it (annotations save normally via the REST API).

`make setup` creates `crdt/.env.local` automatically. If you are setting up manually,
create the file first:

```bash
cat > crdt/.env.local << 'EOF'
PORT=1234
CRDT_API_URL=http://localhost:8000
REDIS_URL=redis://localhost:6379
CRDT_SERVER_TOKEN=local-crdt-dev-token
EOF
```

Open a **third terminal** and go to `crdt/`:

```bash
cd crdt
npm install
npm run dev
```

The CRDT server is now running at ws://localhost:1234

**Requires Node 22.** The dev script uses `node --env-file=.env.local` which is not
available in older Node versions. Run `node --version` to confirm.

---

## Running all three at once

You need three terminal windows open simultaneously:

| Terminal | Directory | Command                                                                   |
| -------- | --------- | ------------------------------------------------------------------------- |
| 1        | `api/`    | `DJANGO_SETTINGS_MODULE=papadapi.config.local python manage.py runserver` |
| 2        | `ui/`     | `npm run dev`                                                             |
| 3        | `crdt/`   | `npm run dev` (optional)                                                  |

The data services (Docker) keep running in the background from Step 2.

Open http://localhost:5173 in your browser.

---

## Running tests

### Backend tests

```bash
cd api
source .venv/bin/activate

# Run all tests
pytest

# Run with coverage report
pytest --cov=papadapi --cov-report=term-missing
```

Tests use an in-memory SQLite database — no running services needed.

### Frontend tests

```bash
cd ui

# Unit tests (Vitest)
npm test

# Unit tests with coverage
npm test -- --coverage

# End-to-end tests (Playwright) — requires a running dev server
npm run test:e2e
```

---

## Linting

### Backend

```bash
cd api
source .venv/bin/activate

# Style + security + async rules
ruff check papadapi/

# Architecture contracts (dependency direction between Django apps)
lint-imports

# Type checking
mypy papadapi/
```

### Frontend

```bash
cd ui

# ESLint (includes architecture boundary enforcement)
npm run lint

# TypeScript + Svelte type checking
npm run check
```

---

## Stopping

Stop the dev servers: `Ctrl+C` in each terminal.

Stop the Docker data services:

```bash
docker compose -f deploy/dev.yml down
```

To also delete the database and storage data (start fresh):

```bash
docker compose -f deploy/dev.yml down -v
```

---

## Common issues

**`No module named 'django'` or similar**

You forgot to activate the virtual environment:

```bash
source api/.venv/bin/activate
```

**`connection refused` on port 5432 or 6379**

The Docker data services are not running:

```bash
docker compose -f deploy/dev.yml up -d
docker compose -f deploy/dev.yml ps
```

**`REQUIRED` env var error on Django startup**

The `service_config.env` file was not created in `api/`:

```bash
cp api/service_config.dev.env.sample api/service_config.env
```

**MinIO errors on file upload**

The `papadam` bucket may not have been created. The `minio-init` container does
this automatically, but it can miss if MinIO wasn't ready in time:

```bash
docker compose -f deploy/dev.yml restart minio-init
```

Or create the bucket manually:

1. Open http://localhost:9001
2. Log in: `minioadmin` / `minioadmin`
3. Create bucket named `papadam`
4. Set access to `public`

**Port 5173 already in use**

Another dev server is running. Stop it, or change the port:

```bash
npm run dev -- --port 5174
```

**`CORS` error in browser console**

The UI is sending requests to a different port than `VITE_API_URL`.
Check that `api/.venv` is active and Django is running on port 8000.

**Changes to Python files not reloading**

Django's dev server watches for changes automatically. If it stops responding,
restart it with `Ctrl+C` then re-run `python manage.py runserver`.

**`make setup` fails with "port already allocated"**

`make setup` / `dev-setup.sh` auto-detects occupied ports. Redis is skipped if
something is already on port 6379 (any Redis works). Postgres always uses a Docker
container — if 5432 is occupied by a native postgres, the script picks 5433 or 5434
and patches `service_config.env` automatically.

If you see this from a manual `docker compose` command rather than `make setup`,
check what is holding the port:

```bash
ss -tlnp | grep 5432
```

**CRDT server: `getaddrinfo ENOTFOUND redis`**

The CRDT server is trying to connect to `redis` (Docker hostname) instead of
`redis://localhost:6379`. This means `crdt/.env.local` does not exist or was not loaded.

`make setup` creates `crdt/.env.local` automatically. To create it manually:

```bash
cat > crdt/.env.local << 'EOF'
PORT=1234
CRDT_API_URL=http://localhost:8000
REDIS_URL=redis://localhost:6379
CRDT_SERVER_TOKEN=local-crdt-dev-token
EOF
```

The dev script uses `node --env-file=.env.local`, which requires **Node 22**.
Run `node --version` — if it is below 22, update Node.js.

**`make setup` passes but `make dev` CRDT still fails**

The CRDT server is optional. The UI works fully without it — annotations save via the
REST API. Only live collaborative annotation requires the CRDT server.

If you want the CRDT server running, ensure Redis is up:

```bash
docker compose -f deploy/dev.yml ps   # redis should show "running"
```

**Django fails to start: `AppRegistryNotReady` or import errors**

Usually caused by environment not being set up. Check:

1. `api/service_config.env` exists
2. You are using `DJANGO_SETTINGS_MODULE=papadapi.config.local` (set by `make dev`)
3. The venv is active and `django-configurations` is installed:
   ```bash
   source api/.venv/bin/activate
   pip show django-configurations
   ```

**`FATAL: password authentication failed for user "papadam"` from Django**

Django is connecting to the wrong postgres. Your machine has a native postgres running
on 5432 that does not have the `papadam` user.

`make setup` handles this by running postgres in Docker. If you set up manually,
check `api/service_config.env` — `DB_URL` must point to the Docker postgres port
(may be 5433 if 5432 was occupied):

```bash
grep DB_URL api/service_config.env
docker compose -f deploy/dev.yml ps postgres
```

**Resetting to a clean state**

To wipe everything and start fresh:

```bash
# Stop and remove all dev containers + their data volumes
docker compose -f deploy/dev.yml down -v

# Remove venv
rm -rf api/.venv

# Remove generated config files
rm -f api/service_config.env crdt/.env.local

# Run setup again
make setup
```

---

## File structure reference

```
papadam/
├── api/                  Django REST API
│   ├── service_config.env          your local config (gitignored)
│   ├── service_config.dev.env.sample  template for local dev
│   ├── papadapi/         Django project
│   └── .venv/            Python virtual environment (gitignored)
│
├── ui/                   SvelteKit frontend
│   ├── .env.local        your local config (gitignored)
│   ├── .env.example      template
│   └── src/
│       ├── lib/          shared utilities (api, stores, crdt, config)
│       └── routes/       pages
│
├── crdt/                 Real-time collaboration server
│   └── src/index.ts      entry point
│
├── deploy/               Docker Compose stack
│   ├── dev.yml           local data services only
│   └── docker-compose.yml  full production stack
│
├── SETUP.md              production deployment guide
└── DEVELOPMENT.md        this file
```
