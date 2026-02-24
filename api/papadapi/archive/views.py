import json
import uuid
from datetime import timedelta

import structlog
from django.conf import settings
from django.core.files.storage import default_storage
from django.db.models import Count, Q
from django.db.models.functions import TruncDate
from rest_framework import generics, mixins, status, viewsets
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from papadapi.archive.permissions import (
    IsArchiveCopyAllowed,
    IsArchiveCreateOrReadOnly,
    IsArchiveUpdateOrReadOnly,
)
from papadapi.archive.signals import media_copied
from papadapi.common.functions import create_or_update_tag, recalculate_tag_count
from papadapi.common.models import Group, Question, Tags
from papadapi.common.serializers import CustomPageNumberPagination
from papadapi.queue import enqueue_after
from papadapi.users.permissions import IsSuperUser

from .models import MediaStore
from .serializers import MediaStatsSerializer, MediaStoreSerializer

log = structlog.get_logger(__name__)

class MediaStoreRemoveTag(
    mixins.RetrieveModelMixin, mixins.UpdateModelMixin, viewsets.GenericViewSet
):

    """
    Remove Tag from a media
    """

    queryset = MediaStore.objects.all()
    serializer_class = MediaStoreSerializer
    permission_classes = [IsArchiveUpdateOrReadOnly]

    lookup_field = "uuid"
    lookup_url_kwarg = "uuid"
    pagination_class = CustomPageNumberPagination

    def get_object(self):
        obj = super().get_object()
        # perform some extra checks on obj, e.g custom permissions
        return obj

    def update(self, request, *args, **kwargs):
        data = request.data

        obj = self.get_object()
        m = MediaStore.objects.get(uuid=obj.uuid)

        tags = data.get("tags")
        if tags:
            for tag_id in tags:
                t = Tags.objects.get(id=tag_id)
                m.tags.remove(t)
                recalculate_tag_count(t)
        serializer = MediaStoreSerializer(m)
        return Response(serializer.data)

class MediaStoreAddTag(
    mixins.RetrieveModelMixin, mixins.UpdateModelMixin, viewsets.GenericViewSet
):

    """
    Add Tag from a media
    """

    queryset = MediaStore.objects.all()
    serializer_class = MediaStoreSerializer
    permission_classes = [IsArchiveUpdateOrReadOnly]

    lookup_field = "uuid"
    lookup_url_kwarg = "uuid"
    pagination_class = CustomPageNumberPagination

    def get_object(self):
        obj = super().get_object()
        # perform some extra checks on obj, e.g custom permissions
        return obj

    def update(self, request, *args, **kwargs):
        data = request.data

        obj = self.get_object()
        m = MediaStore.objects.get(uuid=obj.uuid)

        tags = data.get("tags")
        if tags:
            for tag in tags:
                m.tags.add(create_or_update_tag(tag))
        serializer = MediaStoreSerializer(m)
        return Response(serializer.data)

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

    def get_object(self):
        obj = super().get_object()
        # perform some extra checks on obj, e.g custom permissions
        return obj

    def update(self, request, *args, **kwargs):
        data = request.data

        obj = self.get_object()
        m = MediaStore.objects.get(uuid=obj.uuid)

        name = data.get("name", m.name)
        description = data.get("description", m.description)
        extra_group_response = data.get("extra_group_response", m.extra_group_response)
        m.name = name
        m.description = description
        m.extra_group_response = extra_group_response
        m.save()
        serializer = MediaStoreSerializer(m)
        return Response(serializer.data)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)

    def perform_destroy(self, instance):
        obj = self.get_object()
        m = MediaStore.objects.get(id=obj.id)
        m.is_delete = True
        m.save()
        if m.group.delete_wait_for == 0:
            enqueue_after("delete_media_post_schedule", m.id, delay=10)
        else:
            enqueue_after(
                "delete_media_post_schedule",
                m.id,
                delay=timedelta(days=m.group.delete_wait_for),
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

    def update(self, request, *args, **kwargs):
        my_file=request.FILES.get('upload')

        obj = self.get_object()
        media = MediaStore.objects.get(uuid=obj.uuid)

        media.upload=my_file
        media.orig_name=my_file.name,
        media.file_extension=my_file.content_type,
        media.orig_size=my_file.size
        media.save()

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

    def get_queryset(self, *args, **kwargs):
        query = None
        search_query = self.request.GET.get("search")
        search_where = self.request.GET.get("searchWhere",None)
        search_from = self.request.GET.get("searchFrom",None)
        search_collections = self.request.GET.get("searchCollections",None)
        final_query = None
        group_query = None

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

        # search_from
        # Is anonymouus or non-logged in user :
        public_q = Q(group__in=Group.objects.filter(is_public=True, is_active=True))
        if self.request.user.is_anonymous:
            group_query = public_q
            if search_from in ("all_collections", "public"):
                group_query = public_q
            elif (
                search_from == "selected_collections"
                and search_collections is not None
            ):
                group_list = search_collections.split(",")
                group_query = Q(group__in=Group.objects.filter(id__in=group_list))
            else:
                pass
        else:
            if search_from == "all_collections":
                group_query = public_q | Q(
                    group__in=Group.objects.filter(users__in=[self.request.user])
                )
            if search_from == "my_collections":
                group_query = Q(
                    group__in=Group.objects.filter(users__in=[self.request.user])
                )
            elif search_from == "public":
                group_query = public_q
            elif (
                search_from == "selected_collections"
                and search_collections is not None
            ):
                group_list = search_collections.split(",")
                group_query = Q(group__in=Group.objects.filter(id__in=group_list))
            else:
                pass

        final_query = query & group_query if query else group_query

        if final_query:
            return (
                MediaStore.objects.filter(final_query & Q(is_delete=False))
                .distinct()
                .order_by("created_at")
            )
        else:
            return None

    def create(self, request, *args, **kwargs):
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
            extra_group_response = (
                json.loads(data["extra_group_response"])
                if "extra_group_response" in data
                else []
            )
            group_extra_response = []
            if extra_group_response and len(extra_group_response["answers"]) > 0:
                for answer in extra_group_response["answers"]:
                    q = answer["question_id"]
                    question = Question.objects.get(id=q)
                    if question:
                        group_extra_response.append(
                            {
                                "question_id": q,
                                "question": question.question,
                                "question_type": question.question_type,
                                "question_mandatory": question.question_mandatory,
                                "response": answer["response"],
                            }
                        )

            group_instance = Group.objects.get(id=group)
            try:
                m = MediaStore.objects.create(
                    name=name,
                    description=description,
                    group=group_instance,
                    extra_group_response=group_extra_response,
                    created_by=request.user,
                )
                m.upload = files
                m.orig_name = m.upload.name
                m.orig_size = m.upload.file.size
                m.file_extension = m.upload.file.content_type
                m.save()

                for tag in data["tags"].split(","):
                    m.tags.add(create_or_update_tag(tag))

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
                    m.media_processing_status = "Media unknown"
                    m.save()

                serializer = MediaStoreSerializer(m)
                return Response({**serializer.data, "job_id": job_id})

            except Exception as e:
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

    def update(self, request, *args, **kwargs):
        data = request.data
        obj_uuid = self.kwargs["uuid"]
        group_to = Group.objects.get(id=data["to_group"])
        extra_group_response = (
            json.loads(data["extra_group_response"])
            if "extra_group_response" in data
            else {}
        )
        group_extra_response = []
        if extra_group_response and len(extra_group_response["answers"]) > 0:
            for answer in extra_group_response["answers"]:
                q = answer["question_id"]
                question = Question.objects.get(id=q)
                if question:
                    group_extra_response.append(
                        {
                            "question_id": q,
                            "question": question.question,
                            "question_type": question.question_type,
                            "question_mandatory": question.question_mandatory,
                            "response": answer["response"],
                        }
                    )

        old_media = MediaStore.objects.get(uuid=obj_uuid)
        m = MediaStore.objects.get(uuid=obj_uuid)
        m.pk = None
        m._state.adding = True
        m.group = group_to
        m.extra_group_response = group_extra_response
        m.uuid = uuid.uuid4()
        m.save()
        if "copy_tags" in data and data["copy_tags"] == "True":
            for tag in old_media.tags.all():
                m.tags.add(create_or_update_tag(tag.name))
        if "copy_annotations" in data and data["copy_annotations"] == "True":
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

    def get_paginated_response(self, data):
        return Response(data)

    def get_queryset(self):
        data = (
            MediaStore.objects.values("id")
            .annotate(created_date=TruncDate("created_at"))
            .order_by("created_date")
            .values("created_date")
            .annotate(**{"total": Count("created_date")})
        )
        return data

class GroupMediaStats(
    viewsets.GenericViewSet, generics.ListAPIView, generics.RetrieveAPIView
):

    queryset = MediaStore.objects.all()
    serializer_class = MediaStatsSerializer
    permission_classes = [IsArchiveCreateOrReadOnly]
    lookup_field = "id"
    lookup_url_kwarg = "id"

    def retrieve(self, request, *args, **kwargs):
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


class MediaStoreTranscriptView(APIView):
    """POST /api/v1/archive/<uuid>/transcript/ — store a WebVTT file for a media item.

    Called by the transcribe worker after Whisper finishes.  Authenticated via
    the ``X-Internal-Key`` header (must match ``settings.INTERNAL_SERVICE_KEY``).
    Storing the VTT through Django's default storage backend lets us reuse
    whatever backend (MinIO, S3) is already configured.
    """

    permission_classes = [AllowAny]
    authentication_classes = []  # no JWT — key-based auth only

    def post(self, request, uuid: str) -> Response:
        expected: str = getattr(settings, "INTERNAL_SERVICE_KEY", "")
        key: str = request.headers.get("X-Internal-Key", "")
        if not expected or key != expected:
            return Response({"detail": "Forbidden."}, status=status.HTTP_403_FORBIDDEN)

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
