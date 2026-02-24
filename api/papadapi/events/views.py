"""
events/views.py — ARQ job status polling endpoint.

Clients poll GET /api/v1/events/jobs/<job_id>/ to track background task
progress.  The view returns current status without streaming; the UI polls
at ~2 s intervals.  When ARQ async workers are fully migrated (Phase 2),
this can be upgraded to SSE or WebSocket.
"""

import asyncio

import structlog
from django.conf import settings
from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

log = structlog.get_logger(__name__)

# ARQ is an optional runtime dependency — tests mock it out.
try:
    import redis.asyncio as aioredis
    from arq.jobs import Job

    ARQ_AVAILABLE = True
except ImportError:  # pragma: no cover
    ARQ_AVAILABLE = False


async def _fetch_job_status(redis_url: str, job_id: str) -> str:
    """Return the ARQ job status string or 'not_found'."""
    pool = aioredis.from_url(redis_url)
    try:
        job = Job(job_id, pool)
        js = await job.status()
        return js.value  # e.g. "queued", "in_progress", "complete", "not_found"
    finally:
        await pool.aclose()


class JobStatusView(APIView):
    """
    GET /api/v1/events/jobs/<job_id>/

    Returns the current status of an ARQ background job.

    Response shape:
        {"job_id": "...", "status": "queued|in_progress|complete|not_found|failed"}
    """

    def get(self, request: Request, job_id: str) -> Response:
        if not ARQ_AVAILABLE:
            log.warning("arq_not_available")
            return Response(
                {"detail": "Background task system unavailable."},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        redis_url: str = getattr(settings, "REDIS_URL", "redis://localhost:6379/0")
        try:
            job_status = asyncio.run(_fetch_job_status(redis_url, job_id))
        except Exception as exc:
            log.error("job_status_fetch_failed", job_id=job_id, error=str(exc))
            return Response(
                {"job_id": job_id, "status": "not_found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        http_status = (
            status.HTTP_404_NOT_FOUND
            if job_status == "not_found"
            else status.HTTP_200_OK
        )
        return Response({"job_id": job_id, "status": job_status}, status=http_status)
