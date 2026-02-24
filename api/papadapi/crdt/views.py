"""
crdt/views.py — Y.js document persistence bridge.

The CRDT WebSocket server (Node/y-websocket) calls these endpoints to load
and save document state so that it survives container restarts.
"""

import uuid as _uuid

import structlog
from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from papadapi.crdt.models import YDocState
from papadapi.crdt.serializers import YDocStateSerializer

log = structlog.get_logger(__name__)


class YDocStateView(APIView):
    """
    GET  /api/v1/crdt/<media_uuid>/  — load document state
    PUT  /api/v1/crdt/<media_uuid>/  — save (upsert) document state

    The CRDT server is the only writer; human clients are read-only here.
    Authentication is enforced by the global DRF JWT policy.
    """

    def get(self, request: Request, media_uuid: str) -> Response:
        try:
            state = YDocState.objects.get(media_uuid=media_uuid)
        except YDocState.DoesNotExist:
            return Response(
                {"detail": "No document state found for this media."},
                status=status.HTTP_404_NOT_FOUND,
            )
        serializer = YDocStateSerializer(state)
        return Response(serializer.data)

    def put(self, request: Request, media_uuid: str) -> Response:
        try:
            uuid_val = _uuid.UUID(str(media_uuid))
        except ValueError:
            return Response(
                {"detail": "Invalid media UUID."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        state, created = YDocState.objects.get_or_create(media_uuid=uuid_val)
        serializer = YDocStateSerializer(state, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)

        # state_vector is the only mutable field exposed via PUT
        raw = serializer.validated_data.get("state_vector")
        if raw is not None:
            state.state_vector = raw
            state.save(update_fields=["state_vector", "updated_at"])

        log.info(
            "crdt_state_saved",
            media_uuid=str(uuid_val),
            created=created,
            bytes=len(raw) if raw else 0,
        )
        serializer = YDocStateSerializer(state)
        return Response(
            serializer.data,
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
        )
