from __future__ import annotations

import copy
import hashlib
import json
import logging
import os
import uuid
from functools import partial
from typing import TYPE_CHECKING, Any

from django.db import models
from django.urls import reverse
from django.utils.translation import gettext as _
from djrichtextfield.models import RichTextField

if TYPE_CHECKING:
    from typing import IO

    from papadapi.common.models import Group as GroupModel

from papadapi.archive.models import MediaStore

logger = logging.getLogger(__name__)


def hash_file(file: IO[bytes], block_size: int = 65536) -> str:
    hasher = hashlib.md5(usedforsecurity=False)
    for buf in iter(partial(file.read, block_size), b""):
        hasher.update(buf)
    return hasher.hexdigest()


def upload_to(instance: Annotation, filename: str) -> str:
    """
    :type instance: dolphin.models.File
    """
    instance.annotation_image.open()
    _, filename_ext = os.path.splitext(filename)

    return f"annotate/{hash_file(instance.annotation_image)}{filename_ext}"


def upload_to_audio(instance: Annotation, filename: str) -> str:
    _, filename_ext = os.path.splitext(filename)
    return f"annotate/audio/{uuid.uuid4()}{filename_ext}"


def upload_to_video(instance: Annotation, filename: str) -> str:
    _, filename_ext = os.path.splitext(filename)
    return f"annotate/video/{uuid.uuid4()}{filename_ext}"


class Annotation(models.Model):

    class AnnotationType(models.TextChoices):
        TEXT = "text", _("Text")
        IMAGE = "image", _("Image")
        AUDIO = "audio", _("Audio")
        VIDEO = "video", _("Video")
        MEDIA_REF = "media_ref", _("Media Reference")

    media_reference_id = models.CharField(_("Media Reference ID"), max_length=500)
    media_target = models.CharField(
        _("Media Target(Time start and end)"), max_length=100
    )
    uuid = models.UUIDField(default=uuid.uuid4, editable=False)

    annotation_text = RichTextField(_("Annotation text"))
    annotation_image = models.ImageField(
        _("Annotation Reference Image"), upload_to=upload_to, blank=True, null=True
    )
    annotation_audio = models.FileField(
        _("Annotation Audio File"), upload_to=upload_to_audio, blank=True, null=True
    )
    annotation_video = models.FileField(
        _("Annotation Video File"), upload_to=upload_to_video, blank=True, null=True
    )
    tags = models.ManyToManyField("common.Tags", verbose_name=_("tags"))
    is_public = models.BooleanField(_("Public"), default=True)
    is_delete = models.BooleanField(_("Soft Deleted ?"), default=False)
    is_instance_admin_withheld = models.BooleanField(
        _("withheld by instance admin?"), default=False
    )
    group = models.ForeignKey(
        "common.Group",
        verbose_name=_("Group"),
        on_delete=models.CASCADE,
        blank=True,
        null=True,
    )
    annotation_type = models.CharField(
        _("Annotation type"),
        max_length=20,
        choices=AnnotationType.choices,
        default=AnnotationType.TEXT,
    )
    reply_to = models.ForeignKey(
        "self",
        verbose_name=_("Reply to annotation"),
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="replies",
    )
    media_ref_uuid = models.UUIDField(
        _("Referenced media UUID"),
        null=True,
        blank=True,
    )
    is_instance_group_withheld = models.BooleanField(
        _("withheld by group admin?"), default=False
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        "users.User",
        verbose_name=_("Who created the annotation"),
        on_delete=models.CASCADE,
        blank=True,
        null=True,
    )

    class Meta:
        verbose_name = _("Annotation")
        verbose_name_plural = _("Annotations")
        ordering = ["updated_at"]

    def __str__(self) -> str:
        return self.media_reference_id

    def get_absolute_url(self) -> str:
        return reverse("Annotation_detail", kwargs={"pk": self.pk})

    def compute_group_id(self) -> GroupModel | None:
        try:
            m = MediaStore.objects.get(uuid=uuid.UUID(self.media_reference_id))
            return m.group if m.group else None
        except (MediaStore.DoesNotExist, ValueError):
            return None

    def save(self, *args: Any, **kwargs: Any) -> None:
        if not self.group:
            self.group = self.compute_group_id()
        super().save(*args, **kwargs)

    def annotation_structure(self, media_id: str) -> dict[str, Any]:
        "Returns every object in annotation structure"
        data = Annotation.objects.filter(media_reference_id=media_id)

        resp_data: list[dict[str, Any]] = []
        resp: dict[str, Any] = {}  # This is the final response

        # Load the reference annotation structure template once
        with open("./papadapi/annotate/annotation_structure.json") as f:
            ref_json: dict[str, Any] = json.loads(f.read())

        for d in data:
            a_struct = copy.deepcopy(ref_json)
            a_struct["id"] = d.uuid
            a_struct["created"] = d.created_at
            a_struct["modified"] = d.updated_at
            a_struct["target"]["id"] = d.media_reference_id
            a_struct["target"]["selector"]["value"] = d.media_target
            a_struct["body"][0]["id"] = d.id  # id, value, created
            tags = ""
            for tag in d.tags.all():
                tags = tags + "," + tag.name
            a_struct["body"][0]["value"] = tags
            a_struct["body"][0]["created"] = d.created_at

            a_struct["body"][1]["items"][0]["id"] = d.id
            a_struct["body"][1]["items"][0]["value"] = d.annotation_text
            a_struct["body"][1]["items"][0]["created"] = d.created_at
            if d.annotation_image:
                a_struct["body"][1]["items"].append({})
                a_struct["body"][1]["items"][1]["id"] = d.id
                a_struct["body"][1]["items"][1]["type"] = "Image"
                a_struct["body"][1]["items"][1]["value"] = d.annotation_image.url
                a_struct["body"][1]["items"][1]["created"] = d.created_at
            resp_data.append(a_struct)
        resp["count"] = data.count()
        resp["prev"] = "null"
        resp["next"] = "null"
        resp["results"] = resp_data
        return resp
