"""
media_relation/views.py — threaded replies and media-reference annotations.

These views layer on top of the existing Annotation model; no new DB tables.
The import-linter contract allows media_relation to import from annotate and
archive (they are below it in the dependency graph).
"""

from typing import TYPE_CHECKING, cast

import structlog
from rest_framework import status
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from papadapi.annotate.models import Annotation
from papadapi.annotate.serializers import AnnotationSerializer

if TYPE_CHECKING:
    from papadapi.users.models import User as UserModel

log = structlog.get_logger(__name__)


class AnnotationRepliesView(APIView):
    """
    GET  /api/v1/media-relation/replies/<annotation_uuid>/
         — list direct replies to an annotation

    POST /api/v1/media-relation/replies/<annotation_uuid>/
         — create a reply annotation (any AnnotationType except media_ref)
    """

    permission_classes = [IsAuthenticatedOrReadOnly]

    def _get_parent(self, annotation_uuid: str) -> Annotation | None:
        try:
            return Annotation.objects.get(uuid=annotation_uuid, is_delete=False)
        except Annotation.DoesNotExist:
            return None

    def get(self, request: Request, annotation_uuid: str) -> Response:
        parent = self._get_parent(annotation_uuid)
        if parent is None:
            return Response(
                {"detail": "Annotation not found."}, status=status.HTTP_404_NOT_FOUND
            )
        replies = Annotation.objects.filter(
            reply_to=parent, is_delete=False
        ).order_by("created_at")
        serializer = AnnotationSerializer(replies, many=True)
        return Response(serializer.data)

    def post(self, request: Request, annotation_uuid: str) -> Response:
        parent = self._get_parent(annotation_uuid)
        if parent is None:
            return Response(
                {"detail": "Annotation not found."}, status=status.HTTP_404_NOT_FOUND
            )

        data = {
            "media_reference_id": request.data.get(
                "media_reference_id", parent.media_reference_id
            ),
            "annotation_text": request.data.get("annotation_text", ""),
            "media_target": request.data.get("media_target", ""),
            "annotation_type": request.data.get("annotation_type", "text"),
        }
        reply = Annotation.objects.create(
            **data,
            reply_to=parent,
            group=parent.group,
            created_by=cast("UserModel", request.user),
        )
        if "tags" in request.data:
            from papadapi.common.functions import create_or_update_tag

            for tag in request.data["tags"].split(","):
                reply.tags.add(create_or_update_tag(tag.strip()))

        log.info(
            "reply_annotation_created",
            parent_uuid=str(parent.uuid),
            reply_uuid=str(reply.uuid),
        )
        serializer = AnnotationSerializer(reply)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class MediaRefAnnotationsView(APIView):
    """
    GET /api/v1/media-relation/media-refs/<media_uuid>/
        — list all annotations of type `media_ref` that reference this media.

    These are cross-media annotation links: one annotation pointing at
    another media item as its subject.
    """

    permission_classes = [IsAuthenticatedOrReadOnly]

    def get(self, request: Request, media_uuid: str) -> Response:
        annotations = Annotation.objects.filter(
            annotation_type=Annotation.AnnotationType.MEDIA_REF,
            media_ref_uuid=media_uuid,
            is_delete=False,
        ).order_by("created_at")
        serializer = AnnotationSerializer(annotations, many=True)
        return Response(serializer.data)
