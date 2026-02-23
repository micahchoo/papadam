from rest_framework import serializers

from papadapi.annotate.models import Annotation
from papadapi.annotate.serializers import AnnotationSerializer

# Archive
from papadapi.archive.models import MediaStore

# Common
from papadapi.common.models import Tags
from papadapi.common.serializers import GroupSerializer, TagsSerializer
from papadapi.users.serializers import UserSerializer


class UpdateMediaStoreSerializer(serializers.ModelSerializer):
    tags = TagsSerializer(many=True, read_only=True)
    group = GroupSerializer(read_only=True)
    annotations = serializers.SerializerMethodField()

    class Meta:
        model = MediaStore
        fields = (
            "id",
            "name",
            "description",
            "upload",
            "tags",
            "extra_group_response",
            "uuid",
            "created_at",
            "group",
            "annotations",
            "updated_at",
            "orig_size",
            "orig_name",
            "file_extension"
            
        )
        read_only_fields = ("id", "created_at", "uuid")

    def get_annotations(self, obj):
        annotations = Annotation.objects.filter(
            media_reference_id=obj.uuid, is_delete=False
        )
        return AnnotationSerializer(annotations, many=True).data


class CreateMediaStoreSerializer(serializers.ModelSerializer):
    tags = TagsSerializer(many=True, read_only=True)
    group = GroupSerializer(read_only=True)
    annotations = serializers.SerializerMethodField()

    class Meta:
        model = MediaStore
        fields = (
            "id",
            "name",
            "description",
            "upload",
            "tags",
            "extra_group_response",
            "uuid",
            "created_at",
            "group",
            "annotations",
            "created_by",
            "updated_at",
            "orig_size",
            "orig_name",
            "file_extension"
            
        )
        read_only_fields = (
            "uuid",
            "created_at",
        )
        depth = 1

    def get_annotations(self, obj):
        annotations = Annotation.objects.filter(
            media_reference_id=obj.uuid, is_delete=False
        )
        return AnnotationSerializer(annotations, many=True).data


class MediaStoreSerializer(serializers.ModelSerializer):
    tags = TagsSerializer(many=True, read_only=True)
    group = GroupSerializer(read_only=True)
    annotations = serializers.SerializerMethodField()
    created_by = UserSerializer(read_only=True)

    class Meta:
        model = MediaStore
        fields = (
            "id",
            "name",
            "description",
            "upload",
            "tags",
            "extra_group_response",
            "uuid",
            "created_at",
            "group",
            "annotations",
            "created_by",
            "orig_size",
            "orig_name",
            "file_extension"
        )
        read_only_fields = (
            "uuid",
            "created_at",
        )
        depth = 1

    def get_annotations(self, obj):
        annotations = Annotation.objects.filter(
            media_reference_id=obj.uuid, is_delete=False
        )
        return AnnotationSerializer(annotations, many=True).data


class MediaStatsSerializer(serializers.Serializer):
    created_date = serializers.DateField()
    total = serializers.IntegerField()
