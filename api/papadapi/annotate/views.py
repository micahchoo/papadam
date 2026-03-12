from __future__ import annotations

from datetime import timedelta
from typing import TYPE_CHECKING, Any, cast

from django.db.models import Count, Q
from django.db.models.functions import TruncDate
from rest_framework import generics, mixins, status, viewsets
from rest_framework.response import Response

if TYPE_CHECKING:
    from django.db.models import QuerySet
    from rest_framework.request import Request

    from papadapi.users.models import User

from papadapi.annotate.permissions import (
    IsAnnotateCreateOrReadOnly,
    IsAnnotateUpdateOrReadOnly,
)
from papadapi.archive.models import MediaStore
from papadapi.common.functions import create_or_update_tag, recalculate_tag_count
from papadapi.common.models import Group, Tags
from papadapi.common.serializers import CustomPageNumberPagination
from papadapi.queue import enqueue, enqueue_after
from papadapi.users.permissions import IsSuperUser

from .models import Annotation
from .serializers import AnnotationSerializer, AnnotationStatsSerializer


class AnnotationCreateSet(
    mixins.CreateModelMixin, mixins.ListModelMixin, viewsets.GenericViewSet
):
    """
    Creates and allows search of Annotation belonging to a media store
    """

    queryset = Annotation.objects.filter(is_delete=False)
    serializer_class = AnnotationSerializer
    permission_classes = [IsAnnotateCreateOrReadOnly]

    def get_queryset(self) -> QuerySet[Annotation]:  # type: ignore[override]
        query = None
        search_query = self.request.GET.get("search")
        search_where = self.request.GET.get("searchWhere", None)
        search_from = self.request.GET.get("searchFrom", None)
        search_collections = self.request.GET.get("searchCollections", None)
        group_query = None

        # By default search in name and description unless overridden
        if search_query:
            if search_where == "name":
                query = Q(annotation_text__icontains=search_query)
            elif search_where == "tags":
                query = Q(tags__name__in=search_query)

        annotation_type = self.request.GET.get("annotation_type")
        if annotation_type:
            type_query = Q(annotation_type=annotation_type)
            query = query & type_query if query else type_query

        if self.request.user.is_anonymous:
            group_query = Q(
                group__in=Group.objects.filter(is_public=True, is_active=True)
            )
        else:
            if search_from == "all_collections":
                group_query = Q(
                    group__in=Group.objects.filter(is_public=True, is_active=True)
                ) | Q(group__in=Group.objects.filter(users__in=[self.request.user]))

            elif search_from == "my_collections":
                group_query = Q(
                    group__in=Group.objects.filter(users__in=[self.request.user])
                )
            elif search_from == "public":
                group_query = Q(
                    group__in=Group.objects.filter(is_public=True, is_active=True)
                )
            elif (
                search_from == "selected_collections"
                and search_collections is not None
            ):
                group_list = search_collections.split(",")
                group_query = Q(mediagroup__in=Group.objects.filter(id__in=group_list))
            else:
                # Support ?group=<id> shorthand from frontend
                group_param = self.request.GET.get("group")
                if group_param:
                    group_query = Q(
                        group_id=group_param,
                        group__in=Group.objects.filter(users__in=[self.request.user])
                        | Group.objects.filter(is_public=True, is_active=True),
                    )
                else:
                    # Bare list: show all annotations from user's groups + public
                    group_query = Q(
                        group__in=Group.objects.filter(is_public=True, is_active=True)
                    ) | Q(group__in=Group.objects.filter(users__in=[self.request.user]))

        final_query = query & group_query if query else group_query
        if final_query:
            return (
                Annotation.objects.filter(final_query & Q(is_delete=False))
                .distinct()
                .order_by("created_at")
            )
        return Annotation.objects.none()

    def create(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        serializer = AnnotationSerializer(
            data=request.data, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)

        m = serializer.save(
            created_by=cast("User", request.user),
        )

        # File fields — assigned after create so upload_to functions run
        changed = False
        for field_name in ("annotation_image", "annotation_audio", "annotation_video"):
            f = request.FILES.get(field_name)
            if f:
                setattr(m, field_name, f)
                changed = True
        if changed:
            m.save()

        # Enqueue HLS transcoding for audio/video reply files
        if request.FILES.get("annotation_audio"):
            enqueue("transcode_annotation_audio", m.id)
        if request.FILES.get("annotation_video"):
            enqueue("transcode_annotation_video", m.id)

        # Tags — comma-separated string
        for tag in request.data.get("tags", "").split(","):
            tag = tag.strip()
            if tag:
                tag_obj = create_or_update_tag(tag)
                if tag_obj:
                    m.tags.add(tag_obj)

        return Response(AnnotationSerializer(m).data, status=status.HTTP_201_CREATED)

class AnnotationRetreiveSet(
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):

    """
    Retreive Annotations for a media
    """

    queryset = Annotation.objects.filter(is_delete=False)
    serializer_class = AnnotationSerializer
    permission_classes = [IsAnnotateUpdateOrReadOnly]
    pagination_class = CustomPageNumberPagination

    lookup_field = "uuid"
    lookup_url_kwarg = "uuid"

    def get_object(self) -> Annotation:
        obj = super().get_object()
        return obj  # type: ignore[no-any-return]  # TYPE_DEBT: DRF get_object returns Any

    def get_queryset(self) -> QuerySet[Annotation]:
        return Annotation.objects.filter(is_delete=False)

    def update(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        instance = self.get_object()
        serializer = AnnotationSerializer(
            instance, data=request.data, partial=True, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        m = serializer.save()

        # Tags — comma-separated string replaces existing set
        if "tags" in request.data:
            for tag in m.tags.all():
                m.tags.remove(tag)
                recalculate_tag_count(tag)
            for tag_name in request.data["tags"].split(","):
                tag_name = tag_name.strip()
                if tag_name:
                    tag_obj = create_or_update_tag(tag_name)
                    if tag_obj:
                        m.tags.add(tag_obj)

        # File fields
        changed = False
        for field_name in ("annotation_image", "annotation_audio", "annotation_video"):
            f = request.FILES.get(field_name)
            if f:
                setattr(m, field_name, f)
                changed = True
        if changed:
            m.save()

        return Response(AnnotationSerializer(m).data, status=status.HTTP_200_OK)

    def destroy(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)

    def perform_destroy(self, instance: Annotation) -> None:
        obj = self.get_object()
        m = Annotation.objects.get(id=obj.id)
        m.is_delete = True
        m.save()
        media = MediaStore.objects.get(uuid=m.media_reference_id)
        if media.group.delete_wait_for == 0:
            enqueue_after("delete_annotate_post_schedule", m.id, delay=10)
        else:
            enqueue_after(
                "delete_annotate_post_schedule",
                m.id,
                delay=timedelta(days=media.group.delete_wait_for),
            )

class AnnotationAddTag(
    mixins.RetrieveModelMixin, mixins.UpdateModelMixin, viewsets.GenericViewSet
):

    """
    Add Tag to an annotation
    """

    queryset = Annotation.objects.filter(is_delete=False)
    serializer_class = AnnotationSerializer
    permission_classes = [IsAnnotateUpdateOrReadOnly]
    pagination_class = CustomPageNumberPagination

    lookup_field = "uuid"
    lookup_url_kwarg = "uuid"

    def get_object(self) -> Annotation:
        obj = super().get_object()
        return obj  # type: ignore[no-any-return]  # TYPE_DEBT: DRF get_object returns Any

    def update(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        data = request.data

        obj = self.get_object()
        m = Annotation.objects.get(id=obj.id)

        tags = data.get("tags")
        if tags:
            for tag in tags:
                tag_obj = create_or_update_tag(tag)
                if tag_obj:
                    m.tags.add(tag_obj)
        serializer = AnnotationSerializer(m)
        return Response(serializer.data)


class AnnotationRemoveTag(
    mixins.RetrieveModelMixin, mixins.UpdateModelMixin, viewsets.GenericViewSet
):

    """
    Remove a  Tag from an annotation
    """

    queryset = Annotation.objects.filter(is_delete=False)
    serializer_class = AnnotationSerializer
    permission_classes = [IsAnnotateUpdateOrReadOnly]
    pagination_class = CustomPageNumberPagination

    lookup_field = "uuid"
    lookup_url_kwarg = "uuid"

    def get_object(self) -> Annotation:
        obj = super().get_object()
        return obj  # type: ignore[no-any-return]  # TYPE_DEBT: DRF get_object returns Any

    def update(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        data = request.data

        obj = self.get_object()
        m = Annotation.objects.get(id=obj.id)

        tags = data.get("tags")
        if tags:
            for tag_id in tags:
                t = Tags.objects.get(id=tag_id)
                m.tags.remove(t)
                recalculate_tag_count(t)
        serializer = AnnotationSerializer(m)
        return Response(serializer.data)


class AnnotationByMediaRetreiveSet(mixins.RetrieveModelMixin, viewsets.GenericViewSet):

    """
    Retreive Annotations for a media
    """

    queryset = Annotation.objects.filter(is_delete=False)
    serializer_class = AnnotationSerializer
    permission_classes = (IsAnnotateCreateOrReadOnly,)
    pagination_class = CustomPageNumberPagination
    lookup_field = "uuid"
    lookup_url_kwarg = "uuid"

    def retrieve(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        media_id = self.kwargs["uuid"]
        queryset = Annotation.objects.filter(
            is_delete=False, media_reference_id=media_id
        )
        serializer = AnnotationSerializer(queryset, many=True)
        return Response(data=serializer.data, status=status.HTTP_200_OK)


class InstanceAnnotationStats(viewsets.GenericViewSet, generics.ListAPIView):

    queryset = Annotation.objects.all()
    serializer_class = AnnotationStatsSerializer
    permission_classes = [IsSuperUser]
    pagination_class = CustomPageNumberPagination

    def get_paginated_response(self, data: Any) -> Response:
        return Response(data)

    def get_queryset(self) -> QuerySet[Annotation]:
        data = (
            Annotation.objects.values("id")
            .annotate(created_date=TruncDate("created_at"))
            .order_by("created_date")
            .values("created_date")
            .annotate(**{"total": Count("created_date")})
        )
        return data  # type: ignore[return-value]  # TYPE_DEBT: annotated queryset loses model type param


class GroupAnnotationStats(
    viewsets.GenericViewSet, generics.ListAPIView, generics.RetrieveAPIView
):

    queryset = Annotation.objects.all()
    serializer_class = AnnotationStatsSerializer
    pagination_class = CustomPageNumberPagination
    permission_classes = [IsAnnotateCreateOrReadOnly]
    lookup_field = "id"
    lookup_url_kwarg = "id"

    def retrieve(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        group_id = self.kwargs.get("id")
        if group_id:

            base_data = MediaStore.objects.filter(
                group=Group.objects.get(id=int(group_id))
            ).values_list("uuid", flat=True)
            base_annotation_query = (
                Annotation.objects.filter(media_reference_id__in=list(base_data))
                .values("id")
                .annotate(created_date=TruncDate("created_at"))
                .order_by("created_date")
                .values("created_date")
                .annotate(**{"total": Count("created_date")})
            )
            serializer = AnnotationStatsSerializer(base_annotation_query, many=True)
            return Response(serializer.data)
        return Response(data=[], status=status.HTTP_200_OK)
