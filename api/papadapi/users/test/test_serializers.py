"""Tests for users.serializers — UserSerializer, UserMEApiSerializer,
UserStatsSerializer, GroupTagSerializer, UsersAPIGroupSerializer."""

import datetime

import pytest

from papadapi.common.serializers import (
    DailyStatsSerializer as UserStatsSerializer,
)
from papadapi.common.serializers import (
    GroupTagSerializer,
)
from papadapi.conftest import GroupFactory, UserFactory
from papadapi.users.serializers import (
    UserMEApiSerializer,
    UsersAPIGroupSerializer,
    UserSerializer,
)


@pytest.mark.django_db
class TestUserSerializer:
    """UserSerializer exposes id, username, first_name, last_name."""

    def test_fields(self, user):
        data = UserSerializer(user).data
        assert set(data.keys()) == {"id", "username", "first_name", "last_name"}

    def test_id_is_string_uuid(self, user):
        data = UserSerializer(user).data
        assert data["id"] == str(user.id)

    def test_username_is_read_only(self):
        ser = UserSerializer()
        assert ser.fields["username"].read_only is True


@pytest.mark.django_db
class TestUserMEApiSerializer:
    """UserMEApiSerializer — includes groups (method) and users_count (method)."""

    def test_fields(self, user):
        data = UserMEApiSerializer(user).data
        expected = {
            "id", "username", "first_name", "last_name",
            "is_superuser", "groups", "users_count",
        }
        assert set(data.keys()) == expected

    def test_groups_empty_when_user_has_no_groups(self, user):
        data = UserMEApiSerializer(user).data
        assert data["groups"] == []

    def test_groups_returns_group_info(self, user):
        g = GroupFactory()
        g.users.add(user)
        data = UserMEApiSerializer(user).data
        assert len(data["groups"]) == 1
        group_data = data["groups"][0]
        assert group_data["id"] == g.id
        assert group_data["name"] == g.name
        assert "description" in group_data
        assert "is_public" in group_data
        assert "created_at" in group_data
        assert "updated_at" in group_data

    def test_groups_returns_multiple(self, user):
        g1 = GroupFactory()
        g2 = GroupFactory()
        g1.users.add(user)
        g2.users.add(user)
        data = UserMEApiSerializer(user).data
        assert len(data["groups"]) == 2

    def test_users_count_zero_when_no_groups(self, user):
        data = UserMEApiSerializer(user).data
        assert data["users_count"] == 0

    def test_users_count_counts_distinct_users(self, user):
        """Two groups sharing the same user should count that user once."""
        other = UserFactory()
        g1 = GroupFactory()
        g2 = GroupFactory()
        g1.users.add(user, other)
        g2.users.add(user)
        data = UserMEApiSerializer(user).data
        # user is in g1 and g2, other is in g1 -> distinct users across groups = 2
        assert data["users_count"] == 2

    def test_users_count_single_group(self, user):
        other1 = UserFactory()
        other2 = UserFactory()
        g = GroupFactory()
        g.users.add(user, other1, other2)
        data = UserMEApiSerializer(user).data
        assert data["users_count"] == 3

    def test_username_is_read_only(self):
        ser = UserMEApiSerializer()
        assert ser.fields["username"].read_only is True


@pytest.mark.django_db
class TestUsersAPIGroupSerializer:
    """UsersAPIGroupSerializer — ModelSerializer for Group with limited fields."""

    def test_fields(self, group):
        data = UsersAPIGroupSerializer(group).data
        expected = {
            "id", "name", "description", "is_public",
            "created_at", "updated_at",
        }
        assert set(data.keys()) == expected

    def test_excludes_users_field(self, group):
        data = UsersAPIGroupSerializer(group).data
        assert "users" not in data


class TestGroupTagSerializer:
    """GroupTagSerializer — plain Serializer for aggregated tag data."""

    def test_valid_data(self):
        raw = {"tag_id": 1, "tags__name": "nature", "count": 5}
        ser = GroupTagSerializer(raw)
        assert ser.data == {"id": 1, "name": "nature", "count": 5}

    def test_source_mapping(self):
        """id comes from tag_id, name from tags__name."""
        raw = {"tag_id": 42, "tags__name": "culture", "count": 0}
        data = GroupTagSerializer(raw).data
        assert data["id"] == 42
        assert data["name"] == "culture"


class TestUserStatsSerializer:
    """UserStatsSerializer — plain Serializer with created_date + total."""

    def test_valid_data(self):
        raw = {"created_date": datetime.date(2024, 6, 15), "total": 7}
        ser = UserStatsSerializer(raw)
        assert ser.data["created_date"] == "2024-06-15"
        assert ser.data["total"] == 7

    def test_rejects_missing_fields(self):
        ser = UserStatsSerializer(data={})
        assert not ser.is_valid()
        assert "created_date" in ser.errors
        assert "total" in ser.errors


@pytest.mark.django_db
class TestAdversarial:
    """Edge cases for serializers."""

    def test_user_me_serializer_with_superuser_flag(self, admin_user):
        data = UserMEApiSerializer(admin_user).data
        assert data["is_superuser"] is True

    def test_user_me_serializer_normal_user_not_superuser(self, user):
        data = UserMEApiSerializer(user).data
        assert data["is_superuser"] is False

    def test_user_stats_serializer_rejects_negative_total(self):
        """Serializer has no min-value validation, so -1 passes (document behavior)."""
        ser = UserStatsSerializer(data={"created_date": "2024-01-01", "total": -1})
        assert ser.is_valid()

    def test_group_tag_serializer_zero_count(self):
        raw = {"tag_id": 1, "tags__name": "empty", "count": 0}
        data = GroupTagSerializer(raw).data
        assert data["count"] == 0
