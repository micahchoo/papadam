import base64
import binascii

from rest_framework import serializers

from papadapi.crdt.models import YDocState


class Base64BinaryField(serializers.Field[str, bytes]):  # type: ignore[type-arg]  # TYPE_DEBT: djangorestframework-stubs Field expects 4 generic params; stubs version mismatch
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
        except (binascii.Error, ValueError) as exc:
            raise serializers.ValidationError("Invalid base64 encoding.") from exc


class YDocStateSerializer(serializers.ModelSerializer[YDocState]):
    state_vector = Base64BinaryField()

    class Meta:
        model = YDocState
        fields = ("media_uuid", "state_vector", "updated_at")
        read_only_fields = ("media_uuid", "updated_at")
