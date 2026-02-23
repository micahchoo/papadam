#!/usr/bin/env bash
set -euo pipefail

echo '{"level":"info","msg":"waiting for postgres"}'
until python manage-prod.py check --database default > /dev/null 2>&1; do
  sleep 2
done
echo '{"level":"info","msg":"postgres ready, starting arq worker"}'

exec python -m arq papadapi.worker.WorkerSettings
