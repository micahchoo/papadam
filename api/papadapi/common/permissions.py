from __future__ import annotations

from typing import TYPE_CHECKING

from rest_framework.permissions import SAFE_METHODS, BasePermission

if TYPE_CHECKING:
    from rest_framework.request import Request
    from rest_framework.views import APIView

from papadapi.common.models import Group


class ReadOnly(BasePermission):
    def has_permission(self, request: Request, view: APIView) -> bool:
        return request.method in SAFE_METHODS


class IsGroupOwnerMemberOrReadOnly(BasePermission):
    message = "You are not a member of the group to perform this action"

    def has_permission(self, request: Request, view: APIView) -> bool:
        # Always allow GET, HEAD or OPTIONS requests.
        # User must be a part of the group.

        group_id = request.META["PATH_INFO"].split("/")[-2]
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
            if request.method in SAFE_METHODS and group.is_public:
                return True
            else:
                return user in group.users.all()  # type: ignore[operator]  # TYPE_DEBT: view ensures authenticated user
        else:
            self.message = "User or Group detail missing"
            return False
