from __future__ import annotations

from django.apps import AppConfig


class ArchiveConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "papadapi.archive"

    def ready(self) -> None:
        import papadapi.archive.signals  # noqa: F401
