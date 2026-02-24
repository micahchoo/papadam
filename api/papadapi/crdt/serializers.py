import base64

from rest_framework import serializers

from papadapi.crdt.models import YDocState


class Base64BinaryField(serializers.Field):
    """Encode BinaryField bytes as base64 for JSON transport."""

    def to_representation(self, value: bytes | memoryview) -> str:
        if isinstance(value, memoryview):
            value = bytes(value)
        return base64.b64encode(value).decode("ascii")

    def to_internal_value(self, data: str) -> bytes:
        if not isinstance(data, str):
            raise serializers.ValidationError("Expected a base64-encoded string.")
        try:
            return base64.b64decode(data)
        except Exception as exc:
            raise serializers.ValidationError("Invalid base64 encoding.") from exc


class YDocStateSerializer(serializers.ModelSerializer):
    state_vector = Base64BinaryField()

    class Meta:
        model = YDocState
        fields = ("media_uuid", "state_vector", "updated_at")
        read_only_fields = ("media_uuid", "updated_at")
