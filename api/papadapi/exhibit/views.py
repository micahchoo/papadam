"""
exhibit/views.py — CRUD for Exhibit and ExhibitBlock.
"""

import structlog
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from rest_framework.request import Request
from rest_framework.response import Response

from papadapi.common.models import Group
from papadapi.exhibit.models import Exhibit, ExhibitBlock
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
    viewsets.GenericViewSet,
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
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get_serializer_class(self):
        if self.action in ("create", "update", "partial_update"):
            return ExhibitWriteSerializer
        return ExhibitSerializer

    def get_queryset(self):
        user = self.request.user
        if user.is_anonymous:
            return Exhibit.objects.filter(is_public=True).select_related("group")
        return Exhibit.objects.filter(
            group__in=Group.objects.filter(users__in=[user])
        ).select_related("group") | Exhibit.objects.filter(is_public=True)

    def perform_create(self, serializer: ExhibitWriteSerializer) -> None:
        serializer.save(created_by=self.request.user)
        log.info("exhibit_created", title=serializer.instance.title)

    @action(
        detail=True,
        methods=["post"],
        url_path="blocks",
        permission_classes=[IsAuthenticated],
    )
    def add_block(self, request: Request, uuid: str | None = None) -> Response:
        """POST /api/v1/exhibit/<uuid>/blocks/ — append a block to this exhibit."""
        exhibit = self.get_object()
        serializer = ExhibitBlockSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(exhibit=exhibit)
        log.info("exhibit_block_added", exhibit_uuid=str(exhibit.uuid))
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(
        detail=True,
        methods=["get"],
        url_path="blocks",
        permission_classes=[IsAuthenticatedOrReadOnly],
    )
    def list_blocks(self, request: Request, uuid: str | None = None) -> Response:
        """GET /api/v1/exhibit/<uuid>/blocks/ — list blocks for this exhibit."""
        exhibit = self.get_object()
        blocks = ExhibitBlock.objects.filter(exhibit=exhibit).order_by("order")
        serializer = ExhibitBlockSerializer(blocks, many=True)
        return Response(serializer.data)
