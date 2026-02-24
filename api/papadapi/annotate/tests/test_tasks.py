"""Tests for annotate async ARQ task functions."""

import pytest

from papadapi.annotate.models import Annotation
from papadapi.annotate.tasks import delete_annotate_post_schedule


@pytest.mark.django_db(transaction=True)
async def test_delete_annotate_removes_row(annotation):
    """Task hard-deletes the annotation row from the database."""
    annotation_id = annotation.id
    await delete_annotate_post_schedule({}, annotation_id)
    assert not await Annotation.objects.filter(id=annotation_id).aexists()


@pytest.mark.django_db(transaction=True)
async def test_delete_annotate_noop_when_already_gone(annotation):
    """Task is idempotent — silently succeeds when the row is already absent."""
    annotation_id = annotation.id
    await Annotation.objects.filter(id=annotation_id).adelete()
    # Should not raise
    await delete_annotate_post_schedule({}, annotation_id)


@pytest.mark.django_db(transaction=True)
async def test_delete_annotate_leaves_other_annotations_intact(annotation, group):
    """Task only deletes the targeted annotation, not siblings."""
    other = await Annotation.objects.acreate(
        media_reference_id=annotation.media_reference_id,
        annotation_text="sibling",
        media_target="t=0,5",
        group=group,
    )
    await delete_annotate_post_schedule({}, annotation.id)
    assert await Annotation.objects.filter(id=other.id).aexists()
