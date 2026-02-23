from django.conf import settings
from huey.contrib.djhuey import db_task

from papadapi.annotate.models import Annotation


@db_task()
def delete_annotate_post_schedule(annotation_id):
    media = Annotation.objects.get(id=annotation_id)
    print(media)
    media.delete()
