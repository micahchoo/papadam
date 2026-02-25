"""
Tests for annotate view endpoints -- authentication, retrieval, deletion,
and adversarial cases not covered by test_create_update.py or
test_annotation_types.py.
"""

import uuid

import pytest

from papadapi.annotate.models import Annotation


@pytest.mark.django_db
class TestUnauthenticatedAccess:
    """Unauthenticated users cannot create or modify annotations."""

    def test_create_annotation_returns_401(self, api_client, media):
        resp = api_client.post(
            "/api/v1/annotate/",
            {
                "media_reference_id": str(media.uuid),
                "annotation_text": "should fail",
                "media_target": "t=0,10",
            },
        )
        assert resp.status_code == 401

    def test_delete_annotation_returns_401(self, api_client, annotation):
        resp = api_client.delete(f"/api/v1/annotate/{annotation.uuid}/")
        assert resp.status_code == 401


@pytest.mark.django_db
class TestAnnotationRetrieve:
    """Retrieve a single annotation by UUID."""

    def test_retrieve_returns_annotation_fields(self, auth_client, annotation):
        resp = auth_client.get(f"/api/v1/annotate/{annotation.uuid}/")
        assert resp.status_code == 200
        assert resp.data["uuid"] == str(annotation.uuid)
        assert "annotation_text" in resp.data
        assert "media_target" in resp.data
        assert "created_at" in resp.data

    def test_retrieve_nonexistent_uuid_returns_404(self, auth_client):
        fake_uuid = uuid.uuid4()
        resp = auth_client.get(f"/api/v1/annotate/{fake_uuid}/")
        assert resp.status_code == 404


@pytest.mark.django_db
class TestAnnotationsByMedia:
    """List annotations for a specific media UUID."""

    def test_list_annotations_for_media(self, auth_client, member_media):
        # Create two annotations attached to the same media
        Annotation.objects.create(
            media_reference_id=str(member_media.uuid),
            annotation_text="first",
            media_target="t=0,5",
            group=member_media.group,
        )
        Annotation.objects.create(
            media_reference_id=str(member_media.uuid),
            annotation_text="second",
            media_target="t=5,10",
            group=member_media.group,
        )
        resp = auth_client.get(
            f"/api/v1/annotate/search/{member_media.uuid}/"
        )
        assert resp.status_code == 200
        assert len(resp.data) == 2
        texts = {item["annotation_text"] for item in resp.data}
        assert texts == {"first", "second"}

    def test_list_excludes_soft_deleted(self, auth_client, member_media):
        Annotation.objects.create(
            media_reference_id=str(member_media.uuid),
            annotation_text="visible",
            media_target="t=0,5",
            group=member_media.group,
        )
        Annotation.objects.create(
            media_reference_id=str(member_media.uuid),
            annotation_text="deleted",
            media_target="t=5,10",
            group=member_media.group,
            is_delete=True,
        )
        resp = auth_client.get(
            f"/api/v1/annotate/search/{member_media.uuid}/"
        )
        assert resp.status_code == 200
        assert len(resp.data) == 1
        assert resp.data[0]["annotation_text"] == "visible"


@pytest.mark.django_db
class TestAnnotationDelete:
    """Soft-delete via the destroy endpoint."""

    def test_delete_sets_is_delete_flag(self, member_client, member_annotation):
        resp = member_client.delete(
            f"/api/v1/annotate/{member_annotation.uuid}/"
        )
        assert resp.status_code == 204
        member_annotation.refresh_from_db()
        assert member_annotation.is_delete is True

    def test_deleted_annotation_not_in_retrieve(
        self, member_client, member_annotation,
    ):
        member_client.delete(
            f"/api/v1/annotate/{member_annotation.uuid}/"
        )
        resp = member_client.get(
            f"/api/v1/annotate/{member_annotation.uuid}/"
        )
        assert resp.status_code == 404


@pytest.mark.django_db
class TestAdversarial:
    """Edge cases and malformed requests."""

    def test_create_missing_media_reference_id_raises(
        self, member_client, member_media,
    ):
        """Permission class reads data['media_reference_id'] directly --
        a missing key raises MultiValueDictKeyError (uncaught 500)."""
        from django.utils.datastructures import MultiValueDictKeyError

        with pytest.raises(MultiValueDictKeyError):
            member_client.post(
                "/api/v1/annotate/",
                {
                    "annotation_text": "no ref",
                    "media_target": "t=0,5",
                },
            )

    def test_create_with_nonexistent_media_uuid_returns_error(
        self, member_client,
    ):
        fake = str(uuid.uuid4())
        resp = member_client.post(
            "/api/v1/annotate/",
            {
                "media_reference_id": fake,
                "annotation_text": "ghost media",
                "media_target": "t=0,5",
            },
        )
        # Permission check looks up MediaStore -- nonexistent UUID -> 403
        assert resp.status_code == 403
