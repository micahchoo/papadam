from rest_framework import permissions
from rest_framework.request import Request
from rest_framework.views import APIView


class IsUserOrReadOnly(permissions.BasePermission):
    """
    Object-level permission to only allow owners of an object to edit it.
    """

    def has_object_permission(
        self, request: Request, view: APIView, obj: object,
    ) -> bool:
        if request.method in permissions.SAFE_METHODS:
            return True

        return obj == request.user


class IsSuperUser(permissions.BasePermission):
    def has_permission(self, request: Request, view: APIView) -> bool:
        return bool(request.user.is_superuser)
