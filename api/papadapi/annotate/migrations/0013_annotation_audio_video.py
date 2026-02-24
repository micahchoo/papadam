from django.db import migrations, models

import papadapi.annotate.models


class Migration(migrations.Migration):

    dependencies = [
        ("annotate", "0012_annotation_type_reply_to_media_ref_uuid"),
    ]

    operations = [
        migrations.AddField(
            model_name="annotation",
            name="annotation_audio",
            field=models.FileField(
                blank=True,
                null=True,
                upload_to=papadapi.annotate.models.upload_to_audio,
                verbose_name="Annotation Audio File",
            ),
        ),
        migrations.AddField(
            model_name="annotation",
            name="annotation_video",
            field=models.FileField(
                blank=True,
                null=True,
                upload_to=papadapi.annotate.models.upload_to_video,
                verbose_name="Annotation Video File",
            ),
        ),
    ]
