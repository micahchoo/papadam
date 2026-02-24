"""Tests for the Exhibit CRUD API."""

import uuid

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


@pytest.mark.django_db
def test_delete_block(auth_client, exhibit, media):
    block = ExhibitBlock.objects.create(
        exhibit=exhibit, block_type="media", media_uuid=media.uuid, order=0
    )
    resp = auth_client.delete(f"/api/v1/exhibit/{exhibit.uuid}/blocks/{block.id}/")
    assert resp.status_code == 204
    assert ExhibitBlock.objects.filter(id=block.id).count() == 0


@pytest.mark.django_db
def test_delete_block_404_for_unknown(auth_client, exhibit):
    resp = auth_client.delete(f"/api/v1/exhibit/{exhibit.uuid}/blocks/99999/")
    assert resp.status_code == 404


@pytest.mark.django_db
def test_delete_block_requires_auth(api_client, exhibit, media):
    block = ExhibitBlock.objects.create(
        exhibit=exhibit, block_type="media", media_uuid=media.uuid, order=0
    )
    resp = api_client.delete(f"/api/v1/exhibit/{exhibit.uuid}/blocks/{block.id}/")
    assert resp.status_code == 401


# ── Block UUID referential integrity ──────────────────────────────────────────


@pytest.mark.django_db
def test_block_rejects_nonexistent_media_uuid(auth_client, exhibit):
    """media_uuid must reference an existing MediaStore."""
    resp = auth_client.post(
        f"/api/v1/exhibit/{exhibit.uuid}/blocks/",
        data={
            "block_type": "media",
            "media_uuid": str(uuid.uuid4()),  # random — does not exist
            "order": 0,
        },
        format="json",
    )
    assert resp.status_code == 400
    assert "media_uuid" in resp.data


@pytest.mark.django_db
def test_block_rejects_nonexistent_annotation_uuid(auth_client, exhibit):
    """annotation_uuid must reference an existing Annotation."""
    resp = auth_client.post(
        f"/api/v1/exhibit/{exhibit.uuid}/blocks/",
        data={
            "block_type": "annotation",
            "annotation_uuid": str(uuid.uuid4()),  # random — does not exist
            "order": 0,
        },
        format="json",
    )
    assert resp.status_code == 400
    assert "annotation_uuid" in resp.data


@pytest.mark.django_db
def test_block_accepts_valid_annotation_uuid(auth_client, exhibit, annotation):
    """annotation_uuid that exists passes validation."""
    resp = auth_client.post(
        f"/api/v1/exhibit/{exhibit.uuid}/blocks/",
        data={
            "block_type": "annotation",
            "annotation_uuid": str(annotation.uuid),
            "order": 0,
        },
        format="json",
    )
    assert resp.status_code == 201


# ── Block reorder ──────────────────────────────────────────────────────────────


@pytest.mark.django_db
def test_reorder_blocks(auth_client, exhibit, media):
    """Reorder reverses the position of two blocks."""
    b0 = ExhibitBlock.objects.create(
        exhibit=exhibit, block_type="media", media_uuid=media.uuid, order=0
    )
    b1 = ExhibitBlock.objects.create(
        exhibit=exhibit, block_type="media", media_uuid=media.uuid, order=1
    )
    resp = auth_client.post(
        f"/api/v1/exhibit/{exhibit.uuid}/blocks/reorder/",
        data={"block_ids": [b1.id, b0.id]},
        format="json",
    )
    assert resp.status_code == 200
    b0.refresh_from_db()
    b1.refresh_from_db()
    assert b1.order == 0
    assert b0.order == 1


@pytest.mark.django_db
def test_reorder_blocks_unknown_id(auth_client, exhibit):
    """Returns 400 when a block_id does not belong to this exhibit."""
    resp = auth_client.post(
        f"/api/v1/exhibit/{exhibit.uuid}/blocks/reorder/",
        data={"block_ids": [99999]},
        format="json",
    )
    assert resp.status_code == 400


@pytest.mark.django_db
def test_reorder_blocks_requires_auth(api_client, exhibit, media):
    """Unauthenticated reorder is rejected."""
    b0 = ExhibitBlock.objects.create(
        exhibit=exhibit, block_type="media", media_uuid=media.uuid, order=0
    )
    resp = api_client.post(
        f"/api/v1/exhibit/{exhibit.uuid}/blocks/reorder/",
        data={"block_ids": [b0.id]},
        format="json",
    )
    assert resp.status_code == 401


@pytest.mark.django_db
def test_reorder_blocks_invalid_payload(auth_client, exhibit):
    """Non-list block_ids returns 400."""
    resp = auth_client.post(
        f"/api/v1/exhibit/{exhibit.uuid}/blocks/reorder/",
        data={"block_ids": "not-a-list"},
        format="json",
    )
    assert resp.status_code == 400


# ── Update ────────────────────────────────────────────────────────────────────


@pytest.mark.django_db
def test_exhibit_update_title(auth_client, exhibit):
    resp = auth_client.patch(
        f"/api/v1/exhibit/{exhibit.uuid}/",
        data={"title": "Renamed"},
        format="json",
    )
    assert resp.status_code == 200
    exhibit.refresh_from_db()
    assert exhibit.title == "Renamed"


@pytest.mark.django_db
def test_exhibit_update_requires_auth(api_client, exhibit):
    resp = api_client.patch(
        f"/api/v1/exhibit/{exhibit.uuid}/",
        data={"title": "No auth"},
        format="json",
    )
    assert resp.status_code == 401


# ── Delete ────────────────────────────────────────────────────────────────────


@pytest.mark.django_db
def test_exhibit_delete(auth_client, exhibit):
    resp = auth_client.delete(f"/api/v1/exhibit/{exhibit.uuid}/")
    assert resp.status_code == 204
    assert Exhibit.objects.filter(uuid=exhibit.uuid).count() == 0


@pytest.mark.django_db
def test_exhibit_delete_cascades_blocks(auth_client, exhibit, media):
    ExhibitBlock.objects.create(
        exhibit=exhibit, block_type="media", media_uuid=media.uuid, order=0
    )
    auth_client.delete(f"/api/v1/exhibit/{exhibit.uuid}/")
    assert ExhibitBlock.objects.filter(exhibit=exhibit).count() == 0
