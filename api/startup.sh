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
  --forwarded-allow-ips="${FORWARDED_ALLOW_IPS:-172.16.0.0/12,192.168.0.0/16,10.0.0.0/8}" \
  --workers=4 \
  --timeout=120 \
  --preload \
  --access-logfile=- \
  --error-logfile=- \
  papadapi.wsgi:application
