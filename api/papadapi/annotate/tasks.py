"""
annotate/tasks.py — ARQ background tasks for the annotate app.
"""

import structlog

from papadapi.annotate.models import Annotation

log = structlog.get_logger(__name__)


async def delete_annotate_post_schedule(ctx: dict, annotation_id: int) -> None:
    """ARQ task: hard-delete an Annotation row after its soft-delete grace period."""
    deleted, _ = await Annotation.objects.filter(id=annotation_id).adelete()
    if deleted:
        log.info("annotation_deleted", annotation_id=annotation_id)
    else:
        log.warning("annotation_delete_noop", annotation_id=annotation_id,
                    reason="already_gone")
