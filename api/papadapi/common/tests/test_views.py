"""Tests for common views.

Covers: TagsViewSet, GroupViewSet, UpdateGroupViewSet,
        AddUserFromGroupView, RemoveUserFromGroupView,
        RemoveCustomQuestionFromGroupView, AddCustomQuestionFromGroupView,
        UpdateCustomQuestionFromGroupView, InstanceGroupStats,
        GroupTagGraphView, HealthCheck, RuntimeConfigView
"""

import json

import pytest
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from papadapi.common.models import Group, Question, Tags
from papadapi.conftest import (
    GroupFactory,
    MediaStoreFactory,
    TagFactory,
    UserFactory,
)


def _auth_client_for(user):
    """Return an APIClient authenticated as the given user."""
    client = APIClient()
    refresh = RefreshToken.for_user(user)
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {refresh.access_token}")
    return client


# ── TagsViewSet ──────────────────────────────────────────────────────────────


@pytest.mark.django_db
class TestTagsViewSet:
    def test_list_tags_anon_returns_200(self):
        """Anonymous GET returns 200 with tag results."""
        client = APIClient()
        resp = client.get("/api/v1/tags/")
        assert resp.status_code == 200

    def test_list_tags_authed_returns_200(self):
        """Authenticated GET returns 200."""
        user = UserFactory()
        client = _auth_client_for(user)
        resp = client.get("/api/v1/tags/")
        assert resp.status_code == 200

    def test_create_tag_requires_auth(self):
        """POST from anon returns 401."""
        client = APIClient()
        resp = client.post("/api/v1/tags/", data={"name": "new"}, format="json")
        assert resp.status_code == 401

    def test_create_tag_authed_succeeds(self):
        """Authenticated POST creates a tag."""
        user = UserFactory()
        client = _auth_client_for(user)
        resp = client.post("/api/v1/tags/", data={"name": "fresh"}, format="json")
        assert resp.status_code == 201
        assert Tags.objects.filter(name="fresh").exists()

    def test_list_tags_includes_count(self):
        """GET tags endpoint returns tag count data from groups."""
        group = GroupFactory(is_public=True)
        tag = TagFactory(name="counted")
        media = MediaStoreFactory(group=group)
        media.tags.add(tag)
        client = APIClient()
        resp = client.get("/api/v1/tags/")
        assert resp.status_code == 200
        # Response has "results" key with tag count data
        assert "results" in resp.data


# ── GroupViewSet ─────────────────────────────────────────────────────────────


@pytest.mark.django_db
class TestGroupViewSet:
    def test_list_public_groups_anon(self):
        """Anonymous user sees public groups."""
        group = GroupFactory(is_public=True, is_active=True)
        client = APIClient()
        resp = client.get("/api/v1/group/")
        assert resp.status_code == 200
        names = [g["name"] for g in resp.data["results"]]
        assert group.name in names

    def test_list_excludes_user_groups_for_authed(self):
        """Authenticated user does not see their own groups in the list."""
        user = UserFactory()
        my_group = GroupFactory(is_public=True, is_active=True)
        my_group.users.add(user)
        other_group = GroupFactory(is_public=True, is_active=True)
        client = _auth_client_for(user)
        resp = client.get("/api/v1/group/")
        assert resp.status_code == 200
        names = [g["name"] for g in resp.data["results"]]
        assert my_group.name not in names
        assert other_group.name in names

    def test_create_group_requires_auth(self):
        """POST from anon returns 401."""
        client = APIClient()
        resp = client.post(
            "/api/v1/group/", data={"name": "test"}, format="json"
        )
        assert resp.status_code == 401

    def test_create_group_authed(self):
        """Authenticated POST creates group and adds creator as member."""
        user = UserFactory()
        other = UserFactory()
        client = _auth_client_for(user)
        resp = client.post(
            "/api/v1/group/",
            data={
                "name": "New Group",
                "description": "A test group",
                "users": str(other.id),
            },
            format="multipart",
        )
        assert resp.status_code == 200
        g = Group.objects.get(name="New Group")
        assert user in g.users.all()
        assert other in g.users.all()

    def test_create_group_with_extra_questions(self):
        """Creating group with group_extra_questions creates Questions."""
        user = UserFactory()
        client = _auth_client_for(user)
        extra = json.dumps(
            {
                "extra": [
                    {"question": "Age?", "mandatory": False, "type": "number"},
                    {"question": "Location?", "mandatory": True, "type": "text"},
                ]
            }
        )
        resp = client.post(
            "/api/v1/group/",
            data={
                "name": "Q Group",
                "description": "has questions",
                "users": "",
                "group_extra_questions": extra,
            },
            format="multipart",
        )
        assert resp.status_code == 200
        g = Group.objects.get(name="Q Group")
        assert g.extra_group_questions.count() == 2


# ── UpdateGroupViewSet ───────────────────────────────────────────────────────


@pytest.mark.django_db
class TestUpdateGroupViewSet:
    def test_retrieve_group_by_id(self):
        """GET /group/<id>/ returns group details."""
        group = GroupFactory(is_public=True)
        client = APIClient()
        resp = client.get(f"/api/v1/group/{group.id}/")
        assert resp.status_code == 200
        assert resp.data["name"] == group.name

    def test_update_group_as_member(self):
        """PUT from member updates group name/description."""
        group = GroupFactory()
        user = UserFactory()
        group.users.add(user)
        client = _auth_client_for(user)
        resp = client.put(
            f"/api/v1/group/{group.id}/",
            data={
                "name": "Updated",
                "description": "New desc",
                "users": "",
            },
            format="multipart",
        )
        assert resp.status_code == 200
        assert resp.data["name"] == "Updated"

    def test_update_group_denied_for_non_member(self):
        """PUT from non-member returns 403."""
        group = GroupFactory()
        user = UserFactory()
        client = _auth_client_for(user)
        resp = client.put(
            f"/api/v1/group/{group.id}/",
            data={"name": "Hacked", "description": "No", "users": ""},
            format="multipart",
        )
        assert resp.status_code == 403

    def test_update_group_adds_new_users(self):
        """PUT with users CSV adds those users to the group."""
        group = GroupFactory()
        user = UserFactory()
        group.users.add(user)
        new_user = UserFactory()
        client = _auth_client_for(user)
        resp = client.put(
            f"/api/v1/group/{group.id}/",
            data={
                "name": group.name,
                "description": group.description,
                "users": str(new_user.id),
            },
            format="multipart",
        )
        assert resp.status_code == 200
        group.refresh_from_db()
        assert new_user in group.users.all()


# ── AddUserFromGroupView ────────────────────────────────────────────────────


@pytest.mark.django_db
class TestAddUserFromGroupView:
    def test_add_user_to_group(self):
        """PUT adds a user to the group."""
        group = GroupFactory()
        member = UserFactory()
        group.users.add(member)
        new_user = UserFactory()
        client = _auth_client_for(member)
        resp = client.put(
            f"/api/v1/group/add_user/{group.id}/",
            data={"user": new_user.id},
            format="json",
        )
        assert resp.status_code == 200
        assert new_user in group.users.all()

    def test_add_user_already_member_is_noop(self):
        """Adding an already-present user does not duplicate membership."""
        group = GroupFactory()
        member = UserFactory()
        group.users.add(member)
        client = _auth_client_for(member)
        resp = client.put(
            f"/api/v1/group/add_user/{group.id}/",
            data={"user": member.id},
            format="json",
        )
        assert resp.status_code == 200
        assert group.users.filter(id=member.id).count() == 1

    def test_add_user_denied_for_non_member(self):
        """Non-member cannot add users."""
        group = GroupFactory()
        outsider = UserFactory()
        new_user = UserFactory()
        client = _auth_client_for(outsider)
        resp = client.put(
            f"/api/v1/group/add_user/{group.id}/",
            data={"user": new_user.id},
            format="json",
        )
        assert resp.status_code == 403


# ── RemoveUserFromGroupView ──────────────────────────────────────────────────


@pytest.mark.django_db
class TestRemoveUserFromGroupView:
    def test_remove_user_from_group(self):
        """PUT removes a user from the group when >1 members."""
        group = GroupFactory()
        member1 = UserFactory()
        member2 = UserFactory()
        group.users.add(member1, member2)
        client = _auth_client_for(member1)
        resp = client.put(
            f"/api/v1/group/remove_user/{group.id}/",
            data={"user": member2.id},
            format="json",
        )
        assert resp.status_code == 200
        assert member2 not in group.users.all()

    def test_remove_last_user_returns_403(self):
        """Cannot remove the last user from a group."""
        group = GroupFactory()
        sole_member = UserFactory()
        group.users.add(sole_member)
        client = _auth_client_for(sole_member)
        resp = client.put(
            f"/api/v1/group/remove_user/{group.id}/",
            data={"user": sole_member.id},
            format="json",
        )
        assert resp.status_code == 403
        assert "Not allowed" in resp.data["detail"]

    def test_remove_user_denied_for_non_member(self):
        """Non-member cannot remove users."""
        group = GroupFactory()
        member = UserFactory()
        group.users.add(member)
        outsider = UserFactory()
        client = _auth_client_for(outsider)
        resp = client.put(
            f"/api/v1/group/remove_user/{group.id}/",
            data={"user": member.id},
            format="json",
        )
        assert resp.status_code == 403


# ── RemoveCustomQuestionFromGroupView ────────────────────────────────────────


@pytest.mark.django_db
class TestRemoveCustomQuestionFromGroupView:
    def test_remove_question_from_group(self):
        """PUT removes a question from the group."""
        group = GroupFactory()
        user = UserFactory()
        group.users.add(user)
        q = Question.objects.create(
            question="Test?", question_type="text", question_mandatory=False
        )
        group.extra_group_questions.add(q)
        client = _auth_client_for(user)
        resp = client.put(
            f"/api/v1/group/remove_question/{group.id}/",
            data={
                "question_id": q.id,
                "remove_existing_data": "False",
            },
            format="json",
        )
        assert resp.status_code == 200
        assert q not in group.extra_group_questions.all()

    def test_remove_question_with_existing_data_cleanup(self):
        """PUT with remove_existing_data=True cleans media extra_group_response."""
        group = GroupFactory()
        user = UserFactory()
        group.users.add(user)
        q = Question.objects.create(
            question="Where?", question_type="text", question_mandatory=False
        )
        group.extra_group_questions.add(q)
        media = MediaStoreFactory(
            group=group,
            extra_group_response=[
                {
                    "question_id": q.id,
                    "question": "Where?",
                    "question_type": "text",
                    "question_mandatory": False,
                    "response": "Here",
                }
            ],
        )
        client = _auth_client_for(user)
        resp = client.put(
            f"/api/v1/group/remove_question/{group.id}/",
            data={
                "question_id": q.id,
                "remove_existing_data": "True",
            },
            format="json",
        )
        assert resp.status_code == 200
        media.refresh_from_db()
        # The question response should be removed from the media
        remaining_ids = [r["question_id"] for r in media.extra_group_response]
        assert q.id not in remaining_ids


# ── AddCustomQuestionFromGroupView ───────────────────────────────────────────


@pytest.mark.django_db
class TestAddCustomQuestionFromGroupView:
    def test_add_question_to_group(self):
        """PUT creates and adds a question to the group."""
        group = GroupFactory()
        user = UserFactory()
        group.users.add(user)
        client = _auth_client_for(user)
        resp = client.put(
            f"/api/v1/group/add_question/{group.id}/",
            data={
                "question": "How many?",
                "mandatory": True,
                "type": "number",
                "add_default_value": "False",
            },
            format="json",
        )
        assert resp.status_code == 200
        assert group.extra_group_questions.filter(question="How many?").exists()

    def test_add_question_with_default_value_backfills_media(self):
        """PUT with add_default_value=True backfills existing media."""
        group = GroupFactory()
        user = UserFactory()
        group.users.add(user)
        media = MediaStoreFactory(group=group, extra_group_response=[])
        client = _auth_client_for(user)
        resp = client.put(
            f"/api/v1/group/add_question/{group.id}/",
            data={
                "question": "Name?",
                "mandatory": False,
                "type": "text",
                "add_default_value": "True",
                "default_value": "Unknown",
            },
            format="json",
        )
        assert resp.status_code == 200
        media.refresh_from_db()
        assert len(media.extra_group_response) == 1
        assert media.extra_group_response[0]["response"] == "Unknown"

    def test_add_question_denied_for_non_member(self):
        """Non-member cannot add questions."""
        group = GroupFactory()
        user = UserFactory()
        client = _auth_client_for(user)
        resp = client.put(
            f"/api/v1/group/add_question/{group.id}/",
            data={
                "question": "hack?",
                "mandatory": False,
                "type": "text",
                "add_default_value": "False",
            },
            format="json",
        )
        assert resp.status_code == 403


# ── UpdateCustomQuestionFromGroupView ────────────────────────────────────────


@pytest.mark.django_db
class TestUpdateCustomQuestionFromGroupView:
    def test_update_question_text(self):
        """PUT updates the question text and cascades to media responses."""
        group = GroupFactory()
        user = UserFactory()
        group.users.add(user)
        q = Question.objects.create(
            question="Old?", question_type="text", question_mandatory=False
        )
        group.extra_group_questions.add(q)
        media = MediaStoreFactory(
            group=group,
            extra_group_response=[
                {
                    "question_id": q.id,
                    "question": "Old?",
                    "question_type": "text",
                    "question_mandatory": False,
                    "response": "ans",
                }
            ],
        )
        client = _auth_client_for(user)
        resp = client.put(
            f"/api/v1/group/update_question/{group.id}/",
            data={"question_id": q.id, "question": "New?"},
            format="json",
        )
        assert resp.status_code == 200
        q.refresh_from_db()
        assert q.question == "New?"
        media.refresh_from_db()
        assert media.extra_group_response[0]["question"] == "New?"

    def test_update_nonexistent_question_returns_404(self):
        """PUT with invalid question_id returns 404."""
        group = GroupFactory()
        user = UserFactory()
        group.users.add(user)
        client = _auth_client_for(user)
        resp = client.put(
            f"/api/v1/group/update_question/{group.id}/",
            data={"question_id": 99999, "question": "Nope"},
            format="json",
        )
        assert resp.status_code == 404

    def test_update_question_denied_for_non_member(self):
        """Non-member cannot update questions."""
        group = GroupFactory()
        user = UserFactory()
        q = Question.objects.create(
            question="X?", question_type="text", question_mandatory=False
        )
        client = _auth_client_for(user)
        resp = client.put(
            f"/api/v1/group/update_question/{group.id}/",
            data={"question_id": q.id, "question": "Y?"},
            format="json",
        )
        assert resp.status_code == 403


# ── InstanceGroupStats ───────────────────────────────────────────────────────


@pytest.mark.django_db
class TestInstanceGroupStats:
    def test_superuser_gets_stats(self):
        """Superuser gets 200 with group creation stats."""
        admin = UserFactory(is_superuser=True)
        GroupFactory()
        client = _auth_client_for(admin)
        resp = client.get("/api/v1/instancegroupstats/")
        assert resp.status_code == 200

    def test_normal_user_denied(self):
        """Non-superuser gets 403."""
        user = UserFactory()
        client = _auth_client_for(user)
        resp = client.get("/api/v1/instancegroupstats/")
        assert resp.status_code == 403

    def test_anon_denied(self):
        """Unauthenticated user gets 401."""
        client = APIClient()
        resp = client.get("/api/v1/instancegroupstats/")
        assert resp.status_code == 401


# ── GroupTagGraphView ────────────────────────────────────────────────────────


@pytest.mark.django_db
class TestGroupTagGraphView:
    def test_member_gets_tag_graph(self):
        """Member gets 200 with nodes/links/categories structure."""
        group = GroupFactory()
        user = UserFactory()
        group.users.add(user)
        tag = TagFactory(name="graphtag")
        media = MediaStoreFactory(group=group)
        media.tags.add(tag)
        client = _auth_client_for(user)
        resp = client.get(f"/api/v1/group/taggraph/{group.id}/")
        assert resp.status_code == 200
        assert "nodes" in resp.data
        assert "links" in resp.data
        assert "categories" in resp.data
        assert len(resp.data["categories"]) == 3

    def test_anon_public_group_gets_graph(self):
        """Anonymous user can access tag graph of a public group."""
        group = GroupFactory(is_public=True)
        client = APIClient()
        resp = client.get(f"/api/v1/group/taggraph/{group.id}/")
        assert resp.status_code == 200
        assert "nodes" in resp.data

    def test_empty_group_returns_empty_graph(self):
        """Group with no media returns empty nodes/links."""
        group = GroupFactory()
        user = UserFactory()
        group.users.add(user)
        client = _auth_client_for(user)
        resp = client.get(f"/api/v1/group/taggraph/{group.id}/")
        assert resp.status_code == 200
        assert resp.data["nodes"] == []
        assert resp.data["links"] == []


# ── HealthCheck ──────────────────────────────────────────────────────────────


@pytest.mark.django_db
class TestHealthCheck:
    def test_returns_200(self):
        """GET /healthcheck/ returns 200."""
        client = APIClient()
        resp = client.get("/healthcheck/")
        assert resp.status_code == 200


# ── RuntimeConfigView ────────────────────────────────────────────────────────


@pytest.mark.django_db
class TestRuntimeConfigView:
    def test_returns_api_and_crdt_urls(self):
        """GET /config.json returns API_URL and CRDT_URL."""
        client = APIClient()
        resp = client.get("/config.json")
        assert resp.status_code == 200
        assert "API_URL" in resp.data
        assert "CRDT_URL" in resp.data

    def test_returns_empty_string_defaults(self, settings):
        """When env vars not set, values are empty strings."""
        # Ensure no settings are set
        if hasattr(settings, "PUBLIC_API_URL"):
            delattr(settings, "PUBLIC_API_URL")
        if hasattr(settings, "PUBLIC_CRDT_URL"):
            delattr(settings, "PUBLIC_CRDT_URL")
        client = APIClient()
        resp = client.get("/config.json")
        assert resp.status_code == 200
        assert resp.data["API_URL"] == ""
        assert resp.data["CRDT_URL"] == ""


# ── Adversarial ──────────────────────────────────────────────────────────────


@pytest.mark.django_db
class TestCommonViewsAdversarial:
    def test_update_group_with_nonexistent_user_id_raises(self):
        """PUT /group/<id>/ with non-existent user in CSV causes error."""
        group = GroupFactory()
        user = UserFactory()
        group.users.add(user)
        client = _auth_client_for(user)
        resp = client.put(
            f"/api/v1/group/{group.id}/",
            data={
                "name": "ok",
                "description": "ok",
                "users": "999999",
            },
            format="multipart",
        )
        # User.objects.get(id=999999) raises DoesNotExist -> 500
        assert resp.status_code == 500

    def test_remove_user_anon_returns_401(self):
        """Anon PUT to remove_user returns 401."""
        group = GroupFactory()
        client = APIClient()
        resp = client.put(
            f"/api/v1/group/remove_user/{group.id}/",
            data={"user": 1},
            format="json",
        )
        assert resp.status_code == 401

    def test_tag_graph_nonexistent_group_returns_404(self):
        """Tag graph for non-existent group returns 404."""
        client = APIClient()
        resp = client.get("/api/v1/group/taggraph/999999/")
        assert resp.status_code == 404

    def test_create_group_empty_users_string(self):
        """Creating group with empty users string does not crash."""
        user = UserFactory()
        client = _auth_client_for(user)
        resp = client.post(
            "/api/v1/group/",
            data={
                "name": "Solo Group",
                "description": "just me",
                "users": "",
            },
            format="multipart",
        )
        # data["users"] is "" which is falsy, so the `if data["users"]:` branch
        # is skipped. Creator is still added.
        assert resp.status_code == 200
        g = Group.objects.get(name="Solo Group")
        assert g.users.count() == 1
        assert user in g.users.all()
