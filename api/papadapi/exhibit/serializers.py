from __future__ import annotations

from typing import TYPE_CHECKING, Any

from rest_framework import serializers

from papadapi.annotate.models import Annotation
from papadapi.archive.models import MediaStore
from papadapi.exhibit.models import Exhibit, ExhibitBlock

if TYPE_CHECKING:
    from uuid import UUID


class ExhibitBlockSerializer(serializers.ModelSerializer[ExhibitBlock]):
    class Meta:
        model = ExhibitBlock
        fields = (
            "id",
            "block_type",
            "media_uuid",
            "annotation_uuid",
            "caption",
            "order",
            "created_at",
        )
        read_only_fields = ("id", "created_at")

    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
        block_type = attrs.get("block_type", ExhibitBlock.BlockType.MEDIA)
        if block_type == ExhibitBlock.BlockType.MEDIA:
            media_uuid: UUID | None = attrs.get("media_uuid")
            if not media_uuid:
                raise serializers.ValidationError(
                    {"media_uuid": "Required for media-type blocks."}
                )
            if not MediaStore.objects.filter(uuid=media_uuid).exists():
                raise serializers.ValidationError(
                    {"media_uuid": "No MediaStore found with this UUID."}
                )
        if block_type == ExhibitBlock.BlockType.ANNOTATION:
            annotation_uuid: UUID | None = attrs.get("annotation_uuid")
            if not annotation_uuid:
                raise serializers.ValidationError(
                    {"annotation_uuid": "Required for annotation-type blocks."}
                )
            if not Annotation.objects.filter(uuid=annotation_uuid).exists():
                raise serializers.ValidationError(
                    {"annotation_uuid": "No Annotation found with this UUID."}
                )
        return attrs


class ExhibitSerializer(serializers.ModelSerializer[Exhibit]):
    blocks = ExhibitBlockSerializer(many=True, read_only=True)

    class Meta:
        model = Exhibit
        fields = (
            "id",
            "uuid",
            "title",
            "description",
            "is_public",
            "group",
            "created_by",
            "blocks",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "uuid", "created_by", "created_at", "updated_at")


class ExhibitWriteSerializer(serializers.ModelSerializer[Exhibit]):
    """Used for create/update — excludes nested blocks (managed separately)."""

    class Meta:
        model = Exhibit
        fields = ("uuid", "title", "description", "is_public", "group")
        read_only_fields = ("uuid",)
