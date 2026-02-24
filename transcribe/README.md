# papadam/transcribe

Optional Whisper transcription worker — automatically generates VTT captions for uploaded audio and video.

**Status: Phase 3 (not yet implemented).** The Docker container and ARQ worker shell exist.
The `transcribe_media` task body is a Phase 3 deliverable. See the roadmap in
[`../ARCHITECTURE.md`](../ARCHITECTURE.md#phase-3--media-depth--inclusivity).

---

## What it will do (Phase 3)

1. Receive a `transcribe_media(ctx, media_uuid)` ARQ job from the Django background worker
2. Download the media file from MinIO via Django `/api/v1/archive/<uuid>/`
3. Extract audio with ffmpeg (if video)
4. Run OpenAI Whisper (`base` model by default) to produce a VTT transcript
5. POST the VTT back to `/api/v1/archive/<uuid>/transcript/`
6. Emit SSE progress events at each stage so the UI can show a progress bar

---

## How to enable it

```bash
cd deploy
docker compose --profile minio --profile transcribe up -d
```

The service is excluded from the default stack — add `--profile transcribe` to any
`docker compose` command to include it.

---

## Environment variables

These are read from `deploy/service_config.env` (same file as all other services):

| Variable | Description |
|---|---|
| `REDIS_URL` | Redis connection string for the ARQ queue |
| `CRDT_API_URL` | Base URL of the Django API (used to download media + POST transcripts) |
| `CRDT_SERVER_TOKEN` | Service-account token for authenticated API calls |

---

## Resource requirements

The container requests up to **2 GB RAM** (`deploy.resources.limits.memory: 2G` in compose).
The Whisper `base` model uses ~1 GB RAM. The `small` model uses ~2 GB.
A machine with less than 4 GB free RAM will likely OOM during transcription.

There is no GPU requirement — Whisper runs on CPU. Transcription is slower on CPU
(roughly 2–5× real-time for `base`), but functional.

---

## Building the image

The Dockerfile installs ffmpeg and all Python dependencies.
It does not bake in model weights — Whisper downloads them on first use (cached in the container).

```bash
cd deploy
docker compose --profile transcribe build transcribe
```

---

## Healthcheck

```
python -c "import arq, whisper; print('ok')"
```

This verifies both packages are importable and the Whisper model can be loaded.
On first container start, this may take 30–60 seconds while Whisper downloads model weights.
If the container appears unhealthy during this window, wait and check again.

---

## Dependencies

```
openai-whisper==20231117
arq==0.26.1
structlog==24.4.0
httpx==0.27.2
ffmpeg  (system package, installed in Dockerfile)
```
