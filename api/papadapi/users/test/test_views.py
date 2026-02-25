"""Tests for users.views — SearchUserView and InstanceUserStats endpoints."""

import pytest
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from papadapi.conftest import UserFactory

SEARCH_URL = "/api/v1/users/search/"
STATS_URL = "/api/v1/instanceuserstats/"


# ── Helpers ───────────────────────────────────────────────────────────────────


def _results(resp):
    """Extract the results list from a paginated DRF response."""
    return resp.data["results"]


# ── Fixtures ──────────────────────────────────────────────────────────────────


@pytest.fixture
def admin_client(db, admin_user):
    """Client authenticated as superuser."""
    client = APIClient()
    refresh = RefreshToken.for_user(admin_user)
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {refresh.access_token}")
    return client


# ── SearchUserView: unauthenticated ──────────────────────────────────────────


@pytest.mark.django_db
class TestSearchUserUnauthenticated:
    """SearchUserView requires authentication."""

    def test_list_returns_401(self, api_client):
        resp = api_client.get(SEARCH_URL)
        assert resp.status_code == 401

    def test_search_returns_401(self, api_client):
        resp = api_client.get(SEARCH_URL, {"search": "alice"})
        assert resp.status_code == 401


# ── SearchUserView: list all ─────────────────────────────────────────────────


@pytest.mark.django_db
class TestSearchUserListAll:
    """Without ?search, returns all users."""

    def test_list_returns_all_users(self, auth_client, user):
        other = UserFactory()
        resp = auth_client.get(SEARCH_URL)
        assert resp.status_code == 200
        returned_ids = {str(u["id"]) for u in _results(resp)}
        assert str(user.id) in returned_ids
        assert str(other.id) in returned_ids

    def test_response_is_paginated(self, auth_client, user):
        resp = auth_client.get(SEARCH_URL)
        assert resp.status_code == 200
        assert "count" in resp.data
        assert "results" in resp.data

    def test_response_fields(self, auth_client, user):
        resp = auth_client.get(SEARCH_URL)
        assert resp.status_code == 200
        results = _results(resp)
        assert len(results) >= 1
        item = results[0]
        assert set(item.keys()) == {"id", "username", "first_name", "last_name"}


# ── SearchUserView: search by field ──────────────────────────────────────────


@pytest.mark.django_db
class TestSearchUser:
    """Search users by username, email, first_name, last_name."""

    def test_search_by_username_returns_matching_users(self, auth_client):
        target = UserFactory(username="findme_unique")
        UserFactory(username="otherperson")
        resp = auth_client.get(SEARCH_URL, {"search": "findme"})
        assert resp.status_code == 200
        ids = {u["id"] for u in _results(resp)}
        assert str(target.id) in ids

    def test_search_by_email_returns_matching_users(self, auth_client):
        target = UserFactory(email="rare_email_xyz@example.com")
        resp = auth_client.get(SEARCH_URL, {"search": "rare_email_xyz"})
        assert resp.status_code == 200
        ids = {u["id"] for u in _results(resp)}
        assert str(target.id) in ids

    def test_search_by_first_name_returns_matching_users(self, auth_client):
        target = UserFactory(first_name="Zephyrine")
        resp = auth_client.get(SEARCH_URL, {"search": "Zephyrine"})
        assert resp.status_code == 200
        ids = {u["id"] for u in _results(resp)}
        assert str(target.id) in ids

    def test_search_by_last_name_returns_matching_users(self, auth_client):
        target = UserFactory(last_name="Quetzalcoatl")
        resp = auth_client.get(SEARCH_URL, {"search": "Quetzalcoatl"})
        assert resp.status_code == 200
        ids = {u["id"] for u in _results(resp)}
        assert str(target.id) in ids

    def test_search_is_case_insensitive(self, auth_client):
        target = UserFactory(username="CamelCaseUser")
        resp = auth_client.get(SEARCH_URL, {"search": "camelcaseuser"})
        assert resp.status_code == 200
        ids = {u["id"] for u in _results(resp)}
        assert str(target.id) in ids

    def test_search_partial_match(self, auth_client):
        target = UserFactory(username="abcdefghij")
        resp = auth_client.get(SEARCH_URL, {"search": "cdefg"})
        assert resp.status_code == 200
        ids = {u["id"] for u in _results(resp)}
        assert str(target.id) in ids

    def test_search_no_match_returns_empty(self, auth_client):
        resp = auth_client.get(SEARCH_URL, {"search": "zzz_nonexistent_zzz"})
        assert resp.status_code == 200
        assert len(_results(resp)) == 0

    def test_search_excludes_non_matching(self, auth_client):
        UserFactory(username="visible_user_abc")
        UserFactory(username="hidden_user_xyz")
        resp = auth_client.get(SEARCH_URL, {"search": "visible_user_abc"})
        assert resp.status_code == 200
        usernames = {u["username"] for u in _results(resp)}
        assert "hidden_user_xyz" not in usernames


# ── InstanceUserStats: unauthenticated / non-superuser ──────────────────────


@pytest.mark.django_db
class TestInstanceUserStatsPermissions:
    """InstanceUserStats requires superuser."""

    def test_unauthenticated_returns_401(self, api_client):
        resp = api_client.get(STATS_URL)
        assert resp.status_code == 401

    def test_normal_user_returns_403(self, auth_client):
        resp = auth_client.get(STATS_URL)
        assert resp.status_code == 403


# ── InstanceUserStats: superuser ─────────────────────────────────────────────


@pytest.mark.django_db
class TestInstanceUserStats:
    """Superuser can access date-aggregated user registration stats."""

    def test_superuser_gets_200(self, admin_client):
        resp = admin_client.get(STATS_URL)
        assert resp.status_code == 200

    def test_response_is_flat_list(self, admin_client):
        """get_paginated_response returns Response(data) — no pagination wrapper."""
        resp = admin_client.get(STATS_URL)
        assert resp.status_code == 200
        assert isinstance(resp.data, list)

    def test_response_contains_stats_fields(self, admin_client):
        resp = admin_client.get(STATS_URL)
        assert resp.status_code == 200
        assert len(resp.data) > 0
        item = resp.data[0]
        assert "created_date" in item
        assert "total" in item

    def test_stats_reflect_user_count(self, admin_client):
        """Creating users should appear in the aggregated stats."""
        UserFactory()
        UserFactory()
        resp = admin_client.get(STATS_URL)
        assert resp.status_code == 200
        total_sum = sum(item["total"] for item in resp.data)
        # At least the admin_user + 2 new users exist
        assert total_sum >= 3

    def test_stats_grouped_by_date(self, admin_client):
        """Each entry has a unique created_date (no duplicate dates)."""
        resp = admin_client.get(STATS_URL)
        dates = [item["created_date"] for item in resp.data]
        assert len(dates) == len(set(dates))


# ── Adversarial ──────────────────────────────────────────────────────────────


@pytest.mark.django_db
class TestAdversarial:
    """Edge cases and adversarial inputs."""

    def test_search_with_empty_string_returns_all(self, auth_client, user):
        """Empty search string matches everything via icontains."""
        UserFactory()
        resp = auth_client.get(SEARCH_URL, {"search": ""})
        assert resp.status_code == 200
        from papadapi.users.models import User as UserModel

        assert resp.data["count"] == UserModel.objects.count()

    def test_search_with_sql_injection_attempt(self, auth_client):
        """ORM parameterizes queries — SQL injection string is treated as literal."""
        resp = auth_client.get(SEARCH_URL, {"search": "'; DROP TABLE users; --"})
        assert resp.status_code == 200
        # No crash, returns empty or matching (no real user has this name)

    def test_search_with_special_characters(self, auth_client):
        """Percent and underscore (SQL wildcards) treated as literals by icontains."""
        target = UserFactory(username="percent%user")
        resp = auth_client.get(SEARCH_URL, {"search": "percent%user"})
        assert resp.status_code == 200
        ids = {u["id"] for u in _results(resp)}
        assert str(target.id) in ids

    def test_stats_endpoint_rejects_post(self, admin_client):
        """InstanceUserStats is list-only (GET)."""
        resp = admin_client.post(STATS_URL, {})
        assert resp.status_code == 405

    def test_search_endpoint_rejects_post(self, auth_client):
        """SearchUserView is list-only (GET)."""
        resp = auth_client.post(SEARCH_URL, {})
        assert resp.status_code == 405
