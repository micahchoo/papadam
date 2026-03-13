"""
papadam ARQ worker

Replaces Huey. All background tasks are registered here.
Run with: python -m arq papadapi.worker.WorkerSettings
"""

import os

import structlog
from arq.connections import RedisSettings

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "papadapi.config.production")
os.environ.setdefault("DJANGO_CONFIGURATION", "Production")

# Django must be set up before importing models/tasks
import configurations

configurations.setup()

log = structlog.get_logger()


# ── Task functions (imported after Django setup) ──────────────────────────────

from papadapi.annotate.tasks import (  # noqa: E402
    delete_annotate_post_schedule,
    transcode_annotation_audio,
    transcode_annotation_video,
)
from papadapi.archive.tasks import (  # noqa: E402
    convert_to_hls,
    convert_to_hls_audio,
    delete_media_post_schedule,
    upload_to_storage,
)
from papadapi.importexport.tasks import (  # noqa: E402
    export_request_task,
    import_request_task,
)


async def startup(ctx: dict) -> None:
    log.info("arq_worker_started")


async def shutdown(ctx: dict) -> None:
    log.info("arq_worker_stopped")


class WorkerSettings:
    redis_settings = RedisSettings.from_dsn(
        os.environ.get("REDIS_URL", "redis://redis:6379/0")
    )
    functions = [
        delete_annotate_post_schedule,
        transcode_annotation_audio,
        transcode_annotation_video,
        delete_media_post_schedule,
        convert_to_hls,
        convert_to_hls_audio,
        upload_to_storage,
        export_request_task,
        import_request_task,
    ]
    on_startup = startup
    on_shutdown = shutdown
    max_jobs = 4
    job_timeout = 3600      # 1 hour max per job (HLS transcoding can be slow)
    keep_result = 3600      # keep job results for 1 hour
    retry_jobs = True
    max_tries = 3
