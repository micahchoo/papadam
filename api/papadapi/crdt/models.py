"""
crdt/models.py — Y.js document state persistence.

One row per media item; the binary column holds the full Y.js encoded
document state (result of Y.encodeStateAsUpdate).  The CRDT WebSocket
server (crdt/ container) reads and writes this via the persistence bridge
API view.
"""


from django.db import models
from django.utils.translation import gettext_lazy as _


class YDocState(models.Model):
    """Persisted Y.js document state keyed by media UUID."""

    media_uuid = models.UUIDField(
        _("Media UUID"),
        unique=True,
        db_index=True,
        help_text="UUID of the MediaStore item this document belongs to.",
    )
    state_vector = models.BinaryField(
        _("Y.js encoded state vector"),
        help_text="Result of Y.encodeStateAsUpdate(doc) serialised as bytes.",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("Y.js doc state")
        verbose_name_plural = _("Y.js doc states")
        ordering = ["-updated_at"]

    def __str__(self) -> str:
        return f"YDocState({self.media_uuid})"
