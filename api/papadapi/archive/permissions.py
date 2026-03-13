from __future__ import annotations

from typing import TYPE_CHECKING, Any

from rest_framework.permissions import SAFE_METHODS, BasePermission

if TYPE_CHECKING:
    from rest_framework.request import Request
    from rest_framework.views import APIView

from papadapi.common.models import Group
from papadapi.common.permissions import user_can_access_group


class IsArchiveCreateOrReadOnly(BasePermission):
    message = "You are not a member of the group to perform this action"

    def has_permission(self, request: Request, view: APIView) -> bool:
        # Always allow GET, HEAD or OPTIONS requests.
        # User must be a part of the group.

        data = request.data
        if request.method == 'GET':
            group_id = request.query_params.get('group')
        else:
            group_id = data.get("group")
            if not group_id and request.method not in SAFE_METHODS:
                self.message = "Missing required field: group"
                return False
        user = request.user
        if group_id and user:
            group = Group.objects.get(id=group_id)
            return user_can_access_group(user, group, request.method in SAFE_METHODS)
        elif not group_id and user:  # this is a search function to allow
            return request.method in SAFE_METHODS
        else:
            self.message = "User or Group detail missing"
            return False


class IsArchiveCopyAllowed(BasePermission):
    message = "You are not a member of the group to perform this action"

    def has_permission(self, request: Request, view: APIView) -> bool:
        if request.method == "PUT":
            data = request.data
            from_group_id = data.get("from_group")
            to_group_id = data.get("to_group")
            if not from_group_id or not to_group_id:
                self.message = "Missing required fields: from_group, to_group"
                return False
            user = request.user
            if from_group_id and to_group_id and user:
                group = Group.objects.get(id=to_group_id)
                return user_can_access_group(user, group, is_safe_method=False)
            else:
                self.message = "User or Group detail missing"
                return False
        else:
            self.message = "Only POST method allowed"
            return False


class IsArchiveUpdateOrReadOnly(BasePermission):
    message = "You are not a member of the group to perform this action"

    def has_object_permission(self, request: Request, view: APIView, obj: Any) -> bool:
        # User must be a part of the group.
        group = obj.group
        user = request.user
        if group and user:
            return user_can_access_group(user, group, request.method in SAFE_METHODS)
        else:
            self.message = "User or Group detail missing"
            return False
