"""Tests for media_relation reply and cross-media annotation views."""

import pytest

from papadapi.annotate.models import Annotation

# ── Replies ───────────────────────────────────────────────────────────────────


@pytest.mark.django_db
def test_replies_list_empty(auth_client, annotation):
    resp = auth_client.get(f"/api/v1/media-relation/replies/{annotation.uuid}/")
    assert resp.status_code == 200
    assert resp.data == []


@pytest.mark.django_db
def test_replies_list_returns_children(auth_client, annotation):
    Annotation.objects.create(
        media_reference_id=annotation.media_reference_id,
        annotation_text="child",
        media_target="t=0,5",
        reply_to=annotation,
        annotation_type=Annotation.AnnotationType.TEXT,
        group=annotation.group,
    )
    resp = auth_client.get(f"/api/v1/media-relation/replies/{annotation.uuid}/")
    assert resp.status_code == 200
    assert len(resp.data) == 1
    assert resp.data[0]["annotation_text"] == "child"


@pytest.mark.django_db
def test_replies_404_for_unknown_annotation(auth_client):
    import uuid
    resp = auth_client.get(f"/api/v1/media-relation/replies/{uuid.uuid4()}/")
    assert resp.status_code == 404


@pytest.mark.django_db
def test_create_reply(auth_client, annotation):
    resp = auth_client.post(
        f"/api/v1/media-relation/replies/{annotation.uuid}/",
        data={
            "annotation_text": "my reply",
            "media_target": "t=0,3",
            "annotation_type": "audio",
        },
        format="json",
    )
    assert resp.status_code == 201
    assert resp.data["annotation_type"] == "audio"
    assert annotation.replies.count() == 1


@pytest.mark.django_db
def test_create_reply_404_for_unknown_parent(auth_client):
    import uuid
    resp = auth_client.post(
        f"/api/v1/media-relation/replies/{uuid.uuid4()}/",
        data={"annotation_text": "orphan"},
        format="json",
    )
    assert resp.status_code == 404


@pytest.mark.django_db
def test_create_reply_defaults_to_text_type(auth_client, annotation):
    resp = auth_client.post(
        f"/api/v1/media-relation/replies/{annotation.uuid}/",
        data={"annotation_text": "default type reply"},
        format="json",
    )
    assert resp.status_code == 201
    assert resp.data["annotation_type"] == "text"


@pytest.mark.django_db
def test_create_reply_inherits_media_reference_id(auth_client, annotation):
    resp = auth_client.post(
        f"/api/v1/media-relation/replies/{annotation.uuid}/",
        data={"annotation_text": "inherits parent media"},
        format="json",
    )
    assert resp.status_code == 201
    assert resp.data["media_reference_id"] == annotation.media_reference_id


@pytest.mark.django_db
def test_create_reply_sets_created_by(auth_client, user, annotation):
    resp = auth_client.post(
        f"/api/v1/media-relation/replies/{annotation.uuid}/",
        data={"annotation_text": "authored reply"},
        format="json",
    )
    assert resp.status_code == 201
    from papadapi.annotate.models import Annotation
    reply = Annotation.objects.get(uuid=resp.data["uuid"])
    assert reply.created_by == user


# ── Media refs ────────────────────────────────────────────────────────────────


@pytest.mark.django_db
def test_media_refs_returns_empty_for_unreferenced_media(auth_client, media):
    resp = auth_client.get(f"/api/v1/media-relation/media-refs/{media.uuid}/")
    assert resp.status_code == 200
    assert resp.data == []


@pytest.mark.django_db
def test_media_refs_returns_referencing_annotations(auth_client, annotation, media):
    Annotation.objects.create(
        media_reference_id=annotation.media_reference_id,
        annotation_text="cross-media",
        media_target="t=0,5",
        annotation_type=Annotation.AnnotationType.MEDIA_REF,
        media_ref_uuid=media.uuid,
        group=annotation.group,
    )
    resp = auth_client.get(f"/api/v1/media-relation/media-refs/{media.uuid}/")
    assert resp.status_code == 200
    assert len(resp.data) == 1
    assert resp.data[0]["media_ref_uuid"] == str(media.uuid)
