"""
papadam transcribe worker

Pulls transcription jobs from the ARQ Redis queue.
Each job: downloads media from MinIO, runs Whisper, posts VTT captions to Django API.
"""

from __future__ import annotations

import os
import tempfile
from io import BytesIO

import httpx
import structlog
import whisper
from arq.connections import RedisSettings

log = structlog.get_logger()

_DJANGO_API_URL = os.environ.get("DJANGO_API_URL", "http://api:8000")
_INTERNAL_KEY = os.environ.get("INTERNAL_SERVICE_KEY", "")
_WHISPER_MODEL = os.environ.get("WHISPER_MODEL", "base")

_model: whisper.Whisper | None = None


def _get_model() -> whisper.Whisper:
    """Load Whisper model once and reuse across jobs."""
    global _model  # noqa: PLW0603
    if _model is None:
        _model = whisper.load_model(_WHISPER_MODEL)
    return _model


def _segments_to_vtt(segments: list[dict]) -> str:  # type: ignore[type-arg]
    """Convert Whisper segment list to a WebVTT string."""
    lines = ["WEBVTT", ""]
    for i, seg in enumerate(segments, 1):
        start = _fmt_ts(float(seg["start"]))
        end = _fmt_ts(float(seg["end"]))
        text = str(seg["text"]).strip()
        lines += [str(i), f"{start} --> {end}", text, ""]
    return "\n".join(lines)


def _fmt_ts(t: float) -> str:
    hours = int(t // 3600)
    minutes = int((t % 3600) // 60)
    seconds = int(t % 60)
    ms = int((t % 1) * 1000)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}.{ms:03d}"


async def transcribe_media(ctx: dict, media_uuid: str) -> None:
    """ARQ task: transcribe a media item and post the VTT caption file to Django.

    Flow:
    1. Fetch media info from ``GET /api/v1/archive/<uuid>/``.
    2. Download the raw upload to a temp file.
    3. Run Whisper on the audio track.
    4. Convert segments to WebVTT.
    5. POST VTT to ``POST /api/v1/archive/<uuid>/transcript/``.
    """
    log.info("transcribe_start", media_uuid=media_uuid)

    async with httpx.AsyncClient(base_url=_DJANGO_API_URL, timeout=30) as client:
        media_resp = await client.get(f"/api/v1/archive/{media_uuid}/")
        media_resp.raise_for_status()
        media_data = media_resp.json()

    upload_url: str | None = media_data.get("upload")
    if not upload_url:
        log.warning("transcribe_skip_no_upload", media_uuid=media_uuid)
        return

    # Ensure the URL is absolute — if it's path-only, prepend Django base.
    if upload_url.startswith("/"):
        upload_url = _DJANGO_API_URL.rstrip("/") + upload_url

    with tempfile.NamedTemporaryFile(suffix=".media", delete=False) as tmp:
        tmp_path = tmp.name

    try:
        # Download the media file.
        async with httpx.AsyncClient(timeout=120) as dl:
            async with dl.stream("GET", upload_url) as stream:
                stream.raise_for_status()
                with open(tmp_path, "wb") as f:
                    async for chunk in stream.aiter_bytes(65536):
                        f.write(chunk)

        log.info("transcribe_download_done", media_uuid=media_uuid, path=tmp_path)

        model = _get_model()
        result = model.transcribe(tmp_path, task="transcribe", language=None)  # type: ignore[arg-type]
        vtt_text = _segments_to_vtt(result["segments"])  # type: ignore[index]

        log.info("transcribe_whisper_done", media_uuid=media_uuid)

        async with httpx.AsyncClient(base_url=_DJANGO_API_URL, timeout=30) as client:
            resp = await client.post(
                f"/api/v1/archive/{media_uuid}/transcript/",
                files={"vtt": ("transcript.vtt", BytesIO(vtt_text.encode()), "text/vtt")},
                headers={"X-Internal-Key": _INTERNAL_KEY},
            )
            resp.raise_for_status()

        log.info("transcribe_done", media_uuid=media_uuid)

    finally:
        os.unlink(tmp_path)


class WorkerSettings:
    redis_settings = RedisSettings.from_dsn(
        os.environ.get("REDIS_URL", "redis://redis:6379/0")
    )
    functions = [transcribe_media]
    on_startup = lambda ctx: log.info("transcribe_worker_started")  # noqa: E731
    on_shutdown = lambda ctx: log.info("transcribe_worker_stopped")  # noqa: E731
