# Deploying papadam

## Quickstart

```bash
# 1. Clone
git clone <your-papadam-repo-url> /opt/papadam
cd /opt/papadam

# 2. Run the setup script (generates secrets, builds UI, starts stack)
bash scripts/deploy-setup.sh

# 3. Create admin account
docker exec -it papadam-api python manage.py createsuperuser

# 4. Configure your reverse proxy — see Step 7 below
```

The script prompts for your domain name and handles everything else:
generates all secret keys, writes `deploy/service_config.env`, creates the
Docker network, builds the UI, and starts the stack.

---

## What you need

- A Linux server (Ubuntu 22.04+ recommended)
- Docker and Docker Compose v2 installed
  - Install: `curl -fsSL https://get.docker.com | sh`
- Node.js 22+ on the machine where you'll build the UI
  - Install: https://nodejs.org (download the LTS installer)
- A domain name pointed at your server (for HTTPS)
- Nginx Proxy Manager running on your server
  - NPM manages HTTPS certificates and routes traffic to your services

---

## Manual steps (if you prefer not to use the script)

### Step 1: Get the code

On your server (or your local machine — you'll copy the build output):

```bash
git clone <your-papadam-repo-url> /opt/papadam
cd /opt/papadam
```

---

### Step 2: Build the web interface (or `make build` on the server)

The SvelteKit UI must be compiled before the Docker stack can serve it.
Run this wherever Node.js is installed (can be your laptop or the server):

```bash
cd /opt/papadam/ui
npm install
npm run build
```

You should see output ending with:

```
> Using @sveltejs/adapter-static
  Wrote site to "build"
  done
```

This creates `ui/build/` — a folder of plain HTML/CSS/JS files that nginx serves.

If you built on your laptop, copy the build folder to the server:

```bash
rsync -av ui/build/ user@yourserver:/opt/papadam/ui/build/
```

---

### Step 3: Configure

```bash
cd /opt/papadam/deploy
cp service_config.env.sample service_config.env
nano service_config.env

# Create the .env symlink so Docker Compose variable substitution works
ln -sf service_config.env .env
```

Fill in every line marked `REQUIRED`. Here is what each one means:

---

### DJANGO_SECRET_KEY

A random secret used to sign session cookies and tokens.
Generate one by running:

```bash
python3 -c "import secrets; print(secrets.token_hex(50))"
```

Paste the output as the value. Example:

```
DJANGO_SECRET_KEY=a3f9b2c8d1e4f7a0b3c6d9e2f5a8b1c4d7e0f3a6b9c2d5e8f1a4b7c0d3e6f9
```

Never share this value or commit it to git.

---

### POSTGRES_PASSWORD and DB_URL

The password for the database. Pick anything strong.
Then update DB_URL to use the same password:

```
POSTGRES_PASSWORD=my-strong-db-password
DB_URL=postgres://papadam:my-strong-db-password@postgres:5432/papadam
```

The part before `@postgres` is `user:password`. The `postgres` after `@` is the
Docker service name — do not change it.

---

### MINIO_ROOT_USER and MINIO_ROOT_PASSWORD

The admin credentials for the file storage server (MinIO).
These are used for the MinIO admin console.

```
MINIO_ROOT_USER=admin
MINIO_ROOT_PASSWORD=my-minio-password
```

Password must be at least 8 characters.

---

### CRDT_SERVER_TOKEN

A shared secret between the real-time collaboration server and the API.
Generate one:

```bash
python3 -c "import secrets; print(secrets.token_hex(32))"
```

This is not a password you'll type — it's a machine-to-machine secret.

```
CRDT_SERVER_TOKEN=b2c4d6e8f0a2b4c6d8e0f2a4b6c8d0e2f4a6b8c0d2e4f6a8b0c2d4e6f8a0b2
```

---

### PUBLIC_API_URL and PUBLIC_CRDT_URL

These tell the browser where to find the API and the real-time sync server.
Use your actual domain:

```
PUBLIC_API_URL=https://papad.yourorganisation.org
PUBLIC_CRDT_URL=wss://papad.yourorganisation.org/ws
```

- `PUBLIC_API_URL`: the full HTTPS URL — no trailing slash
- `PUBLIC_CRDT_URL`: always `wss://` + your domain + `/ws`

---

### DOMAIN (Caddy only)

Only needed if you use `--profile webserver` (standalone Caddy).
Set it to your domain: `DOMAIN=papad.yourorganisation.org`

Leave it as-is if you use NPM — it is ignored.

---

Leave all other values unchanged unless you know what you're doing.

---

### Step 4: Create the Docker network

NPM and papadam share a Docker network so they can communicate.
NPM creates this network automatically, but if it doesn't exist yet:

```bash
docker network create nginx_network 2>/dev/null || true
```

---

### Step 5: Start the stack

```bash
cd /opt/papadam/deploy
docker compose --profile minio up -d
```

This starts: database, cache, file storage, API, background worker, real-time server, and the web UI container.

Check that everything came up:

```bash
docker compose ps
```

All services should show `running` or `healthy`. If anything shows `exited`, check its logs:

```bash
docker compose logs api
docker compose logs crdt
```

Wait about 30 seconds after first start — the API runs database migrations on startup.

---

### Step 6: Create an admin account

```bash
docker exec -it papadam-api python manage.py createsuperuser
```

Follow the prompts. Use a real email — it is shown to users as a support contact.

Admin interface: `https://yourdomain/nimda/`

---

### Step 7: Set up Nginx Proxy Manager

Open your NPM web interface and add a proxy host.

**Hosts → Add Proxy Host:**

| Field                 | Value                        |
| --------------------- | ---------------------------- |
| Domain Names          | `papad.yourorganisation.org` |
| Scheme                | `http`                       |
| Forward Hostname      | `papadam-ui`                 |
| Forward Port          | `80`                         |
| Block Common Exploits | On                           |
| Websockets Support    | On                           |

**SSL tab:**

- Request a new SSL certificate
- Enable "Force SSL"

**Advanced tab** — paste this entire block:

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

Save and apply.

---

### Step 8: Verify

Open a terminal and run these checks:

```bash
# API is alive
curl https://papad.yourorganisation.org/healthcheck/
# Expected: {"status": "ok"}  or similar

# Frontend config is served by Django
curl https://papad.yourorganisation.org/config.json
# Expected: {"API_URL": "https://papad.yourorganisation.org", "CRDT_URL": "wss://..."}

# Open the site in your browser
# Expected: the papadam home page loads, login works
```

If `/config.json` returns the HTML of the home page instead of JSON, the NPM Advanced
config block was not applied correctly — go back and re-save it.

---

## Updating

When you pull new code:

```bash
cd /opt/papadam

# 1. Pull latest code
git pull

# 2. Rebuild the UI
cd ui && npm install && npm run build && cd ..

# 3. Rebuild and restart the stack
cd deploy
docker compose --profile minio up -d --build
```

Migrations run automatically on startup.

---

## Optional: access MinIO console

The MinIO file storage has a web interface on port 9001, but it is not exposed
publicly by default. Access it via an SSH tunnel:

```bash
ssh -L 9001:localhost:9001 user@yourserver
```

Then open http://localhost:9001 in your browser and log in with your
`MINIO_ROOT_USER` and `MINIO_ROOT_PASSWORD` from service_config.env.

---

## Optional: automated backups

Add daily database backups (keeps 7 days, 4 weeks, 6 months):

```bash
mkdir -p /opt/papadam/deploy/backups
docker compose --profile minio --profile backup up -d
```

Backups are stored in `deploy/backups/`.

---

## Troubleshooting

**The site loads but API calls fail / login doesn't work**

Check that the NPM Advanced nginx block was saved. Verify:

```bash
curl https://yourdomain/config.json
```

It must return JSON, not HTML.

**The page is blank after login**

The JWT token may not be stored. Open browser developer tools → Application → Local Storage
and check that `access_token` is set after login.

**"502 Bad Gateway" from NPM**

The Docker containers are not on `nginx_network`. Check:

```bash
docker network inspect nginx_network | grep papadam
```

You should see `papadam-api`, `papadam-crdt`, and `papadam-ui` listed.
If not: `docker compose --profile minio down && docker compose --profile minio up -d`

**Database connection error on startup**

The API container starts before PostgreSQL is fully ready.
It retries automatically — wait 60 seconds and check again:

```bash
docker compose logs api --tail=20
```

**"ALLOWED_HOSTS" error (400 Bad Request)**

`PUBLIC_API_URL` in service_config.env does not match the domain you are visiting.
Make sure `PUBLIC_API_URL=https://papad.yourorganisation.org` with no trailing slash.
Then restart: `docker compose --profile minio restart api`

**Container exited immediately**

```bash
docker compose logs <service-name>
```

Common causes: missing env var, wrong password in DB_URL, port already in use.

**`WARN: The "POSTGRES_PASSWORD" variable is not set`**

Docker Compose uses `.env` (not `service_config.env`) for YAML variable substitution
(`${POSTGRES_PASSWORD}` in the compose file). The setup script creates a `.env` symlink
automatically. If you skipped the script, create it manually:

```bash
cd deploy
ln -sf service_config.env .env
```

**MinIO: `FATAL Unable to initialize backend: decodeXLHeaders: Unknown xl meta version`**

A stale `minio-data` volume exists from a previous failed run (e.g. one that started
with blank credentials). Wipe it and restart:

```bash
cd deploy
docker compose --profile minio down -v
docker compose --profile minio up -d
```

`deploy-setup.sh` does this automatically on a fresh install.

**MinIO container stays unhealthy for a long time**

MinIO can take 1–2 minutes to initialise on first start, especially on slower disks.
The healthcheck allows up to 2 minutes (`retries: 12` × `interval: 10s`).
Wait and check again:

```bash
docker compose ps minio
docker compose logs minio --tail=20
```

If it is still unhealthy after 3 minutes, check for the XL meta version error above.

**CRDT server: `getaddrinfo ENOTFOUND api`**

The CRDT server starts before the Django API is fully ready.
Docker Compose waits for the API healthcheck (`/healthcheck/` returning 200) before
starting `crdt`, but the first startup can take 30–60 seconds for migrations.
The CRDT server will keep retrying — this message is harmless if it disappears within
a minute.

If it persists:

```bash
docker compose logs api --tail=20  # check if api started successfully
docker compose ps                  # crdt should be "healthy" eventually
```

**Running locally with `localhost` as domain (no HTTPS)**

Use `localhost` as the domain when prompted by `deploy-setup.sh`. The script
detects this and writes `http://` and `ws://` URLs to `service_config.env` instead
of `https://` and `wss://`. No SSL certificate is requested.

You still need the `nginx_network` Docker network (the script creates it).
Access the app at `http://localhost` with a reverse proxy on port 80 pointing to
`papadam-ui:80`, or expose port 80 directly from the `ui` container.
