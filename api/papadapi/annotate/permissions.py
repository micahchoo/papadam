from rest_framework.permissions import SAFE_METHODS, BasePermission

from papadapi.archive.models import MediaStore
from papadapi.common.models import Group

class IsAnnotateCreateOrReadOnly(BasePermission):
    message = "You are not a member of the group to perform this action"

    def has_permission(self, request, view):
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
        else:
            archive = MediaStore.objects.get(uuid=archive_id)
            group = None
            if archive:
                group = archive.group
            user = request.user
            if group and user:
                if request.method in SAFE_METHODS and group.is_public:
                    return True
                else:
                    if user in group.users.all():
                        return True
                    else:
                        self.message = "User does not belong to the group. Cannot modify any data."
                        return False
            else:
                self.message = "User or Group detail missing"
                return False

class IsAnnotateUpdateOrReadOnly(BasePermission):
    message = "You are not a member of the group to perform this action"

    def has_object_permission(self, request, view, obj):
        # User must be a part of the group.
        archive = MediaStore.objects.get(uuid=obj.media_reference_id)
        group = archive.group
        user = request.user
        if group and user:
            if user in group.users.all():
                return True
            else:
                self.message = "User does not belong to the group. Cannot modify any data."
                return False
        else:
            self.message = "User or Group detail missing"
            return False