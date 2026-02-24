
from rest_framework import serializers

from papadapi.common.models import Group
from papadapi.users.models import User


class GroupTagSerializer(serializers.Serializer):
    id = serializers.IntegerField(source="tag_id")
    name = serializers.CharField(source="tags__name")
    count = serializers.IntegerField()


class UsersAPIGroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = Group
        fields = (
            "id",
            "name",
            "description",
            "is_public",
            "created_at",
            "updated_at",
        )


class UserMEApiSerializer(serializers.ModelSerializer):
    groups = serializers.SerializerMethodField()
    users_count = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            "id",
            "username",
            "first_name",
            "last_name",
            "is_superuser",
            "groups",
            "users_count",
        )
        read_only_fields = ("username",)

    def get_groups(self, obj):
        groups_user_in = Group.objects.filter(users__in=[obj])
        return UsersAPIGroupSerializer(groups_user_in, many=True).data

    def get_users_count(self, obj) -> int:
        """Count of distinct users across all groups this user belongs to."""
        user_groups = Group.objects.filter(users__in=[obj])
        return User.objects.filter(group__in=user_groups).distinct().count()


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("id", "username", "first_name", "last_name")
        read_only_fields = ("username",)


class UserStatsSerializer(serializers.Serializer):
    created_date = serializers.DateField()
    total = serializers.IntegerField()
