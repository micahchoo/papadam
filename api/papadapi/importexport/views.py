from __future__ import annotations

from typing import TYPE_CHECKING

from rest_framework import mixins, status, viewsets
from rest_framework.response import Response

if TYPE_CHECKING:
    from django.db.models import QuerySet
    from rest_framework.request import Request

    from papadapi.users.models import User

from papadapi.common.serializers import CustomPageNumberPagination
from papadapi.importexport.models import IERequest
from papadapi.importexport.serializers import (
    ExportGroupDataSerializer,
)
from papadapi.queue import enqueue_after


class ExportGroupCreateListSet(
    viewsets.GenericViewSet, mixins.ListModelMixin, mixins.CreateModelMixin
):
    queryset = IERequest.objects.filter(is_complete=True)
    serializer_class = ExportGroupDataSerializer
    pagination_class = CustomPageNumberPagination

    def create(self, request: Request, *args: object, **kwargs: object) -> Response:
        data = request.data
        requested_by: User = self.request.user  # type: ignore[assignment]

        # Verify the user has access to the requested resource
        export_type = data.get("type")
        export_id = data.get("id")
        if export_type == "group" and export_id:
            from papadapi.common.models import Group
            from papadapi.common.permissions import user_can_access_group

            try:
                group = Group.objects.get(id=export_id)
            except Group.DoesNotExist:
                return Response(
                    {"detail": "Group not found."},
                    status=status.HTTP_404_NOT_FOUND,
                )
            if not user_can_access_group(requested_by, group, is_safe_method=False):
                return Response(
                    {"detail": "You are not a member of this group."},
                    status=status.HTTP_403_FORBIDDEN,
                )

        request_type = "export"
        ie_metadata = data
        ie = IERequest.objects.create(
            requested_by=requested_by,
            request_type=request_type,
            ie_metadata=ie_metadata,
        )
        enqueue_after("export_request_task", ie.id, delay=1)
        serilizer = ExportGroupDataSerializer(ie)
        return Response(serilizer.data)


class ImportGroupCreateSet(viewsets.GenericViewSet, mixins.CreateModelMixin):
    queryset = IERequest.objects.filter(is_complete=True)
    serializer_class = ExportGroupDataSerializer
    pagination_class = CustomPageNumberPagination

    def create(self, request: Request, *args: object, **kwargs: object) -> Response:
        data = request.data
        files = request.FILES.get("upload", None)
        if not files:
            return Response(
                {"detail": "Media missing"}, status=status.HTTP_400_BAD_REQUEST
            )
        requested_by: User = self.request.user  # type: ignore[assignment]
        request_type = "import"
        ie_metadata = data["ie_metadata"]
        ie = IERequest.objects.create(
            requested_by=requested_by,
            request_type=request_type,
            ie_metadata=ie_metadata,
        )
        ie.requested_file = files
        ie.save()
        enqueue_after("import_request_task", ie.id, delay=1)
        serilizer = ExportGroupDataSerializer(ie)
        return Response(serilizer.data)


class ImportExportGroupViewSet(viewsets.GenericViewSet, mixins.RetrieveModelMixin):
    queryset = IERequest.objects.filter(is_complete=True)
    serializer_class = ExportGroupDataSerializer
    pagination_class = CustomPageNumberPagination
    lookup_field = "uuid"
    lookup_url_kwarg = "uuid"

    def retrieve(self, request: Request, *args: object, **kwargs: object) -> Response:
        request_id = self.kwargs["uuid"]
        queryset = IERequest.objects.filter(request_id=request_id)
        serializer = ExportGroupDataSerializer(queryset, many=True)
        return Response(data=serializer.data)


class UserImportExportViewer(viewsets.GenericViewSet, mixins.ListModelMixin):
    queryset = IERequest.objects.filter(is_complete=True)
    serializer_class = ExportGroupDataSerializer
    pagination_class = CustomPageNumberPagination

    def get_queryset(self) -> QuerySet[IERequest]:
        user: User = self.request.user  # type: ignore[assignment]
        return IERequest.objects.filter(requested_by=user)
