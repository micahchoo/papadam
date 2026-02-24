"""
annotate/tasks.py — ARQ background tasks for the annotate app.
"""

from __future__ import annotations

import asyncio
import os
import subprocess
from urllib.parse import urlparse

import structlog
from django.conf import settings
from minio import Minio
from minio.error import S3Error

from papadapi.annotate.models import Annotation

log = structlog.get_logger(__name__)


# ── MinIO helpers
# Duplicated from archive/tasks.py — two consumers does not justify extraction.
# TODO(loop): extract to archive/_hls.py or common/hls.py when a third consumer appears.


def _minio_client(endpoint: str, access_key: str, secret_key: str) -> Minio:
    return Minio(endpoint, access_key=access_key, secret_key=secret_key, secure=False)


def _extract_domain(url: str) -> str:
    """Strip bucket prefix from MinIO endpoint URL to get the bare host."""
    if not url.startswith(("http://", "https://")):
        url = "http://" + url
    netloc = urlparse(url).netloc
    if netloc.startswith("www."):
        netloc = netloc[4:]
    bucket = getattr(settings, "AWS_STORAGE_BUCKET_NAME", "")
    if bucket and bucket in netloc:
        return netloc.strip(f"{bucket}.")
    return netloc


async def _upload_hls_folder(folder: str, remote_prefix: str) -> None:
    """Upload every file produced by ffmpeg HLS output to MinIO, then remove locally."""
    client = _minio_client(
        _extract_domain(settings.AWS_S3_ENDPOINT_URL),
        settings.AWS_ACCESS_KEY_ID,
        settings.AWS_SECRET_ACCESS_KEY,
    )
    bucket: str = settings.AWS_STORAGE_BUCKET_NAME

    def _upload() -> None:
        for root, _, files in os.walk(folder):
            for fname in files:
                local_path = os.path.join(root, fname)
                remote_path = remote_prefix + fname
                try:
                    client.stat_object(bucket, remote_path)
                    log.info("annotation_hls_upload_skipped", remote=remote_path,
                             reason="already_exists")
                except S3Error:
                    client.fput_object(bucket, remote_path, local_path)
                    log.info("annotation_hls_uploaded", remote=remote_path)
                os.remove(local_path)

    await asyncio.to_thread(_upload)


# ── ARQ tasks ─────────────────────────────────────────────────────────────────


async def delete_annotate_post_schedule(ctx: dict, annotation_id: int) -> None:
    """ARQ task: hard-delete an Annotation row after its soft-delete grace period."""
    deleted, _ = await Annotation.objects.filter(id=annotation_id).adelete()
    if deleted:
        log.info("annotation_deleted", annotation_id=annotation_id)
    else:
        log.warning("annotation_delete_noop", annotation_id=annotation_id,
                    reason="already_gone")


async def transcode_annotation_audio(ctx: dict, annotation_id: int) -> None:
    """ARQ task: transcode a raw annotation audio file to HLS and update the field.

    Why: raw uploads play only where the browser supports the codec; HLS gives
    adaptive bitrate and broad browser support via HLS.js.
    On ffmpeg failure the field is NOT updated — raw file remains playable natively.
    """
    annotation = await Annotation.objects.aget(id=annotation_id)
    if not annotation.annotation_audio or not annotation.annotation_audio.name:
        log.warning("transcode_annotation_audio_noop", annotation_id=annotation_id,
                    reason="no_file")
        return

    input_url = annotation.annotation_audio.url
    folder = f"/tmp/papadam/annotate_audio/{annotation_id}"  # noqa: S108
    await asyncio.to_thread(os.makedirs, folder, exist_ok=True)

    # Probe original bitrate to pick the right output quality.
    probe = await asyncio.create_subprocess_exec(
        "ffprobe", "-v", "error", "-select_streams", "a",
        "-show_entries", "stream=bit_rate",
        "-of", "default=noprint_wrappers=1:nokey=1",
        "-i", input_url,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, _ = await probe.communicate()
    try:
        original_bitrate = int(stdout.decode().strip())
    except ValueError:
        original_bitrate = 128_000  # safe fallback

    bitrate = "128k" if original_bitrate >= 128_000 else "64k"
    manifest_name = "stream.m3u8"
    manifest_local = os.path.join(folder, manifest_name)

    proc = await asyncio.create_subprocess_exec(
        "ffmpeg", "-i", input_url,
        "-vn", "-c:a", "aac", "-b:a", bitrate,
        "-hls_time", "10", "-hls_list_size", "0",
        "-f", "hls", manifest_local,
    )
    returncode = await proc.wait()
    if returncode != 0:
        log.error("transcode_annotation_audio_failed", annotation_id=annotation_id)
        raise subprocess.CalledProcessError(returncode, "ffmpeg")

    remote_prefix = f"annotate/audio/{annotation_id}/"
    await _upload_hls_folder(folder, remote_prefix)

    # Raw file remains in MinIO as orphan — scheduling deletion is deferred.
    # TODO(loop): enqueue raw file deletion after HLS upload succeeds.
    annotation.annotation_audio.name = f"{remote_prefix}{manifest_name}"
    await annotation.asave(update_fields=["annotation_audio"])
    log.info("transcode_annotation_audio_done", annotation_id=annotation_id)


async def transcode_annotation_video(ctx: dict, annotation_id: int) -> None:
    """ARQ task: transcode a raw annotation video file to HLS and update the field.

    Uses a single 720p variant — sufficient for short reply clips.
    On ffmpeg failure the field is NOT updated — raw file remains playable natively.
    """
    annotation = await Annotation.objects.aget(id=annotation_id)
    if not annotation.annotation_video or not annotation.annotation_video.name:
        log.warning("transcode_annotation_video_noop", annotation_id=annotation_id,
                    reason="no_file")
        return

    input_url = annotation.annotation_video.url
    folder = f"/tmp/papadam/annotate_video/{annotation_id}"  # noqa: S108
    await asyncio.to_thread(os.makedirs, folder, exist_ok=True)

    # Probe resolution to cap at 720p if the source is larger.
    probe = await asyncio.create_subprocess_exec(
        "ffprobe", "-v", "error", "-select_streams", "v",
        "-show_entries", "stream=width,height",
        "-of", "csv=s=x:p=0",
        "-i", input_url,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, _ = await probe.communicate()
    try:
        width, height = map(int, stdout.decode().strip().split("x"))
    except ValueError:
        width, height = 1280, 720  # safe fallback

    scale = "1280:720" if width >= 1280 else f"{width}:{height}"
    manifest_name = "stream.m3u8"
    manifest_local = os.path.join(folder, manifest_name)

    proc = await asyncio.create_subprocess_exec(
        "ffmpeg", "-i", input_url,
        "-vf", f"scale={scale}",
        "-c:v", "libx264", "-b:v", "1400k",
        "-c:a", "aac", "-b:a", "128k",
        "-hls_time", "10", "-hls_list_size", "0",
        "-f", "hls", manifest_local,
    )
    returncode = await proc.wait()
    if returncode != 0:
        log.error("transcode_annotation_video_failed", annotation_id=annotation_id)
        raise subprocess.CalledProcessError(returncode, "ffmpeg")

    remote_prefix = f"annotate/video/{annotation_id}/"
    await _upload_hls_folder(folder, remote_prefix)

    # TODO(loop): enqueue raw file deletion after HLS upload succeeds.
    annotation.annotation_video.name = f"{remote_prefix}{manifest_name}"
    await annotation.asave(update_fields=["annotation_video"])
    log.info("transcode_annotation_video_done", annotation_id=annotation_id)
