from __future__ import annotations

from typing import TYPE_CHECKING, Any

from rest_framework.permissions import SAFE_METHODS, BasePermission

if TYPE_CHECKING:
    from rest_framework.request import Request
    from rest_framework.views import APIView

from papadapi.common.models import Group


class IsArchiveCreateOrReadOnly(BasePermission):
    message = "You are not a member of the group to perform this action"

    def has_permission(self, request: Request, view: APIView) -> bool:
        # Always allow GET, HEAD or OPTIONS requests.
        # User must be a part of the group.

        data = request.data
        if request.method == 'GET':
            group_id = request.query_params.get('group')
        else:
            group_id = data["group"]
        user = request.user
        if group_id and user:
            group = Group.objects.get(id=group_id)
            if request.method in SAFE_METHODS and group.is_public:
                return True
            return user in group.users.all()  # type: ignore[operator]  # TYPE_DEBT: view ensures authenticated user
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
            from_group_id = data["from_group"]
            to_group_id = data["to_group"]
            user = request.user
            if from_group_id and to_group_id and user:
                group = Group.objects.get(id=to_group_id)
                return user in group.users.all()  # type: ignore[operator]  # TYPE_DEBT: view ensures authenticated user
            else:
                self.message = "User or Group detail missing"
                return False
        else:
            self.message = "Only POST method allowed"
            return False


class IsArchiveUpdateOrReadOnly(BasePermission):
    message = "You are not a member of the group to perform this action"

    def has_object_permission(self, request: Request, view: APIView, obj: Any) -> bool:
        # Always allow GET, HEAD or OPTIONS requests.
        if request.method in SAFE_METHODS:
            return True
        # User must be a part of the group.
        group = obj.group
        user = request.user
        if group and user:
            return user in group.users.all()
        else:
            self.message = "User or Group detail missing"
            return False
