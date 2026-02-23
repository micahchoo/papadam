from rest_framework.permissions import SAFE_METHODS, BasePermission, IsAuthenticated

from papadapi.common.models import Group


class ReadOnly(BasePermission):
    def has_permission(self, request, view):
        return request.method in SAFE_METHODS


class IsGroupOwnerMemberOrReadOnly(BasePermission):
    message = "You are not a member of the group to perform this action"

    def has_permission(self, request, view):
        # Always allow GET, HEAD or OPTIONS requests.
        # User must be a part of the group.

        group_id = request.META["PATH_INFO"].split("/")[-2]
        user = request.user
        if group_id and user:
            group = Group.objects.get(id=group_id)
            if request.method in SAFE_METHODS and group.is_public:
                return True
            else:
                if user in group.users.all():
                    return True
                else:
                    return False
        else:
            self.message = "User or Group detail missing"
            return False
