FROM python:3.12-alpine AS base
ENV PYTHONUNBUFFERED 1

RUN apk add --update --no-cache gcc musl-dev libffi-dev libc-dev bash curl git

WORKDIR /app
COPY requirements/ requirements/
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements/requirements-prod.txt \
    && pip install --no-cache-dir django-configurations@git+https://github.com/jazzband/django-configurations@2.5.1 \
    && apk del git

COPY . .

RUN addgroup -S appgroup && adduser -S appuser -G appgroup \
    && chown -R appuser:appgroup /app
USER appuser

# ── API target (default) ───────────────────────────────────────────────
FROM base AS api
EXPOSE 8000

# ── Background worker target ──────────────────────────────────────────
FROM base AS bgapps
CMD ["bash", "startup-bgapps.sh"]
