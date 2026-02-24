
from rest_framework import mixins, status, viewsets
from rest_framework.response import Response

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

    def create(self, request, *args, **kwargs):
        data = request.data
        requested_by = self.request.user
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

    def create(self, request, *args, **kwargs):
        data = request.data
        files = request.FILES.get("upload", None)
        if not files:
            return Response(
                {"detail": "Media missing"}, status=status.HTTP_400_BAD_REQUEST
            )
        requested_by = self.request.user
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

    def retrieve(self, request, *args, **kwargs):
        request_id = self.kwargs["uuid"]
        queryset = IERequest.objects.filter(request_id=request_id)
        serializer = ExportGroupDataSerializer(queryset, many=True)
        return Response(data=serializer.data)


class UserImportExportViewer(viewsets.GenericViewSet, mixins.ListModelMixin):
    queryset = IERequest.objects.filter(is_complete=True)
    serializer_class = ExportGroupDataSerializer
    pagination_class = CustomPageNumberPagination

    def get_queryset(self):
        user = self.request.user
        return IERequest.objects.filter(requested_by=user)
