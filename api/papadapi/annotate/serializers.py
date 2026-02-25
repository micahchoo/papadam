from __future__ import annotations

from rest_framework import serializers

from papadapi.annotate.models import Annotation
from papadapi.common.serializers import TagsSerializer
from papadapi.users.serializers import UserSerializer


class AnnotationSerializer(serializers.ModelSerializer):
    tags = TagsSerializer(many=True, read_only=True)
    created_by = UserSerializer(read_only=True)
    annotation_type = serializers.ChoiceField(
        choices=Annotation.AnnotationType.choices,
        default=Annotation.AnnotationType.TEXT,
    )

    class Meta:
        model = Annotation
        fields = (
            "id",
            "annotation_text",
            "annotation_type",
            "tags",
            "media_reference_id",
            "media_target",
            "annotation_image",
            "annotation_audio",
            "annotation_video",
            "reply_to",
            "media_ref_uuid",
            "uuid",
            "created_at",
            "updated_at",
            "created_by",
        )
        read_only_fields = (
            "id",
            "uuid",
            "created_at",
            "updated_at",
            "created_by",
        )


class AnnotationStatsSerializer(serializers.Serializer):
    created_date = serializers.DateField()
    total = serializers.IntegerField()
