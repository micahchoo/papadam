FROM python:3.12-slim

# ffmpeg for audio extraction before Whisper
RUN apt-get update && apt-get install -y ffmpeg && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN groupadd -r appgroup && useradd -r -g appgroup appuser
RUN chown -R appuser:appgroup /app
USER appuser

HEALTHCHECK --interval=60s --timeout=10s \
  CMD python -c "import arq, whisper; print('ok')" || exit 1

CMD ["python", "-m", "arq", "worker.WorkerSettings"]
