from __future__ import annotations

from typing import TYPE_CHECKING

from rest_framework.permissions import SAFE_METHODS, BasePermission

if TYPE_CHECKING:
    from rest_framework.request import Request
    from rest_framework.views import APIView

    from papadapi.users.models import User

from papadapi.common.models import Group


def user_can_access_group(user: User, group: Group, is_safe_method: bool) -> bool:
    """Return True if *user* may access *group* for the given method safety."""
    if is_safe_method and group.is_public:
        return True
    return group.users.filter(pk=user.pk).exists()


class ReadOnly(BasePermission):
    def has_permission(self, request: Request, view: APIView) -> bool:
        return request.method in SAFE_METHODS


class IsGroupOwnerMemberOrReadOnly(BasePermission):
    message = "You are not a member of the group to perform this action"

    def has_permission(self, request: Request, view: APIView) -> bool:
        # Always allow GET, HEAD or OPTIONS requests.
        # User must be a part of the group.

        kw = getattr(view, "kwargs", {})
        group_id = kw.get("id") or kw.get("pk")
        user = request.user
        if group_id and user:
            try:
                group = Group.objects.get(id=group_id)
            except (Group.DoesNotExist, ValueError):
                # Let safe methods through — the view's get_object() will 404
                if request.method in SAFE_METHODS:
                    return True
                self.message = "Group not found"
                return False
            return user_can_access_group(user, group, request.method in SAFE_METHODS)
        else:
            self.message = "User or Group detail missing"
            return False
