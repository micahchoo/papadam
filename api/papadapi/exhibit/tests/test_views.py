"""Tests for the Exhibit CRUD API."""


import pytest

from papadapi.exhibit.models import Exhibit, ExhibitBlock

# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture
def exhibit(db, group, user):
    return Exhibit.objects.create(
        title="Test Exhibit",
        description="desc",
        group=group,
        created_by=user,
        is_public=True,
    )


# ── List ──────────────────────────────────────────────────────────────────────


@pytest.mark.django_db
def test_exhibit_list_public_unauthenticated(api_client, exhibit):
    resp = api_client.get("/api/v1/exhibit/")
    assert resp.status_code == 200
    assert any(e["uuid"] == str(exhibit.uuid) for e in resp.data["results"])


# ── Create ────────────────────────────────────────────────────────────────────


@pytest.mark.django_db
def test_exhibit_create_requires_auth(api_client, group):
    resp = api_client.post(
        "/api/v1/exhibit/",
        data={"title": "No auth", "group": group.id},
        format="json",
    )
    assert resp.status_code == 401


@pytest.mark.django_db
def test_exhibit_create(member_client, group_with_member):
    resp = member_client.post(
        "/api/v1/exhibit/",
        data={
            "title": "New Exhibit",
            "description": "d",
            "group": group_with_member.id,
        },
        format="json",
    )
    assert resp.status_code == 201
    assert resp.data["title"] == "New Exhibit"
    assert "uuid" in resp.data


# ── Retrieve ──────────────────────────────────────────────────────────────────


@pytest.mark.django_db
def test_exhibit_retrieve(api_client, exhibit):
    resp = api_client.get(f"/api/v1/exhibit/{exhibit.uuid}/")
    assert resp.status_code == 200
    assert resp.data["title"] == exhibit.title
    assert isinstance(resp.data["blocks"], list)


# ── Blocks ────────────────────────────────────────────────────────────────────


@pytest.mark.django_db
def test_add_block_to_exhibit(auth_client, exhibit, media):
    resp = auth_client.post(
        f"/api/v1/exhibit/{exhibit.uuid}/blocks/",
        data={
            "block_type": "media",
            "media_uuid": str(media.uuid),
            "caption": "First slide",
            "order": 0,
        },
        format="json",
    )
    assert resp.status_code == 201
    assert ExhibitBlock.objects.filter(exhibit=exhibit).count() == 1


@pytest.mark.django_db
def test_block_validation_requires_media_uuid_for_media_type(auth_client, exhibit):
    resp = auth_client.post(
        f"/api/v1/exhibit/{exhibit.uuid}/blocks/",
        data={"block_type": "media", "order": 0},
        format="json",
    )
    assert resp.status_code == 400


@pytest.mark.django_db
def test_list_blocks(auth_client, exhibit, media):
    ExhibitBlock.objects.create(
        exhibit=exhibit, block_type="media", media_uuid=media.uuid, order=0
    )
    resp = auth_client.get(f"/api/v1/exhibit/{exhibit.uuid}/blocks/")
    assert resp.status_code == 200
    assert len(resp.data) == 1
