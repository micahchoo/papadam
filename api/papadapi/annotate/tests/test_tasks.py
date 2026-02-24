"""Tests for annotate async ARQ task functions."""

import subprocess
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from papadapi.annotate.models import Annotation
from papadapi.annotate.tasks import (
    delete_annotate_post_schedule,
    transcode_annotation_audio,
    transcode_annotation_video,
)


@pytest.mark.django_db(transaction=True)
async def test_delete_annotate_removes_row(annotation):
    """Task hard-deletes the annotation row from the database."""
    annotation_id = annotation.id
    await delete_annotate_post_schedule({}, annotation_id)
    assert not await Annotation.objects.filter(id=annotation_id).aexists()


@pytest.mark.django_db(transaction=True)
async def test_delete_annotate_noop_when_already_gone(annotation):
    """Task is idempotent — silently succeeds when the row is already absent."""
    annotation_id = annotation.id
    await Annotation.objects.filter(id=annotation_id).adelete()
    # Should not raise
    await delete_annotate_post_schedule({}, annotation_id)


@pytest.mark.django_db(transaction=True)
async def test_delete_annotate_leaves_other_annotations_intact(annotation, group):
    """Task only deletes the targeted annotation, not siblings."""
    other = await Annotation.objects.acreate(
        media_reference_id=annotation.media_reference_id,
        annotation_text="sibling",
        media_target="t=0,5",
        group=group,
    )
    await delete_annotate_post_schedule({}, annotation.id)
    assert await Annotation.objects.filter(id=other.id).aexists()


# ── transcode_annotation_audio ────────────────────────────────────────────────


@pytest.mark.django_db(transaction=True)
async def test_transcode_audio_updates_field_to_hls_manifest(annotation):
    """After successful transcode, annotation_audio.name points to the HLS manifest."""
    annotation.annotation_audio.name = "annotate/audio/raw.mp3"
    await annotation.asave(update_fields=["annotation_audio"])

    fake_proc = AsyncMock()
    fake_proc.communicate = AsyncMock(return_value=(b"128000\n", b""))
    fake_proc.wait = AsyncMock(return_value=0)

    with (
        patch("papadapi.annotate.tasks.asyncio.create_subprocess_exec",
              return_value=fake_proc),
        patch("papadapi.annotate.tasks.Minio") as mock_minio_cls,
        patch("papadapi.annotate.tasks.os.makedirs"),
        patch("papadapi.annotate.tasks.os.walk",
              return_value=[("/tmp/x", [], ["stream.m3u8", "stream0.ts"])]),
        patch("papadapi.annotate.tasks.os.remove"),
    ):
        mock_minio_cls.return_value = MagicMock()
        await transcode_annotation_audio({}, annotation.id)

    await annotation.arefresh_from_db()
    assert annotation.annotation_audio.name.endswith(".m3u8")
    assert f"annotate/audio/{annotation.id}/" in annotation.annotation_audio.name


@pytest.mark.django_db(transaction=True)
async def test_transcode_audio_noop_when_no_file(annotation):
    """Task exits cleanly when annotation has no audio file."""
    annotation.annotation_audio = None
    await annotation.asave(update_fields=["annotation_audio"])

    with patch("papadapi.annotate.tasks.asyncio.create_subprocess_exec") as mock_exec:
        await transcode_annotation_audio({}, annotation.id)
        mock_exec.assert_not_called()


@pytest.mark.django_db(transaction=True)
async def test_transcode_audio_leaves_field_unchanged_on_ffmpeg_error(annotation):
    """If ffmpeg fails, annotation_audio field is NOT updated — raw file is kept."""
    annotation.annotation_audio.name = "annotate/audio/raw.mp3"
    await annotation.asave(update_fields=["annotation_audio"])
    original_name = annotation.annotation_audio.name

    fake_probe = AsyncMock()
    fake_probe.communicate = AsyncMock(return_value=(b"128000\n", b""))
    fake_ffmpeg = AsyncMock()
    fake_ffmpeg.wait = AsyncMock(return_value=1)  # non-zero = ffmpeg failure

    with (
        patch("papadapi.annotate.tasks.asyncio.create_subprocess_exec",
              side_effect=[fake_probe, fake_ffmpeg]),
        patch("papadapi.annotate.tasks.os.makedirs"),
        pytest.raises(subprocess.CalledProcessError),
    ):
        await transcode_annotation_audio({}, annotation.id)

    await annotation.arefresh_from_db()
    assert annotation.annotation_audio.name == original_name


# ── transcode_annotation_video ────────────────────────────────────────────────


@pytest.mark.django_db(transaction=True)
async def test_transcode_video_updates_field_to_hls_manifest(annotation):
    """After successful transcode, annotation_video.name points to the HLS manifest."""
    annotation.annotation_video.name = "annotate/video/raw.mp4"
    await annotation.asave(update_fields=["annotation_video"])

    fake_probe = AsyncMock()
    fake_probe.communicate = AsyncMock(return_value=(b"1280x720\n", b""))
    fake_ffmpeg = AsyncMock()
    fake_ffmpeg.wait = AsyncMock(return_value=0)

    with (
        patch("papadapi.annotate.tasks.asyncio.create_subprocess_exec",
              side_effect=[fake_probe, fake_ffmpeg]),
        patch("papadapi.annotate.tasks.Minio") as mock_minio_cls,
        patch("papadapi.annotate.tasks.os.makedirs"),
        patch("papadapi.annotate.tasks.os.walk",
              return_value=[("/tmp/x", [], ["stream.m3u8", "stream0.ts"])]),
        patch("papadapi.annotate.tasks.os.remove"),
    ):
        mock_minio_cls.return_value = MagicMock()
        await transcode_annotation_video({}, annotation.id)

    await annotation.arefresh_from_db()
    assert annotation.annotation_video.name.endswith(".m3u8")
    assert f"annotate/video/{annotation.id}/" in annotation.annotation_video.name


@pytest.mark.django_db(transaction=True)
async def test_transcode_video_noop_when_no_file(annotation):
    """Task exits cleanly when annotation has no video file."""
    annotation.annotation_video = None
    await annotation.asave(update_fields=["annotation_video"])

    with patch("papadapi.annotate.tasks.asyncio.create_subprocess_exec") as mock_exec:
        await transcode_annotation_video({}, annotation.id)
        mock_exec.assert_not_called()
