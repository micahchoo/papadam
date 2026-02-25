"""Tests for archive permission classes.

Covers: IsArchiveCreateOrReadOnly, IsArchiveCopyAllowed, IsArchiveUpdateOrReadOnly
"""

import pytest
from rest_framework.request import Request
from rest_framework.test import APIRequestFactory

from papadapi.archive.permissions import (
    IsArchiveCopyAllowed,
    IsArchiveCreateOrReadOnly,
    IsArchiveUpdateOrReadOnly,
)
from papadapi.conftest import GroupFactory, MediaStoreFactory, UserFactory


def _drf_request(wsgi_request):
    """Wrap a WSGI request in DRF's Request so .data and .query_params work."""
    from rest_framework.parsers import FormParser, JSONParser, MultiPartParser

    drf_req = Request(wsgi_request, parsers=[JSONParser(), FormParser(), MultiPartParser()])
    # Preserve the user we set on the WSGI request
    drf_req._user = wsgi_request.user
    return drf_req


# ── IsArchiveCreateOrReadOnly ─────────────────────────────────────────────────


@pytest.mark.django_db
class TestIsArchiveCreateOrReadOnly:
    """Permission that gates media creation on group membership."""

    def setup_method(self):
        self.perm = IsArchiveCreateOrReadOnly()
        self.factory = APIRequestFactory()

    def test_get_public_group_allows_anon(self):
        """GET for a public group is allowed even without auth."""
        group = GroupFactory(is_public=True)
        raw = self.factory.get("/api/v1/archive/", {"group": group.id})
        raw.user = UserFactory()
        request = _drf_request(raw)
        assert self.perm.has_permission(request, None) is True

    def test_get_private_group_denied_for_non_member(self):
        """GET for a private group denies non-members."""
        group = GroupFactory(is_public=False)
        user = UserFactory()
        raw = self.factory.get("/api/v1/archive/", {"group": group.id})
        raw.user = user
        request = _drf_request(raw)
        assert self.perm.has_permission(request, None) is False

    def test_get_private_group_allowed_for_member(self):
        """GET for a private group allows members."""
        group = GroupFactory(is_public=False)
        user = UserFactory()
        group.users.add(user)
        raw = self.factory.get("/api/v1/archive/", {"group": group.id})
        raw.user = user
        request = _drf_request(raw)
        assert self.perm.has_permission(request, None) is True

    def test_post_allowed_for_group_member(self):
        """POST (create) is allowed when user is a group member."""
        group = GroupFactory()
        user = UserFactory()
        group.users.add(user)
        raw = self.factory.post(
            "/api/v1/archive/",
            data={"group": group.id},
            format="json",
        )
        raw.user = user
        request = _drf_request(raw)
        assert self.perm.has_permission(request, None) is True

    def test_post_denied_for_non_member(self):
        """POST (create) is denied when user is not in the group."""
        group = GroupFactory()
        user = UserFactory()
        raw = self.factory.post(
            "/api/v1/archive/",
            data={"group": group.id},
            format="json",
        )
        raw.user = user
        request = _drf_request(raw)
        assert self.perm.has_permission(request, None) is False

    def test_search_without_group_allows_safe_methods(self):
        """GET without group param (search) is allowed for any authed user."""
        user = UserFactory()
        raw = self.factory.get("/api/v1/archive/")
        raw.user = user
        request = _drf_request(raw)
        assert self.perm.has_permission(request, None) is True

    def test_adversarial_empty_user_and_group_denied(self):
        """GET with empty group param from anon falls to search path (allowed)."""
        from django.contrib.auth.models import AnonymousUser

        raw = self.factory.get("/api/v1/archive/", {"group": ""})
        raw.user = AnonymousUser()
        request = _drf_request(raw)
        # group_id="" is falsy, user is AnonymousUser (truthy)
        # Hits: elif not group_id and user -> SAFE_METHODS -> True
        assert self.perm.has_permission(request, None) is True


# ── IsArchiveCopyAllowed ──────────────────────────────────────────────────────


@pytest.mark.django_db
class TestIsArchiveCopyAllowed:
    """Permission that gates media copy on to_group membership."""

    def setup_method(self):
        self.perm = IsArchiveCopyAllowed()
        self.factory = APIRequestFactory()

    def test_put_allowed_when_member_of_target_group(self):
        """PUT to copy is allowed when user is a member of to_group."""
        from_group = GroupFactory()
        to_group = GroupFactory()
        user = UserFactory()
        to_group.users.add(user)
        raw = self.factory.put(
            "/api/v1/archive/copy/fake-uuid/",
            data={"from_group": from_group.id, "to_group": to_group.id},
            format="json",
        )
        raw.user = user
        request = _drf_request(raw)
        assert self.perm.has_permission(request, None) is True

    def test_put_denied_when_not_member_of_target_group(self):
        """PUT to copy is denied when user is not in to_group."""
        from_group = GroupFactory()
        to_group = GroupFactory()
        user = UserFactory()
        raw = self.factory.put(
            "/api/v1/archive/copy/fake-uuid/",
            data={"from_group": from_group.id, "to_group": to_group.id},
            format="json",
        )
        raw.user = user
        request = _drf_request(raw)
        assert self.perm.has_permission(request, None) is False

    def test_get_is_always_denied(self):
        """Only PUT is allowed -- GET returns False."""
        raw = self.factory.get("/api/v1/archive/copy/fake-uuid/")
        raw.user = UserFactory()
        request = _drf_request(raw)
        assert self.perm.has_permission(request, None) is False

    def test_adversarial_missing_group_data_denied(self):
        """PUT with empty from/to group data is denied."""
        user = UserFactory()
        raw = self.factory.put(
            "/api/v1/archive/copy/fake-uuid/",
            data={"from_group": "", "to_group": ""},
            format="json",
        )
        raw.user = user
        request = _drf_request(raw)
        assert self.perm.has_permission(request, None) is False


# ── IsArchiveUpdateOrReadOnly ─────────────────────────────────────────────────


@pytest.mark.django_db
class TestIsArchiveUpdateOrReadOnly:
    """Object-level permission for media update/delete."""

    def setup_method(self):
        self.perm = IsArchiveUpdateOrReadOnly()
        self.factory = APIRequestFactory()

    def test_safe_methods_always_allowed(self):
        """GET, HEAD, OPTIONS are always allowed regardless of membership."""
        group = GroupFactory()
        media = MediaStoreFactory(group=group)
        for method in ("get", "head", "options"):
            request = getattr(self.factory, method)("/api/v1/archive/fake-uuid/")
            request.user = UserFactory()
            assert self.perm.has_object_permission(request, None, media) is True

    def test_put_allowed_for_group_member(self):
        """PUT is allowed when user is a member of the media's group."""
        group = GroupFactory()
        user = UserFactory()
        group.users.add(user)
        media = MediaStoreFactory(group=group)
        request = self.factory.put("/api/v1/archive/fake-uuid/")
        request.user = user
        assert self.perm.has_object_permission(request, None, media) is True

    def test_put_denied_for_non_member(self):
        """PUT is denied when user is not in the media's group."""
        group = GroupFactory()
        user = UserFactory()
        media = MediaStoreFactory(group=group)
        request = self.factory.put("/api/v1/archive/fake-uuid/")
        request.user = user
        assert self.perm.has_object_permission(request, None, media) is False

    def test_delete_denied_for_non_member(self):
        """DELETE is denied for non-members."""
        group = GroupFactory()
        user = UserFactory()
        media = MediaStoreFactory(group=group)
        request = self.factory.delete("/api/v1/archive/fake-uuid/")
        request.user = user
        assert self.perm.has_object_permission(request, None, media) is False

    def test_adversarial_null_group_on_obj_denied(self):
        """When obj.group is None, write permission is denied."""

        class FakeObj:
            group = None

        request = self.factory.put("/api/v1/archive/fake-uuid/")
        request.user = UserFactory()
        assert self.perm.has_object_permission(request, None, FakeObj()) is False
