"""
exhibit/views.py — CRUD for Exhibit and ExhibitBlock.
"""

from typing import Any, cast

import structlog
from django.db.models import QuerySet
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.serializers import BaseSerializer

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
        permission_classes=[IsAuthenticatedOrReadOnly],
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
