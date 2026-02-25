from __future__ import annotations

import re
import uuid as _uuid_mod
from typing import TYPE_CHECKING, Any

from rest_framework.permissions import SAFE_METHODS, BasePermission

if TYPE_CHECKING:
    from rest_framework.request import Request
    from rest_framework.views import APIView

from papadapi.archive.models import MediaStore

_MEMBERSHIP_MSG = "User does not belong to the group. Cannot modify any data."

# media_reference_id may be stored as a bare UUID or as a full URL
# (e.g. "http://host/api/v1/archive/<uuid>/").  This helper normalises it.
_UUID_RE = re.compile(
    r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}",
    re.IGNORECASE,
)


def _to_uuid(value: str) -> _uuid_mod.UUID | None:
    """Return UUID from a bare UUID string or a URL embedding one, or None."""
    m = _UUID_RE.search(value)
    if m is None:
        return None
    try:
        return _uuid_mod.UUID(m.group())
    except ValueError:
        return None


class IsAnnotateCreateOrReadOnly(BasePermission):
    message = "You are not a member of the group to perform this action"

    def has_permission(self, request: Request, view: APIView) -> bool:
        # Always allow GET, HEAD or OPTIONS requests.
        # User must be a part of the group.

        data = request.data
        if request.method == 'GET':
            # Try to get from query parameters for search
            archive_id = request.query_params.get('media_reference_id')
            # If not it is expected to be in the url path. Get it from there
            if not archive_id:
                archive_id = request.path.split("/")[-2]
        else:
            archive_id = data["media_reference_id"]
        if archive_id == "annotate" and request.method in SAFE_METHODS:
            return True
        media_uuid = _to_uuid(archive_id) if archive_id else None
        if media_uuid is None:
            if request.method in SAFE_METHODS:
                return True
            self.message = "Invalid media reference."
            return False
        try:
            archive = MediaStore.objects.get(uuid=media_uuid)
        except MediaStore.DoesNotExist:
            self.message = "Referenced media not found."
            return False
        group = archive.group
        user = request.user
        if group and user:
            if request.method in SAFE_METHODS and group.is_public:
                return True
            if user in group.users.all():  # type: ignore[operator]  # TYPE_DEBT: view ensures authenticated user
                return True
            self.message = _MEMBERSHIP_MSG
            return False
        self.message = "User or Group detail missing"
        return False

class IsAnnotateUpdateOrReadOnly(BasePermission):
    message = "You are not a member of the group to perform this action"

    def has_object_permission(
        self, request: Request, view: APIView, obj: Any,
    ) -> bool:
        # User must be a part of the group.
        media_uuid = _to_uuid(obj.media_reference_id)
        if media_uuid is None:
            self.message = "Invalid media reference on annotation."
            return False
        try:
            archive = MediaStore.objects.get(uuid=media_uuid)
        except MediaStore.DoesNotExist:
            self.message = "Referenced media not found."
            return False
        group = archive.group
        user = request.user
        if group and user:
            if request.method in SAFE_METHODS and group.is_public:
                return True
            if user in group.users.all():  # type: ignore[operator]  # TYPE_DEBT: view ensures authenticated user
                return True
            self.message = _MEMBERSHIP_MSG
            return False
        self.message = "User or Group detail missing"
        return False
