from datetime import timedelta

from django.db.models import Count, Q
from django.db.models.functions import TruncDate
from rest_framework import generics, mixins, status, viewsets
from rest_framework.response import Response

from papadapi.annotate.permissions import (
    IsAnnotateCreateOrReadOnly,
    IsAnnotateUpdateOrReadOnly,
)
from papadapi.archive.models import MediaStore
from papadapi.common.functions import create_or_update_tag, recalculate_tag_count
from papadapi.common.models import Group, Tags
from papadapi.common.serializers import CustomPageNumberPagination
from papadapi.queue import enqueue_after
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

    def get_queryset(self):
        query = None
        search_query = self.request.GET.get("search")
        search_where = self.request.GET.get("searchWhere", None)
        search_from = self.request.GET.get("searchFrom", None)
        search_collections = self.request.GET.get("searchCollections", None)
        final_query = None
        group_query = None

        # By default search in name and description unless overridden
        if search_query:
            if search_where == "name":
                query = Q(annotation_text__icontains=search_query)
            elif search_where == "tags":
                query = Q(tags__name__in=search_query)

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
                error_message = "No results found for the given search criteria."
                return Response(
                    {"detail": error_message}, status=status.HTTP_404_NOT_FOUND
                )

        final_query = query & group_query if query else group_query
        if final_query:
            return (
                Annotation.objects.filter(query & Q(is_delete=False))
                .distinct()
                .order_by("created_at")
            )
        else:
            return None

    def create(self, request, *args, **kwargs):
        data = request.data
        files = request.FILES.get("annotation_image", None)

        # Mandatory fields
        media_reference_id = data["media_reference_id"]
        annotation_text = data["annotation_text"]
        media_target = data["media_target"]

        m = Annotation.objects.create(
            media_reference_id=media_reference_id,
            annotation_text=annotation_text,
            media_target=media_target,
            created_by=self.request.user,
        )
        m.annotation_image = files
        m.save()
        for tag in data["tags"].split(","):
            m.tags.add(create_or_update_tag(tag))
        serializer = AnnotationSerializer(m)
        return Response(serializer.data)

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

    def get_object(self):
        obj = super().get_object()
        # perform some extra checks on obj, e.g custom permissions
        return obj

    def get_queryset(self):
        return Annotation.objects.filter(is_delete=False)

    def update(self, request, *args, **kwargs):
        data = request.data
        files = request.FILES.get("annotation_image", None)

        obj = self.get_object()
        m = Annotation.objects.get(id=obj.id)
        if "annotation_text" in data:
            m.annotation_text = data["annotation_text"]
        if "media_target" in data:
            m.media_target = data["media_target"]
        if "tags" in data:
            for tag in m.tags.all():
                m.tags.remove(tag)
                recalculate_tag_count(tag)
            for tag in data["tags"].split(","):
                m.tags.add(create_or_update_tag(tag))
        if files:
            m.annotation_image = files
        m.save()
        serializer = AnnotationSerializer(m)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)

    def perform_destroy(self, instance):
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

    def get_object(self):
        obj = super().get_object()
        # perform some extra checks on obj, e.g custom permissions
        return obj

    def update(self, request, *args, **kwargs):
        data = request.data

        obj = self.get_object()
        m = Annotation.objects.get(id=obj.id)

        tags = data.get("tags")
        if tags:
            for tag in tags:
                m.tags.add(create_or_update_tag(tag))
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

    def get_object(self):
        obj = super().get_object()
        # perform some extra checks on obj, e.g custom permissions
        return obj

    def update(self, request, *args, **kwargs):
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

    def retrieve(self, request, *args, **kwargs):
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

    def get_paginated_response(self, data):
        return Response(data)

    def get_queryset(self):
        data = (
            Annotation.objects.values("id")
            .annotate(created_date=TruncDate("created_at"))
            .order_by("created_date")
            .values("created_date")
            .annotate(**{"total": Count("created_date")})
        )
        return data


class GroupAnnotationStats(
    viewsets.GenericViewSet, generics.ListAPIView, generics.RetrieveAPIView
):

    queryset = Annotation.objects.all()
    serializer_class = AnnotationStatsSerializer
    pagination_class = CustomPageNumberPagination
    permission_classes = [IsAnnotateCreateOrReadOnly]
    lookup_field = "id"
    lookup_url_kwarg = "id"

    def retrieve(self, request, *args, **kwargs):
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
