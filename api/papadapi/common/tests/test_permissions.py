"""Tests for common permission classes.

Covers: ReadOnly, IsGroupOwnerMemberOrReadOnly
"""

import pytest
from django.test import RequestFactory

from papadapi.common.permissions import IsGroupOwnerMemberOrReadOnly, ReadOnly
from papadapi.conftest import GroupFactory, UserFactory


# ── ReadOnly ─────────────────────────────────────────────────────────────────


class TestReadOnly:
    """ReadOnly allows only GET, HEAD, OPTIONS."""

    def setup_method(self):
        self.perm = ReadOnly()
        self.factory = RequestFactory()

    def test_get_allowed(self):
        request = self.factory.get("/")
        assert self.perm.has_permission(request, None) is True

    def test_head_allowed(self):
        request = self.factory.head("/")
        assert self.perm.has_permission(request, None) is True

    def test_options_allowed(self):
        request = self.factory.options("/")
        assert self.perm.has_permission(request, None) is True

    def test_post_denied(self):
        request = self.factory.post("/")
        assert self.perm.has_permission(request, None) is False

    def test_put_denied(self):
        request = self.factory.put("/")
        assert self.perm.has_permission(request, None) is False

    def test_delete_denied(self):
        request = self.factory.delete("/")
        assert self.perm.has_permission(request, None) is False

    def test_patch_denied(self):
        request = self.factory.patch("/")
        assert self.perm.has_permission(request, None) is False


# ── IsGroupOwnerMemberOrReadOnly ─────────────────────────────────────────────


@pytest.mark.django_db
class TestIsGroupOwnerMemberOrReadOnly:
    """Permission that extracts group_id from the URL path."""

    def setup_method(self):
        self.perm = IsGroupOwnerMemberOrReadOnly()
        self.factory = RequestFactory()

    def test_get_public_group_allows_anon(self):
        """GET on a public group is allowed for any user."""
        group = GroupFactory(is_public=True)
        request = self.factory.get(f"/api/v1/group/{group.id}/")
        request.user = UserFactory()
        request.META["PATH_INFO"] = f"/api/v1/group/{group.id}/"
        assert self.perm.has_permission(request, None) is True

    def test_get_private_group_denied_for_non_member(self):
        """GET on a private group denies non-members."""
        group = GroupFactory(is_public=False)
        user = UserFactory()
        request = self.factory.get(f"/api/v1/group/{group.id}/")
        request.user = user
        request.META["PATH_INFO"] = f"/api/v1/group/{group.id}/"
        assert self.perm.has_permission(request, None) is False

    def test_get_private_group_allowed_for_member(self):
        """GET on a private group is allowed for members."""
        group = GroupFactory(is_public=False)
        user = UserFactory()
        group.users.add(user)
        request = self.factory.get(f"/api/v1/group/{group.id}/")
        request.user = user
        request.META["PATH_INFO"] = f"/api/v1/group/{group.id}/"
        assert self.perm.has_permission(request, None) is True

    def test_put_allowed_for_member(self):
        """PUT is allowed when user is a member."""
        group = GroupFactory()
        user = UserFactory()
        group.users.add(user)
        request = self.factory.put(f"/api/v1/group/{group.id}/")
        request.user = user
        request.META["PATH_INFO"] = f"/api/v1/group/{group.id}/"
        assert self.perm.has_permission(request, None) is True

    def test_put_denied_for_non_member(self):
        """PUT is denied when user is not in the group."""
        group = GroupFactory()
        user = UserFactory()
        request = self.factory.put(f"/api/v1/group/{group.id}/")
        request.user = user
        request.META["PATH_INFO"] = f"/api/v1/group/{group.id}/"
        assert self.perm.has_permission(request, None) is False

    def test_nonexistent_group_get_allowed(self):
        """GET with nonexistent group_id in URL allows safe methods through."""
        request = self.factory.get("/api/v1/group/999999/")
        request.user = UserFactory()
        request.META["PATH_INFO"] = "/api/v1/group/999999/"
        assert self.perm.has_permission(request, None) is True

    def test_nonexistent_group_put_denied(self):
        """PUT with nonexistent group_id returns denied with 'Group not found' message."""
        request = self.factory.put("/api/v1/group/999999/")
        request.user = UserFactory()
        request.META["PATH_INFO"] = "/api/v1/group/999999/"
        assert self.perm.has_permission(request, None) is False
        assert self.perm.message == "Group not found"

    def test_invalid_group_id_in_path_get_allowed(self):
        """GET with non-numeric group_id (ValueError) allows safe methods through."""
        request = self.factory.get("/api/v1/group/abc/")
        request.user = UserFactory()
        request.META["PATH_INFO"] = "/api/v1/group/abc/"
        assert self.perm.has_permission(request, None) is True

    def test_invalid_group_id_in_path_put_denied(self):
        """PUT with non-numeric group_id (ValueError) is denied."""
        request = self.factory.put("/api/v1/group/abc/")
        request.user = UserFactory()
        request.META["PATH_INFO"] = "/api/v1/group/abc/"
        assert self.perm.has_permission(request, None) is False
        assert self.perm.message == "Group not found"

    def test_adversarial_empty_path_segment(self):
        """Path that resolves to empty group_id segment is handled."""
        from django.contrib.auth.models import AnonymousUser

        # Path "/api/v1/group//" -> split("/") -> ["", "api", "v1", "group", "", ""]
        # [-2] = ""
        request = self.factory.get("/api/v1/group//")
        request.user = AnonymousUser()
        request.META["PATH_INFO"] = "/api/v1/group//"
        # group_id="" is falsy, user is AnonymousUser (truthy)
        # So hits the elif not group_id and user block? No -- the code checks
        # `if group_id and user:` which is False, then falls to else.
        # "User or Group detail missing" -> False
        assert self.perm.has_permission(request, None) is False
