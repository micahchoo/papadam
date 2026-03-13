from __future__ import annotations

from typing import Any

from rest_framework import serializers

from papadapi.annotate.models import Annotation
from papadapi.archive.models import MediaStore
from papadapi.common.models import Group
from papadapi.common.serializers import TagsSerializer
from papadapi.users.serializers import UserSerializer

MAX_REPLY_DEPTH = 2  # 0-indexed: root=0, reply=1, reply-to-reply=2


def compute_depth(annotation: Annotation) -> int:
    """Walk reply_to chain, capped at MAX_REPLY_DEPTH + 1 hops."""
    depth = 0
    current = annotation
    while current.reply_to_id is not None and depth <= MAX_REPLY_DEPTH:
        current = Annotation.objects.only("id", "reply_to_id").get(
            pk=current.reply_to_id,
        )
        depth += 1
    return depth


class AnnotationSerializer(serializers.ModelSerializer):
    tags = TagsSerializer(many=True, read_only=True)
    created_by = UserSerializer(read_only=True)
    annotation_type = serializers.ChoiceField(
        choices=Annotation.AnnotationType.choices,
        default=Annotation.AnnotationType.TEXT,
    )
    # The model uses URLField but the app stores bare UUIDs; override to skip
    # URL validation so existing data and clients are accepted.
    media_reference_id = serializers.CharField(max_length=500)
    # Allow blank — audio/video/image annotations may have no text body.
    annotation_text = serializers.CharField(
        allow_blank=True, required=False, default=""
    )
    # Allow blank — replies inherit parent target; callers may omit it.
    media_target = serializers.CharField(
        max_length=100, allow_blank=True, required=False, default=""
    )
    group = serializers.SerializerMethodField()

    def get_group(self, obj: Annotation) -> int | None:
        return obj.group_id

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
            "group",
        )
        read_only_fields = (
            "id",
            "uuid",
            "created_at",
            "updated_at",
            "created_by",
        )

    def validate_reply_to(self, value: Annotation | None) -> Annotation | None:
        if value is None:
            return None
        if value.group is None:
            raise serializers.ValidationError(
                "Cannot reply to an annotation with no group."
            )
        parent_depth = compute_depth(value)
        if parent_depth >= MAX_REPLY_DEPTH:
            raise serializers.ValidationError(
                f"Maximum reply depth ({MAX_REPLY_DEPTH}) exceeded."
            )
        return value

    def validate_media_ref_uuid(self, value: Any) -> Any:
        if value is None:
            return None
        try:
            media = MediaStore.objects.get(uuid=value)
        except MediaStore.DoesNotExist:
            raise serializers.ValidationError(
                "Referenced media does not exist."
            ) from None
        request = self.context.get("request")
        if (
            request
            and request.user
            and not request.user.is_anonymous
            and not Group.objects.filter(users=request.user, pk=media.group_id).exists()
        ):
            raise serializers.ValidationError(
                "You do not have access to the referenced media."
            )
        return value

    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
        """Cross-field: reply_to must be in the same group as the target media."""
        reply_to = attrs.get("reply_to")
        media_ref_id = attrs.get("media_reference_id")
        if reply_to and media_ref_id:
            try:
                target_media = MediaStore.objects.get(uuid=media_ref_id)
            except MediaStore.DoesNotExist:
                raise serializers.ValidationError(
                    {"media_reference_id": "Target media does not exist."}
                ) from None
            if reply_to.group_id != target_media.group_id:
                raise serializers.ValidationError(
                    {"reply_to": "Reply must be to an annotation in the same group."}
                )
        return attrs
