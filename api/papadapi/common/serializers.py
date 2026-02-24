from django.db.models import Count, F
from rest_framework import serializers
from rest_framework.pagination import PageNumberPagination

from papadapi.annotate.models import Annotation
from papadapi.archive.models import MediaStore
from papadapi.common.functions import get_final_tags_count
from papadapi.users.serializers import UserSerializer

from .models import Group, Question, Tags


class CustomPageNumberPagination(PageNumberPagination):
    page_size_query_param = "page_size"  # items per page


class TagsSerializer(serializers.ModelSerializer):
    def create(self, validated_data):
        tag = Tags.objects.create(**validated_data)
        return tag

    class Meta:
        model = Tags
        fields = ("id", "name", "count")


class QuestionsSerializer(serializers.ModelSerializer):
    def create(self, validated_data):
        question = Question.objects.create(**validated_data)
        return question

    class Meta:
        model = Question
        fields = ("id", "question", "question_type", "question_mandatory")


class GroupTagSerializer(serializers.Serializer):
    id = serializers.IntegerField(source="tag_id")
    name = serializers.CharField(source="tags__name")
    count = serializers.IntegerField()


class GroupSerializer(serializers.ModelSerializer):
    users = UserSerializer(many=True, read_only=True)
    extra_group_questions = QuestionsSerializer(many=True)
    tags = serializers.SerializerMethodField()
    media_count = serializers.SerializerMethodField()
    users_count = serializers.SerializerMethodField()

    def create(self, validated_data):
        group = Group.objects.create(**validated_data)
        return group

    class Meta:
        model = Group
        fields = (
            "id",
            "name",
            "description",
            "is_active",
            "is_public",
            "users",
            "users_count",
            "extra_group_questions",
            "delete_wait_for",
            "tags",
            "created_at",
            "updated_at",
            "media_count"
        )

    def get_media_count(self, obj):
        return MediaStore.objects.filter(group=obj.id).count()

    def get_users_count(self, obj):
        return Group.objects.get(id=obj.id).users.count()

    def get_tags(self, obj):
        media_tags_count = (
            MediaStore.objects.filter(group=obj.id)
            .annotate(count=Count("tags"))
            .annotate(tag_id=F("tags__id"))
            .values("tag_id", "tags__name", "count")
            .order_by("-count")
        )
        annotation_tags_count = (
            Annotation.objects.filter(
                media_reference_id__in=list(
                    MediaStore.objects.filter(group=obj.id)
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
        return GroupTagSerializer(tags_count, many=True).data


class UpdateGroupSerializer(serializers.ModelSerializer):
    users = UserSerializer(many=True, read_only=True)
    extra_group_questions = QuestionsSerializer(many=True)
    tags = serializers.SerializerMethodField()

    # TODO: Filter questions belonging to group

    class Meta:
        model = Group
        fields = (
            "id",
            "name",
            "description",
            "users",
            "extra_group_questions",
            "delete_wait_for",
            "tags",
            "is_public",
            "created_at",
            "updated_at"
        )

    def get_tags(self, obj):
        media_tags_count = (
            MediaStore.objects.filter(group=obj.id)
            .annotate(count=Count("tags"))
            .annotate(tag_id=F("tags__id"))
            .values("tag_id", "tags__name", "count")
            .order_by("-count")
        )
        annotation_tags_count = (
            Annotation.objects.filter(
                media_reference_id__in=list(
                    MediaStore.objects.filter(group=obj.id)
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
        return GroupTagSerializer(tags_count, many=True).data


class GroupStatsSerializer(serializers.Serializer):
    created_date = serializers.DateField()
    total = serializers.IntegerField()
