from __future__ import annotations

import uuid
from datetime import timedelta
from typing import TYPE_CHECKING, Any

import structlog
from django.core.files.storage import default_storage
from django.db.models import Count, Q
from django.db.models.functions import TruncDate
from rest_framework import generics, mixins, status, viewsets
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

if TYPE_CHECKING:
    from django.db.models import QuerySet
    from rest_framework.request import Request

from papadapi.archive.permissions import (
    IsArchiveCopyAllowed,
    IsArchiveCreateOrReadOnly,
    IsArchiveUpdateOrReadOnly,
)
from papadapi.archive.signals import media_copied
from papadapi.common.authentication import InternalServiceKeyAuthentication
from papadapi.common.functions import (
    build_extra_group_response,
    build_group_filter,
    create_or_update_tag,
    is_truthy,
)
from papadapi.common.mixins import TagAddMixin, TagRemoveMixin
from papadapi.common.models import Group
from papadapi.common.serializers import (
    CustomPageNumberPagination,
)
from papadapi.common.serializers import (
    DailyStatsSerializer as MediaStatsSerializer,
)
from papadapi.queue import enqueue_after
from papadapi.users.permissions import IsSuperUser

from .models import MediaStore
from .serializers import MediaStoreSerializer

log = structlog.get_logger(__name__)

class MediaStoreRemoveTag(
    TagRemoveMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    viewsets.GenericViewSet,
):
    """Remove Tag from a media."""

    queryset = MediaStore.objects.all()
    serializer_class = MediaStoreSerializer
    permission_classes = [IsArchiveUpdateOrReadOnly]
    pagination_class = CustomPageNumberPagination
    lookup_field = "uuid"
    lookup_url_kwarg = "uuid"


class MediaStoreAddTag(
    TagAddMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    viewsets.GenericViewSet,
):
    """Add Tag to a media."""

    queryset = MediaStore.objects.all()
    serializer_class = MediaStoreSerializer
    permission_classes = [IsArchiveUpdateOrReadOnly]
    pagination_class = CustomPageNumberPagination
    lookup_field = "uuid"
    lookup_url_kwarg = "uuid"

class MediaStoreUpdateSet(
    mixins.RetrieveModelMixin, mixins.UpdateModelMixin, viewsets.GenericViewSet
):

    """
    Update a given media set
    """

    queryset = MediaStore.objects.all()
    serializer_class = MediaStoreSerializer
    permission_classes = [IsArchiveUpdateOrReadOnly]

    lookup_field = "uuid"
    lookup_url_kwarg = "uuid"
    pagination_class = CustomPageNumberPagination

    def update(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        data = request.data
        m = self.get_object()

        m.name = data.get("name", m.name)
        m.description = data.get("description", m.description)
        m.extra_group_response = data.get(
            "extra_group_response", m.extra_group_response
        )
        m.save()
        serializer = MediaStoreSerializer(m)
        return Response(serializer.data)

    def destroy(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)

    def perform_destroy(self, instance: MediaStore) -> None:
        instance.is_delete = True
        instance.save()
        if instance.group.delete_wait_for == 0:
            enqueue_after("delete_media_post_schedule", instance.id, delay=10)
        else:
            enqueue_after(
                "delete_media_post_schedule",
                instance.id,
                delay=timedelta(days=instance.group.delete_wait_for),
            )

class MediaStoreUploadFileView(
    mixins.UpdateModelMixin, viewsets.GenericViewSet
):
    """
    Upload file to an existing archive record
    """

    queryset = MediaStore.objects.all()
    permission_classes = [IsArchiveCreateOrReadOnly]

    serializer_class = MediaStoreSerializer
    pagination_class = CustomPageNumberPagination

    lookup_field = "uuid"
    lookup_url_kwarg = "uuid"

    def update(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        my_file = request.FILES.get('upload')
        media = self.get_object()

        media.upload = my_file
        media.orig_name = my_file.name
        media.file_extension = my_file.content_type
        media.orig_size = my_file.size
        media.save()
        return Response(status=status.HTTP_204_NO_CONTENT)

class MediaStoreCreateSet(
    mixins.CreateModelMixin, mixins.ListModelMixin, viewsets.GenericViewSet
):
    """
    Creates MediaStore
    """

    queryset = MediaStore.objects.all()
    permission_classes = [IsArchiveCreateOrReadOnly]

    serializer_class = MediaStoreSerializer
    pagination_class = CustomPageNumberPagination

    def get_queryset(self) -> QuerySet[MediaStore] | None:  # type: ignore[override]  # TYPE_DEBT: returns None for empty search
        query = None
        search_query = self.request.GET.get("search")
        search_where = self.request.GET.get("searchWhere",None)
        search_from = self.request.GET.get("searchFrom",None)
        search_collections = self.request.GET.get("searchCollections",None)

        # By default search in name and description unless overridden
        if search_query and not search_where:
            query = (
                Q(name__icontains=search_query)
                | Q(description__icontains=search_query)
            )
        if search_where and search_query:
            if search_where == "name":
                query = Q(name__icontains=search_query)
            elif search_where == "description":
                query = Q(description__icontains=search_query)
            elif search_where == "tags":
                query = Q(tags__name__in=search_query)

        group_query = build_group_filter(
            self.request.user, search_from, search_collections,
        )

        if query and group_query:
            final_query = query & group_query
        else:
            final_query = query or group_query

        # mediaType filter: narrows by MIME prefix (audio/video/image).
        # Unknown values silently ignored — no 400, preserves existing client behaviour.
        _ALLOWED_MEDIA_TYPES: frozenset[str] = frozenset({"audio", "video", "image"})
        media_type_param = self.request.GET.get("mediaType")
        if media_type_param in _ALLOWED_MEDIA_TYPES:
            media_type_q = Q(file_extension__startswith=media_type_param)
            final_query = final_query & media_type_q if final_query else media_type_q

        if final_query:
            return (
                MediaStore.objects.filter(final_query & Q(is_delete=False))
                .distinct()
                .order_by("created_at")
            )
        else:
            return None

    def create(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        data = request.data
        if "upload" not in request.FILES:
            return Response(
                {"detail": "Media missing"}, status=status.HTTP_400_BAD_REQUEST
            )
        files = request.FILES["upload"]
        group = data.get("group")
        if group:
            if "name" not in data or data["name"] == "":
                return Response(
                    {"detail": "Name not found"}, status=status.HTTP_400_BAD_REQUEST
                )
            name = data["name"]
            description = data["description"]
            group_extra_response = build_extra_group_response(
                data.get("extra_group_response", "[]")
            )

            group_instance = Group.objects.get(id=group)
            try:
                m = MediaStore.objects.create(
                    name=name,
                    description=description,
                    group=group_instance,
                    extra_group_response=group_extra_response,
                    created_by=request.user,  # type: ignore[misc]  # TYPE_DEBT: view requires auth; user is always User
                )
                m.upload = files
                m.orig_name = m.upload.name
                m.orig_size = m.upload.file.size
                m.file_extension = m.upload.file.content_type
                m.save()

                for tag in data["tags"].split(","):
                    tag_obj = create_or_update_tag(tag)
                    if tag_obj:
                        m.tags.add(tag_obj)

                job_id: str | None = None
                media_type = m.file_extension.split("/")[0]
                if media_type == "video":
                    job_id = enqueue_after(
                        "convert_to_hls", m.id, "/tmp/upload/", delay=10
                    )
                elif media_type == "audio":
                    job_id = enqueue_after(
                        "convert_to_hls_audio", m.id, "/tmp/upload/", delay=10
                    )
                else:
                    m.media_processing_status = (
                        MediaStore.ProcessingStatus.MEDIA_UNKNOWN
                    )
                    m.save()

                serializer = MediaStoreSerializer(m)
                return Response({**serializer.data, "job_id": job_id})

            except Exception as e:  # noqa: BLE001 — cleanup handler for any file-upload failure; narrowing is impractical
                # Clean up: delete metadata if the file upload failed
                if m.pk:  # Check if the instance was saved to the database
                    m.delete()
                return Response(
                    {"detail": f"An error occurred: {e!s}"},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )
        else:
            return Response(
                {"detail": "Group data missing"}, status=status.HTTP_400_BAD_REQUEST
            )

class MediaStoreCopySet(
    mixins.UpdateModelMixin, mixins.ListModelMixin, viewsets.GenericViewSet
):
    """
    Creates MediaStore
    """

    queryset = MediaStore.objects.all()
    permission_classes = [IsArchiveCopyAllowed]
    lookup_field = "uuid"
    lookup_url_kwarg = "uuid"
    serializer_class = MediaStoreSerializer
    pagination_class = CustomPageNumberPagination

    def update(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        data = request.data
        obj_uuid = self.kwargs["uuid"]
        group_to = Group.objects.get(id=data["to_group"])
        group_extra_response = build_extra_group_response(
            data.get("extra_group_response", "{}")
        )

        old_media = MediaStore.objects.get(uuid=obj_uuid)
        m = MediaStore.objects.get(uuid=obj_uuid)  # clone source — pk nulled below
        m.pk = None
        m._state.adding = True
        m.group = group_to
        m.extra_group_response = group_extra_response
        m.uuid = uuid.uuid4()
        m.save()
        if is_truthy(data.get("copy_tags", False)):
            for tag in old_media.tags.all():
                tag_obj = create_or_update_tag(tag.name)
                if tag_obj:
                    m.tags.add(tag_obj)
        if is_truthy(data.get("copy_annotations", False)):
            media_copied.send(
                sender=self.__class__,
                old_uuid=str(obj_uuid),
                new_uuid=str(m.uuid),
            )
        serializer = MediaStoreSerializer(m)
        return Response(serializer.data)

class InstanceMediaStats(viewsets.GenericViewSet, generics.ListAPIView):

    queryset = MediaStore.objects.all()
    serializer_class = MediaStatsSerializer
    permission_classes = [IsSuperUser]

    def get_paginated_response(self, data: list[dict[str, Any]]) -> Response:
        return Response(data)

    def get_queryset(self) -> QuerySet[MediaStore]:
        data = (
            MediaStore.objects.values("id")
            .annotate(created_date=TruncDate("created_at"))
            .order_by("created_date")
            .values("created_date")
            .annotate(**{"total": Count("created_date")})
        )
        return data  # type: ignore[return-value]

class GroupMediaStats(
    viewsets.GenericViewSet, generics.ListAPIView, generics.RetrieveAPIView
):

    queryset = MediaStore.objects.all()
    serializer_class = MediaStatsSerializer
    permission_classes = [IsArchiveCreateOrReadOnly]
    lookup_field = "id"
    lookup_url_kwarg = "id"

    def retrieve(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        group_id = self.kwargs.get("id")
        if group_id:

            base_data = (
                MediaStore.objects.filter(group=Group.objects.get(id=int(group_id)))
                .values("id")
                .annotate(created_date=TruncDate("created_at"))
                .order_by("created_date")
                .values("created_date")
                .annotate(**{"total": Count("created_date")})
            )
            serializer = MediaStatsSerializer(base_data, many=True)
            return Response(serializer.data)
        return Response(status=status.HTTP_404_NOT_FOUND)


class MediaStoreTranscriptView(APIView):
    """POST /api/v1/archive/<uuid>/transcript/ — store a WebVTT file for a media item.

    Called by the transcribe worker after Whisper finishes.  Authenticated via
    the ``X-Internal-Key`` header (must match ``settings.INTERNAL_SERVICE_KEY``).
    Storing the VTT through Django's default storage backend lets us reuse
    whatever backend (MinIO, S3) is already configured.
    """

    permission_classes = [AllowAny]
    authentication_classes = [InternalServiceKeyAuthentication]

    def post(self, request: Request, uuid: str) -> Response:
        vtt_file = request.FILES.get("vtt")
        if not vtt_file:
            return Response(
                {"detail": "vtt file required."}, status=status.HTTP_400_BAD_REQUEST
            )

        try:
            m = MediaStore.objects.get(uuid=uuid)
        except MediaStore.DoesNotExist:
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)

        vtt_path = default_storage.save(f"transcripts/{uuid}.vtt", vtt_file)
        m.transcript_vtt_url = default_storage.url(vtt_path)
        m.save(update_fields=["transcript_vtt_url"])
        log.info("transcript_saved", media_uuid=uuid, url=m.transcript_vtt_url)
        return Response({"transcript_vtt_url": m.transcript_vtt_url})
