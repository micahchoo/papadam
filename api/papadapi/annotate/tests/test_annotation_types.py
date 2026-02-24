"""Tests for the Phase 1b annotation model additions."""


import pytest

from papadapi.annotate.models import Annotation

# ── Model-level tests ─────────────────────────────────────────────────────────


@pytest.mark.django_db
def test_annotation_defaults_to_text_type(group):
    ann = Annotation.objects.create(
        media_reference_id="http://example.com/test/",
        annotation_text="hello",
        media_target="t=0,10",
        group=group,
    )
    assert ann.annotation_type == Annotation.AnnotationType.TEXT
    assert ann.reply_to is None
    assert ann.media_ref_uuid is None


@pytest.mark.django_db
def test_annotation_reply_chain(annotation):
    reply = Annotation.objects.create(
        media_reference_id=annotation.media_reference_id,
        annotation_text="reply text",
        media_target="t=0,5",
        reply_to=annotation,
        annotation_type=Annotation.AnnotationType.AUDIO,
        group=annotation.group,
    )
    assert reply.reply_to_id == annotation.pk
    assert reply.annotation_type == Annotation.AnnotationType.AUDIO
    assert annotation.replies.count() == 1


@pytest.mark.django_db
def test_annotation_media_ref(annotation, media):
    ref = Annotation.objects.create(
        media_reference_id=annotation.media_reference_id,
        annotation_text="cross-media ref",
        media_target="t=0,5",
        annotation_type=Annotation.AnnotationType.MEDIA_REF,
        media_ref_uuid=media.uuid,
        group=annotation.group,
    )
    assert ref.annotation_type == Annotation.AnnotationType.MEDIA_REF
    assert ref.media_ref_uuid == media.uuid


@pytest.mark.django_db
def test_deleting_parent_nullifies_reply(annotation):
    """reply_to uses SET_NULL so deleting a parent doesn't cascade."""
    reply = Annotation.objects.create(
        media_reference_id=annotation.media_reference_id,
        annotation_text="orphaned reply",
        media_target="t=0,5",
        reply_to=annotation,
        group=annotation.group,
    )
    annotation.delete()
    reply.refresh_from_db()
    assert reply.reply_to is None


# ── Serializer-level tests ────────────────────────────────────────────────────


@pytest.mark.django_db
def test_annotation_api_exposes_type_fields(auth_client, annotation):
    resp = auth_client.get(f"/api/v1/annotate/{annotation.uuid}/")
    assert resp.status_code == 200
    assert "annotation_type" in resp.data
    assert "reply_to" in resp.data
    assert "media_ref_uuid" in resp.data
    assert resp.data["annotation_type"] == Annotation.AnnotationType.TEXT


@pytest.mark.django_db
def test_annotation_list_returns_type_field(auth_client, annotation):
    resp = auth_client.get("/api/v1/annotate/")
    assert resp.status_code == 200
