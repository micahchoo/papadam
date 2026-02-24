"""Tests for crdt YDocState model and persistence bridge."""

import base64
import uuid

import pytest
from django.db import IntegrityError

from papadapi.crdt.models import YDocState

# ── Model ─────────────────────────────────────────────────────────────────────


@pytest.mark.django_db
def test_ydocstate_str():
    m_uuid = uuid.uuid4()
    state = YDocState.objects.create(media_uuid=m_uuid, state_vector=b"test-bytes")
    assert str(m_uuid) in str(state)


@pytest.mark.django_db
def test_ydocstate_unique_per_media():
    m_uuid = uuid.uuid4()
    YDocState.objects.create(media_uuid=m_uuid, state_vector=b"v1")
    with pytest.raises(IntegrityError):
        YDocState.objects.create(media_uuid=m_uuid, state_vector=b"v2")


# ── API ───────────────────────────────────────────────────────────────────────


@pytest.mark.django_db
def test_crdt_get_404_when_no_state(auth_client, media):
    resp = auth_client.get(f"/api/v1/crdt/{media.uuid}/")
    assert resp.status_code == 404


@pytest.mark.django_db
def test_crdt_put_creates_state(auth_client, media):
    payload = {"state_vector": base64.b64encode(b"yjs-state").decode()}
    resp = auth_client.put(
        f"/api/v1/crdt/{media.uuid}/",
        data=payload,
        format="json",
    )
    assert resp.status_code == 201
    assert resp.data["media_uuid"] == str(media.uuid)
    assert resp.data["state_vector"] == base64.b64encode(b"yjs-state").decode()


@pytest.mark.django_db
def test_crdt_put_updates_existing_state(auth_client, media):
    YDocState.objects.create(media_uuid=media.uuid, state_vector=b"old")
    payload = {"state_vector": base64.b64encode(b"new-state").decode()}
    resp = auth_client.put(
        f"/api/v1/crdt/{media.uuid}/",
        data=payload,
        format="json",
    )
    assert resp.status_code == 200
    assert resp.data["state_vector"] == base64.b64encode(b"new-state").decode()


@pytest.mark.django_db
def test_crdt_roundtrip(auth_client, media):
    payload = {"state_vector": base64.b64encode(b"round-trip").decode()}
    auth_client.put(f"/api/v1/crdt/{media.uuid}/", data=payload, format="json")
    resp = auth_client.get(f"/api/v1/crdt/{media.uuid}/")
    assert resp.status_code == 200
    assert resp.data["state_vector"] == base64.b64encode(b"round-trip").decode()


@pytest.mark.django_db
def test_crdt_requires_auth(api_client, media):
    resp = api_client.get(f"/api/v1/crdt/{media.uuid}/")
    assert resp.status_code == 401
