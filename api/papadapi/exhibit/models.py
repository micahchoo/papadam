"""
exhibit/models.py — Exhibit builder models.

An Exhibit is an ordered, publicly shareable collection of MediaStore items
and/or Annotations curated by a group member.  ExhibitBlocks are the ordered
"slides" of an exhibit.
"""

import uuid

from django.db import models
from django.utils.translation import gettext_lazy as _


class Exhibit(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    title = models.CharField(_("Title"), max_length=255)
    description = models.TextField(_("Description"), blank=True)
    is_public = models.BooleanField(_("Public"), default=True)
    group = models.ForeignKey(
        "common.Group",
        verbose_name=_("Group"),
        on_delete=models.CASCADE,
        related_name="exhibits",
    )
    created_by = models.ForeignKey(
        "users.User",
        verbose_name=_("Created by"),
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="exhibits",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("Exhibit")
        verbose_name_plural = _("Exhibits")
        ordering = ["-updated_at"]

    def __str__(self) -> str:
        return self.title


class ExhibitBlock(models.Model):
    class BlockType(models.TextChoices):
        MEDIA = "media", _("Media item")
        ANNOTATION = "annotation", _("Annotation")

    exhibit = models.ForeignKey(
        Exhibit,
        on_delete=models.CASCADE,
        related_name="blocks",
        verbose_name=_("Exhibit"),
    )
    block_type = models.CharField(
        _("Block type"),
        max_length=20,
        choices=BlockType.choices,
        default=BlockType.MEDIA,
    )
    # One of these will be set depending on block_type
    media_uuid = models.UUIDField(
        _("Media UUID"),
        null=True,
        blank=True,
        help_text="UUID of the MediaStore item for media-type blocks.",
    )
    annotation_uuid = models.UUIDField(
        _("Annotation UUID"),
        null=True,
        blank=True,
        help_text="UUID of the Annotation for annotation-type blocks.",
    )
    caption = models.TextField(_("Caption"), blank=True)
    order = models.PositiveIntegerField(_("Display order"), default=0, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _("Exhibit block")
        verbose_name_plural = _("Exhibit blocks")
        ordering = ["exhibit", "order"]

    def __str__(self) -> str:
        return f"{self.exhibit.title} — block {self.order}"
