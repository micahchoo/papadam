"""
papadam ARQ worker

Replaces Huey. All background tasks are registered here.
Run with: python -m arq papadapi.worker.WorkerSettings

Phase 1: infrastructure stub — task functions will be migrated from
archive/tasks.py, annotate/tasks.py, and importexport/tasks.py in Phase 1c.
"""

import os

import django
import structlog

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "papadapi.config.production")
os.environ.setdefault("DJANGO_CONFIGURATION", "Production")

# Django must be set up before importing models/tasks
import configurations  # noqa: E402
configurations.setup()

log = structlog.get_logger()


# ── Task functions (imported after Django setup) ──────────────────────────────
# These will be populated as tasks are migrated from Huey in Phase 1c.
# Each task is an async function decorated with nothing — ARQ calls them directly.

# from papadapi.archive.tasks import process_media, upload_to_storage
# from papadapi.importexport.tasks import export_group, import_group


async def startup(ctx: dict) -> None:
    log.info("arq_worker_started")


async def shutdown(ctx: dict) -> None:
    log.info("arq_worker_stopped")


class WorkerSettings:
    redis_settings_from_dsn = os.environ.get("REDIS_URL", "redis://redis:6379/0")
    functions = []          # populated as tasks are migrated
    on_startup = startup
    on_shutdown = shutdown
    max_jobs = 4
    job_timeout = 3600      # 1 hour max per job (HLS transcoding can be slow)
    keep_result = 3600      # keep job results for 1 hour
    retry_jobs = True
    max_tries = 3
