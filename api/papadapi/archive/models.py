import hashlib
import os
import uuid
from functools import partial

from django.db import models
from django.urls import reverse
from django.utils.translation import gettext as _
from djrichtextfield.models import RichTextField


def hash_file(file, block_size=65536):
    hasher = hashlib.md5(usedforsecurity=False)
    for buf in iter(partial(file.read, block_size), b""):
        hasher.update(buf)
    return hasher.hexdigest()


def upload_to(instance, filename):
    """
    :type instance: dolphin.models.File
    """
    instance.upload.open()
    _, filename_ext = os.path.splitext(filename)

    return f"archive/{hash_file(instance.upload)}{filename_ext}"


class MediaStore(models.Model):

    media_processing_choices = (
        ("Yet to process", " Media processing yet to start"),
        ("Video identified", "Media identified as Video"),
        ("Audio identified", "Media identified as Audio"),
        (
            "Processing started",
            "Media processing started. This will take a long time.",
        ),
        (
            "Processing completed",
            "Media processing completed. Stream will be available soon",
        ),
        (
            "Processing error",
            "Media processing error. Notify admin to take a look at this",
        ),
        (
            "Media unknown",
            "The uploaded media is not recognized as audio/video. "
            "Notify admin if you think this is a mistake",
        ),
        ("Stream uploading", "Media streams have started uploading"),
        ("Stream completed", "Media streams upload completed"),
        (
            "Stream upload error",
            "Media streams upload error. Notify admin to take a look at this",
        ),
    )

    upload = models.FileField(
        _("Uploaded Archive"),
        max_length=100,
        upload_to=upload_to,
        blank=True,
        null=True,
    )
    uuid = models.UUIDField(default=uuid.uuid4, editable=False)
    name = models.CharField(_("Name"), max_length=300)
    description = RichTextField(_("Description"))
    tags = models.ManyToManyField("common.Tags", verbose_name=_("tags"))
    is_public = models.BooleanField(_("Public"), default=True)
    group = models.ForeignKey(
        "common.Group",
        verbose_name=_("Group belonging to"),
        on_delete=models.CASCADE,
        default=1,
    )
    extra_group_response = models.JSONField(blank=True, null=True, default=[])
    is_delete = models.BooleanField(_("User requested soft delete ?"), default=False)
    is_instance_admin_withheld = models.BooleanField(
        _("withheld by instance admin?"), default=False
    )
    is_instance_group_withheld = models.BooleanField(
        _("withheld by group admin?"), default=False
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        "users.User",
        verbose_name=_("Who created the media"),
        on_delete=models.CASCADE,
        blank=True,
        null=True,
    )
    orig_name = models.CharField(
        _("Original Media name"), max_length=500, default="None"
    )
    orig_size = models.PositiveIntegerField(_("File Size"), default=0)
    file_extension = models.CharField(_("File extension"), max_length=50, default="")
    media_processing_status = models.CharField(
        _("Media processing status"),
        max_length=100,
        default="Yet to process",
        choices=media_processing_choices,
    )

    class Meta:
        verbose_name = _("MediaStore")
        verbose_name_plural = _("MediaStores")

    def __str__(self):
        return str(self.uuid)

    def get_absolute_url(self):
        return reverse("MediaStore_detail", kwargs={"pk": self.pk})
