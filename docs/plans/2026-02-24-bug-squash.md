# Bug & Lint Squash Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Resolve all remaining ruff violations, the pre-existing Vitest config-cache flake, and the orphaned raw-annotation-file leak in MinIO — leaving the repo at zero linter errors, 85/85 tests green, and no open TODO(loop) items from the debt table.

**Architecture:** Six independent fixes touching different layers (backend linting, frontend module init, and an async task). Each task is self-contained and commits cleanly. No cross-task dependencies except Task 6 (raw-file deletion) which builds on helpers already in `common/storage.py`.

**Tech Stack:** Python 3.12 · ruff · pytest · SvelteKit 2 · Svelte 5 · Vitest · TypeScript · ARQ · MinIO (minio SDK)

---

## Background: what broke and why

| # | File | Violation | Cause |
|---|------|-----------|-------|
| 1 | `archive/views.py` | E402 (9 × import-not-at-top) | `log = structlog.get_logger(...)` inserted between stdlib block and local-import block in round 15 |
| 2 | `archive/views.py:469` | RUF100 (unused noqa directive) | `# noqa: ANN001` added but `*/archive/*` is already ANN-exempt via `per-file-ignores` |
| 3 | `annotate/tests/test_tasks.py:63,129` | E501 (line > 88 chars) | Long `patch(...)` strings introduced when updating minio helper names in round 15 |
| 4 | `manage.py` + `manage-prod.py` | ANN201, PGH004, B904 | Pre-existing; `manage*.py` only has T20 exempted |
| 5 | `wait_for_postgres.py` | ANN201, ANN001 × 4, E501 | Pre-existing; no per-file exemption |
| 6 | `config.test.ts > loadConfig > is cached` | Vitest flake (fetch called 2×) | `api.ts` calls `resolveBaseUrl()` eagerly at module init; `vi.resetModules()` in each test re-imports `$lib/api` → fires a second fetch before `loadConfig()` runs |
| 7 | `annotate/tasks.py` | Raw MinIO file leaked after HLS transcode | `transcode_annotation_audio` and `transcode_annotation_video` overwrite the field name but never delete the original object from MinIO |

---

## How to run checks

```bash
# Backend
cd api
.venv/bin/python -m ruff check .          # must print nothing
.venv/bin/python -m pytest --no-cov -q   # 118 → 122 passed after task 7

# Frontend
cd ../ui
npx svelte-check --tsconfig ./tsconfig.json 2>&1 | tail -3   # 0 ERRORS 0 WARNINGS
npx eslint src --max-warnings=1                               # no output
npx vitest run                                                # 85/85 after task 6
```

---

## Task 1: Fix E402 in archive/views.py (log declared mid-imports)

**File:** `api/papadapi/archive/views.py:1-31`

**Root cause:** `log = structlog.get_logger(__name__)` sits between the third-party import block and the local-import block, triggering E402 on every subsequent import.

**Fix:** Move the `log` assignment to after all imports.

**Step 1: Edit the file**

Current lines 1–31:
```python
import json
import uuid
from datetime import timedelta

import structlog
from django.conf import settings
from django.core.files.storage import default_storage
from django.db.models import Count, Q
from django.db.models.functions import TruncDate
from rest_framework import generics, mixins, status, viewsets
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

log = structlog.get_logger(__name__)   # ← causes E402 on everything below

from papadapi.archive.permissions import (
    ...
```

Replace the `log = ...` line at position 15 so the file reads:
```python
import json
import uuid
from datetime import timedelta

import structlog
from django.conf import settings
from django.core.files.storage import default_storage
from django.db.models import Count, Q
from django.db.models.functions import TruncDate
from rest_framework import generics, mixins, status, viewsets
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from papadapi.archive.permissions import (
    IsArchiveCopyAllowed,
    IsArchiveCreateOrReadOnly,
    IsArchiveUpdateOrReadOnly,
)
from papadapi.archive.signals import media_copied
from papadapi.common.functions import create_or_update_tag, recalculate_tag_count
from papadapi.common.models import Group, Question, Tags
from papadapi.common.serializers import CustomPageNumberPagination
from papadapi.queue import enqueue_after
from papadapi.users.permissions import IsSuperUser

from .models import MediaStore
from .serializers import MediaStatsSerializer, MediaStoreSerializer

log = structlog.get_logger(__name__)
```

**Step 2: Verify**
```bash
cd api
.venv/bin/python -m ruff check papadapi/archive/views.py
```
Expected: only the RUF100 violation remains (line 469 — handled in Task 2).

**Step 3: Commit**
```bash
git add api/papadapi/archive/views.py
git commit -m "fix: move structlog log declaration below imports in archive/views"
```

---

## Task 2: Fix RUF100 in archive/views.py (unused noqa directive)

**File:** `api/papadapi/archive/views.py:469`

**Root cause:** `# noqa: ANN001` was added to the `post()` method signature of `MediaStoreTranscriptView`, but `*/archive/*` already has `ANN` fully exempted via `per-file-ignores` in `pyproject.toml`. The noqa directive is therefore unused.

**Step 1: Remove the directive**

Current line 469:
```python
    def post(self, request, uuid: str) -> Response:  # noqa: ANN001
```

Change to:
```python
    def post(self, request, uuid: str) -> Response:
```

**Step 2: Verify**
```bash
.venv/bin/python -m ruff check papadapi/archive/views.py
```
Expected: no output.

**Step 3: Commit**
```bash
git add api/papadapi/archive/views.py
git commit -m "fix: remove unused noqa directive in MediaStoreTranscriptView.post"
```

---

## Task 3: Fix E501 in annotate/tests/test_tasks.py (lines 63 and 129)

**File:** `api/papadapi/annotate/tests/test_tasks.py:63,129`

Both lines are the same pattern — `patch("papadapi.annotate.tasks.extract_minio_domain", return_value="minio:9000")` at 89 chars. The limit is 88. Wrap to a two-line form.

**Step 1: Edit line 63**

Current:
```python
        patch("papadapi.annotate.tasks.extract_minio_domain", return_value="minio:9000"),
```
Replace with:
```python
        patch("papadapi.annotate.tasks.extract_minio_domain",
              return_value="minio:9000"),
```

**Step 2: Edit line 129** (same pattern, in `test_transcode_video_updates_field_to_hls_manifest`)

Current:
```python
        patch("papadapi.annotate.tasks.extract_minio_domain", return_value="minio:9000"),
```
Replace with:
```python
        patch("papadapi.annotate.tasks.extract_minio_domain",
              return_value="minio:9000"),
```

**Step 3: Verify**
```bash
.venv/bin/python -m ruff check papadapi/annotate/tests/test_tasks.py
.venv/bin/python -m pytest papadapi/annotate/tests/test_tasks.py -q --no-cov
```
Expected: ruff clean; all tests pass.

**Step 4: Commit**
```bash
git add api/papadapi/annotate/tests/test_tasks.py
git commit -m "fix: wrap long patch() lines in annotate test_tasks (E501)"
```

---

## Task 4: Fix manage.py and manage-prod.py (ANN201, PGH004, B904)

**Files:** `api/manage.py` and `api/manage-prod.py` (identical pattern)

Three violations per file:
- **ANN201** — `main()` missing `-> None`
- **PGH004** — `# noqa` must name the specific code: `# noqa: F401`
- **B904** — re-raise inside an except block must use `raise ... from err`

**Step 1: Edit manage.py**

Current (lines 7–26):
```python
def main():
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "papadapi.config")
    os.environ.setdefault("DJANGO_CONFIGURATION", "Local")

    try:
        from configurations.management import execute_from_command_line
    except ImportError:
        try:
            import django  # noqa
        except ImportError:
            raise ImportError(
                "Couldn't import Django. Are you sure it's installed and "
                "available on your PYTHONPATH environment variable? Did you "
                "forget to activate a virtual environment?"
            )
        raise
    execute_from_command_line(sys.argv)
```

Replace with:
```python
def main() -> None:
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "papadapi.config")
    os.environ.setdefault("DJANGO_CONFIGURATION", "Local")

    try:
        from configurations.management import execute_from_command_line
    except ImportError as exc:
        try:
            import django  # noqa: F401
        except ImportError:
            raise ImportError(
                "Couldn't import Django. Are you sure it's installed and "
                "available on your PYTHONPATH environment variable? Did you "
                "forget to activate a virtual environment?"
            ) from exc
        raise
    execute_from_command_line(sys.argv)
```

**Step 2: Apply the same fix to manage-prod.py**

Same replacements, except the `setdefault` line uses `"Local"` → `"Production"` (don't change that).

**Step 3: Verify**
```bash
.venv/bin/python -m ruff check manage.py manage-prod.py
```
Expected: no output.

**Step 4: Commit**
```bash
git add api/manage.py api/manage-prod.py
git commit -m "fix: annotate main(), noqa codes, and raise-from in manage files"
```

---

## Task 5: Fix wait_for_postgres.py (ANN201, ANN001 × 4, E501)

**File:** `api/wait_for_postgres.py`

This is a standalone utility script — not part of the Django app, no per-file exemptions.

**Step 1: Rewrite the function signature and fix the long line**

Current (lines 23–35):
```python
def pg_isready(host, user, password, dbname):
    while time() - start_time < check_timeout:
        try:
            conn = psycopg2.connect(**vars())
            logger.info("Postgres is ready! ✨ 💅")
            conn.close()
            return True
        except psycopg2.OperationalError:
            logger.info(f"Postgres isn't ready. Waiting for {check_interval} {interval_unit}...")
            sleep(check_interval)

    logger.error(f"We could not connect to Postgres within {check_timeout} seconds.")
    return False
```

Replace with:
```python
def pg_isready(host: str, user: str, password: str, dbname: str) -> bool:
    while time() - start_time < check_timeout:
        try:
            conn = psycopg2.connect(**vars())
            logger.info("Postgres is ready! ✨ 💅")
            conn.close()
            return True
        except psycopg2.OperationalError:
            logger.info(
                f"Postgres isn't ready. Waiting for {check_interval} {interval_unit}..."
            )
            sleep(check_interval)

    logger.error(f"We could not connect to Postgres within {check_timeout} seconds.")
    return False
```

**Step 2: Verify**
```bash
.venv/bin/python -m ruff check wait_for_postgres.py
```
Expected: no output.

**Step 3: Run full ruff sweep to confirm zero violations**
```bash
.venv/bin/python -m ruff check .
```
Expected: exits with code 0, no output.

**Step 4: Commit**
```bash
git add api/wait_for_postgres.py
git commit -m "fix: annotate pg_isready() and wrap long log line in wait_for_postgres"
```

---

## Task 6: Fix Vitest config-cache flake (api.ts eager resolveBaseUrl)

**Files:**
- Modify: `ui/src/lib/api.ts:208-218`

**Root cause:** `api.ts` calls `resolveBaseUrl()` at module-init time:
```typescript
void resolveBaseUrl().then((url) => {
    baseURL = url;
    http.defaults.baseURL = url;
});
```
When `vi.resetModules()` runs in `beforeEach` of `config.test.ts`, re-importing `$lib/config` also re-imports `$lib/api` (since `config.ts` imports from `api.ts`). The re-imported `api.ts` fires `resolveBaseUrl()` immediately, calling `fetch('/config.json')`. Then `loadConfig()` also calls `fetch`. Total = 2 calls, but the test asserts 1.

**Fix:** Move URL resolution from module-init to request-interceptor. The interceptor awaits the resolution promise on the first request (and resolves it once), making subsequent requests skip the await.

**Step 1: Read the current interceptor block in api.ts (lines ~208–225)**

Current:
```typescript
let baseURL = '';
const http = axios.create({ baseURL });

// Propagate the resolved URL into the already-created axios instance.
// Must come after `http` is declared so the closure captures the binding.
void resolveBaseUrl().then((url) => {
    baseURL = url;
    http.defaults.baseURL = url;
});

// Attach access token from localStorage on every request
http.interceptors.request.use((config) => {
    const token = localStorage.getItem('access_token');
    if (token) config.headers.Authorization = `Bearer ${token}`;
    return config;
});
```

**Step 2: Replace with lazy resolution**

```typescript
let baseURL = '';
const http = axios.create({ baseURL });

// Lazy URL resolution — fires on the first request, not at module init.
// This prevents an extra fetch() when the module is re-imported in tests.
let _urlReady: Promise<void> | null = null;
function ensureBaseUrl(): Promise<void> {
    if (!_urlReady) {
        _urlReady = resolveBaseUrl().then((url) => {
            baseURL = url;
            http.defaults.baseURL = url;
        });
    }
    return _urlReady;
}

// Attach access token and resolve base URL on every request
http.interceptors.request.use(async (config) => {
    await ensureBaseUrl();
    const token = localStorage.getItem('access_token');
    if (token) config.headers.Authorization = `Bearer ${token}`;
    return config;
});
```

**Step 3: Run svelte-check to verify no TypeScript errors**
```bash
cd ui
npx svelte-check --tsconfig ./tsconfig.json 2>&1 | tail -3
```
Expected: `0 ERRORS 0 WARNINGS`

**Step 4: Run eslint**
```bash
npx eslint src --max-warnings=1
```
Expected: no output.

**Step 5: Run vitest**
```bash
npx vitest run
```
Expected: **85/85 passed** (the config-cache flake resolves).

**Step 6: Commit**
```bash
git add ui/src/lib/api.ts
git commit -m "fix: defer resolveBaseUrl to first request — eliminates Vitest config-cache flake"
```

---

## Task 7: Delete raw annotation files from MinIO after HLS transcode

**Files:**
- Modify: `api/papadapi/common/storage.py`
- Modify: `api/papadapi/annotate/tasks.py:107-114` and `:165-171`
- Test: `api/papadapi/annotate/tests/test_tasks.py`

**Root cause:** After `transcode_annotation_audio` and `transcode_annotation_video` successfully upload HLS files to MinIO and overwrite the field name, the original raw uploaded file is still sitting in the bucket. Over time this leaks storage proportional to the number of transcoded annotations.

### Step 1: Add `delete_minio_object` to common/storage.py

Add to the end of `api/papadapi/common/storage.py`:
```python
import structlog as _structlog
from minio.error import S3Error as _S3Error

_log = _structlog.get_logger(__name__)


def delete_minio_object(key: str) -> None:
    """Delete a single object from the configured bucket.

    Logs but swallows S3Error so a missing or already-deleted object does not
    propagate as an exception — the caller's HLS files are already uploaded and
    the field already updated; failing here should not roll back that success.
    """
    from django.conf import settings  # local to avoid circular at module load

    client = minio_client(
        extract_minio_domain(settings.AWS_S3_ENDPOINT_URL),
        settings.AWS_ACCESS_KEY_ID,
        settings.AWS_SECRET_ACCESS_KEY,
    )
    bucket: str = getattr(settings, "AWS_STORAGE_BUCKET_NAME", "")
    try:
        client.remove_object(bucket, key)
        _log.info("minio_raw_deleted", key=key)
    except _S3Error as exc:
        _log.warning("minio_raw_delete_failed", key=key, error=str(exc))
```

### Step 2: Run the test to verify it fails (TDD)

Add the following test to `api/papadapi/annotate/tests/test_tasks.py`:

```python
@pytest.mark.django_db(transaction=True)
async def test_transcode_audio_deletes_raw_file_after_hls(annotation):
    """After successful audio transcode, the original raw file is deleted from MinIO."""
    annotation.annotation_audio.name = "annotate/audio/raw.mp3"
    await annotation.asave(update_fields=["annotation_audio"])

    fake_proc = AsyncMock()
    fake_proc.communicate = AsyncMock(return_value=(b"128000\n", b""))
    fake_proc.wait = AsyncMock(return_value=0)

    mock_minio = MagicMock()

    with (
        patch("papadapi.annotate.tasks.asyncio.create_subprocess_exec",
              return_value=fake_proc),
        patch("papadapi.annotate.tasks.minio_client", return_value=mock_minio),
        patch("papadapi.annotate.tasks.extract_minio_domain",
              return_value="minio:9000"),
        patch("papadapi.common.storage.minio_client", return_value=mock_minio),
        patch("papadapi.common.storage.extract_minio_domain",
              return_value="minio:9000"),
        patch("papadapi.annotate.tasks.os.makedirs"),
        patch("papadapi.annotate.tasks.os.walk",
              return_value=[("/tmp/x", [], ["stream.m3u8", "stream0.ts"])]),
        patch("papadapi.annotate.tasks.os.remove"),
    ):
        await transcode_annotation_audio({}, annotation.id)

    mock_minio.remove_object.assert_called_once()
    call_args = mock_minio.remove_object.call_args
    assert call_args[0][1] == "annotate/audio/raw.mp3"  # key matches original


@pytest.mark.django_db(transaction=True)
async def test_transcode_video_deletes_raw_file_after_hls(annotation):
    """After successful video transcode, the original raw file is deleted from MinIO."""
    annotation.annotation_video.name = "annotate/video/raw.mp4"
    await annotation.asave(update_fields=["annotation_video"])

    fake_probe = AsyncMock()
    fake_probe.communicate = AsyncMock(return_value=(b"1280x720\n", b""))
    fake_ffmpeg = AsyncMock()
    fake_ffmpeg.wait = AsyncMock(return_value=0)

    mock_minio = MagicMock()

    with (
        patch("papadapi.annotate.tasks.asyncio.create_subprocess_exec",
              side_effect=[fake_probe, fake_ffmpeg]),
        patch("papadapi.annotate.tasks.minio_client", return_value=mock_minio),
        patch("papadapi.annotate.tasks.extract_minio_domain",
              return_value="minio:9000"),
        patch("papadapi.common.storage.minio_client", return_value=mock_minio),
        patch("papadapi.common.storage.extract_minio_domain",
              return_value="minio:9000"),
        patch("papadapi.annotate.tasks.os.makedirs"),
        patch("papadapi.annotate.tasks.os.walk",
              return_value=[("/tmp/x", [], ["stream.m3u8", "stream0.ts"])]),
        patch("papadapi.annotate.tasks.os.remove"),
    ):
        await transcode_annotation_video({}, annotation.id)

    mock_minio.remove_object.assert_called_once()
    call_args = mock_minio.remove_object.call_args
    assert call_args[0][1] == "annotate/video/raw.mp4"
```

Run to confirm FAIL:
```bash
cd api
.venv/bin/python -m pytest papadapi/annotate/tests/test_tasks.py::test_transcode_audio_deletes_raw_file_after_hls -v --no-cov
```
Expected: FAIL — `assert_called_once()` fails since `remove_object` is never called.

### Step 3: Implement raw-file deletion in annotate/tasks.py

In `transcode_annotation_audio`, capture the raw key before overwriting, then delete it:

```python
# Replace lines 107-114:
    remote_prefix = f"annotate/audio/{annotation_id}/"
    await _upload_hls_folder(folder, remote_prefix)

    raw_key = annotation.annotation_audio.name         # save before overwrite
    annotation.annotation_audio.name = f"{remote_prefix}{manifest_name}"
    await annotation.asave(update_fields=["annotation_audio"])
    await asyncio.to_thread(delete_minio_object, raw_key)
    log.info("transcode_annotation_audio_done", annotation_id=annotation_id)
```

In `transcode_annotation_video`, same pattern (lines 165-171):

```python
    remote_prefix = f"annotate/video/{annotation_id}/"
    await _upload_hls_folder(folder, remote_prefix)

    raw_key = annotation.annotation_video.name         # save before overwrite
    annotation.annotation_video.name = f"{remote_prefix}{manifest_name}"
    await annotation.asave(update_fields=["annotation_video"])
    await asyncio.to_thread(delete_minio_object, raw_key)
    log.info("transcode_annotation_video_done", annotation_id=annotation_id)
```

Add the import at the top of `annotate/tasks.py`:
```python
from papadapi.common.storage import delete_minio_object, extract_minio_domain, minio_client
```

Also remove the now-stale TODO comment on both functions:
```python
    # Raw file remains in MinIO as orphan — scheduling deletion is deferred.
    # TODO(loop): enqueue raw file deletion after HLS upload succeeds.
```

### Step 4: Run the new tests

```bash
.venv/bin/python -m pytest papadapi/annotate/tests/test_tasks.py -v --no-cov
```
Expected: all pass (was N before; now N+2).

### Step 5: Run full pytest suite

```bash
.venv/bin/python -m pytest --no-cov -q
```
Expected: 122 passed (118 + 4 new tests).

### Step 6: Run ruff on common/storage.py and annotate/tasks.py

```bash
.venv/bin/python -m ruff check papadapi/common/storage.py papadapi/annotate/tasks.py
```
Expected: no output.

### Step 7: Commit

```bash
git add api/papadapi/common/storage.py \
        api/papadapi/annotate/tasks.py \
        api/papadapi/annotate/tests/test_tasks.py
git commit -m "feat: delete raw annotation files from MinIO after HLS transcode"
```

---

## Final verification

```bash
# Backend
cd api
.venv/bin/python -m ruff check .        # must exit 0 with no output
.venv/bin/python -m pytest -q --no-cov  # 122 passed
.venv/bin/lint-imports                  # 10/10 contracts kept

# Frontend
cd ../ui
npx svelte-check --tsconfig ./tsconfig.json 2>&1 | tail -3   # 0 errors 0 warnings
npx eslint src --max-warnings=1                               # no output
npx vitest run                                                # 85/85
```

Then overwrite `STATE.md` and update `memory/MEMORY.md`.

---

## Plan complete and saved to `docs/plans/2026-02-24-bug-squash.md`.

**Two execution options:**

**1. Subagent-Driven (this session)** — I dispatch a fresh subagent per task, review between tasks, fast iteration

**2. Parallel Session (separate)** — Open a new session in this worktree with `superpowers:executing-plans`, batch execution with checkpoints

**Which approach?**
