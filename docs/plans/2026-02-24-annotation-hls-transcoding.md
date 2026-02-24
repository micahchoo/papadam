# Annotation HLS Transcoding Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Transcode audio/video annotation reply files to adaptive HLS streams so they play reliably at low bandwidth, and render them with HLS.js in AnnotationViewer.

**Architecture:** Two new ARQ tasks (`transcode_annotation_audio`, `transcode_annotation_video`) in `annotate/tasks.py` mirror the `convert_to_hls_audio`/`convert_to_hls` pattern from `archive/tasks.py`. On success each task overwrites the annotation's `FileField.name` to the HLS manifest path already uploaded to MinIO — leaving the raw file as fallback if transcoding fails. `AnnotationViewer.svelte` delegates audio/video rendering to a new `primitives/AnnotationMedia.svelte` that initialises HLS.js for `.m3u8` URLs (same pattern as `MediaPlayer.svelte`).

**Tech Stack:** Python 3.12, Django 4.2, ARQ, ffmpeg/ffprobe, minio SDK, pytest + AsyncMock; SvelteKit 2 + Svelte 5, HLS.js, TypeScript strict.

**Dependency graph note:** `annotate → archive` is permitted. MinIO helpers are duplicated from `archive/tasks.py` (not extracted yet — YAGNI). `# TODO(loop):` added for future extraction.

---

## Task 1: Write failing tests for `transcode_annotation_audio`

**Files:**
- Modify: `api/papadapi/annotate/tests/test_tasks.py`

Tests go FIRST. The task function does not exist yet; imports will fail — that is the expected failure.

**Step 1: Append three tests to test_tasks.py**

Add these tests AFTER the existing `test_delete_annotate_leaves_other_annotations_intact` test.
Keep the existing `import pytest` and existing imports — just append.

```python
# ── transcode_annotation_audio ────────────────────────────────────────────────

from unittest.mock import AsyncMock, MagicMock, patch

# This import will fail until Task 2 is done — that is expected.
from papadapi.annotate.tasks import transcode_annotation_audio


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
    """If ffmpeg fails, annotation_audio field is NOT updated — raw file remains playable."""
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
    ):
        import subprocess as _subprocess
        with pytest.raises(_subprocess.CalledProcessError):
            await transcode_annotation_audio({}, annotation.id)

    await annotation.arefresh_from_db()
    assert annotation.annotation_audio.name == original_name
```

**Step 2: Run to confirm failure**

```bash
cd /media/2TA/DevStuff/papad/papadam/api
source .venv/bin/activate
pytest papadapi/annotate/tests/test_tasks.py::test_transcode_audio_noop_when_no_file -v 2>&1 | head -20
```
Expected: `ImportError: cannot import name 'transcode_annotation_audio'`

---

## Task 2: Implement `transcode_annotation_audio`

**Files:**
- Modify: `api/papadapi/annotate/tasks.py`

**Step 1: Replace the entire file**

The complete new content of `api/papadapi/annotate/tasks.py`:

```python
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
    folder = f"/tmp/papadam/annotate_audio/{annotation_id}"
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
    folder = f"/tmp/papadam/annotate_video/{annotation_id}"
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
```

**Step 2: Run all task tests**

```bash
pytest papadapi/annotate/tests/test_tasks.py -v
```
Expected: 7/7 pass (3 existing + 4 new — the video tests from Task 3 will also be added here).

**Step 3: Commit**

```bash
git add api/papadapi/annotate/tasks.py api/papadapi/annotate/tests/test_tasks.py
git commit -m "feat(annotate): add transcode_annotation_audio/video ARQ tasks"
```

---

## Task 3: Write tests + wire video test

**Files:**
- Modify: `api/papadapi/annotate/tests/test_tasks.py`

**Step 1: Append video tests** (if not already added in Task 1)

```python
from papadapi.annotate.tasks import transcode_annotation_video


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
```

**Step 2: Run all task tests**

```bash
pytest papadapi/annotate/tests/test_tasks.py -v
```
Expected: 7/7 pass.

---

## Task 4: Wire enqueue in `annotate/views.py` + view tests

**Files:**
- Modify: `api/papadapi/annotate/views.py`
- Modify: `api/papadapi/annotate/tests/test_create_update.py`

**Step 1: Append three failing view tests**

Append to `test_create_update.py` (keep the Annotation import already at the top):

```python
from unittest.mock import patch

from django.core.files.uploadedfile import SimpleUploadedFile


@pytest.mark.django_db
def test_create_audio_annotation_enqueues_transcode(member_client, member_media):
    """Posting an audio file triggers transcode_annotation_audio enqueue."""
    audio_file = SimpleUploadedFile("clip.mp3", b"RIFF" + b"\x00" * 40,
                                    content_type="audio/mpeg")
    with patch("papadapi.annotate.views.enqueue") as mock_enqueue:
        resp = member_client.post(
            "/api/v1/annotate/",
            {
                "media_reference_id": str(member_media.uuid),
                "annotation_text": "",
                "media_target": "t=0,10",
                "annotation_type": "audio",
                "annotation_audio": audio_file,
                "tags": "",
            },
            format="multipart",
        )
    assert resp.status_code == 200
    created_id = Annotation.objects.get(uuid=resp.data["uuid"]).id
    mock_enqueue.assert_called_once_with("transcode_annotation_audio", created_id)


@pytest.mark.django_db
def test_create_video_annotation_enqueues_transcode(member_client, member_media):
    """Posting a video file triggers transcode_annotation_video enqueue."""
    video_file = SimpleUploadedFile("clip.mp4", b"\x00" * 64, content_type="video/mp4")
    with patch("papadapi.annotate.views.enqueue") as mock_enqueue:
        resp = member_client.post(
            "/api/v1/annotate/",
            {
                "media_reference_id": str(member_media.uuid),
                "annotation_text": "",
                "media_target": "t=0,10",
                "annotation_type": "video",
                "annotation_video": video_file,
                "tags": "",
            },
            format="multipart",
        )
    assert resp.status_code == 200
    created_id = Annotation.objects.get(uuid=resp.data["uuid"]).id
    mock_enqueue.assert_called_once_with("transcode_annotation_video", created_id)


@pytest.mark.django_db
def test_create_text_annotation_does_not_enqueue(member_client, member_media):
    """Text annotations (no media file) do not trigger any transcode enqueue."""
    with patch("papadapi.annotate.views.enqueue") as mock_enqueue:
        resp = member_client.post(
            "/api/v1/annotate/",
            {
                "media_reference_id": str(member_media.uuid),
                "annotation_text": "note",
                "media_target": "t=0,5",
                "tags": "",
            },
            format="multipart",
        )
    assert resp.status_code == 200
    mock_enqueue.assert_not_called()
```

**Step 2: Confirm failures**

```bash
pytest papadapi/annotate/tests/test_create_update.py::test_create_audio_annotation_enqueues_transcode -v
```
Expected: FAIL (enqueue not yet called in view).

**Step 3: Edit `annotate/views.py`**

Find the existing import line for `enqueue_after`:
```python
from papadapi.queue import enqueue_after
```
Change to:
```python
from papadapi.queue import enqueue, enqueue_after
```

In `AnnotationCreateSet.create()`, find the block that checks for file fields and calls `m.save()`:
```python
        m.save()

        for tag in data.get("tags", "").split(","):
```

Insert between `m.save()` and the tag loop:
```python
        # Enqueue HLS transcoding for audio/video reply files — raw files remain
        # playable natively if the worker hasn't processed them yet.
        if audio_file:
            enqueue("transcode_annotation_audio", m.id)
        if video_file:
            enqueue("transcode_annotation_video", m.id)
```

**Step 4: Run full view test suite**

```bash
pytest papadapi/annotate/tests/test_create_update.py -v
```
Expected: all 13 tests pass (10 existing + 3 new).

**Step 5: Commit**

```bash
git add api/papadapi/annotate/views.py api/papadapi/annotate/tests/test_create_update.py
git commit -m "feat(annotate): enqueue HLS transcode on audio/video annotation create"
```

---

## Task 5: Register new tasks in `worker.py`

**Files:**
- Modify: `api/papadapi/worker.py`

**Step 1: Update imports and functions list**

Find:
```python
from papadapi.annotate.tasks import delete_annotate_post_schedule  # noqa: E402
```
Replace with:
```python
from papadapi.annotate.tasks import (  # noqa: E402
    delete_annotate_post_schedule,
    transcode_annotation_audio,
    transcode_annotation_video,
)
```

Find `WorkerSettings.functions` list and add the two new tasks:
```python
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
```

**Step 2: Smoke-test import chain**

```bash
DJANGO_SETTINGS_MODULE=papadapi.config.test python -m pytest papadapi/annotate/ -v --tb=short -q
```
Expected: all pass (proves worker imports don't break anything).

**Step 3: Commit**

```bash
git add api/papadapi/worker.py
git commit -m "feat(worker): register transcode_annotation_audio/video"
```

---

## Task 6: Create `AnnotationMedia.svelte` primitive

**Files:**
- Create: `ui/src/lib/components/primitives/AnnotationMedia.svelte`

This component wraps `<audio>`/`<video>` with HLS.js init — identical pattern to MediaPlayer.svelte.

**Step 1: Create the file**

Content of `ui/src/lib/components/primitives/AnnotationMedia.svelte`:

```svelte
<script lang="ts">
	import { onDestroy } from 'svelte';
	import Hls from 'hls.js';

	interface Props {
		src: string;
		mediaType: 'audio' | 'video';
	}

	const { src, mediaType }: Props = $props();

	let mediaEl = $state<HTMLMediaElement | null>(null);
	let hls: Hls | null = null;

	function initHls(el: HTMLMediaElement, url: string): void {
		if (hls) {
			hls.destroy();
			hls = null;
		}
		if (url.includes('.m3u8') && Hls.isSupported()) {
			hls = new Hls({ enableWorker: false });
			hls.loadSource(url);
			hls.attachMedia(el);
		} else {
			el.src = url;
		}
	}

	$effect(() => {
		if (mediaEl && src) initHls(mediaEl, src);
		return () => {
			hls?.destroy();
			hls = null;
		};
	});

	onDestroy(() => {
		hls?.destroy();
	});
</script>

{#if mediaType === 'audio'}
	<audio bind:this={mediaEl} controls class="mt-2 w-full">
		Your browser does not support audio playback.
	</audio>
{:else}
	<video bind:this={mediaEl} controls class="mt-2 w-full bg-black">
		<track kind="captions" src="" label="Captions" />
		Your browser does not support video playback.
	</video>
{/if}
```

**Step 2: svelte-check**

```bash
cd /media/2TA/DevStuff/papad/papadam/ui
npm run check 2>&1 | tail -5
```
Expected: 0 errors, 0 warnings.

**Step 3: Commit**

```bash
git add ui/src/lib/components/primitives/AnnotationMedia.svelte
git commit -m "feat(ui): AnnotationMedia primitive — HLS.js-capable audio/video player"
```

---

## Task 7: Wire `AnnotationMedia` into `AnnotationViewer.svelte`

**Files:**
- Modify: `ui/src/lib/components/AnnotationViewer.svelte`

**Step 1: Add import**

In the `<script>` block of `AnnotationViewer.svelte`, add after the existing imports:
```typescript
import AnnotationMedia from '$lib/components/primitives/AnnotationMedia.svelte';
```

**Step 2: Replace bare media elements**

Find and replace the audio block:
```svelte
	{:else if annotation.annotation_type === 'audio' && annotation.annotation_audio}
					<audio src={annotation.annotation_audio} controls class="mt-2 w-full">
						Your browser does not support audio playback.
					</audio>
```
With:
```svelte
	{:else if annotation.annotation_type === 'audio' && annotation.annotation_audio}
					<AnnotationMedia src={annotation.annotation_audio} mediaType="audio" />
```

Find and replace the video block:
```svelte
	{:else if annotation.annotation_type === 'video' && annotation.annotation_video}
					<video src={annotation.annotation_video} controls class="mt-2 w-full bg-black">
						<track kind="captions" src="" label="Captions" />
						Your browser does not support video playback.
					</video>
```
With:
```svelte
	{:else if annotation.annotation_type === 'video' && annotation.annotation_video}
					<AnnotationMedia src={annotation.annotation_video} mediaType="video" />
```

**Step 3: svelte-check + lint**

```bash
npm run check && npm run lint
```
Expected: 0 errors. 1 intentional warning (`svelte/no-at-html-tags` in AnnotationViewer — pre-existing, DOMPurify-sanitised).

**Step 4: Vitest (regression check)**

```bash
npm run test 2>&1 | tail -10
```
Expected: 83/83 pass (no regression — no new TS tests needed since AnnotationMedia contains no pure-function logic).

**Step 5: Commit**

```bash
git add ui/src/lib/components/AnnotationViewer.svelte
git commit -m "feat(ui): use AnnotationMedia in AnnotationViewer for HLS audio/video playback"
```

---

## Task 8: RECTIFY — full lint + type-check + test pass

**Step 1: Backend full sweep**

```bash
cd /media/2TA/DevStuff/papad/papadam/api
source .venv/bin/activate
ruff check papadapi/annotate/
mypy papadapi/annotate/ papadapi/worker.py
lint-imports
pytest papadapi/ -v --tb=short -q
```
Expected: 0 ruff violations, 0 mypy errors, 10/10 import-linter contracts, all tests pass.

**Step 2: Frontend full sweep**

```bash
cd /media/2TA/DevStuff/papad/papadam/ui
npm run check && npm run lint && npm run test
```
Expected: 0 errors, 83/83 tests.

Fix any issue found before proceeding to SYNC.

---

## Task 9: SYNC — update STATE.md, ARCHITECTURE.md, MEMORY.md

**Step 1: Update ARCHITECTURE.md Phase 3 checklist**

In `ARCHITECTURE.md` under `### Phase 3 — Media depth + inclusivity`, change:
```
- [ ] Image overlay annotations during video/audio playback
- [ ] Audio + video reply annotation upload UI (backend needs new file fields; API model has `annotation_image` only)
```
To:
```
- [x] Image overlay annotations during video/audio playback
- [x] Audio + video reply annotation upload UI — raw upload + HLS transcode pipeline wired
```

**Step 2: Update MEMORY.md**

Remove the incorrect entry:
```
- `Annotation` has `annotation_image` (ImageField)
- NO audio/video file fields on Annotation yet — needs new migration for audio/video reply upload
```

Replace with:
```
- `Annotation` has `annotation_image` (ImageField), `annotation_audio` (FileField), `annotation_video` (FileField)
- On create, if audio/video file present, view enqueues `transcode_annotation_audio`/`transcode_annotation_video`
- Task transcodes to single-variant HLS (128k audio, 720p video), uploads to MinIO, updates field `.name` to manifest path
- Raw file remains as MinIO orphan — TODO(loop): schedule deletion after HLS success
- `AnnotationViewer.svelte` uses `primitives/AnnotationMedia.svelte` for HLS-capable audio/video playback
```

Also remove the incorrect STATE.md note: `ARQ transcoding for annotation_audio / annotation_video | 3 | Fields exist, view saves files, no ARQ convert task. Phase 5.`

**Step 3: Overwrite STATE.md**

Overwrite (not append) `STATE.md` with the updated status reflecting this round's changes:
- Status: GREEN
- All checks re-verified
- Delta: tasks from this round
- Gaps: none (or remaining TODO(loop) items)
- Remove the old ARQ transcoding TODO(loop) row from the debt table

**Step 4: Final commit**

```bash
git add ARCHITECTURE.md memory/MEMORY.md STATE.md
git commit -m "docs: sync Phase 3 checklist, MEMORY.md, STATE.md after annotation HLS transcoding"
```
