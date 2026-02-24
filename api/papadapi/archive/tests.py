"""Tests for archive async ARQ task functions."""

import subprocess
from unittest.mock import AsyncMock, patch

import pytest

from papadapi.archive.models import MediaStore
from papadapi.archive.tasks import (
    convert_to_hls,
    convert_to_hls_audio,
    delete_media_post_schedule,
    upload_to_storage,
)

# ── delete_media_post_schedule ────────────────────────────────────────────────


@pytest.mark.django_db(transaction=True)
async def test_delete_media_removes_row(media):
    """Task hard-deletes the MediaStore row."""
    media_id = media.id
    await delete_media_post_schedule({}, media_id)
    assert not await MediaStore.objects.filter(id=media_id).aexists()


@pytest.mark.django_db(transaction=True)
async def test_delete_media_noop_when_already_gone(media):
    """Task is idempotent — silently succeeds when the row is absent."""
    media_id = media.id
    await MediaStore.objects.filter(id=media_id).adelete()
    await delete_media_post_schedule({}, media_id)  # must not raise


@pytest.mark.django_db(transaction=True)
async def test_delete_media_leaves_siblings_intact(media, group):
    """Task only deletes the targeted media, not siblings."""
    other = await MediaStore.objects.acreate(
        name="sibling",
        description="sibling desc",
        group=group,
        is_public=True,
    )
    await delete_media_post_schedule({}, media.id)
    assert await MediaStore.objects.filter(id=other.id).aexists()


# ── convert_to_hls ────────────────────────────────────────────────────────────


@pytest.mark.django_db(transaction=True)
async def test_convert_to_hls_sets_completed_status(media):
    """HLS video conversion task updates status to 'Processing completed'."""
    mock_media = AsyncMock()
    mock_media.id = media.id
    mock_media.uuid = media.uuid
    mock_media.upload.url = "http://example.com/video.mp4"

    probe_proc = AsyncMock()
    probe_proc.communicate = AsyncMock(return_value=(b"1280x720", b""))

    ffmpeg_proc = AsyncMock()
    ffmpeg_proc.wait = AsyncMock(return_value=0)

    with (
        patch(
            "papadapi.archive.tasks.MediaStore.objects.aget",
            new=AsyncMock(return_value=mock_media),
        ),
        patch(
            "asyncio.create_subprocess_exec",
            new=AsyncMock(side_effect=[probe_proc, ffmpeg_proc]),
        ),
        patch("asyncio.to_thread", new=AsyncMock(return_value=None)),
        patch("papadapi.queue.enqueue_after"),
    ):
        await convert_to_hls({}, media.id, "/tmp/test")

    assert mock_media.media_processing_status == "Processing completed"


@pytest.mark.django_db(transaction=True)
async def test_convert_to_hls_sets_error_on_ffmpeg_failure(media):
    """HLS task sets 'Processing error' and raises when ffmpeg exits non-zero."""
    mock_media = AsyncMock()
    mock_media.id = media.id
    mock_media.uuid = media.uuid
    mock_media.upload.url = "http://example.com/video.mp4"

    probe_proc = AsyncMock()
    probe_proc.communicate = AsyncMock(return_value=(b"1280x720", b""))

    failing_proc = AsyncMock()
    failing_proc.wait = AsyncMock(return_value=1)

    with (
        patch(
            "papadapi.archive.tasks.MediaStore.objects.aget",
            new=AsyncMock(return_value=mock_media),
        ),
        patch(
            "asyncio.create_subprocess_exec",
            new=AsyncMock(side_effect=[probe_proc, failing_proc]),
        ),
        patch("asyncio.to_thread", new=AsyncMock(return_value=None)),
        pytest.raises(subprocess.CalledProcessError),
    ):
        await convert_to_hls({}, media.id, "/tmp/test")

    assert mock_media.media_processing_status == "Processing error"


# ── convert_to_hls_audio ──────────────────────────────────────────────────────


@pytest.mark.django_db(transaction=True)
async def test_convert_to_hls_audio_sets_completed_status(media):
    """HLS audio conversion task updates status to 'Processing completed'."""
    mock_media = AsyncMock()
    mock_media.id = media.id
    mock_media.uuid = media.uuid
    mock_media.upload.url = "http://example.com/audio.mp3"

    probe_proc = AsyncMock()
    probe_proc.communicate = AsyncMock(return_value=(b"256000", b""))

    ffmpeg_proc = AsyncMock()
    ffmpeg_proc.wait = AsyncMock(return_value=0)

    with (
        patch(
            "papadapi.archive.tasks.MediaStore.objects.aget",
            new=AsyncMock(return_value=mock_media),
        ),
        patch(
            "asyncio.create_subprocess_exec",
            new=AsyncMock(
                side_effect=[probe_proc, ffmpeg_proc, ffmpeg_proc, ffmpeg_proc]
            ),
        ),
        patch("asyncio.to_thread", new=AsyncMock(return_value=None)),
        patch("papadapi.queue.enqueue_after"),
    ):
        await convert_to_hls_audio({}, media.id, "/tmp/test")

    assert mock_media.media_processing_status == "Processing completed"


# ── upload_to_storage ─────────────────────────────────────────────────────────


@pytest.mark.django_db(transaction=True)
async def test_upload_to_storage_sets_completed_on_success(media):
    """Upload task sets 'Stream completed' when the upload loop reports no errors."""
    mock_media = AsyncMock()
    mock_media.id = media.id
    mock_media.uuid = media.uuid

    with (
        patch(
            "papadapi.archive.tasks.MediaStore.objects.aget",
            new=AsyncMock(return_value=mock_media),
        ),
        patch("asyncio.to_thread", new=AsyncMock(return_value=False)),
        patch("papadapi.archive.tasks._minio_client"),
        patch("papadapi.archive.tasks._extract_domain", return_value="minio:9000"),
        patch("django.conf.settings") as mock_settings,
    ):
        mock_settings.AWS_S3_ENDPOINT_URL = "http://minio:9000"
        mock_settings.AWS_ACCESS_KEY_ID = "key"
        mock_settings.AWS_SECRET_ACCESS_KEY = "secret"
        mock_settings.AWS_STORAGE_BUCKET_NAME = "bucket"
        await upload_to_storage({}, media.id, "/tmp/stream/")

    assert mock_media.media_processing_status == "Stream completed"


@pytest.mark.django_db(transaction=True)
async def test_upload_to_storage_sets_error_on_failure(media):
    """Upload task sets 'Stream upload error' when the upload loop reports errors."""
    mock_media = AsyncMock()
    mock_media.id = media.id
    mock_media.uuid = media.uuid

    with (
        patch(
            "papadapi.archive.tasks.MediaStore.objects.aget",
            new=AsyncMock(return_value=mock_media),
        ),
        patch("asyncio.to_thread", new=AsyncMock(return_value=True)),  # True = errors
        patch("papadapi.archive.tasks._minio_client"),
        patch("papadapi.archive.tasks._extract_domain", return_value="minio:9000"),
        patch("django.conf.settings") as mock_settings,
    ):
        mock_settings.AWS_S3_ENDPOINT_URL = "http://minio:9000"
        mock_settings.AWS_ACCESS_KEY_ID = "key"
        mock_settings.AWS_SECRET_ACCESS_KEY = "secret"
        mock_settings.AWS_STORAGE_BUCKET_NAME = "bucket"
        await upload_to_storage({}, media.id, "/tmp/stream/")

    assert mock_media.media_processing_status == "Stream upload error"
