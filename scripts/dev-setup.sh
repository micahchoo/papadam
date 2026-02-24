#!/usr/bin/env bash
# dev-setup.sh — one-shot local development setup
#
# Run once after cloning. Then: make dev
# Safe to re-run — skips steps that are already done.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# ── colours ───────────────────────────────────────────────────────────────────
bold=$'\033[1m'
green=$'\033[32m'
yellow=$'\033[33m'
red=$'\033[31m'
reset=$'\033[0m'

step()  { echo "${bold}==> $*${reset}"; }
ok()    { echo "    ${green}ok${reset}  $*"; }
skip()  { echo "    ${yellow}skip${reset} $*"; }
warn()  { echo "    ${yellow}warn${reset} $*"; }
die()   { echo "${red}ERROR: $*${reset}" >&2; exit 1; }

# Returns 0 (true) if a TCP port on localhost is already in use
port_in_use() { nc -z -w1 localhost "$1" 2>/dev/null; }

# Pick the first port from the list that is free
pick_free_port() {
    for p in "$@"; do
        port_in_use "$p" || { echo "$p"; return 0; }
    done
    die "all candidate ports occupied (tried: $*) — free one up and re-run"
}

# ── prerequisite check ────────────────────────────────────────────────────────
step "Checking prerequisites"
command -v docker  >/dev/null || die "docker not found — https://docs.docker.com/get-docker/"
command -v python3 >/dev/null || die "python3 not found — https://python.org/downloads/"
command -v node    >/dev/null || die "node not found — https://nodejs.org"
command -v npm     >/dev/null || die "npm not found — install with node"
ok "docker, python3, node, npm all present"

# ── data services ─────────────────────────────────────────────────────────────
step "Starting data services (PostgreSQL · Redis · MinIO)"
# Redis: any Redis works — skip Docker if one is already listening on :6379
# Postgres / MinIO: need papadam-specific setup (db/user/bucket) — always use
# our Docker containers. If the default port is taken, pick the next free one.

# Redis — optional Docker start
if port_in_use 6379; then
    skip "redis (port 6379 already in use — using existing)"
    REDIS_HOST_PORT=6379
else
    REDIS_HOST_PORT=6379
fi

# Postgres — always our Docker container
PG_HOST_PORT=$(pick_free_port 5432 5433 5434)
[ "$PG_HOST_PORT" = "5432" ] || warn "port 5432 in use — starting Docker postgres on :$PG_HOST_PORT"

# MinIO — always our Docker container
MINIO_HOST_PORT=$(pick_free_port 9000 9002 9004)
MINIO_CONSOLE_HOST_PORT=$(pick_free_port 9001 9003 9005)
[ "$MINIO_HOST_PORT" = "9000" ] || warn "port 9000 in use — starting Docker MinIO on :$MINIO_HOST_PORT"

export PG_HOST_PORT REDIS_HOST_PORT MINIO_HOST_PORT MINIO_CONSOLE_HOST_PORT

SVCS="postgres minio minio-init"
port_in_use 6379 || SVCS="redis $SVCS"
# shellcheck disable=SC2086
docker compose -f "$ROOT/deploy/dev.yml" up -d $SVCS >/dev/null

ok "data services ready (postgres::$PG_HOST_PORT  redis::$REDIS_HOST_PORT  minio::$MINIO_HOST_PORT)"

# ── api setup ─────────────────────────────────────────────────────────────────
step "Setting up api/"
cd "$ROOT/api"

if [ ! -f service_config.env ]; then
    cp service_config.dev.env.sample service_config.env
    ok "created api/service_config.env"
else
    skip "api/service_config.env"
fi
# Patch ports in config if Docker is using non-default host ports
[ "$PG_HOST_PORT"    = "5432" ] || sed -i "s|@localhost:5432/|@localhost:${PG_HOST_PORT}/|g" service_config.env
[ "$REDIS_HOST_PORT" = "6379" ] || sed -i "s|redis://localhost:6379|redis://localhost:${REDIS_HOST_PORT}|g" service_config.env
[ "$MINIO_HOST_PORT" = "9000" ] || sed -i "s|localhost:9000|localhost:${MINIO_HOST_PORT}|g" service_config.env

if [ ! -d .venv ]; then
    python3 -m venv .venv
    ok "created python venv"
else
    skip ".venv"
fi

step "Installing python dependencies"
.venv/bin/pip install --quiet --upgrade pip
.venv/bin/pip install --quiet -r requirements/requirements-dev.txt
ok "python deps installed"

step "Running database migrations"
DJANGO_SETTINGS_MODULE=papadapi.config.local .venv/bin/python manage.py migrate --no-input
ok "migrations complete"

step "Seeding development data"
DJANGO_SETTINGS_MODULE=papadapi.config.local .venv/bin/python manage.py seed_dev
ok "dev data seeded (admin/admin · demo/demo · Demo Community group · tags)"

# ── ui setup ──────────────────────────────────────────────────────────────────
step "Setting up ui/"
cd "$ROOT/ui"

if [ ! -f .env.local ]; then
    cp .env.example .env.local
    ok "created ui/.env.local"
else
    skip "ui/.env.local"
fi

npm install --silent
ok "ui npm deps installed"

# ── crdt setup ────────────────────────────────────────────────────────────────
step "Setting up crdt/"
cd "$ROOT/crdt"

if [ ! -f .env.local ]; then
    cat > .env.local <<'EOF'
PORT=1234
CRDT_API_URL=http://localhost:8000
REDIS_URL=redis://localhost:6379
CRDT_SERVER_TOKEN=local-crdt-dev-token
EOF
    ok "created crdt/.env.local"
else
    skip "crdt/.env.local"
fi

npm install --silent
ok "crdt npm deps installed"

# ── done ──────────────────────────────────────────────────────────────────────
echo ""
echo "${bold}Setup complete.${reset}"
echo ""
echo "Dev accounts seeded:"
echo "  admin / admin  (superuser — change this password!)"
echo "  demo  / demo   (regular user, member of Demo Community)"
echo ""
echo "Start all servers:"
echo "  make dev"
echo ""
echo "Then open http://localhost:5173"
