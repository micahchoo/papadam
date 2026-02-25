"""Tests for users.permissions — IsUserOrReadOnly and IsSuperUser."""

import pytest
from django.test import RequestFactory
from rest_framework.test import force_authenticate

from papadapi.conftest import UserFactory
from papadapi.users.permissions import IsSuperUser, IsUserOrReadOnly

rf = RequestFactory()


# ── IsUserOrReadOnly ─────────────────────────────────────────────────────────


@pytest.mark.django_db
class TestIsUserOrReadOnly:
    """Object-level permission: safe methods pass, owner passes, others rejected."""

    def _check(self, method, user, obj):
        request = getattr(rf, method)("/fake/")
        force_authenticate(request, user=user)
        request.user = user
        perm = IsUserOrReadOnly()
        return perm.has_object_permission(request, view=None, obj=obj)

    def test_get_allowed_for_any_user(self, user):
        other = UserFactory()
        assert self._check("get", user, other) is True

    def test_head_allowed_for_any_user(self, user):
        other = UserFactory()
        assert self._check("head", user, other) is True

    def test_options_allowed_for_any_user(self, user):
        other = UserFactory()
        assert self._check("options", user, other) is True

    def test_put_allowed_for_owner(self, user):
        assert self._check("put", user, user) is True

    def test_patch_allowed_for_owner(self, user):
        assert self._check("patch", user, user) is True

    def test_delete_allowed_for_owner(self, user):
        assert self._check("delete", user, user) is True

    def test_put_rejected_for_other_user(self, user):
        other = UserFactory()
        assert self._check("put", user, other) is False

    def test_patch_rejected_for_other_user(self, user):
        other = UserFactory()
        assert self._check("patch", user, other) is False

    def test_delete_rejected_for_other_user(self, user):
        other = UserFactory()
        assert self._check("delete", user, other) is False

    def test_post_rejected_for_other_user(self, user):
        """POST is not a safe method — should be rejected when obj != user."""
        other = UserFactory()
        assert self._check("post", user, other) is False

    def test_post_allowed_for_owner(self, user):
        assert self._check("post", user, user) is True


# ── IsSuperUser ──────────────────────────────────────────────────────────────


@pytest.mark.django_db
class TestIsSuperUser:
    """View-level permission: only superusers pass."""

    def _check(self, user):
        request = rf.get("/fake/")
        force_authenticate(request, user=user)
        request.user = user
        perm = IsSuperUser()
        return perm.has_permission(request, view=None)

    def test_superuser_allowed(self, admin_user):
        assert self._check(admin_user) is True

    def test_normal_user_rejected(self, user):
        assert self._check(user) is False

    def test_staff_non_superuser_rejected(self):
        staff = UserFactory(is_staff=True, is_superuser=False)
        assert self._check(staff) is False


# ── Adversarial ──────────────────────────────────────────────────────────────


@pytest.mark.django_db
class TestAdversarial:
    """Edge cases for permission classes."""

    def test_is_user_or_read_only_with_non_user_object(self, user):
        """When obj is not a User instance, PUT should be rejected
        because obj != request.user."""
        request = rf.put("/fake/")
        force_authenticate(request, user=user)
        request.user = user
        perm = IsUserOrReadOnly()
        non_user_obj = {"id": 1, "name": "not a user"}
        assert perm.has_object_permission(request, view=None, obj=non_user_obj) is False

    def test_is_superuser_with_anonymous_user(self):
        """AnonymousUser.is_superuser is False — should be rejected."""
        from django.contrib.auth.models import AnonymousUser

        request = rf.get("/fake/")
        request.user = AnonymousUser()
        perm = IsSuperUser()
        assert perm.has_permission(request, view=None) is False

    def test_is_user_or_read_only_safe_methods_pass_even_for_anonymous(self):
        """GET on object-level perm passes regardless of user identity."""
        from django.contrib.auth.models import AnonymousUser

        request = rf.get("/fake/")
        request.user = AnonymousUser()
        perm = IsUserOrReadOnly()
        some_obj = object()
        assert perm.has_object_permission(request, view=None, obj=some_obj) is True
