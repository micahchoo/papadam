"""
papadapi/queue.py — synchronous ARQ enqueue helpers for Django views.

Django views are synchronous; ARQ's Redis pool is async.  These helpers wrap
the async enqueue calls with asyncio.run() so views can fire-and-forget jobs
without converting to async views.

Usage:
    from papadapi.queue import enqueue, enqueue_after

    enqueue("delete_annotate_post_schedule", ann.id)
    enqueue_after("delete_media_post_schedule", m.id, delay=10)
    enqueue_after("delete_media_post_schedule", m.id,
                  delay=timedelta(days=group.delete_wait_for))
"""

import asyncio
from datetime import timedelta

import structlog
from arq.connections import ArqRedis, RedisSettings, create_pool
from django.conf import settings

log = structlog.get_logger(__name__)


def _redis_settings() -> RedisSettings:
    return RedisSettings.from_dsn(
        getattr(settings, "REDIS_URL", "redis://localhost:6379/0")
    )


async def _enqueue_async(
    function: str,
    *args: object,
    _defer_by: timedelta | None = None,
) -> str:
    pool: ArqRedis = await create_pool(_redis_settings())
    try:
        job = await pool.enqueue_job(function, *args, _defer_by=_defer_by)
        return job.job_id if job else ""
    finally:
        await pool.aclose()


def enqueue(function: str, *args: object) -> str:
    """Enqueue an ARQ job immediately. Returns the job ID."""
    try:
        return asyncio.run(_enqueue_async(function, *args))
    except Exception as exc:
        log.error("enqueue_failed", function=function, error=str(exc))
        raise


def enqueue_after(
    function: str,
    *args: object,
    delay: int | timedelta = 0,
) -> str:
    """Enqueue an ARQ job with a delay. Returns the job ID.

    Args:
        function: ARQ function name (must be registered in WorkerSettings.functions).
        *args: Positional arguments forwarded to the task function.
        delay: Seconds (int) or timedelta to defer execution.
    """
    defer_by = delay if isinstance(delay, timedelta) else timedelta(seconds=delay)
    try:
        return asyncio.run(
            _enqueue_async(function, *args, _defer_by=defer_by)
        )
    except Exception as exc:
        log.error(
            "enqueue_after_failed",
            function=function,
            delay=str(delay),
            error=str(exc),
        )
        raise
