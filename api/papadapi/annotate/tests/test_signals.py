"""
Tests for annotate.signals — on_media_copied handler.

Verifies that firing media_copied duplicates annotations from the old
media UUID to the new one, preserving the is_delete state of each row.
"""

import pytest

from papadapi.annotate.models import Annotation
from papadapi.annotate.signals import on_media_copied
from papadapi.archive.signals import media_copied

OLD = "http://media.test/old"
NEW = "http://media.test/new"


def _ensure_connected() -> None:
    """Connect handler with its stable dispatch_uid (idempotent)."""
    media_copied.connect(
        on_media_copied,
        dispatch_uid="annotate.copy_annotations_on_media_copied",
    )


@pytest.mark.django_db
class TestOnMediaCopied:
    def setup_method(self) -> None:
        _ensure_connected()

    def test_live_annotations_are_copied(self) -> None:
        Annotation.objects.create(
            media_reference_id=OLD, media_target="0,10", annotation_text="first"
        )
        Annotation.objects.create(
            media_reference_id=OLD, media_target="10,20", annotation_text="second"
        )

        media_copied.send(sender=None, old_uuid=OLD, new_uuid=NEW)

        copies = Annotation.objects.filter(media_reference_id=NEW)
        assert copies.count() == 2
        texts = set(copies.values_list("annotation_text", flat=True))
        assert texts == {"first", "second"}

    def test_deleted_annotations_are_also_copied(self) -> None:
        """Handler preserves original behaviour: is_delete state is carried over."""
        Annotation.objects.create(
            media_reference_id=OLD, media_target="0,5", annotation_text="live"
        )
        Annotation.objects.create(
            media_reference_id=OLD, media_target="5,10",
            annotation_text="dead", is_delete=True
        )

        media_copied.send(sender=None, old_uuid=OLD, new_uuid=NEW)

        copies = Annotation.objects.filter(media_reference_id=NEW)
        assert copies.count() == 2
        assert copies.filter(is_delete=True).count() == 1

    def test_no_annotations_no_error(self) -> None:
        media_copied.send(sender=None, old_uuid="http://ghost/", new_uuid="http://ghost-new/")
        count = Annotation.objects.filter(media_reference_id="http://ghost-new/").count()
        assert count == 0

    def test_originals_are_unchanged(self) -> None:
        Annotation.objects.create(
            media_reference_id=OLD, media_target="0,5", annotation_text="orig"
        )

        media_copied.send(sender=None, old_uuid=OLD, new_uuid=NEW)

        assert Annotation.objects.filter(media_reference_id=OLD).count() == 1
