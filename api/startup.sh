#!/usr/bin/env bash
set -euo pipefail

# ── Wait for PostgreSQL ───────────────────────────────────────────────────────
echo '{"level":"info","msg":"waiting for postgres"}'
until python manage-prod.py check --database default > /dev/null 2>&1; do
  sleep 2
done
echo '{"level":"info","msg":"postgres ready"}'

# ── Migrations & static files ─────────────────────────────────────────────────
python manage-prod.py migrate --noinput
python manage-prod.py collectstatic --noinput

# ── Start Gunicorn ────────────────────────────────────────────────────────────
echo '{"level":"info","msg":"starting gunicorn","port":"'"$PORT"'"}'
exec gunicorn \
  --bind "0.0.0.0:${PORT}" \
  --forwarded-allow-ips="*" \
  --workers=4 \
  --timeout=0 \
  --preload \
  --access-logfile=- \
  --error-logfile=- \
  papadapi.wsgi:application
