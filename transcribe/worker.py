"""
papadam transcribe worker

Pulls transcription jobs from the ARQ Redis queue.
Each job: downloads media from MinIO, runs Whisper, posts VTT captions to Django API.

TODO Phase 3:
  - implement transcribe_media(ctx, media_uuid)
  - download media via Django /api/v1/archive/{uuid}/
  - run whisper.transcribe(audio_path, task="transcribe", language=None)
  - POST VTT to /api/v1/archive/{uuid}/transcript/
  - emit SSE progress events at each stage
"""

import os
import structlog

log = structlog.get_logger()


class WorkerSettings:
    redis_settings_from_url = os.environ.get("REDIS_URL", "redis://redis:6379")
    functions = []  # populated in Phase 3
    on_startup = lambda ctx: log.info("transcribe_worker_started")  # noqa: E731
    on_shutdown = lambda ctx: log.info("transcribe_worker_stopped")  # noqa: E731
