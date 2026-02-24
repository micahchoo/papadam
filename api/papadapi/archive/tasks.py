"""
archive/tasks.py — ARQ background tasks for the archive app.
"""

from __future__ import annotations

import asyncio
import os
import subprocess

import structlog
from django.conf import settings
from minio.error import S3Error

from papadapi.archive.models import MediaStore
from papadapi.common.storage import extract_minio_domain, minio_client

log = structlog.get_logger(__name__)


# ── helpers ───────────────────────────────────────────────────────────────────


async def _set_status(media: MediaStore, status: str) -> None:
    """Async helper: update media_processing_status and persist."""
    media.media_processing_status = status
    await media.asave(update_fields=["media_processing_status"])


# ── tasks ─────────────────────────────────────────────────────────────────────


async def delete_media_post_schedule(ctx: dict, media_id: int) -> None:
    """ARQ task: hard-delete a MediaStore row after its soft-delete grace period."""
    deleted, _ = await MediaStore.objects.filter(id=media_id).adelete()
    if deleted:
        log.info("media_deleted", media_id=media_id)
    else:
        log.warning("media_delete_noop", media_id=media_id, reason="already_gone")


async def convert_to_hls(ctx: dict, media_id: int, output_folder: str) -> None:
    """ARQ task: transcode a video upload to adaptive HLS streams."""
    m = await MediaStore.objects.aget(id=media_id)
    await _set_status(m, "Processing started")
    input_video = m.upload.url

    # Probe video resolution
    probe = await asyncio.create_subprocess_exec(
        "ffprobe",
        "-v", "error",
        "-select_streams", "v",
        "-show_entries", "stream=width,height",
        "-of", "csv=s=x:p=0",
        "-i", input_video,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, _ = await probe.communicate()
    width, height = map(int, stdout.decode().strip().split("x"))

    resolutions = [(640, 360), (842, 480), (1280, 720)]
    bitrates = ["800k", "1400k", "2800k"]

    folder = os.path.join(output_folder + "/" + str(m.uuid))
    await asyncio.to_thread(os.makedirs, folder, exist_ok=True)

    commands = ["ffmpeg", "-i", input_video]
    for (res_w, res_h), bitrate in zip(resolutions, bitrates, strict=False):
        if res_w <= width and res_h <= height:
            commands.extend([
                "-s", f"{res_w}x{res_h}", "-c:v", "libx264", "-b:v", bitrate,
                "-hls_time", "10", "-hls_list_size", "0",
                "-f", "hls", f"{folder}/stream_{bitrate}.m3u8",
            ])

    proc = await asyncio.create_subprocess_exec(*commands)
    returncode = await proc.wait()
    if returncode != 0:
        await _set_status(m, "Processing error")
        raise subprocess.CalledProcessError(returncode, "ffmpeg")

    await _set_status(m, "Processing completed")

    from papadapi.queue import enqueue_after  # local import to avoid circular
    enqueue_after("upload_to_storage", media_id, folder, delay=10)


async def convert_to_hls_audio(ctx: dict, media_id: int, output_folder: str) -> None:
    """ARQ task: transcode an audio upload to adaptive HLS streams."""
    m = await MediaStore.objects.aget(id=media_id)
    await _set_status(m, "Processing started")
    input_audio = m.upload.url

    # Probe original bitrate
    probe = await asyncio.create_subprocess_exec(
        "ffprobe",
        "-v", "error",
        "-select_streams", "a",
        "-show_entries", "stream=bit_rate",
        "-of", "default=noprint_wrappers=1:nokey=1",
        "-i", input_audio,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, _ = await probe.communicate()
    original_bitrate = int(stdout.decode().strip())

    potential_bitrates = [64000, 128000, 256000]
    bitrates = [
        f"{b // 1000}k"
        for b in potential_bitrates
        if b <= original_bitrate
    ]
    if not bitrates:
        raise ValueError("No suitable bitrate found for audio conversion.")

    folder = os.path.join(output_folder + "/" + str(m.uuid))
    await asyncio.to_thread(os.makedirs, folder, exist_ok=True)

    for bitrate in bitrates:
        proc = await asyncio.create_subprocess_exec(
            "ffmpeg", "-i", input_audio,
            "-vn", "-c:a", "aac", "-b:a", bitrate,
            "-hls_time", "10", "-hls_list_size", "0",
            "-f", "hls", f"{folder}/stream_{bitrate}.m3u8",
        )
        returncode = await proc.wait()
        if returncode != 0:
            await _set_status(m, "Processing error")
            raise subprocess.CalledProcessError(returncode, "ffmpeg")

    await _set_status(m, "Processing completed")

    from papadapi.queue import enqueue_after  # local import to avoid circular
    enqueue_after("upload_to_storage", media_id, folder, delay=10)


async def upload_to_storage(ctx: dict, media_id: int, folder_path: str) -> None:
    """ARQ task: upload a local HLS folder to MinIO/S3 object storage."""
    m = await MediaStore.objects.aget(id=media_id)
    await _set_status(m, "Stream uploading")

    client = minio_client(
        extract_minio_domain(settings.AWS_S3_ENDPOINT_URL),
        settings.AWS_ACCESS_KEY_ID,
        settings.AWS_SECRET_ACCESS_KEY,
    )
    target_prefix = f"stream/{m.uuid}/"
    bucket = settings.AWS_STORAGE_BUCKET_NAME
    is_error = False

    def _upload_all() -> bool:
        """Synchronous upload loop — runs in a thread pool."""
        error = False
        for root, _, files in os.walk(folder_path):
            for fname in files:
                local_path = os.path.join(root, fname)
                rel_path = os.path.relpath(local_path, folder_path)
                remote_path = os.path.join(target_prefix, rel_path).replace("\\", "/")
                try:
                    try:
                        client.stat_object(bucket, remote_path)
                        log.info(
                            "storage_upload_skipped",
                            path=remote_path,
                            reason="already_exists",
                        )
                        continue
                    except S3Error:
                        pass
                    client.fput_object(bucket, remote_path, local_path)
                    log.info(
                        "storage_upload_complete",
                        local=local_path,
                        remote=remote_path,
                    )
                    os.remove(local_path)
                except S3Error as exc:
                    error = True
                    log.error("storage_upload_failed", local=local_path, error=str(exc))
        return error

    is_error = await asyncio.to_thread(_upload_all)

    if not is_error:
        await _set_status(m, "Stream completed")
    else:
        await _set_status(m, "Stream upload error")
