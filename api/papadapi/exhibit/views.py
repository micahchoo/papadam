"""
exhibit/views.py — CRUD for Exhibit and ExhibitBlock.
"""

from typing import Any, cast

import structlog
from django.db import transaction
from django.db.models import QuerySet
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.serializers import BaseSerializer

from papadapi.common.models import Group
from papadapi.exhibit.models import Exhibit, ExhibitBlock
from papadapi.exhibit.permissions import IsExhibitGroupMemberOrReadOnly
from papadapi.exhibit.serializers import (
    ExhibitBlockSerializer,
    ExhibitSerializer,
    ExhibitWriteSerializer,
)

log = structlog.get_logger(__name__)


class ExhibitViewSet(
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
    mixins.ListModelMixin,
    viewsets.GenericViewSet[Exhibit],
):
    """
    list:   GET  /api/v1/exhibit/                — public exhibits
    create: POST /api/v1/exhibit/                — authenticated
    retrieve: GET /api/v1/exhibit/<uuid>/
    update: PUT  /api/v1/exhibit/<uuid>/
    destroy: DELETE /api/v1/exhibit/<uuid>/
    blocks: POST /api/v1/exhibit/<uuid>/blocks/  — add a block
    """

    lookup_field = "uuid"
    permission_classes = [IsAuthenticatedOrReadOnly, IsExhibitGroupMemberOrReadOnly]

    def get_serializer_class(self) -> type[BaseSerializer[Any]]:
        if self.action in ("create", "update", "partial_update"):
            return ExhibitWriteSerializer
        return ExhibitSerializer

    def get_queryset(self) -> QuerySet[Exhibit]:
        user = self.request.user
        if user.is_anonymous:
            return Exhibit.objects.filter(is_public=True).select_related("group")
        return Exhibit.objects.filter(
            group__in=Group.objects.filter(users__in=[user])
        ).select_related("group") | Exhibit.objects.filter(is_public=True)

    def perform_create(self, serializer: BaseSerializer[Any]) -> None:
        instance = cast("Exhibit", serializer.save(created_by=self.request.user))
        log.info("exhibit_created", title=instance.title)

    @action(
        detail=True,
        methods=["get", "post"],
        url_path="blocks",
        permission_classes=[IsAuthenticatedOrReadOnly, IsExhibitGroupMemberOrReadOnly],
    )
    def blocks(self, request: Request, uuid: str | None = None) -> Response:
        """GET|POST /api/v1/exhibit/<uuid>/blocks/ — list or append blocks."""
        exhibit = self.get_object()
        if request.method == "POST":
            serializer = ExhibitBlockSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            serializer.save(exhibit=exhibit)
            log.info("exhibit_block_added", exhibit_uuid=str(exhibit.uuid))
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        blocks_qs = ExhibitBlock.objects.filter(exhibit=exhibit).order_by("order")
        serializer = ExhibitBlockSerializer(blocks_qs, many=True)
        return Response(serializer.data)

    @action(
        detail=True,
        methods=["delete"],
        url_path=r"blocks/(?P<block_id>\d+)",
        permission_classes=[IsAuthenticated, IsExhibitGroupMemberOrReadOnly],
    )
    def delete_block(
        self, request: Request, uuid: str | None = None, block_id: str | None = None
    ) -> Response:
        """DELETE /api/v1/exhibit/<uuid>/blocks/<block_id>/ — remove a block."""
        exhibit = self.get_object()
        try:
            block = ExhibitBlock.objects.get(id=int(block_id or 0), exhibit=exhibit)
        except ExhibitBlock.DoesNotExist:
            return Response(
                {"detail": "Block not found."}, status=status.HTTP_404_NOT_FOUND
            )
        block.delete()
        log.info(
            "exhibit_block_deleted", exhibit_uuid=str(exhibit.uuid), block_id=block_id
        )
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=True,
        methods=["post"],
        url_path="blocks/reorder",
        permission_classes=[IsAuthenticated, IsExhibitGroupMemberOrReadOnly],
    )
    def reorder_blocks(self, request: Request, uuid: str | None = None) -> Response:
        """POST /api/v1/exhibit/<uuid>/blocks/reorder/ — set display order.

        Body: {"block_ids": [<id>, <id>, ...]}  — ordered list of block PKs
        belonging to this exhibit. Each block's ``order`` is set to its index
        in the supplied list.  All IDs must belong to this exhibit.
        """
        exhibit = self.get_object()
        block_ids: Any = request.data.get("block_ids")
        if not isinstance(block_ids, list) or not all(
            isinstance(i, int) for i in block_ids
        ):
            return Response(
                {"detail": "block_ids must be a list of integers."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        blocks_by_id = {
            b.id: b
            for b in ExhibitBlock.objects.filter(exhibit=exhibit, id__in=block_ids)
        }
        if len(blocks_by_id) != len(block_ids):
            return Response(
                {"detail": "Some block IDs not found in this exhibit."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        for idx, block_id in enumerate(block_ids):
            blocks_by_id[block_id].order = idx
        with transaction.atomic():
            ExhibitBlock.objects.bulk_update(list(blocks_by_id.values()), ["order"])
        log.info("exhibit_blocks_reordered", exhibit_uuid=str(exhibit.uuid))
        updated_qs = ExhibitBlock.objects.filter(exhibit=exhibit).order_by("order")
        return Response(ExhibitBlockSerializer(updated_qs, many=True).data)
