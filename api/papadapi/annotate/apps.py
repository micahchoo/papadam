from django.apps import AppConfig


class AnnotateConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "papadapi.annotate"

    def ready(self) -> None:
        import papadapi.annotate.signals  # noqa: F401
