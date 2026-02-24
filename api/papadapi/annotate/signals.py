"""
annotate/signals.py — handlers for cross-app signals.

annotate is above archive in the dependency graph, so it is allowed
to import from archive.signals (not the other way around).
"""

from papadapi.annotate.models import Annotation
from papadapi.archive.signals import media_copied


def on_media_copied(
    sender: type, old_uuid: str, new_uuid: str, **kwargs: object
) -> None:
    """Duplicate all annotations from old_uuid to new_uuid.

    Preserves the original copy behaviour: PK is cleared so Django
    INSERT-s a new row; is_delete status is preserved as-is.
    """
    for annotation in Annotation.objects.filter(media_reference_id=old_uuid):
        annotation.pk = None
        annotation.media_reference_id = new_uuid
        annotation.save()


media_copied.connect(
    on_media_copied,
    dispatch_uid="annotate.copy_annotations_on_media_copied",
)
