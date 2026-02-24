"""
Tests for AnnotationCreateSet.create() and AnnotationRetreiveSet.update().

Verifies that annotation_type, annotation_audio, annotation_video,
media_ref_uuid, and reply_to are persisted correctly via the API.
"""

from unittest.mock import patch

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile

from papadapi.annotate.models import Annotation

# ── Create endpoint ────────────────────────────────────────────────────────────


@pytest.mark.django_db
def test_create_defaults_to_text_type(member_client, member_media):
    resp = member_client.post(
        "/api/v1/annotate/",
        {
            "media_reference_id": str(member_media.uuid),
            "annotation_text": "plain note",
            "media_target": "t=0,10",
            "tags": "",
        },
        format="multipart",
    )
    assert resp.status_code == 200
    assert resp.data["annotation_type"] == "text"


@pytest.mark.django_db
def test_create_stores_annotation_type_audio(member_client, member_media):
    resp = member_client.post(
        "/api/v1/annotate/",
        {
            "media_reference_id": str(member_media.uuid),
            "annotation_text": "",
            "media_target": "t=5,15",
            "annotation_type": "audio",
            "tags": "",
        },
        format="multipart",
    )
    assert resp.status_code == 200
    assert resp.data["annotation_type"] == "audio"
    ann = Annotation.objects.get(uuid=resp.data["uuid"])
    assert ann.annotation_type == Annotation.AnnotationType.AUDIO


@pytest.mark.django_db
def test_create_stores_annotation_type_video(member_client, member_media):
    resp = member_client.post(
        "/api/v1/annotate/",
        {
            "media_reference_id": str(member_media.uuid),
            "annotation_text": "",
            "media_target": "t=0,5",
            "annotation_type": "video",
            "tags": "",
        },
        format="multipart",
    )
    assert resp.status_code == 200
    assert resp.data["annotation_type"] == "video"


@pytest.mark.django_db
def test_create_stores_media_ref_uuid(member_client, member_media, media):
    resp = member_client.post(
        "/api/v1/annotate/",
        {
            "media_reference_id": str(member_media.uuid),
            "annotation_text": "cross-ref",
            "media_target": "t=0,5",
            "annotation_type": "media_ref",
            "media_ref_uuid": str(media.uuid),
            "tags": "",
        },
        format="multipart",
    )
    assert resp.status_code == 200
    assert resp.data["annotation_type"] == "media_ref"
    ann = Annotation.objects.get(uuid=resp.data["uuid"])
    assert str(ann.media_ref_uuid) == str(media.uuid)


@pytest.mark.django_db
def test_create_reply_to_sets_parent(member_client, member_media, member_annotation):
    resp = member_client.post(
        "/api/v1/annotate/",
        {
            "media_reference_id": str(member_media.uuid),
            "annotation_text": "a reply",
            "media_target": "t=0,5",
            "reply_to": str(member_annotation.id),
            "tags": "",
        },
        format="multipart",
    )
    assert resp.status_code == 200
    ann = Annotation.objects.get(uuid=resp.data["uuid"])
    assert ann.reply_to_id == member_annotation.id


@pytest.mark.django_db
def test_create_invalid_reply_to_is_ignored(member_client, member_media):
    """Malformed reply_to should not crash the view."""
    resp = member_client.post(
        "/api/v1/annotate/",
        {
            "media_reference_id": str(member_media.uuid),
            "annotation_text": "note",
            "media_target": "t=0,5",
            "reply_to": "not-an-id",
            "tags": "",
        },
        format="multipart",
    )
    assert resp.status_code == 200
    ann = Annotation.objects.get(uuid=resp.data["uuid"])
    assert ann.reply_to is None


# ── Update endpoint ────────────────────────────────────────────────────────────


@pytest.mark.django_db
def test_update_changes_annotation_type(member_client, member_annotation):
    resp = member_client.patch(
        f"/api/v1/annotate/{member_annotation.uuid}/",
        {"annotation_type": "video"},
        format="multipart",
    )
    assert resp.status_code == 200
    assert resp.data["annotation_type"] == "video"
    member_annotation.refresh_from_db()
    assert member_annotation.annotation_type == Annotation.AnnotationType.VIDEO


@pytest.mark.django_db
def test_update_stores_media_ref_uuid(member_client, member_annotation, media):
    resp = member_client.patch(
        f"/api/v1/annotate/{member_annotation.uuid}/",
        {
            "annotation_type": "media_ref",
            "media_ref_uuid": str(media.uuid),
        },
        format="multipart",
    )
    assert resp.status_code == 200
    member_annotation.refresh_from_db()
    assert str(member_annotation.media_ref_uuid) == str(media.uuid)


@pytest.mark.django_db
def test_update_clears_media_ref_uuid(member_client, member_annotation, media):
    member_annotation.media_ref_uuid = media.uuid
    member_annotation.save()

    resp = member_client.patch(
        f"/api/v1/annotate/{member_annotation.uuid}/",
        {"media_ref_uuid": ""},
        format="multipart",
    )
    assert resp.status_code == 200
    member_annotation.refresh_from_db()
    assert member_annotation.media_ref_uuid is None


@pytest.mark.django_db
def test_update_partial_leaves_other_fields(member_client, member_annotation):
    original_text = member_annotation.annotation_text

    resp = member_client.patch(
        f"/api/v1/annotate/{member_annotation.uuid}/",
        {"annotation_type": "image"},
        format="multipart",
    )
    assert resp.status_code == 200
    member_annotation.refresh_from_db()
    assert member_annotation.annotation_type == Annotation.AnnotationType.IMAGE
    assert member_annotation.annotation_text == original_text


# ── Transcode enqueue on create ────────────────────────────────────────────────


@pytest.mark.django_db
def test_create_audio_annotation_enqueues_transcode(member_client, member_media):
    """Posting an audio file triggers transcode_annotation_audio enqueue."""
    audio_file = SimpleUploadedFile("clip.mp3", b"RIFF" + b"\x00" * 40,
                                    content_type="audio/mpeg")
    with patch("papadapi.annotate.views.enqueue") as mock_enqueue:
        resp = member_client.post(
            "/api/v1/annotate/",
            {
                "media_reference_id": str(member_media.uuid),
                "annotation_text": "",
                "media_target": "t=0,10",
                "annotation_type": "audio",
                "annotation_audio": audio_file,
                "tags": "",
            },
            format="multipart",
        )
    assert resp.status_code == 200
    created_id = Annotation.objects.get(uuid=resp.data["uuid"]).id
    mock_enqueue.assert_called_once_with("transcode_annotation_audio", created_id)


@pytest.mark.django_db
def test_create_video_annotation_enqueues_transcode(member_client, member_media):
    """Posting a video file triggers transcode_annotation_video enqueue."""
    video_file = SimpleUploadedFile("clip.mp4", b"\x00" * 64, content_type="video/mp4")
    with patch("papadapi.annotate.views.enqueue") as mock_enqueue:
        resp = member_client.post(
            "/api/v1/annotate/",
            {
                "media_reference_id": str(member_media.uuid),
                "annotation_text": "",
                "media_target": "t=0,10",
                "annotation_type": "video",
                "annotation_video": video_file,
                "tags": "",
            },
            format="multipart",
        )
    assert resp.status_code == 200
    created_id = Annotation.objects.get(uuid=resp.data["uuid"]).id
    mock_enqueue.assert_called_once_with("transcode_annotation_video", created_id)


@pytest.mark.django_db
def test_create_text_annotation_does_not_enqueue(member_client, member_media):
    """Text annotations (no media file) do not trigger any transcode enqueue."""
    with patch("papadapi.annotate.views.enqueue") as mock_enqueue:
        resp = member_client.post(
            "/api/v1/annotate/",
            {
                "media_reference_id": str(member_media.uuid),
                "annotation_text": "note",
                "media_target": "t=0,5",
                "tags": "",
            },
            format="multipart",
        )
    assert resp.status_code == 200
    mock_enqueue.assert_not_called()
