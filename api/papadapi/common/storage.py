"""
common/storage.py — shared MinIO/S3 helpers.

Extracted from archive/tasks.py when the third consumer (transcript view) appeared.
Import from here rather than duplicating in each app.
"""

from __future__ import annotations

from urllib.parse import urlparse

import structlog as _structlog
from django.conf import settings
from minio import Minio
from minio.error import S3Error as _S3Error


def minio_client(endpoint: str, access_key: str, secret_key: str) -> Minio:
    """Return a path-style MinIO client (no TLS)."""
    return Minio(endpoint, access_key=access_key, secret_key=secret_key, secure=False)


def extract_minio_domain(url: str) -> str:
    """Return the bare MinIO host from an endpoint URL.

    Virtual-hosted-style MinIO puts the bucket name as a subdomain
    (e.g. ``mybucket.minio:9000``).  Path-style (the default) needs no stripping.
    Using ``removeprefix`` avoids ``str.strip()``'s character-set semantics, which
    would silently corrupt hostnames whose characters overlap the bucket name.
    """
    if not url.startswith(("http://", "https://")):
        url = "http://" + url
    netloc = urlparse(url).netloc
    if netloc.startswith("www."):
        netloc = netloc[4:]
    bucket: str = getattr(settings, "AWS_STORAGE_BUCKET_NAME", "")
    if bucket and netloc.startswith(f"{bucket}."):
        return netloc.removeprefix(f"{bucket}.")
    return netloc

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
