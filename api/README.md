# papadam/api

Django 4.2 REST API — papadam hard fork of [papad-api](https://gitlab.com/servelots/papad/papad-api).

See [`../ARCHITECTURE.md`](../ARCHITECTURE.md) for the full system design.

---

## Quick start (local, no Docker)

```bash
# 1. Create venv and install all dev + test dependencies
make install

# 2. Run lint (ruff strict on new code + import-linter architecture contracts)
make lint-full

# 3. Run tests
make test

# 4. Run tests with coverage gate (80%)
make test-cov
```

All `make` targets use `.venv` automatically — no manual `source activate` needed.

---

## Requirements files

| File | Purpose |
|---|---|
| `requirements/requirements.txt` | Runtime dependencies |
| `requirements/requirements-dev.txt` | Lint / type-check / arch (`-r requirements.txt`) |
| `requirements/requirements-test.txt` | Test runner (`-r requirements.txt`) |

---

## Running with Docker

```bash
# Start all services (postgres, redis, minio, api, bg-app, crdt, caddy)
docker compose -f ../deploy/docker-compose.yml up

# Run migrations inside the api container
docker compose -f ../deploy/docker-compose.yml exec api python manage.py migrate

# Tail worker logs
docker compose -f ../deploy/docker-compose.yml logs -f bg-app
```

---

## Django settings

| Module | Used by |
|---|---|
| `papadapi.config.production` | Production (via `DJANGO_CONFIGURATION=Production`) |
| `papadapi.config.local` | Local dev with services (requires `service_config.env`) |
| `papadapi.config.test` | pytest / CI — SQLite in-memory, no external services |

CI sets `DJANGO_SETTINGS_MODULE=papadapi.config.test` — no env file needed.

---

## ARQ worker

```bash
# Start the background task worker locally (requires Redis)
.venv/bin/python -m arq papadapi.worker.WorkerSettings
```

Registered tasks: `delete_annotate_post_schedule`, `delete_media_post_schedule`,
`convert_to_hls`, `convert_to_hls_audio`, `upload_to_storage`,
`export_request_task`, `import_request_task`.

---

## Linting

```bash
make lint          # ruff on new/migrated apps (strict)
make lint-arch     # import-linter — 10 architecture contracts
make lint-full     # both

# Full codebase ruff (informational — legacy violations non-blocking)
.venv/bin/ruff check papadapi/ --exit-zero --statistics
```

### Active ruff rule sets

`E W F I B C4 UP S T20 RUF ASYNC TCH PT SIM DTZ`

Legacy violations (~140) are tracked but not touched until a file is fully migrated.

---

## Architecture contracts (import-linter)

10 contracts enforced in CI. Run locally with `make lint-arch`.

Key constraints:
- `queue.py` is a utility leaf — may not import from any app
- New apps (`crdt`, `events`, `exhibit`, `media_relation`) follow the strict layered graph
- Legacy `common` and `archive` have documented exemptions for pre-existing cross-imports

See `pyproject.toml` `[tool.importlinter]` for the full contract list.
