"""
exhibit/permissions.py — object-level permission for Exhibit writes.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from rest_framework.permissions import SAFE_METHODS, BasePermission

if TYPE_CHECKING:
    from rest_framework.request import Request
    from rest_framework.views import APIView

    from papadapi.exhibit.models import Exhibit


class IsExhibitGroupMemberOrReadOnly(BasePermission):
    """Allow read access to anyone; write access only to group members."""

    message = "You must be a member of the exhibit's group to modify it."

    def has_object_permission(
        self,
        request: Request,
        view: APIView,
        obj: Exhibit,
    ) -> bool:
        if request.method in SAFE_METHODS:
            return True
        if not obj.group:
            return False
        return obj.group.users.filter(pk=request.user.pk).exists()
