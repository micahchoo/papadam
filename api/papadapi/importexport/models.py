import hashlib
import json
import os
import uuid
from functools import partial

from django.core.files import File
from django.db import models
from django.utils.translation import gettext as _

from papadapi.users.models import User


class IERequest(models.Model):
    request_type_choices = (("import", "Import"), ("export", "Export"))
    requested_by = models.ForeignKey(
        "users.User", verbose_name=_("Requested user"), on_delete=models.CASCADE
    )
    requested_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(auto_now=True)
    request_type = models.CharField(
        _("Request type"), max_length=50, choices=request_type_choices
    )
    is_authorized = models.BooleanField(_("Authorized"), default=False)
    is_complete = models.BooleanField(_("Completed"), default=False)
    ie_metadata = models.JSONField(_("Metadata"))
    request_id = models.UUIDField(_("Request ID"), default=uuid.uuid4, editable=False)
    detail = models.TextField(_("Request details"), blank=True, null=True)
    requested_file = models.FileField(
        _("IE File"), max_length=100, upload_to="export/", blank=True, null=True
    )
