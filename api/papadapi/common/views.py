import json

from django.db.models import Count, F, Q, Value
from django.db.models.functions import TruncDate
from django.shortcuts import redirect
from rest_framework import generics, mixins, status, viewsets
from rest_framework.permissions import (
    AllowAny,
    IsAuthenticatedOrReadOnly,
)
from rest_framework.renderers import TemplateHTMLRenderer
from rest_framework.response import Response

from papadapi.annotate.models import Annotation
from papadapi.archive.models import MediaStore
from papadapi.common.functions import get_final_tags_count, get_related_tags
from papadapi.common.permissions import IsGroupOwnerMemberOrReadOnly
from papadapi.common.serializers import CustomPageNumberPagination
from papadapi.users.models import User
from papadapi.users.permissions import IsSuperUser

from .models import Group, Question, Tags
from .serializers import (
    GroupSerializer,
    GroupStatsSerializer,
    TagsSerializer,
    UpdateGroupSerializer,
)


class TagsViewSet(
    mixins.CreateModelMixin, mixins.ListModelMixin, viewsets.GenericViewSet
):
    """
    List all tags
    """

    queryset = Tags.objects.all()
    serializer_class = TagsSerializer
    pagination_class = CustomPageNumberPagination
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get_paginated_response(self, data):
        return Response(data)

    def get(self, request, *args, **kwargs):
        if self.request.user.is_anonymous:
            selected_groups = Group.objects.filter(is_active=True, is_public=True)
        else:
            selected_groups = Group.objects.filter(
                Q(is_public=True, is_active=True) | Q(users__in=[self.request.user])
            )

        media_tags_count = (
            MediaStore.objects.filter(group__in=selected_groups)
            .values("tags")
            .annotate(count=Count("tags"))
            .annotate(tag_id=F("tags__id"))
            .values("tag_id", "tags__name", "count")
            .order_by("-count")
        )
        annotation_tags_count = (
            Annotation.objects.filter(
                media_reference_id__in=list(
                    MediaStore.objects.filter(group__in=selected_groups)
                )
            )
            .values("tags")
            .annotate(count=Count("tags"))
            .annotate(tag_id=F("tags__id"))
            .values("tag_id", "tags__name", "count")
            .order_by("-count")
        )
        tags_count = get_final_tags_count(
            list(media_tags_count), list(annotation_tags_count), count=True
        )
        return Response({"results": tags_count})



class GroupViewSet(
    mixins.CreateModelMixin, mixins.ListModelMixin, viewsets.GenericViewSet
):
    """
    List all tags
    """

    queryset = Group.objects.filter(is_public=True, is_active=True)
    serializer_class = GroupSerializer
    pagination_class = CustomPageNumberPagination
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        if self.request.user.is_anonymous:
            return Group.objects.filter(is_public=True, is_active=True)
        else:
            user = self.request.user
            return Group.objects.filter(is_public=True, is_active=True).exclude(
                users__in=[user]
            )

    def create(self, request, *args, **kwargs):
        data = request.data
        name = data["name"]
        description = data["description"]
        extra_questions = (
            json.loads(data["group_extra_questions"])
            if "group_extra_questions" in data
            else None
        )
        delete_wait_for = data.get("delete_wait_for", 0)
        is_active = True
        is_public = data.get("is_public", True)
        g = Group.objects.create(
            name=name,
            description=description,
            is_active=is_active,
            delete_wait_for=delete_wait_for,
            is_public=is_public,
        )
        g.save()
        if extra_questions and len(extra_questions["extra"]) > 0:
            for question in extra_questions["extra"]:
                q = Question.objects.create(
                    question=question["question"],
                    question_mandatory=question["mandatory"],
                    question_type=question["type"],
                )
                q.save()
                g.extra_group_questions.add(q)
        g.users.add(request.user)
        if data["users"]:
            users = data["users"].split(",")
            if len(data["users"]) > 0:
                for user in users:
                    u = User.objects.get(id=user)
                    if u not in g.users.all():
                        g.users.add(u)
        serializer = GroupSerializer(g)
        return Response(serializer.data)


class UpdateGroupViewSet(
    mixins.UpdateModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet
):
    """
    List all tags
    """

    queryset = Group.objects.all()
    serializer_class = UpdateGroupSerializer
    pagination_class = CustomPageNumberPagination
    permission_classes = [IsGroupOwnerMemberOrReadOnly]
    lookup_field = "id"
    lookup_url_kwarg = "id"

    def update(self, request, *args, **kwargs):
        data = request.data
        obj = self.get_object()

        g = Group.objects.get(id=obj.id)
        name = data.get("name", g.name)
        description = data.get("description", g.description)
        delete_wait_for = data.get("delete_wait_for", g.delete_wait_for)
        is_public = data.get("is_public", g.is_public)
        g.name = name
        g.description = description
        g.delete_wait_for = delete_wait_for
        g.is_public = is_public
        g.save()
        if data["users"]:
            users = data["users"].split(",")
            if len(data["users"]) > 0:
                for user in users:
                    u = User.objects.get(id=user)
                    if u not in g.users.all():
                        g.users.add(u)
        serializer = UpdateGroupSerializer(g)
        return Response(serializer.data)

class AddUserFromGroupView(
    mixins.ListModelMixin, mixins.UpdateModelMixin, viewsets.GenericViewSet
):
    """
    List all tags
    """

    queryset = Group.objects.all()
    serializer_class = UpdateGroupSerializer
    pagination_class = CustomPageNumberPagination
    permission_classes = [IsGroupOwnerMemberOrReadOnly]
    lookup_field = "id"
    lookup_url_kwarg = "id"

    def update(self, request, *args, **kwargs):
        data = request.data
        obj = self.get_object()

        g = Group.objects.get(id=obj.id)
        user = data["user"]
        u = User.objects.get(id=user)
        if u not in g.users.all():
            g.users.add(u)
        serializer = UpdateGroupSerializer(g)
        return Response(serializer.data)


class RemoveUserFromGroupView(
    mixins.ListModelMixin, mixins.UpdateModelMixin, viewsets.GenericViewSet
):
    """
    List all tags
    """

    queryset = Group.objects.all()
    serializer_class = UpdateGroupSerializer
    pagination_class = CustomPageNumberPagination
    permission_classes = [IsGroupOwnerMemberOrReadOnly]
    lookup_field = "id"
    lookup_url_kwarg = "id"

    def update(self, request, *args, **kwargs):
        data = request.data
        obj = self.get_object()

        g = Group.objects.get(id=obj.id)
        user = data["user"]
        u = User.objects.get(id=user)
        if len(g.users.all()) > 1:
            g.users.remove(u)
            serializer = UpdateGroupSerializer(g)
            return Response(serializer.data)
        else:
            return Response(
                {
                    "detail": (
                        "Not allowed to remove the last user in the group. "
                        "Add another user to the group and retry for this user."
                    )
                },
                status=status.HTTP_403_FORBIDDEN,
            )


class RemoveCustomQuestionFromGroupView(
    mixins.ListModelMixin, mixins.UpdateModelMixin, viewsets.GenericViewSet
):

    """
    Remove a custom question from group
    """

    queryset = Group.objects.all()
    serializer_class = UpdateGroupSerializer
    pagination_class = CustomPageNumberPagination
    permission_classes = [IsGroupOwnerMemberOrReadOnly]
    lookup_field = "id"
    lookup_url_kwarg = "id"

    def update(self, request, *args, **kwargs):
        data = request.data
        obj = self.get_object()

        g = Group.objects.get(id=obj.id)
        question_id = data["question_id"]
        question = Question.objects.get(id=question_id)
        g.extra_group_questions.remove(question)
        if data["remove_existing_data"] == "True":
            media_list = MediaStore.objects.filter(group=g)
            for media in media_list:
                for resp in media.extra_group_response:
                    if question.id == int(resp["question_id"]):
                        media.extra_group_response.remove(resp)
                    media.save()
        serializer = UpdateGroupSerializer(g)
        return Response(serializer.data)


class AddCustomQuestionFromGroupView(
    mixins.ListModelMixin, mixins.UpdateModelMixin, viewsets.GenericViewSet
):

    queryset = Group.objects.all()
    serializer_class = UpdateGroupSerializer
    pagination_class = CustomPageNumberPagination
    permission_classes = [IsGroupOwnerMemberOrReadOnly]
    lookup_field = "id"
    lookup_url_kwarg = "id"

    def update(self, request, *args, **kwargs):
        data = request.data
        obj = self.get_object()

        g = Group.objects.get(id=obj.id)
        question = Question.objects.create(
            question=data["question"],
            question_mandatory=data["mandatory"],
            question_type=data["type"],
        )
        question.save()
        g.extra_group_questions.add(question)
        if data["add_default_value"] == "True":
            media_list = MediaStore.objects.filter(group=g)
            for media in media_list:
                media.extra_group_response.append(
                    {
                        "question_id": question.id,
                        "question": question.question,
                        "question_type": question.question_type,
                        "question_mandatory": question.question_mandatory,
                        "response": data.get("default_value", ""),
                    }
                )
                media.save()

        serializer = UpdateGroupSerializer(g)
        return Response(serializer.data)


class UpdateCustomQuestionFromGroupView(
    mixins.ListModelMixin, mixins.UpdateModelMixin, viewsets.GenericViewSet
):

    queryset = Group.objects.all()
    serializer_class = UpdateGroupSerializer
    pagination_class = CustomPageNumberPagination
    permission_classes = [IsGroupOwnerMemberOrReadOnly]
    lookup_field = "id"
    lookup_url_kwarg = "id"

    def update(self, request, *args, **kwargs):
        data = request.data
        obj = self.get_object()

        g = Group.objects.get(id=obj.id)
        question_id = data["question_id"]
        question = data["question"]
        try:
            q = Question.objects.get(id=question_id)
        except Question.DoesNotExist:
            return Response(
                {"detail": "Question not found."}, status=status.HTTP_404_NOT_FOUND
            )
        q.question = question if question else q.question
        q.save()
        media_list = MediaStore.objects.filter(group=g)
        for media in media_list:
            for resp in media.extra_group_response:
                if q.id == int(resp["question_id"]):
                    resp["question"] = q.question
                media.save()
        serializer = UpdateGroupSerializer(g)
        return Response(serializer.data)


class InstanceGroupStats(viewsets.GenericViewSet, generics.ListAPIView):

    queryset = Group.objects.all()
    serializer_class = GroupStatsSerializer
    pagination_class = CustomPageNumberPagination
    permission_classes = [IsSuperUser]

    def get_paginated_response(self, data):
        return Response(data)

    def get_queryset(self):
        data = (
            Group.objects.values("id")
            .annotate(created_date=TruncDate("created_at"))
            .order_by("created_date")
            .values("created_date")
            .annotate(**{"total": Count("created_date")})
        )
        return data


class GroupTagGraphView(viewsets.GenericViewSet, generics.RetrieveAPIView):
    queryset = Group.objects.all()
    serializer_class = GroupStatsSerializer
    pagination_class = CustomPageNumberPagination
    permission_classes = [IsGroupOwnerMemberOrReadOnly]
    lookup_field = "id"
    lookup_url_kwarg = "id"

    def get_paginated_response(self, data):
        return Response(data)

    def retrieve(self, request, *args, **kwargs):
        group_id = self.kwargs.get("id")
        if group_id:
            media_tags_count = (
                MediaStore.objects.filter(group=group_id)
                .values("tags")
                .annotate(symbolSize=Count("tags"))
                .annotate(name=F('tags__name'))
                .annotate(id=F("tags__id"))
                .annotate(tag_in=Value("media"))
                .annotate(category=Value(0))
                .values("id", "name", "symbolSize", "tag_in", "category")
            )
            annotation_tags_count = (
                Annotation.objects.filter(
                    media_reference_id__in=list(
                        MediaStore.objects.filter(group=group_id)
                    )
                )
                .values("tags")
                .annotate(symbolSize=Count("tags"))
                .annotate(name=F('tags__name'))
                .annotate(id=F("tags__id"))
                .annotate(tag_in=Value("annotation"))
                .annotate(value=Value(1))
                .annotate(category=Value(1))
                .values("id", "name", "symbolSize", "tag_in", "category")
            )

            tags_count = get_final_tags_count(
                list(media_tags_count), list(annotation_tags_count)
            )

            ## Now generate the links
            links = []
            for tc in tags_count:
                tcid = tc["id"]
                links += get_related_tags(group_id, tcid, links)
            return Response({
                "nodes": tags_count,
                "links": links,
                "categories": [
                    {"name": "Media"},
                    {"name": "Annotation"},
                    {"name": "Media+Annotation"},
                ],
            })


class RedirectToUIView(generics.GenericAPIView):
    renderer_classes = [TemplateHTMLRenderer]
    permission_classes = [AllowAny]

    def get(self, request, *args, **kwargs):
        return redirect("/ui" + request.path)


class HealthCheck(generics.GenericAPIView):
    permission_classes = [AllowAny]

    def get(self, request, *args, **kwargs):
        return Response(status=200)


class RuntimeConfigView(generics.GenericAPIView):
    """Serve runtime config to the SvelteKit SPA.

    The browser fetches /config.json on startup to discover the API and CRDT
    WebSocket URLs. Values come from PUBLIC_API_URL and PUBLIC_CRDT_URL env vars
    (set in service_config.env). Returns empty strings if not configured so the
    SPA can fall back gracefully in local dev.
    """

    permission_classes = [AllowAny]

    def get(self, request, *args, **kwargs):
        from django.conf import settings

        return Response(
            {
                "API_URL": getattr(settings, "PUBLIC_API_URL", ""),
                "CRDT_URL": getattr(settings, "PUBLIC_CRDT_URL", ""),
            }
        )
