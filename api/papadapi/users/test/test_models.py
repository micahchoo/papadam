"""Tests for users.models — User model with UUID PK."""

import uuid

import pytest

from papadapi.conftest import UserFactory
from papadapi.users.models import User


@pytest.mark.django_db
class TestUserModel:
    """User model: UUID primary key, __str__, REQUIRED_FIELDS, USERNAME_FIELD."""

    def test_pk_is_uuid(self, user):
        assert isinstance(user.id, uuid.UUID)

    def test_pk_is_unique_across_instances(self):
        u1 = UserFactory()
        u2 = UserFactory()
        assert u1.id != u2.id

    def test_str_returns_username(self, user):
        assert str(user) == user.username

    def test_username_field_is_username(self):
        assert User.USERNAME_FIELD == "username"

    def test_required_fields_are_first_and_last_name(self):
        assert set(User.REQUIRED_FIELDS) == {"first_name", "last_name"}

    def test_pk_not_editable(self):
        pk_field = User._meta.get_field("id")
        assert pk_field.editable is False

    def test_pk_default_generates_valid_uuid(self):
        pk_field = User._meta.get_field("id")
        generated = pk_field.default()
        assert isinstance(generated, uuid.UUID)
        # uuid4 version check
        assert generated.version == 4

    def test_inherits_abstract_user_fields(self, user):
        """Sanity check that AbstractUser fields exist."""
        assert hasattr(user, "username")
        assert hasattr(user, "email")
        assert hasattr(user, "first_name")
        assert hasattr(user, "last_name")
        assert hasattr(user, "is_active")
        assert hasattr(user, "is_staff")
        assert hasattr(user, "is_superuser")
        assert hasattr(user, "date_joined")

    def test_set_password_and_check_password(self, user):
        user.set_password("new_secret_42")
        assert user.check_password("new_secret_42")
        assert not user.check_password("wrong")


@pytest.mark.django_db
class TestAdversarial:
    """Edge and adversarial cases."""

    def test_duplicate_username_raises(self, user):
        from django.db import IntegrityError

        with pytest.raises(IntegrityError):
            UserFactory(username=user.username)

    def test_empty_username_can_be_created(self):
        """Django AbstractUser does not forbid empty username at model level."""
        u = UserFactory(username="")
        assert u.pk is not None
        assert str(u) == ""

    def test_very_long_username_fails_validation(self):
        """AbstractUser.username max_length=150 — full_clean rejects >150 chars."""
        from django.core.exceptions import ValidationError

        long_name = "x" * 200
        u = User(username=long_name, first_name="F", last_name="L")
        with pytest.raises(ValidationError) as exc_info:
            u.full_clean()
        assert "username" in exc_info.value.message_dict
