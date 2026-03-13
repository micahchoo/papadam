from __future__ import annotations

from rest_framework import serializers

from papadapi.archive.models import MediaStore
from papadapi.common.serializers import GroupSerializer, TagsSerializer
from papadapi.users.serializers import UserSerializer


class MediaStoreSerializer(serializers.ModelSerializer):
    tags = TagsSerializer(many=True, read_only=True)
    group = GroupSerializer(read_only=True)
    created_by = UserSerializer(read_only=True)

    class Meta:
        model = MediaStore
        fields = (
            "id",
            "name",
            "description",
            "upload",
            "tags",
            "uuid",
            "created_at",
            "updated_at",
            "group",
            "created_by",
            "orig_size",
            "orig_name",
            "file_extension",
            "media_processing_status",
            "is_public",
            "extra_group_response",
            "transcript_vtt_url",
        )
        read_only_fields = (
            "uuid",
            "created_at",
            "updated_at",
        )
        depth = 1
