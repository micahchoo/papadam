from rest_framework import serializers

from papadapi.annotate.models import Annotation
from papadapi.archive.models import MediaStore

# Common
from papadapi.common.models import Group

# Archive
from papadapi.importexport.models import IERequest


class ExportGroupDataSerializer(serializers.ModelSerializer):
    class Meta:
        model = IERequest
        fields = (
            "request_id",
            "requested_at",
            "request_type",
            "is_authorized",
            "is_complete",
            "ie_metadata",
            "completed_at",
            "detail",
            "requested_file",
        )
        read_only_fields = ("request_id", "requested_at", "completed_at")


class ImportGroupDataSerializer(serializers.ModelSerializer):
    class Meta:
        model = IERequest
        fields = (
            "request_id",
            "requested_at",
            "request_type",
            "is_authorized",
            "is_complete",
            "ie_metadata",
            "completed_at",
            "detail",
        )
        read_only_fields = ("request_id", "requested_at", "completed_at")
