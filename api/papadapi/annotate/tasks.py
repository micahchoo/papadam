import structlog

from django.conf import settings

from papadapi.annotate.models import Annotation
from papadapi.tasks_compat import db_task

log = structlog.get_logger(__name__)


@db_task()
def delete_annotate_post_schedule(annotation_id):
    annotation = Annotation.objects.get(id=annotation_id)
    log.info("deleting_annotation", annotation_id=annotation_id)
    annotation.delete()
